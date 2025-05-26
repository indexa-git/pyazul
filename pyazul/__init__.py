"""
PyAzul - Python Client for Azul Payment Gateway.

This package provides a complete interface to interact with Azul services:
- Direct payment processing
- Card tokenization (DataVault)
- Payment Page
- Transaction verification
- Refunds and voids
- Hold/capture of transactions

Features:
    - Direct payments (Sale, Hold)
    - Refunds (Refund), Voids (Void), Post-Authorizations (PostAuth)
    - Card tokenization (DataVault)
    - Hosted payment page generation

Example:
    >>> from pyazul import PyAzul
    >>> azul = PyAzul()  # Uses environment variables for configuration
    >>>
    >>> # Process a payment
    >>> response = await azul.sale({
    ...     "Channel": "EC",
    ...     "Store": "39038540035",
    ...     "CardNumber": "4111111111111111",
    ...     "Expiration": "202812",
    ...     "CVC": "123",
    ...     "Amount": "100000"  # $1,000.00
    ... })
"""

from .core.config import AzulSettings, get_azul_settings
from .core.exceptions import AzulError
from .index import PyAzul

# Import models from the centralized pyazul.models package
from .models import (
    AzulBaseModel,
    CardHolderInfo,
    ChallengeIndicator,
    DataVaultRequestModel,
    HoldTransactionModel,
    PaymentPageModel,
    PostSaleTransactionModel,
    RefundTransactionModel,
    SaleTransactionModel,
    SecureSaleRequest,
    SecureTokenSale,
    ThreeDSAuth,
    TokenSaleModel,
    VerifyTransactionModel,
    VoidTransactionModel,
)
from .services import DataVaultService, PaymentPageService, TransactionService
from .services.secure import SecureService

__all__ = [
    # Main class
    "PyAzul",
    # Configuration
    "get_azul_settings",
    "AzulSettings",
    "AzulError",
    # Services
    "TransactionService",
    "DataVaultService",
    "PaymentPageService",
    "SecureService",
    # Models
    "AzulBaseModel",
    "SaleTransactionModel",
    "HoldTransactionModel",
    "RefundTransactionModel",
    "DataVaultRequestModel",
    "TokenSaleModel",
    "PostSaleTransactionModel",
    "VerifyTransactionModel",
    "VoidTransactionModel",
    "PaymentPageModel",
    "SecureSaleRequest",
    "SecureTokenSale",
    "CardHolderInfo",
    "ThreeDSAuth",
    "ChallengeIndicator",
]
