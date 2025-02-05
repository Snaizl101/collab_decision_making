class AnalysisError(Exception):
    """Base exception for all analysis errors"""
    pass


class LLMAPIError(AnalysisError):
    """Raised when LLM API calls fail"""
    pass


class ValidationError(AnalysisError):
    """Raised when input validation fails"""
    pass


class TopicAnalysisError(AnalysisError):
    """Raised when topic analysis fails"""
    pass


class ArgumentAnalysisError(AnalysisError):
    """Raised when argument analysis fails"""
    pass


class ArgumentExtractionError(ArgumentAnalysisError):
    """Raised when argument extraction fails"""
    pass


class ThreadStructuringError(ArgumentAnalysisError):
    """Raised when thread structuring fails"""
    pass