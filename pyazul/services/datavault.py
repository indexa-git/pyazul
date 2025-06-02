"""
DataVault service for PyAzul.

This module provides services for managing card tokenization through Azul's DataVault,
including creating tokens, deleting tokens, and processing token-based payments.
"""

import logging
from typing import Any, Dict

from ..api.client import AzulAPI
from ..core.config import AzulSettings
from ..core.exceptions import AzulError
from ..models.datavault import TokenError, TokenRequest, TokenResponse, TokenSuccess

_logger = logging.getLogger(__name__)


class DataVaultService:
    """Service for managing DataVault tokenization operations."""

    def __init__(self, client: AzulAPI, settings: AzulSettings):
        """Initialize the DataVault service with API client and settings."""
        self.client = client
        self.settings = settings

    async def create_token(self, request: TokenRequest) -> TokenResponse:
        """
        Create a new DataVault token for a credit card.

        Args:
            request: Token creation request with card details

        Returns:
            TokenResponse (either TokenSuccess or TokenError)

        Raises:
            AzulError: If token creation fails
        """
        try:
            _logger.info("Creating DataVault token")

            if request.TrxType != "CREATE":
                raise AzulError("TrxType must be CREATE for token creation")

            response = await self.client.post(
                "/webservices/JSON/default.aspx?ProcessDatavault",
                request.model_dump(exclude_none=True),
            )

            # Parse response based on success/failure
            if response.get("IsoCode") == "00":
                _logger.info("DataVault token created successfully")
                return TokenSuccess.from_api_response(response)
            else:
                _logger.warning("DataVault token creation failed")
                return TokenError.from_api_response(response)

        except Exception as e:
            _logger.error(f"DataVault token creation failed: {e}")
            raise AzulError(f"DataVault token creation failed: {e}") from e

    async def delete_token(self, request: TokenRequest) -> TokenResponse:
        """
        Delete an existing DataVault token.

        Args:
            request: Token deletion request with token ID

        Returns:
            TokenResponse (either TokenSuccess or TokenError)

        Raises:
            AzulError: If token deletion fails
        """
        try:
            _logger.info("Deleting DataVault token")

            if request.TrxType != "DELETE":
                raise AzulError("TrxType must be DELETE for token deletion")

            response = await self.client.post(
                "/webservices/JSON/default.aspx?ProcessDatavault",
                request.model_dump(exclude_none=True),
            )

            # Parse response based on success/failure
            if response.get("IsoCode") == "00":
                _logger.info("DataVault token deleted successfully")
                return TokenSuccess.from_api_response(response)
            else:
                _logger.warning("DataVault token deletion failed")
                return TokenError.from_api_response(response)

        except Exception as e:
            _logger.error(f"DataVault token deletion failed: {e}")
            raise AzulError(f"DataVault token deletion failed: {e}") from e

    async def process_datavault_request(self, request: TokenRequest) -> TokenResponse:
        """
        Process a DataVault request (CREATE or DELETE).

        Args:
            request: DataVault request model

        Returns:
            TokenResponse based on operation result

        Raises:
            AzulError: If the request processing fails
        """
        if request.TrxType == "CREATE":
            return await self.create_token(request)
        elif request.TrxType == "DELETE":
            return await self.delete_token(request)
        else:
            raise AzulError(f"Unsupported TrxType: {request.TrxType}")

    async def get_token_info(self, token: str) -> Dict[str, Any]:
        """
        Get information about a DataVault token.

        Args:
            token: The DataVault token to query

        Returns:
            Token information dictionary

        Raises:
            AzulError: If token query fails
        """
        try:
            _logger.info("Querying DataVault token information")
            # This would be implementation specific based on Azul's API
            # Currently using a placeholder implementation
            raise NotImplementedError("Token info query not yet implemented")
        except Exception as e:
            _logger.error(f"DataVault token query failed: {e}")
            raise AzulError(f"DataVault token query failed: {e}") from e
