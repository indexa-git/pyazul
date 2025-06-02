"""
PyAzul models organized by business domain.

This module exports all models using clean, Pythonic naming conventions while organizing
them by business domain for better maintainability and developer experience.

Business Domains:
- payment/: Core payment operations (Sale, Hold, Refund, Void, Post)
- datavault/: Card tokenization and token management
- three_ds/: 3D Secure authentication and challenges
- payment_page/: Azul hosted Payment Page functionality
- verification/: Transaction verification and status checking

Recommended imports:
    from pyazul.models.payment import Sale, Hold, Refund
    from pyazul.models.datavault import TokenRequest, TokenSale
    from pyazul.models.three_ds import SecureSale, CardHolderInfo
    from pyazul.models.payment_page import PaymentPage
    from pyazul.models.verification import VerifyTransaction

Legacy imports (deprecated):
    from pyazul.models import SaleTransactionModel  # Use Sale instead
"""

import warnings

# DataVault domain
from .datavault import TokenError, TokenRequest, TokenResponse, TokenSale, TokenSuccess

# Payment domain
from .payment import BaseTransaction, CardPayment, Hold, Post, Refund, Sale, Void

# Payment Page domain
from .payment_page import PaymentPage

# Base classes and validators from schemas
from .schemas import AzulBase, _validate_amount_field, _validate_itbis_field

# 3D Secure domain
from .three_ds import (
    CardHolderInfo,
    ChallengeIndicator,
    ChallengeRequest,
    SecureSale,
    SecureTokenSale,
    SessionID,
    ThreeDSAuth,
)

# Verification domain
from .verification import VerifyTransaction

# ========================================
# Backward Compatibility Aliases (Deprecated)
# ========================================


def _deprecated_alias(new_name: str, old_name: str, obj):
    """Create a deprecated alias with warning."""

    def deprecated_property():
        warnings.warn(
            f"'{old_name}' is deprecated. Use '{new_name}' instead.",
            DeprecationWarning,
            stacklevel=3,
        )
        return obj

    return deprecated_property


# Create deprecated aliases
def __getattr__(name: str):
    """Handle deprecated model name imports with warnings."""
    deprecation_map = {
        # Base classes
        "AzulBaseModel": ("AzulBase", AzulBase),
        "BaseTransactionAttributes": ("BaseTransaction", BaseTransaction),
        "CardPaymentAttributes": ("CardPayment", CardPayment),
        # Payment models
        "SaleTransactionModel": ("Sale", Sale),
        "HoldTransactionModel": ("Hold", Hold),
        "RefundTransactionModel": ("Refund", Refund),
        "VoidTransactionModel": ("Void", Void),
        "PostSaleTransactionModel": ("Post", Post),
        # DataVault models
        "DataVaultRequestModel": ("TokenRequest", TokenRequest),
        "DataVaultResponse": ("TokenResponse", TokenResponse),
        "DataVaultSuccessResponse": ("TokenSuccess", TokenSuccess),
        "DataVaultErrorResponse": ("TokenError", TokenError),
        "TokenSaleModel": ("TokenSale", TokenSale),
        # 3DS models
        "SecureSaleRequest": ("SecureSale", SecureSale),
        "SecureSessionID": ("SessionID", SessionID),
        "SecureChallengeRequest": ("ChallengeRequest", ChallengeRequest),
        # Other models
        "PaymentPageModel": ("PaymentPage", PaymentPage),
        "VerifyTransactionModel": ("VerifyTransaction", VerifyTransaction),
    }

    if name in deprecation_map:
        new_name, obj = deprecation_map[name]
        warnings.warn(
            f"'{name}' is deprecated and will be removed in a future version. "
            f"Use '{new_name}' instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return obj

    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")


# Export new clean names
__all__ = [
    # Base classes and validators
    "AzulBase",
    "BaseTransaction",
    "CardPayment",
    "_validate_amount_field",
    "_validate_itbis_field",
    # Payment domain models
    "Sale",
    "Hold",
    "Refund",
    "Void",
    "Post",
    # DataVault domain models
    "TokenRequest",
    "TokenResponse",
    "TokenSuccess",
    "TokenError",
    "TokenSale",
    # 3D Secure domain models
    "CardHolderInfo",
    "ThreeDSAuth",
    "ChallengeIndicator",
    "SecureSale",
    "SecureTokenSale",
    "SessionID",
    "ChallengeRequest",
    # Payment Page domain models
    "PaymentPage",
    # Verification domain models
    "VerifyTransaction",
]
