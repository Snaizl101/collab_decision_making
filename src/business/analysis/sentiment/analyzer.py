"""
Sentiment analyzer module.
Analyzes emotional tone and sentiment throughout discussions.
Tracks sentiment over time and by speaker.
"""
from typing import List, Dict, Any
from dataclasses import dataclass
from datetime import datetime
from src.business.analysis.base import LLMClientInterface
from src.business.analysis.exceptions import AnalysisError
from src.business.audio.models import TranscriptionSegment


@dataclass
class SentimentResult:
    """
    Dataclass for individual sentiment analysis results.
    Holds sentiment information for a single transcription segment.
    """
    speaker_id: str
    timestamp: float
    sentiment_score: float  # Sentiment score from -1 (negative) to 1 (positive)
    text: str  # The actual text that was analyzed


@dataclass
class SentimentSummary:
    """
    Comprehensive summary of sentiment analysis for an entire discussion.
    Aggregates individual results and provides overview statistics.
    """
    overall_sentiment: float  # Average sentiment across all segments
    sentiment_timeline: List[SentimentResult]  # Chronological list of all sentiment results
    speaker_sentiments: Dict[str, float]  # Average sentiment per speaker
    timestamp: datetime = datetime.now()


class SentimentAnalyzer:
    """Analyzes emotional tone and sentiment in discussions.

    Features:
    - Per-speaker sentiment tracking
    - Timeline-based sentiment analysis
    - Overall discussion mood assessment

    Output:
    - Sentiment scores (-1 to +1)
    - Speaker-specific sentiment profiles
    - Temporal sentiment progression
    """

    def __init__(self, llm_client: LLMClientInterface):
        """
        Initialize the analyzer with an LLM client.

        Args:
            llm_client: Interface to the language model for sentiment analysis
        """
        self.llm_client = llm_client

    async def analyze(self, transcription_segments: List[TranscriptionSegment]) -> SentimentSummary:
        """
        Analyze sentiment in transcription segments and generate a comprehensive summary.

        Args:
            transcription_segments: List of transcription segments to analyze

        Returns:
            SentimentSummary containing overall and per-speaker sentiment analysis

        Raises:
            AnalysisError: If sentiment analysis fails
        """
        try:
            # Analyze each segment individually
            sentiment_results = []
            for segment in transcription_segments:
                # Get sentiment analysis from LLM
                response = await self.llm_client.analyze_sentiment(segment.text)

                # Create sentiment result for this segment
                sentiment_results.append(SentimentResult(
                    speaker_id=segment.speaker,
                    timestamp=(segment.start + segment.end) / 2,  # Use midpoint of segment
                    sentiment_score=float(response['sentiment_score']),
                    text=segment.text
                ))

            # Calculate overall sentiment (average of all scores)
            overall_sentiment = sum(r.sentiment_score for r in sentiment_results) / len(sentiment_results)

            # Calculate per-speaker sentiment
            speaker_sentiments = {}
            speaker_counts = {}

            # First pass: accumulate totals and counts
            for result in sentiment_results:
                if result.speaker_id not in speaker_sentiments:
                    speaker_sentiments[result.speaker_id] = 0
                    speaker_counts[result.speaker_id] = 0
                speaker_sentiments[result.speaker_id] += result.sentiment_score
                speaker_counts[result.speaker_id] += 1

            # Second pass: calculate averages
            for speaker in speaker_sentiments:
                speaker_sentiments[speaker] /= speaker_counts[speaker]

            # Create and return the summary
            return SentimentSummary(
                overall_sentiment=overall_sentiment,
                sentiment_timeline=sentiment_results,
                speaker_sentiments=speaker_sentiments
            )

        except Exception as e:
            raise AnalysisError(f"Sentiment analysis failed: {str(e)}")
