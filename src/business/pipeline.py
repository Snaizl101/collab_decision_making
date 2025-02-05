import logging
import json
from datetime import datetime
from pathlib import Path

from src.business.audio.processors import CombinedProcessor
from src.business.analysis.topic.analyzer import TopicAnalyzer
from src.storage.dao.sqlite.sqlite_dao import SQLiteDAO
from src.storage.files.local_storage import LocalFileStorage
from src.presentation.reports.generators import HTMLReportGenerator

class Pipeline:
    def __init__(self,
                 audio_processor: CombinedProcessor,
                 dao: SQLiteDAO,
                 file_storage: LocalFileStorage,
                 topic_analyzer: TopicAnalyzer,
                 report_generator: HTMLReportGenerator):
        self.audio_processor = audio_processor
        self.dao = dao
        self.file_storage = file_storage
        self.topic_analyzer = topic_analyzer
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
                    'confidence': segment.confidence
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
            try:
                topic_result = await self.topic_analyzer.analyze(processing_result.transcription_segments)
                # Save topic analysis debug output
                self._save_debug_output("topic_analysis", {
                    'topics': [topic.__dict__ for topic in topic_result.topics],
                    'hierarchy': topic_result.hierarchy
                })
            except Exception as e:
                self.logger.error("Topic analysis failed!")
                self.logger.error("Last 5 transcription segments for debugging:")
                for segment in transcription_segments_dict[-5:]:
                    self.logger.error(f"[{segment['start_time']:.2f}-{segment['end_time']:.2f}] "
                                      f"{segment['speaker_id']}: {segment['text']}")
                raise

            # Store topics
            topics_dict = []
            for topic in topic_result.topics:
                topic_id = self.dao.store_topic(file_id, {
                    'topic_name': topic.name,
                    'start_time': topic.start_time,
                    'end_time': topic.end_time,
                    'importance_score': topic.importance_score
                })
                topics_dict.append({
                    'id': topic_id,
                    'name': topic.name,
                    'start_time': topic.start_time,
                    'end_time': topic.end_time,
                    'importance_score': topic.importance_score
                })

            self.logger.info(f"Stored {len(topics_dict)} topics")

            # 4. Generate report
            self.logger.info("Generating final report...")
            discussion_data = {
                'recording_id': file_id,
                'metadata': processing_result.metadata.__dict__,
                'transcription': transcription_segments_dict,
                'topics': topics_dict,
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