from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Any


class ReportGeneratorInterface(ABC):
    """Interface for report generation"""

    @abstractmethod
    def generate(self, data: Dict[str, Any], output_dir: Path) -> Path:
        """
        Generate a report from the provided data.

        Args:
            data: Analysis data to include in the report
            output_dir: Directory where the report should be saved

        Returns:
            Path: Path to the generated report

        Raises:
            ReportGenerationError: If report generation fails
        """
        pass