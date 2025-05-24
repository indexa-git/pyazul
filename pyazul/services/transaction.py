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
    """Service for handling payment transactions like sales, refunds, etc."""

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
            transaction (Union[SaleTransactionModel, TokenSaleModel]): Payment data including card details or token

        Returns:
            Dict[str, Any]: API response containing transaction results
                - IsoCode: '00' indicates success
                - AuthorizationCode: Authorization code if successful
                - ResponseMessage: Transaction status message
                - DataVaultToken: Token if card was saved to vault

        Raises:
            APIError: If the transaction fails or API returns an error
        """
        return await self.client._async_request(transaction.model_dump())

    async def hold(
        self,
        transaction: HoldTransactionModel,
    ) -> Dict[str, Any]:
        """
        Create an authorization hold on a card.
        This reserves the amount but doesn't capture the funds.

        Args:
            transaction (HoldTransactionModel): Hold transaction data

        Returns:
            Dict[str, Any]: API response containing hold results
                - IsoCode: '00' indicates success
                - AuthorizationCode: Hold authorization code
                - RRN: Reference number

        Raises:
            APIError: If the hold fails or API returns an error
        """
        return await self.client._async_request(transaction.model_dump())

    async def refund(
        self,
        transaction: RefundTransactionModel,
    ) -> Dict[str, Any]:
        """
        Process a refund for a previous transaction.

        Args:
            transaction (RefundTransactionModel): Refund data including original transaction ID

        Returns:
            Dict[str, Any]: API response containing refund results
                - IsoCode: '00' indicates success
                - RRN: Reference number for the refund

        Raises:
            APIError: If the refund fails or API returns an error
        """
        return await self.client._async_request(transaction.model_dump())

    async def verify(
        self,
        transaction: VerifyTransactionModel,
    ) -> Dict[str, Any]:
        """
        Verify a transaction by checking its status.

        Args:
            transaction (VerifyTransactionModel): Transaction data including order ID
        """
        return await self.client._async_request(transaction.model_dump())

    async def void(self, transaction: VoidTransactionModel) -> Dict[str, Any]:
        """
        Void a transaction.

        Args:
            transaction (VoidTransactionModel): Transaction data including order ID
        """
        return await self.client._async_request(transaction.model_dump())

    async def post_sale(
        self,
        transaction: PostSaleTransactionModel,
    ) -> Dict[str, Any]:
        """
        Process a post sale transaction.
        """
        return await self.client._async_request(transaction.model_dump())
