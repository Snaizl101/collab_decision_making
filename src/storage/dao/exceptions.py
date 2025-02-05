class DAOError(Exception):
    """Base exception for all DAO-related errors"""
    pass

class ConnectionError(DAOError):
    """Raised when database connection fails"""
    pass

class QueryError(DAOError):
    """Raised when a database query fails"""
    pass

class DataIntegrityError(DAOError):
    """Raised when data constraints are violated"""
    pass

class RecordNotFoundError(DAOError):
    """Raised when a requested record doesn't exist"""
    pass