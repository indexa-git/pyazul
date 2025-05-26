"""
Models module for PyAzul.

Contains data models and schemas for all services.
"""

# Import from schemas.py
from .schemas import AzulBaseModel  # Base model, might be useful
from .schemas import (
    DataVaultRequestModel,
    HoldTransactionModel,
    PaymentPageModel,
    PostSaleTransactionModel,
    RefundTransactionModel,
    SaleTransactionModel,
    TokenSaleModel,
    VerifyTransactionModel,
    VoidTransactionModel,
)

# Import from secure.py
from .secure import (
    CardHolderInfo,
    ChallengeIndicator,
    SecureChallengeRequest,
    SecureSaleRequest,
    SecureSessionID,
    SecureTokenSale,
    ThreeDSAuth,
)

__all__ = [
    # From schemas.py
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
    # From secure.py
    "SecureSaleRequest",
    "SecureTokenSale",
    "CardHolderInfo",
    "ThreeDSAuth",
    "ChallengeIndicator",
    "SecureSessionID",
    "SecureChallengeRequest",
]
