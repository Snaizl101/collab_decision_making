from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional, Dict, List, Any

from abc import ABC, abstractmethod
from typing import Callable, Dict, Any
from custom_types import OutputFormat, ProcessingStatus


class UserInterface(ABC):
    @abstractmethod
    def start_analysis(self, audio_path: Path,
                       progress_callback: Callable[[Dict[str, Any]], None]) -> str:
        """
        Start analysis with progress callback.

        Args:
            audio_path: Path to audio file
            progress_callback: Function called with status updates
                             Expected format: {
                                 'status': str,
                                 'progress': float,
                                 'message': str
                             }
        Returns:
            str: Session ID
        """

    @abstractmethod
    def generate_report(self, session_id: str, output_dir: Path, format: OutputFormat = OutputFormat.HTML) -> Path:
        """
        Generate and return path to analysis report

        Args:
            session_id: ID of the processing session
            format: Output format enum

        Returns:
            Path: Path to generated report
        """
