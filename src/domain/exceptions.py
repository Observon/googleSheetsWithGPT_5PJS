"""Custom exceptions for the application."""


class ApplicationError(Exception):
    """Base exception for the application."""

    pass


class GoogleDriveError(ApplicationError):
    """Exception raised when Google Drive operations fail."""

    pass


class OpenAIError(ApplicationError):
    """Exception raised when OpenAI API operations fail."""

    pass


class ConfigError(ApplicationError):
    """Exception raised when configuration is invalid or missing."""

    pass


class ValidationError(ApplicationError):
    """Exception raised when data validation fails."""

    pass
