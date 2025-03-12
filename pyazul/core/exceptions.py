class AzulError(Exception):
    """Base exception for Azul errors"""
    pass

class APIError(AzulError):
    """Exception raised for API errors"""
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)

class AzulResponseError(AzulError):
    """Exception raised when Azul returns an error response"""
    def __init__(self, message: str, response_data: dict = None):
        self.message = message
        self.response_data = response_data or {}
        super().__init__(self.message)

class ValidationError(AzulError):
    """Exception raised for validation errors"""
    def __init__(self, message: str, errors: dict = None):
        self.message = message
        self.errors = errors or {}
        super().__init__(self.message)

class ConfigurationError(AzulError):
    """Exception raised for configuration errors"""
    pass

class SSLError(AzulError):
    """Exception raised for SSL configuration errors"""
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message) 