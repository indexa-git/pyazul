"""
PyAzul: The Python SDK for Azul Payment Gateway.

This module provides the main `PyAzul` class, which serves as the primary entry point
for interacting with all services offered by the Azul Payment Gateway, including
payments, 3D Secure, DataVault (tokenization), and Payment Page generation.
"""

from typing import Any, Dict, Optional

from .api.client import AzulAPI
from .core.config import AzulSettings, get_azul_settings
from .models.datavault import TokenRequest, TokenResponse, TokenSale
from .models.payment import Hold, Post, Refund, Sale, Void
from .models.payment_page import PaymentPage
from .models.three_ds import SecureSale, SecureTokenSale
from .models.verification import VerifyTransaction
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
        self.transaction = TransactionService(client=self.api, settings=self.settings)
        self.datavault = DataVaultService(client=self.api, settings=self.settings)
        self.payment_page_service = PaymentPageService(settings=self.settings)
        self.secure = SecureService(client=self.api, settings=self.settings)

    async def sale(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process a direct card payment."""
        return await self.transaction.process_sale(Sale(**data))

    async def hold(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Perform a hold on a card (pre-authorization)."""
        return await self.transaction.process_hold(Hold(**data))

    async def refund(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process a refund for a previous transaction."""
        return await self.transaction.process_refund(Refund(**data))

    async def void(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Void a previous transaction."""
        return await self.transaction.process_void(Void(**data))

    async def post_auth(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Capture a previously held amount (post-authorization)."""
        return await self.transaction.process_post(Post(**data))

    async def verify_transaction(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Verify the status of a transaction."""
        return await self.transaction.verify_payment(VerifyTransaction(**data))

    async def create_token(self, data: Dict[str, Any]) -> TokenResponse:
        """
        Create a card token in DataVault.

        Returns:
            TokenResponse: Validated response object with type-safe access
                               to token details or error information.
        """
        return await self.datavault.create_token(TokenRequest(**data))

    async def delete_token(self, data: Dict[str, Any]) -> TokenResponse:
        """
        Delete a token from DataVault.

        Returns:
            TokenResponse: Validated response object with type-safe access
                               to success confirmation or error information.
        """
        return await self.datavault.delete_token(TokenRequest(**data))

    async def token_sale(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process a sale using a token (without 3DS)."""
        return await self.transaction.process_token_sale(TokenSale(**data))

    def payment_page(self, data: Dict[str, Any]) -> str:
        """Generate HTML for Azul's hosted payment page."""
        return self.payment_page_service.generate_payment_form_html(PaymentPage(**data))

    # --- Secure Methods (3D Secure) ---

    async def secure_sale(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process a card payment using 3D Secure authentication."""
        return await self.secure.process_sale(SecureSale(**data))

    async def secure_token_sale(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process a tokenized card payment using 3D Secure authentication."""
        return await self.secure.process_token_sale(SecureTokenSale(**data))

    async def secure_hold(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Perform a hold on a card (pre-authorization) with 3D Secure."""
        # SecureService process_hold expects SecureSale model
        return await self.secure.process_hold(SecureSale(**data))

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

    async def handle_3ds_callback(
        self,
        secure_id: str,
        callback_data: Optional[Dict[str, Any]] = None,
        form_data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Handle 3DS callbacks - automatically detects and routes to appropriate handler.

        This method determines the 3DS phase and processes it accordingly:
        - Method notifications: Processes 3DS method completion
        - Challenge responses: Processes challenge completion
        - Return callbacks: Verifies final transaction status

        Args:
            secure_id: The secure session ID from callback URL
            callback_data: Query parameters from the callback
            form_data: Form data from POST callbacks (for method/challenge data)

        Returns:
            Dict containing:
            - completed: True if transaction is final (success/failure)
            - requires_redirect: True if user needs to be redirected for challenge
            - html: Challenge form HTML if redirect required
            - AzulOrderId: Order ID for reference
            - status: Transaction status (approved/declined/pending)
        """
        return await self.secure.handle_3ds_callback(
            secure_id, callback_data or {}, form_data or {}
        )

    async def get_session_info(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve information about an active 3DS session."""
        return self.secure.get_session_info(session_id)

    def create_challenge_form(
        self, creq: str, term_url: str, redirect_post_url: str
    ) -> str:
        """Create an HTML form for the 3DS challenge redirect."""
        return self.secure.create_challenge_form(redirect_post_url, creq, term_url)
