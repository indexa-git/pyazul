from ..core.base import BaseService
from ..models.schemas import PaymentSchema, RefundTransactionModel, VerifyTransactionModel, VoidTransactionModel, PostSaleTransactionModel
from typing import Dict, Any

class TransactionService(BaseService):
    """
    Service for handling payment transactions through Azul's payment gateway.
    This service provides methods for processing different types of card transactions:
    - Sales (direct card payments)
    - Holds (authorization holds)
    - Refunds
    - Post Sales (post authorization captures)
    - Void (void a transaction)
    - Verify (verify a transaction)
    """

    async def sale(self, transaction: PaymentSchema) -> Dict[str, Any]:
        """
        Process a sale transaction (card payment or token payment).

        Args:
            transaction (PaymentSchema): Payment data including card details or token

        Returns:
            Dict[str, Any]: API response containing transaction results
                - IsoCode: '00' indicates success
                - AuthorizationCode: Authorization code if successful
                - ResponseMessage: Transaction status message
                - DataVaultToken: Token if card was saved to vault

        Raises:
            APIError: If the transaction fails or API returns an error
        """
        return await self.client._async_request(
            transaction.model_dump(),
            operation=''
        )
    
    async def hold(self, transaction: PaymentSchema) -> Dict[str, Any]:
        """
        Create an authorization hold on a card.
        This reserves the amount but doesn't capture the funds.

        Args:
            transaction (PaymentSchema): Hold transaction data

        Returns:
            Dict[str, Any]: API response containing hold results
                - IsoCode: '00' indicates success
                - AuthorizationCode: Hold authorization code
                - RRN: Reference number

        Raises:
            APIError: If the hold fails or API returns an error
        """
        return await self.client._async_request(
            transaction.model_dump(),
            operation=''
        )
    
    async def refund(self, transaction: RefundTransactionModel) -> Dict[str, Any]:
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
        return await self.client._async_request(
            transaction.model_dump(),
            operation=''
        )
    
    async def verify(self, transaction: VerifyTransactionModel) -> Dict[str, Any]:
        """
        Verify a transaction by checking its status.

        Args:
            transaction (VerifyTransactionModel): Transaction data including order ID   
        """
        return await self.client._async_request(
            transaction.model_dump(),
            operation='VerifyPayment'
        )
    
    async def void(self, transaction: VoidTransactionModel) -> Dict[str, Any]:
        """
        Void a transaction.

        Args:
            transaction (VoidTransactionModel): Transaction data including order ID 
        """
        return await self.client._async_request(
            transaction.model_dump(),
            operation='ProcessVoid'
        )
    
    async def post_sale(self, transaction: PostSaleTransactionModel) -> Dict[str, Any]:
        """
        Process a post sale transaction.
        """
        return await self.client._async_request(
            transaction.model_dump(),
            operation='ProcessPost'
        )