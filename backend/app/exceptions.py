"""Custom exceptions for the application."""
from typing import Any, Optional


class AppException(Exception):
    """Base exception for application errors."""

    def __init__(self, message: str, status_code: int = 500):
        """
        Initialize application exception.

        Args:
            message: Error message
            status_code: HTTP status code to return
        """
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class ValidationError(AppException):
    """Invalid input data."""

    def __init__(self, message: str):
        """
        Initialize validation error.

        Args:
            message: Validation error message
        """
        super().__init__(message, status_code=400)


class NotFoundError(AppException):
    """Resource not found."""

    def __init__(self, resource: str, id: Any):
        """
        Initialize not found error.

        Args:
            resource: Resource type (e.g., "Bookmark", "Widget")
            id: Resource identifier
        """
        super().__init__(f"{resource} with id {id} not found", status_code=404)


class ExternalServiceError(AppException):
    """External API call failed."""

    def __init__(self, service: str, message: str):
        """
        Initialize external service error.

        Args:
            service: Name of the external service
            message: Error details
        """
        super().__init__(
            f"Failed to fetch data from {service}: {message}",
            status_code=502
        )


class ConfigurationError(AppException):
    """Invalid configuration."""

    def __init__(self, message: str):
        """
        Initialize configuration error.

        Args:
            message: Configuration error details
        """
        super().__init__(message, status_code=500)


class WidgetError(AppException):
    """Widget operation failed."""

    def __init__(self, widget_id: str, message: str, status_code: int = 500):
        """
        Initialize widget error.

        Args:
            widget_id: Widget identifier
            message: Error details
            status_code: HTTP status code (default: 500)
        """
        super().__init__(f"Widget '{widget_id}': {message}", status_code=status_code)


class CacheError(AppException):
    """Cache operation failed."""

    def __init__(self, message: str):
        """
        Initialize cache error.

        Args:
            message: Cache error details
        """
        super().__init__(f"Cache error: {message}", status_code=500)


class DatabaseError(AppException):
    """Database operation failed."""

    def __init__(self, message: str):
        """
        Initialize database error.

        Args:
            message: Database error details
        """
        super().__init__(f"Database error: {message}", status_code=500)
