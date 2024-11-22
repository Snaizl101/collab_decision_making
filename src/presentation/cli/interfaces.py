from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Dict, Any


@dataclass
class CLIConfig:
    """Basic class for CLI input options"""
    input_dir: Path
    output_dir: Path
    verbose: bool = False


class CLIInterface(ABC):
    @abstractmethod
    def run(self) -> None:
        """Main CLI entrypoint"""
        pass

    @abstractmethod
    def process(self, input_dir: str, output_dir: str, verbose: bool) -> None:
        """Process meeting recordings"""
        pass

    @abstractmethod
    def status(self) -> None:
        """Show processing status"""
        pass

    @abstractmethod
    def report(self) -> None:
        """Generate analysis report"""
        pass

    @abstractmethod
    def display_status(self, status: str, progress: Optional[float] = None) -> None:
        """Display processing status"""
        pass

    @abstractmethod
    def display_error(self, error: str) -> None:
        """Display error messages"""
        pass

    @abstractmethod
    def cleanup(self) -> None:
        """Cleanup operations"""
        pass


