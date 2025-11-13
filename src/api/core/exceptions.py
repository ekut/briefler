"""Custom exceptions for the Briefler API.

This module defines custom exception classes that provide consistent
error responses across the API.
"""


class APIError(Exception):
    """Base exception for API errors with structured error information."""
    
    def __init__(
        self,
        error: str,
        message: str,
        details: any = None,
        status_code: int = 500
    ):
        """Initialize API error.
        
        Args:
            error: Error type identifier (e.g., "ValidationError")
            message: Human-readable error message
            details: Additional error details (optional)
            status_code: HTTP status code
        """
        self.error = error
        self.message = message
        self.details = details
        self.status_code = status_code
        super().__init__(message)


class ValidationError(APIError):
    """Validation error (400 Bad Request)."""
    
    def __init__(self, message: str, details: any = None):
        super().__init__(
            error="ValidationError",
            message=message,
            details=details,
            status_code=400
        )


class InternalServerError(APIError):
    """Internal server error (500 Internal Server Error)."""
    
    def __init__(self, message: str, details: any = None):
        super().__init__(
            error="InternalServerError",
            message=message,
            details=details,
            status_code=500
        )
