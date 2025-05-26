"""
Service for handling standard payment transactions with the Azul API.

This includes sales, holds, refunds, voids, and transaction verifications.
"""

from typing import Any, Dict, Union

from ..api.client import AzulAPI
from ..core.config import AzulSettings
from ..models.schemas import (
    HoldTransactionModel,
    PostSaleTransactionModel,
    RefundTransactionModel,
    SaleTransactionModel,
    TokenSaleModel,
    VerifyTransactionModel,
    VoidTransactionModel,
)


class TransactionService:
    """Service for handling payment transactions (sales, refunds, etc.)."""

    def __init__(self, settings: AzulSettings, api_client: AzulAPI):
        """
        Initialize TransactionService.

        Args:
            settings: Configuration settings for Azul.
            api_client: An instance of AzulAPI for making requests.
        """
        self.settings = settings
        self.client = api_client

    async def sale(
        self, transaction: Union[SaleTransactionModel, TokenSaleModel]
    ) -> Dict[str, Any]:
        """
        Process a sale transaction (card payment or token payment).

        Args:
            transaction: Payment data including card details or token.

        Returns:
            API response containing transaction results.

        Raises:
            APIError: If the transaction fails or API returns an error.
        """
        payload = transaction.model_dump(exclude_none=True)
        return await self.client._async_request(payload)

    async def hold(
        self,
        transaction: HoldTransactionModel,
    ) -> Dict[str, Any]:
        """
        Create an authorization hold on a card.

        This reserves the amount but doesn't capture the funds.

        Args:
            transaction: Hold transaction data.

        Returns:
            API response containing hold results.

        Raises:
            APIError: If the hold fails or API returns an error.
        """
        payload = transaction.model_dump(exclude_none=True)
        return await self.client._async_request(payload)

    async def refund(
        self,
        transaction: RefundTransactionModel,
    ) -> Dict[str, Any]:
        """
        Process a refund for a previous transaction.

        Args:
            transaction: Refund data including original transaction ID.

        Returns:
            API response containing refund results.

        Raises:
            APIError: If the refund fails or API returns an error.
        """
        payload = transaction.model_dump(exclude_none=True)
        return await self.client._async_request(payload)

    async def verify(
        self,
        transaction: VerifyTransactionModel,
    ) -> Dict[str, Any]:
        """Verify a transaction by checking its status."""
        return await self.client._async_request(transaction.model_dump())

    async def void(self, transaction: VoidTransactionModel) -> Dict[str, Any]:
        """Void a transaction."""
        return await self.client._async_request(
            transaction.model_dump(exclude_none=True)
        )

    async def post_sale(
        self,
        transaction: PostSaleTransactionModel,
    ) -> Dict[str, Any]:
        """Process a post sale transaction (capture a hold)."""
        payload = transaction.model_dump(exclude_none=True)
        return await self.client._async_request(payload)
