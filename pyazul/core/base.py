from ..api.client import AzulAPI
from .config import AzulSettings

class BaseService:
    """Base class for all Azul API services."""
    
    def __init__(self, settings: AzulSettings):
        """
        Initialize the service with Azul settings.

        Args:
            settings (AzulSettings): Configuration containing API credentials and endpoints
        """
        self.settings = settings
        self.client = AzulAPI() 