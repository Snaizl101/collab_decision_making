import os
import shutil
import uuid
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

from .base import FileStorageInterface
from .exceptions import FileStorageError, InvalidFormatError, StorageOperationError


class LocalFileStorage(FileStorageInterface):
    """Implementation of file storage using local filesystem"""

    ALLOWED_AUDIO_FORMATS = {'wav', 'mp3', 'm4a'}
    ALLOWED_REPORT_FORMATS = {'html', 'pdf', 'txt'}

    def __init__(self, base_path: Path):
        """
        Initialize local file storage.

        Args:
            base_path: Base directory for file storage
        """
        self.base_path = base_path
        self.audio_path = base_path / 'audio'
        self.reports_path = base_path / 'reports'
        self.logger = logging.getLogger(__name__)
        self._initialize_storage()

    def _initialize_storage(self) -> None:
        """Initialize storage directories"""
        try:
            self.audio_path.mkdir(parents=True, exist_ok=True)
            self.reports_path.mkdir(parents=True, exist_ok=True)
            self.logger.info("Storage directories initialized")
        except Exception as e:
            self.logger.error(f"Failed to initialize storage directories: {e}")
            raise StorageOperationError(f"Storage initialization failed: {str(e)}")

    def _validate_audio_format(self, format: str) -> None:
        """
        Validate audio format.

        Args:
            format: Audio format to validate

        Raises:
            InvalidFormatError: If format is not supported
        """
        if format.lower() not in self.ALLOWED_AUDIO_FORMATS:
            raise InvalidFormatError(
                f"Unsupported audio format: {format}. "
                f"Allowed formats: {', '.join(self.ALLOWED_AUDIO_FORMATS)}"
            )

    def _validate_report_format(self, format: str) -> None:
        """
        Validate report format.

        Args:
            format: Report format to validate

        Raises:
            InvalidFormatError: If format is not supported
        """
        if format.lower() not in self.ALLOWED_REPORT_FORMATS:
            raise InvalidFormatError(
                f"Unsupported report format: {format}. "
                f"Allowed formats: {', '.join(self.ALLOWED_REPORT_FORMATS)}"
            )

    def _generate_file_id(self) -> str:
        """Generate a unique file identifier"""
        return str(uuid.uuid4())

    def store_audio(self, file: Path, format: str) -> str:
        """Store an audio file and return its unique identifier"""
        try:
            self._validate_audio_format(format)

            if not file.exists():
                raise FileNotFoundError(f"Audio file not found: {file}")

            file_id = self._generate_file_id()
            destination = self.audio_path / f"{file_id}.{format.lower()}"

            shutil.copy2(file, destination)
            self.logger.info(f"Stored audio file: {destination}")

            return file_id

        except InvalidFormatError:
            raise
        except FileNotFoundError:
            raise
        except Exception as e:
            self.logger.error(f"Failed to store audio file: {e}")
            raise StorageOperationError(f"Failed to store audio file: {str(e)}")

    def get_audio(self, file_id: str) -> Path:
        """Get path to a stored audio file"""
        try:
            # Search for file with any allowed format
            for format in self.ALLOWED_AUDIO_FORMATS:
                file_path = self.audio_path / f"{file_id}.{format}"
                if file_path.exists():
                    return file_path

            raise FileNotFoundError(f"Audio file not found: {file_id}")

        except FileNotFoundError:
            raise
        except Exception as e:
            self.logger.error(f"Failed to retrieve audio file: {e}")
            raise StorageOperationError(f"Failed to retrieve audio file: {str(e)}")

    def store_report(self, report_id: str, data: bytes, format: str = 'html') -> Path:
        """Store a generated report"""
        try:
            self._validate_report_format(format)

            # Create timestamped directory for report
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_dir = self.reports_path / report_id / timestamp
            report_dir.mkdir(parents=True, exist_ok=True)

            report_path = report_dir / f"report.{format.lower()}"

            # Write report data
            report_path.write_bytes(data)
            self.logger.info(f"Stored report: {report_path}")

            return report_path

        except InvalidFormatError:
            raise
        except Exception as e:
            self.logger.error(f"Failed to store report: {e}")
            raise StorageOperationError(f"Failed to store report: {str(e)}")

    def get_report(self, report_id: str) -> Optional[Path]:
        """Get path to the latest version of a stored report"""
        try:
            report_base = self.reports_path / report_id
            if not report_base.exists():
                return None

            # Get latest report version (based on timestamp directory)
            versions = sorted(report_base.iterdir(), reverse=True)
            if not versions:
                return None

            latest_version = versions[0]

            # Find report file in the latest version directory
            report_files = list(latest_version.glob("report.*"))
            if not report_files:
                return None

            return report_files[0]

        except Exception as e:
            self.logger.error(f"Failed to retrieve report: {e}")
            raise StorageOperationError(f"Failed to retrieve report: {str(e)}")

    def cleanup_old_reports(self, report_id: str, keep_versions: int = 5) -> None:
        """
        Clean up old versions of a report, keeping only the specified number of latest versions.

        Args:
            report_id: Report identifier
            keep_versions: Number of latest versions to keep
        """
        try:
            report_base = self.reports_path / report_id
            if not report_base.exists():
                return

            # Get all versions sorted by timestamp
            versions = sorted(report_base.iterdir(), reverse=True)

            # Remove old versions
            for old_version in versions[keep_versions:]:
                shutil.rmtree(old_version)
                self.logger.info(f"Removed old report version: {old_version}")

        except Exception as e:
            self.logger.error(f"Failed to cleanup old reports: {e}")
            raise StorageOperationError(f"Failed to cleanup old reports: {str(e)}")