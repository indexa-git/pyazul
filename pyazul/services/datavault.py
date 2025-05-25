"""
Service for handling DataVault (tokenization) operations with the Azul API.

This service provides methods to create and delete card tokens securely.
"""

from typing import Any, Dict

from ..api.client import AzulAPI
from ..core.config import AzulSettings
from ..models.schemas import DataVaultCreateModel, DataVaultDeleteModel


class DataVaultService:
    """
    Service for managing DataVault tokens (card tokenization).

    Provides methods to create and delete card tokens using Azul's DataVault.
    """

    def __init__(self, settings: AzulSettings, api_client: AzulAPI):
        """
        Initialize DataVaultService.

        Args:
            settings: Configuration settings for Azul.
            api_client: An instance of AzulAPI for making requests.
        """
        self.settings = settings
        self.api_client = api_client

    async def create(self, token_data: DataVaultCreateModel) -> Dict[str, Any]:
        """
        Create a DataVault token for a card.

        Args:
            token_data (DataVaultCreateModel): Data for creating the token

        Returns:
            Dict[str, Any]: API response containing token details or error

        Raises:
            APIError: If token creation fails or API returns an error
        """
        return await self.api_client._async_request(token_data.model_dump())

    async def delete(self, token_data: DataVaultDeleteModel) -> Dict[str, Any]:
        """
        Delete a DataVault token.

        Args:
            token_data (DataVaultDeleteModel): Data for deleting the token

        Returns:
            Dict[str, Any]: API response indicating success or error

        Raises:
            APIError: If token deletion fails or API returns an error
        """
        return await self.api_client._async_request(token_data.model_dump())
