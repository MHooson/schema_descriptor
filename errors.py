"""
Custom exceptions for the Schema Descriptor application.
Provides a consistent error handling mechanism across the application.
"""

class SchemaDescriptorError(Exception):
    """Base exception for all application-specific errors."""
    def __init__(self, message="An error occurred in the Schema Descriptor application"):
        self.message = message
        super().__init__(self.message)

# Authentication errors
class AuthenticationError(SchemaDescriptorError):
    """Raised when authentication with a service fails."""
    def __init__(self, message="Authentication failed", service=None, details=None):
        self.service = service
        self.details = details
        error_msg = f"{message}"
        if service:
            error_msg += f" for {service}"
        if details:
            error_msg += f": {details}"
        super().__init__(error_msg)

# BigQuery errors
class BigQueryError(SchemaDescriptorError):
    """Raised when a BigQuery operation fails."""
    def __init__(self, message="BigQuery operation failed", operation=None, details=None):
        self.operation = operation
        self.details = details
        error_msg = f"{message}"
        if operation:
            error_msg += f" during {operation}"
        if details:
            error_msg += f": {details}"
        super().__init__(error_msg)

# LLM errors
class LLMError(SchemaDescriptorError):
    """Raised when an LLM operation fails."""
    def __init__(self, message="LLM operation failed", operation=None, details=None):
        self.operation = operation
        self.details = details
        error_msg = f"{message}"
        if operation:
            error_msg += f" during {operation}"
        if details:
            error_msg += f": {details}"
        super().__init__(error_msg)

# Input validation errors
class ValidationError(SchemaDescriptorError):
    """Raised when input validation fails."""
    def __init__(self, message="Input validation failed", field=None, details=None):
        self.field = field
        self.details = details
        error_msg = f"{message}"
        if field:
            error_msg += f" for {field}"
        if details:
            error_msg += f": {details}"
        super().__init__(error_msg)