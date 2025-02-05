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
                     - confidence: Confidence score of transcription
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
    def store_argument(self, recording_id: str, topic_id: int,
                       argument_data: Dict[str, Any]) -> int:
        """
        Store an analyzed argument.

        Args:
            recording_id: ID of the associated recording
            topic_id: ID of the related topic
            argument_data: Argument information containing:
                         - speaker_id: ID of the speaker
                         - start_time: Start time of the argument
                         - end_time: End time of the argument
                         - argument_text: The argument content
                         - argument_type: Type of argument
                         - conclusion: Argument conclusion

        Returns:
            argument_id: Unique identifier for the stored argument
        """
        pass

    @abstractmethod
    def store_agreement(self, recording_id: str, argument_id: int,
                        agreement_data: Dict[str, Any]) -> int:
        """
        Store agreement/disagreement information.

        Args:
            recording_id: ID of the associated recording
            argument_id: ID of the related argument
            agreement_data: Agreement information containing:
                          - speaker_id: ID of the responding speaker
                          - agreement_type: Type of response (agree/disagree)
                          - confidence_score: Confidence in the analysis
                          - timestamp: When the agreement was expressed

        Returns:
            agreement_id: Unique identifier for the stored agreement
        """
        pass

    @abstractmethod
    def store_gap(self, recording_id: str, topic_id: Optional[int],
                  gap_data: Dict[str, Any]) -> int:
        """
        Store identified discussion gaps or suggestions.

        Args:
            recording_id: ID of the associated recording
            topic_id: Optional ID of the related topic
            gap_data: Gap information containing:
                     - gap_type: Type of gap identified
                     - description: Description of the gap
                     - importance_score: Relative importance

        Returns:
            gap_id: Unique identifier for the stored gap
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
    def get_arguments(self, recording_id: str,
                      topic_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Retrieve arguments for a recording.

        Args:
            recording_id: ID of the recording
            topic_id: Optional topic filter

        Returns:
            List of arguments with their details
        """
        pass

    @abstractmethod
    def get_agreements(self, recording_id: str,
                       argument_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Retrieve agreements for a recording.

        Args:
            recording_id: ID of the recording
            argument_id: Optional argument filter

        Returns:
            List of agreements with their details
        """
        pass

    @abstractmethod
    def get_gaps(self, recording_id: str,
                 topic_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Retrieve identified gaps for a recording.

        Args:
            recording_id: ID of the recording
            topic_id: Optional topic filter

        Returns:
            List of gaps with their details
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
