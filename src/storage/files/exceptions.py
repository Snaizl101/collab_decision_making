class FileStorageError(Exception):
    """Base exception for file storage errors"""
    pass

class InvalidFormatError(FileStorageError):
    """Raised when file format is not supported"""
    pass

class StorageOperationError(FileStorageError):
    """Raised when a storage operation fails"""
    pass