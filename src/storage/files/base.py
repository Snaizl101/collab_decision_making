from abc import ABC, abstractmethod
from pathlib import Path
from typing import BinaryIO, Optional


class FileStorageInterface(ABC):
    """Interface for file storage operations"""

    @abstractmethod
    def store_audio(self, file: Path, format: str) -> str:
        """
        Store an audio file and return its unique identifier.

        Args:
            file: Path to the audio file
            format: Audio format (e.g., 'wav', 'mp3', 'm4a')

        Returns:
            str: Unique identifier for the stored file

        Raises:
            FileStorageError: If file storage fails
        """
        pass

    @abstractmethod
    def get_audio(self, file_id: str) -> Path:
        """
        Get path to a stored audio file.

        Args:
            file_id: Unique identifier of the audio file

        Returns:
            Path: Path to the audio file

        Raises:
            FileNotFoundError: If file doesn't exist
            FileStorageError: If retrieval fails
        """
        pass

    @abstractmethod
    def store_report(self, report_id: str, data: bytes, format: str = 'html') -> Path:
        """
        Store a generated report.

        Args:
            report_id: Unique identifier for the report
            data: Report content as bytes
            format: Report format (default: 'html')

        Returns:
            Path: Path to the stored report

        Raises:
            FileStorageError: If storage fails
        """
        pass

    @abstractmethod
    def get_report(self, report_id: str) -> Optional[Path]:
        """
        Get path to a stored report.

        Args:
            report_id: Unique identifier of the report

        Returns:
            Optional[Path]: Path to the report if it exists, None otherwise

        Raises:
            FileStorageError: If retrieval fails
        """
        pass