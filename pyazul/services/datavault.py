from ..core.base import BaseService
from ..models.schemas import DataVaultCreateModel, DataVaultDeleteModel
from typing import Dict, Any
from ..core.config import AzulSettings

class DataVaultService(BaseService):
    """
    Service for managing card tokenization through Azul's DataVault.
    Provides functionality to:
    - Create tokens from card data
    - Delete existing tokens
    - Use tokens for transactions
    
    This service helps maintain PCI compliance by storing card data securely
    in Azul's DataVault instead of your own systems.

    Attributes:
        client (AzulAPI): HTTP client for making API requests
        settings (AzulSettings): Configuration settings for Azul API
    """

    def __init__(self, settings: AzulSettings):
        """
        Initialize the DataVault service with Azul settings.

        Args:
            settings (AzulSettings): Configuration containing API credentials and endpoints
        """
        super().__init__(settings)

    async def create(self, data: DataVaultCreateModel) -> Dict[str, Any]:
        """
        Create a new token from card data in DataVault.

        Args:
            data (DataVaultCreateModel): Card data to tokenize including:
                - Card number
                - Expiration date
                - Merchant ID

        Returns:
            Dict[str, Any]: API response containing:
                - DataVaultToken: Generated token for future use
                - IsoCode: '00' indicates success
                - ResponseMessage: Status message

        Raises:
            APIError: If token creation fails or API returns an error
        """
        return await self.client._async_request(data.model_dump(), operation='ProcessDatavault')
    
    async def delete(self, data: DataVaultDeleteModel) -> Dict[str, Any]:
        """
        Delete an existing token from DataVault.

        Args:
            data (DataVaultDeleteModel): Token deletion data including:
                - DataVaultToken: Token to delete
                - Merchant ID

        Returns:
            Dict[str, Any]: API response containing:
                - IsoCode: '00' indicates successful deletion
                - ResponseMessage: Status message

        Raises:
            APIError: If deletion fails or API returns an error
                     Common error: Token does not exist
        """
        return await self.client._async_request(data.model_dump(), operation='ProcessDatavault')