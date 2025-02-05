from enum import Enum


class OutputFormat(str, Enum):
    HTML = "html"
    PDF = "pdf"
    TEXT = "txt"


class ProcessingStatus(str, Enum):
    STARTED = "Started"
    PROCESSING = "Processing"
    COMPLETED = "Completed"
    FAILED = "Failed"
