from enum import Enum


class OutputFormat(Enum):
    """Supported output formats for reports"""
    HTML = 'html'
    PDF = 'pdf'


class ProcessingStatus(Enum):
    """Status of processing tasks"""
    PENDING = 'pending'
    PROCESSING = 'processing'
    COMPLETED = 'completed'
    FAILED = 'failed'
