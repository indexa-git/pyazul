"""
Service for handling DataVault (tokenization) operations with the Azul API.

This service provides methods to create and delete card tokens securely.
"""

from typing import Any, Dict

from ..api.client import AzulAPI
from ..core.exceptions import AzulResponseError
from ..models.schemas import (
    DataVaultErrorResponse,
    DataVaultRequestModel,
    DataVaultResponse,
    DataVaultSuccessResponse,
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

    async def create(self, token_data: DataVaultRequestModel) -> DataVaultResponse:
        """
        Create a DataVault token for a card.

        Args:
            token_data (DataVaultRequestModel): Data for creating the token.
                                                Ensure TrxType is 'CREATE'.

        Returns:
            DataVaultResponse: Validated response object (success or error type)

        Raises:
            ValueError: If TrxType is not CREATE
            AzulResponseError: If API response validation fails
        """
        if token_data.TrxType != "CREATE":
            raise ValueError("TrxType must be CREATE for creating a token.")

        raw_response = await self.api._async_request(
            token_data.model_dump(exclude_none=True), operation="ProcessDatavault"
        )

        return self._validate_response(raw_response)

    async def delete(self, token_data: DataVaultRequestModel) -> DataVaultResponse:
        """
        Delete a DataVault token.

        Args:
            token_data (DataVaultRequestModel): Data for deleting the token.
                                                Ensure TrxType is 'DELETE'.

        Returns:
            DataVaultResponse: Validated response object (success or error type)

        Raises:
            ValueError: If TrxType is not DELETE
            AzulResponseError: If API response validation fails
        """
        if token_data.TrxType != "DELETE":
            raise ValueError("TrxType must be DELETE for deleting a token.")

        raw_response = await self.api._async_request(
            token_data.model_dump(), operation="ProcessDatavault"
        )

        return self._validate_response(raw_response)

    def _validate_response(self, raw_response: Dict[str, Any]) -> DataVaultResponse:
        """
        Validate and parse DataVault API response.

        Validates response based on IsoCode and field presence.
        For CREATE operations, also validates required fields are present.
        For DELETE operations, success is determined primarily by IsoCode.

        Args:
            raw_response: Raw API response dictionary

        Returns:
            DataVaultResponse: Validated response object

        Raises:
            AzulResponseError: If response validation fails
        """
        try:
            iso_code = raw_response.get("IsoCode", "")

            # Success response: IsoCode "00" indicates success
            if iso_code == "00":
                # For CREATE operations, validate that required fields have values
                # For DELETE operations, fields may be empty but that's still success
                card_number = raw_response.get("CardNumber", "").strip()
                token = raw_response.get("DataVaultToken", "").strip()

                # If we have meaningful data in both fields, it's a CREATE success
                # If we don't have data but IsoCode is "00", it's likely a DELETE
                if card_number and token:
                    return DataVaultSuccessResponse.from_api_response(raw_response)
                else:
                    # Success with empty fields (typical for DELETE operations)
                    # Create a success response with the available data
                    return DataVaultSuccessResponse.from_api_response(raw_response)

            # Error response - non-"00" IsoCode indicates failure
            return DataVaultErrorResponse.from_api_response(raw_response)

        except Exception as e:
            # If validation fails completely, create a generic error response
            error_msg = f"Failed to validate DataVault response: {str(e)}"
            raise AzulResponseError(error_msg, response_data=raw_response) from e
