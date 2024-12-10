from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional, Dict, Any


class UserInterface(ABC):
    """Base interface for user interactions"""

    @abstractmethod
    def process_audio(self, input_dir: Path, output_dir: Path, verbose: bool = False) -> None:
        """
        Process audio files from input directory

        Args:
            input_dir: Directory containing audio files
            output_dir: Directory for output files
            verbose: Whether to show detailed progress
        """
        pass

    @abstractmethod
    def generate_report(self, session_id: str, format: str = 'html') -> None:
        """
        Generate analysis report

        Args:
            session_id: ID of the processing session
            format: Output format (html, pdf)
        """
        pass

    @abstractmethod
    def show_status(self, session_id: Optional[str] = None) -> None:
        """
        Show processing status

        Args:
            session_id: Optional specific session to show status for
        """
        pass

    @abstractmethod
    def display_progress(self, message: str, percentage: Optional[float] = None) -> None:
        """
        Display progress information

        Args:
            message: Progress message to display
            percentage: Optional completion percentage
        """
        pass

    @abstractmethod
    def display_error(self, error: str) -> None:
        """
        Display error message

        Args:
            error: Error message to display
        """
        pass