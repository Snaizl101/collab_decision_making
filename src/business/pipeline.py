import logging
import json
from datetime import datetime
from pathlib import Path

from src.business.audio.processors import CombinedProcessor
from src.business.analysis.topic.analyzer import TopicAnalyzer
from src.business.analysis.sentiment.analyzer import SentimentAnalyzer
from src.storage.dao.sqlite.sqlite_dao import SQLiteDAO
from src.storage.files.local_storage import LocalFileStorage
from src.presentation.reports.generators import HTMLReportGenerator


class Pipeline:
    """Coordinates entire business layer processes in a pipeline.

        Flow:
        1. Process audio file -> transcription
        2. Analyze topics
        3. Analyze sentiment
        4. Store results
        5. Generate report
        """

    def __init__(self,
                 audio_processor: CombinedProcessor,
                 dao: SQLiteDAO,
                 file_storage: LocalFileStorage,
                 topic_analyzer: TopicAnalyzer,
                 sentiment_analyzer: SentimentAnalyzer,
                 report_generator: HTMLReportGenerator):
        self.audio_processor = audio_processor
        self.dao = dao
        self.file_storage = file_storage
        self.topic_analyzer = topic_analyzer
        self.sentiment_analyzer = sentiment_analyzer
        self.report_generator = report_generator
        self.logger = logging.getLogger(__name__)

        # Create debug output directory
        self.debug_dir = Path("debug_output")
        self.debug_dir.mkdir(exist_ok=True)

    def _save_debug_output(self, prefix: str, data: dict):
        """Save intermediate results for debugging"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        debug_file = self.debug_dir / f"{prefix}_{timestamp}.json"
        try:
            with open(debug_file, 'w') as f:
                json.dump(data, f, indent=2, default=str)
            self.logger.debug(f"Debug output saved to {debug_file}")
        except Exception as e:
            self.logger.error(f"Failed to save debug output: {e}")

    async def process(self, audio_path: Path) -> Path:
        # Wrap processing in try/except to catch and log errors
        try:
            session_start = datetime.now()
            self.logger.info(f"Starting processing session at {session_start}")

            # 1. Process audio and get transcription
            self.logger.info("Processing audio file...")
            processing_result = self.audio_processor.process_audio(
                audio_path,
                progress_callback=lambda progress, status: self.logger.info(f"Audio processing: {status}")
            )

            # Save transcription debug output
            transcription_segments_dict = [
                {
                    'speaker_id': segment.speaker,
                    'start_time': segment.start,
                    'end_time': segment.end,
                    'text': segment.text,
                }
                for segment in processing_result.transcription_segments
            ]
            self._save_debug_output("transcription", {
                'metadata': processing_result.metadata.__dict__,
                'segments': transcription_segments_dict
            })

            # 2. Store audio file and metadata
            self.logger.info("Storing audio file and metadata...")
            file_id = self.file_storage.store_audio(audio_path, format=audio_path.suffix[1:])
            self.dao.store_recording(
                recording_id=file_id,
                file_path=audio_path,
                duration=processing_result.metadata.duration,
                recording_date=datetime.now(),
                format=processing_result.metadata.format
            )

            self.dao.store_transcription(file_id, transcription_segments_dict)
            self.logger.info(f"Stored transcription with {len(transcription_segments_dict)} segments")

            # 3. Analyze topics
            self.logger.info("Starting topic analysis...")
            topic_result = await self.topic_analyzer.analyze(processing_result.transcription_segments)

            # Save topic analysis debug output
            self._save_debug_output("topic_analysis", {
                'topics': [topic.__dict__ for topic in topic_result.topics],
                'hierarchy': topic_result.hierarchy
            })

            # 4. Perform sentiment analysis
            self.logger.info("Starting sentiment analysis...")
            sentiment_result = await self.sentiment_analyzer.analyze(processing_result.transcription_segments)

            # Save sentiment analysis debug output
            self._save_debug_output("sentiment_analysis", {
                'overall_sentiment': sentiment_result.overall_sentiment,
                'timeline': [
                    {
                        'speaker_id': r.speaker_id,
                        'timestamp': r.timestamp,
                        'sentiment_score': r.sentiment_score,
                        'text': r.text
                    }
                    for r in sentiment_result.sentiment_timeline
                ],
                'speaker_sentiments': sentiment_result.speaker_sentiments
            })

            # Store sentiment analysis results
            for result in sentiment_result.sentiment_timeline:
                self.dao.store_sentiment(file_id, {
                    'speaker_id': result.speaker_id,
                    'timestamp': result.timestamp,
                    'sentiment_score': result.sentiment_score,
                    'text': result.text
                })

            # Store topics
            topics_dict = []
            for topic in topic_result.topics:
                topic_id = self.dao.store_topic(file_id, {
                    'topic_name': topic.name,
                    'start_time': topic.start_time,
                    'end_time': topic.end_time,
                })
                topics_dict.append({
                    'id': topic_id,
                    'name': topic.name,
                    'start_time': topic.start_time,
                    'end_time': topic.end_time,
                })

            # 5. Generate report
            self.logger.info("Generating final report...")
            discussion_data = {
                'recording_id': file_id,
                'metadata': processing_result.metadata.__dict__,
                'transcription': transcription_segments_dict,
                'topics': topics_dict,
                'sentiment': {
                    'overall_sentiment': sentiment_result.overall_sentiment,
                    'sentiment_timeline': [
                        {
                            'speaker_id': r.speaker_id,
                            'timestamp': r.timestamp,
                            'sentiment_score': r.sentiment_score,
                            'text': r.text
                        }
                        for r in sentiment_result.sentiment_timeline
                    ],
                    'speaker_sentiments': sentiment_result.speaker_sentiments
                },
                'timestamp': datetime.now().isoformat()
            }

            # Save final data for debugging
            self._save_debug_output("final_data", discussion_data)

            report_path = self.report_generator.generate(discussion_data, self.file_storage.reports_path)

            session_duration = datetime.now() - session_start
            self.logger.info(f"Processing completed in {session_duration}. "
                             f"Report generated at: {report_path}")

            return report_path

        except Exception as e:
            self.logger.error(f"Pipeline processing failed: {e}", exc_info=True)
            raise
