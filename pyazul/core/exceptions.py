class AzulError(Exception):
    """Base exception for Azul errors"""

class ValidationError(AzulError):
    """Validation error"""

class APIError(AzulError):
    """API communication error""" 