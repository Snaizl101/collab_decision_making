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
    """Interface for CLI"""

    @abstractmethod
    def run(self) -> None:
        """
        Start the CLI application.
        Main entry point that runs the CLI
        """
        pass

    @abstractmethod
    def handle_input(self, command: str, args: CLIConfig) -> None:
        """
        Handles user input commands and arguments

        Args:
            command: The command to execute
            args: Dicitionary of command arguments
        """
        pass


