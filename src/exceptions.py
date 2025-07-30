"""
Custom exceptions for the Pachinko Revenue Calculator.

This module defines all custom exceptions used throughout the application
to avoid circular import issues.
"""

from enum import Enum


class ErrorSeverity(Enum):
    """Error severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorCategory(Enum):
    """Error category types."""
    SYSTEM = "system"
    DATABASE = "database"
    AUTHENTICATION = "authentication"
    VALIDATION = "validation"
    UI = "ui"
    NETWORK = "network"
    SECURITY = "security"


class DatabaseError(Exception):
    """Custom exception for database-related errors."""

    def __init__(self, message: str, original_error: Exception = None):
        """
        Initialize database error.

        Args:
            message: Error message
            original_error: Original exception that caused this error
        """
        super().__init__(message)
        self.original_error = original_error


class ValidationError(Exception):
    """Custom exception for validation errors."""

    def __init__(self, message: str, field: str = None):
        """
        Initialize validation error.

        Args:
            message: Error message
            field: Field name that failed validation
        """
        super().__init__(message)
        self.field = field


class AuthenticationError(Exception):
    """Custom exception for authentication-related errors."""

    def __init__(self, message: str, error_code: str = None):
        """
        Initialize authentication error.

        Args:
            message: Error message
            error_code: Specific error code
        """
        super().__init__(message)
        self.error_code = error_code


class ConfigurationError(Exception):
    """Custom exception for configuration-related errors."""

    def __init__(self, message: str, config_key: str = None):
        """
        Initialize configuration error.

        Args:
            message: Error message
            config_key: Configuration key that caused the error
        """
        super().__init__(message)
        self.config_key = config_key
