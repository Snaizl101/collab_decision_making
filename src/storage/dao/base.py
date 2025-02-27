from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, TypeVar, Generic

T = TypeVar('T')


class DataAccessInterface(ABC):
    """
    Interface for data access operations in the Discussion Analysis System.
    Provides methods for storing and retrieving analysis results and related data.
    """

    @abstractmethod
    def store_recording(self, recording_id: str, file_path: Path,
                        duration: int, recording_date: datetime,
                        format: str) -> None:
        """
        Store metadata for a new recording.

        Args:
            recording_id: Unique identifier for the recording
            file_path: Path to the audio file
            duration: Duration in seconds
            recording_date: When the recording was made
            format: Audio format (e.g., 'wav', 'mp3')
        """
        pass

    @abstractmethod
    def store_transcription(self, recording_id: str, segments: List[Dict[str, Any]]) -> None:
        """
        Store transcription segments for a recording.

        Args:
            recording_id: ID of the associated recording
            segments: List of transcription segments, each containing:
                     - speaker_id: ID of the speaker
                     - start_time: Start time in seconds
                     - end_time: End time in seconds
                     - text: Transcribed text
        """
        pass

    @abstractmethod
    def store_topic(self, recording_id: str, topic_data: Dict[str, Any]) -> int:
        """
        Store an identified topic.

        Args:
            recording_id: ID of the associated recording
            topic_data: Topic information containing:
                       - topic_name: Name/title of the topic
                       - start_time: When topic discussion started
                       - end_time: When topic discussion ended
                       - importance_score: Relative importance score

        Returns:
            topic_id: Unique identifier for the stored topic
        """
        pass

    @abstractmethod
    def get_recording_metadata(self, recording_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve recording metadata.

        Args:
            recording_id: ID of the recording

        Returns:
            Dict containing recording metadata or None if not found
        """
        pass

    @abstractmethod
    def get_transcription(self, recording_id: str,
                          start_time: Optional[float] = None,
                          end_time: Optional[float] = None) -> List[Dict[str, Any]]:
        """
        Retrieve transcription segments.

        Args:
            recording_id: ID of the recording
            start_time: Optional start time filter
            end_time: Optional end time filter

        Returns:
            List of transcription segments
        """
        pass

    @abstractmethod
    def get_topics(self, recording_id: str) -> List[Dict[str, Any]]:
        """
        Retrieve all topics for a recording.

        Args:
            recording_id: ID of the recording

        Returns:
            List of topics with their details
        """
        pass

    @abstractmethod
    def get_discussion_summary(self, recording_id: str) -> Dict[str, Any]:
        """
        Retrieve a complete summary of the discussion.

        Args:
            recording_id: ID of the recording

        Returns:
            Dict containing summary information including:
            - topics discussed
            - key arguments
            - points of agreement/disagreement
            - identified gaps
        """
        pass
