"""
Service for handling DataVault (tokenization) operations with the Azul API.

This service provides methods to create and delete card tokens securely.
"""

from typing import Any, Dict

from ..api.client import AzulAPI

# Removed: from ..core.config import AzulSettings
from ..models.schemas import (
    DataVaultRequestModel,  # Changed from DataVaultCreateModel, DataVaultDeleteModel
)


class DataVaultService:
    """
    Service for managing DataVault tokens (card tokenization).

    Provides methods to create and delete card tokens using Azul's DataVault.
    """

    def __init__(self, api_client: AzulAPI):
        """
        Initialize DataVaultService.

        Args:
            api_client: An instance of AzulAPI for making requests.
        """
        self.api = api_client

    async def create(
        self, token_data: DataVaultRequestModel
    ) -> Dict[str, Any]:  # Changed type to DataVaultRequestModel
        """
        Create a DataVault token for a card.

        Args:
            token_data (DataVaultRequestModel): Data for creating the token.
                                                Ensure TrxType is 'CREATE'.

        Returns:
            Dict[str, Any]: API response containing token details or error

        Raises:
            APIError: If token creation fails or API returns an error
        """
        if token_data.TrxType != "CREATE":
            raise ValueError("TrxType must be CREATE for creating a token.")
        return await self.api._async_request(
            token_data.model_dump(exclude_none=True), operation="ProcessDatavault"
        )

    async def delete(
        self, token_data: DataVaultRequestModel
    ) -> Dict[str, Any]:  # Changed type to DataVaultRequestModel
        """
        Delete a DataVault token.

        Args:
            token_data (DataVaultRequestModel): Data for deleting the token.
                                                Ensure TrxType is 'DELETE'.

        Returns:
            Dict[str, Any]: API response indicating success or error

        Raises:
            APIError: If token deletion fails or API returns an error
        """
        if token_data.TrxType != "DELETE":
            raise ValueError("TrxType must be DELETE for deleting a token.")
        return await self.api._async_request(
            token_data.model_dump(), operation="ProcessDatavault"
        )
