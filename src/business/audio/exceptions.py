class ProcessingError(Exception):
    """Custom exception for processing errors during audio processing and transcription."""

    def __init__(self, message: str, error_type: str = None, original_error: Exception = None):
        self.message = message
        self.error_type = error_type
        self.original_error = original_error
        super().__init__(self.message)
