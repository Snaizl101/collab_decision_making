# src/business/analysis/sentiment/analyzer.py

from typing import List, Dict, Any
from dataclasses import dataclass
from datetime import datetime
from business.analysis.base import LLMClientInterface
from business.analysis.exceptions import AnalysisError
from business.audio.models import TranscriptionSegment


@dataclass
class SentimentResult:
    """Results from sentiment analysis"""
    speaker_id: str
    timestamp: float
    sentiment_score: float  # -1 (very negative) to 1 (very positive)
    confidence: float
    text: str


@dataclass
class SentimentSummary:
    """Summary of sentiment analysis for the entire discussion"""
    overall_sentiment: float
    sentiment_timeline: List[SentimentResult]
    speaker_sentiments: Dict[str, float]
    timestamp: datetime = datetime.now()


class SentimentAnalyzer:
    """Analyzes sentiment in discussion transcripts"""

    def __init__(self, llm_client: LLMClientInterface):
        self.llm_client = llm_client

    async def analyze(self, transcription_segments: List[TranscriptionSegment]) -> SentimentSummary:
        """
        Analyze sentiment in transcription segments.

        Args:
            transcription_segments: List of transcription segments

        Returns:
            SentimentSummary containing sentiment analysis results
        """
        try:
            sentiment_results = []
            for segment in transcription_segments:
                # Get sentiment analysis from LLM
                response = await self.llm_client.analyze_sentiment(segment.text)

                sentiment_results.append(SentimentResult(
                    speaker_id=segment.speaker,
                    timestamp=(segment.start + segment.end) / 2,
                    sentiment_score=float(response['sentiment_score']),
                    confidence=float(response['confidence']),
                    text=segment.text
                ))

            # Calculate overall sentiment
            overall_sentiment = sum(r.sentiment_score for r in sentiment_results) / len(sentiment_results)

            # Calculate per-speaker sentiment
            speaker_sentiments = {}
            speaker_counts = {}
            for result in sentiment_results:
                if result.speaker_id not in speaker_sentiments:
                    speaker_sentiments[result.speaker_id] = 0
                    speaker_counts[result.speaker_id] = 0
                speaker_sentiments[result.speaker_id] += result.sentiment_score
                speaker_counts[result.speaker_id] += 1

            # Average sentiment per speaker
            for speaker in speaker_sentiments:
                speaker_sentiments[speaker] /= speaker_counts[speaker]

            return SentimentSummary(
                overall_sentiment=overall_sentiment,
                sentiment_timeline=sentiment_results,
                speaker_sentiments=speaker_sentiments
            )

        except Exception as e:
            raise AnalysisError(f"Sentiment analysis failed: {str(e)}")