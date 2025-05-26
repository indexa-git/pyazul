"""
PyAzul: The Python SDK for Azul Payment Gateway.

This module provides the main `PyAzul` class, which serves as the primary entry point
for interacting with all services offered by the Azul Payment Gateway, including
payments, 3D Secure, DataVault (tokenization), and Payment Page generation.
"""

from typing import Any, Dict, Optional

from .api.client import AzulAPI
from .core.config import AzulSettings, get_azul_settings
from .models import (
    DataVaultRequestModel,
    HoldTransactionModel,
    PaymentPageModel,
    PostSaleTransactionModel,
    RefundTransactionModel,
    SaleTransactionModel,
    SecureSaleRequest,
    SecureTokenSale,
    TokenSaleModel,
    VerifyTransactionModel,
    VoidTransactionModel,
)
from .services.datavault import DataVaultService
from .services.payment_page import PaymentPageService
from .services.secure import SecureService
from .services.transaction import TransactionService


class PyAzul:
    """
    Main client for integration with Azul Payment Gateway.

    This class provides a unified interface to all Azul services.

    Key Features:
        - Direct payment processing and 3D Secure
        - Card tokenization (DataVault)
        - Payment Page
        - Transaction verification
        - Refunds and voids
        - Hold/capture of transactions

    Example:
        >>> from pyazul import PyAzul
        >>> azul = PyAzul() # Uses environment variables for configuration
        >>> # Process a payment
        >>> response = await azul.sale(...)
        >>> # Tokenize a card
        >>> token_response = await azul.create_token(...)
        >>> # Use token for a 3DS payment
        >>> secure_response = await azul.secure_token_sale(...)
    """

    def __init__(
        self,
        settings: Optional[AzulSettings] = None,
    ):
        """
        Initialize the PyAzul client.

        Args:
            settings: Optional custom settings. If not provided,
                     environment variables will be used.
        """
        if settings is None:
            settings = get_azul_settings()
        self.settings = settings

        # Create shared API client
        self.api = AzulAPI(settings=self.settings)

        # Initialize services with the API client, settings, and session_store
        self.transaction = TransactionService(api_client=self.api)
        self.datavault = DataVaultService(api_client=self.api)
        self.payment_page_service = PaymentPageService(settings=self.settings)
        self.secure = SecureService(api_client=self.api)

    async def sale(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process a direct card payment."""
        return await self.transaction.sale(SaleTransactionModel(**data))

    async def hold(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Perform a hold on a card (pre-authorization)."""
        return await self.transaction.hold(HoldTransactionModel(**data))

    async def refund(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process a refund for a previous transaction."""
        return await self.transaction.refund(RefundTransactionModel(**data))

    async def void(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Void a previous transaction."""
        return await self.transaction.void(VoidTransactionModel(**data))

    async def post_auth(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Capture a previously held amount (post-authorization)."""
        return await self.transaction.post_sale(PostSaleTransactionModel(**data))

    async def verify_transaction(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Verify the status of a transaction."""
        return await self.transaction.verify(VerifyTransactionModel(**data))

    async def create_token(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a card token in DataVault."""
        return await self.datavault.create(DataVaultRequestModel(**data))

    async def delete_token(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Delete a token from DataVault."""
        return await self.datavault.delete(DataVaultRequestModel(**data))

    async def token_sale(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process a sale using a token (without 3DS)."""
        return await self.transaction.sale(TokenSaleModel(**data))

    def payment_page(self, data: Dict[str, Any]) -> str:
        """Generate HTML for Azul's hosted payment page."""
        return self.payment_page_service.create_payment_form(PaymentPageModel(**data))

    # --- Secure Methods (3D Secure) ---

    async def secure_sale(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process a card payment using 3D Secure authentication."""
        return await self.secure.process_sale(SecureSaleRequest(**data))

    async def secure_token_sale(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process a tokenized card payment using 3D Secure authentication."""
        return await self.secure.process_token_sale(SecureTokenSale(**data))

    async def secure_hold(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Perform a hold on a card (pre-authorization) with 3D Secure."""
        # SecureService process_hold expects SecureSaleRequest model
        return await self.secure.process_hold(SecureSaleRequest(**data))

    async def process_3ds_method(
        self, azul_order_id: str, method_notification_status: str
    ) -> Dict[str, Any]:
        """Process the 3DS method notification received from ACS."""
        return await self.secure.process_3ds_method(
            azul_order_id, method_notification_status
        )

    async def process_challenge(
        self, session_id: str, challenge_response: str
    ) -> Dict[str, Any]:
        """Process the 3DS challenge response received from ACS."""
        return await self.secure.process_challenge(session_id, challenge_response)

    async def get_secure_session_info(
        self, session_id: str
    ) -> Optional[Dict[str, Any]]:
        """Retrieve information about an active 3DS session."""
        return self.secure.secure_sessions.get(session_id)

    def create_challenge_form(
        self, creq: str, term_url: str, redirect_post_url: str
    ) -> str:
        """Create an HTML form for the 3DS challenge redirect."""
        return self.secure._create_challenge_form(creq, term_url, redirect_post_url)
