"""
3D Secure (3DS) models for PyAzul.

This module defines Pydantic models for 3D Secure authentication flows,
including cardholder information, authentication requests, and challenge handling.
"""

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, field_validator

from ..schemas import _validate_amount_field, _validate_itbis_field


class ChallengeIndicator(str, Enum):
    """Challenge indicator values for 3DS authentication."""

    NO_PREFERENCE = "01"  # No preference for challenge
    NO_CHALLENGE = "02"  # Prefer no challenge
    CHALLENGE = "03"  # Request Challenge (default preference)
    MANDATE_CHALLENGE = "04"  # Challenge required by mandate


class CardHolderInfo(BaseModel):
    """Cardholder information for 3DS authentication.

    Contains billing/shipping details to help issuers assess transaction risk.
    Optional fields can be omitted if not available - avoid sending empty strings.
    Ref: Azul Docs "Sub-campos CardHolderInfo"
    """

    # Billing Address (optional but recommended)
    BillingAddressCity: Optional[str] = Field(
        default=None, description="Billing address city."
    )
    BillingAddressCountry: Optional[str] = Field(
        default=None, description="Billing address country."
    )
    BillingAddressLine1: Optional[str] = Field(
        default=None, description="Billing address line 1."
    )
    BillingAddressLine2: Optional[str] = Field(
        default=None, description="Billing address line 2."
    )
    BillingAddressLine3: Optional[str] = Field(
        default=None, description="Billing address line 3."
    )
    BillingAddressState: Optional[str] = Field(
        default=None, description="Billing address state/province."
    )
    BillingAddressZip: Optional[str] = Field(
        default=None, description="Billing address ZIP/postal code."
    )

    # Contact Information (optional but recommended)
    Email: Optional[str] = Field(default=None, description="Cardholder email address.")
    Name: str = Field(..., description="Cardholder name.")
    PhoneHome: Optional[str] = Field(default=None, description="Home phone number.")
    PhoneMobile: Optional[str] = Field(default=None, description="Mobile phone number.")
    PhoneWork: Optional[str] = Field(default=None, description="Work phone number.")

    # Shipping Address (optional, for physical goods)
    ShippingAddressCity: Optional[str] = Field(
        default=None, description="Shipping address city."
    )
    ShippingAddressCountry: Optional[str] = Field(
        default=None, description="Shipping address country."
    )
    ShippingAddressLine1: Optional[str] = Field(
        default=None, description="Shipping address line 1."
    )
    ShippingAddressLine2: Optional[str] = Field(
        default=None, description="Shipping address line 2."
    )
    ShippingAddressLine3: Optional[str] = Field(
        default=None, description="Shipping address line 3."
    )
    ShippingAddressState: Optional[str] = Field(
        default=None, description="Shipping address state/province."
    )
    ShippingAddressZip: Optional[str] = Field(
        default=None, description="Shipping address ZIP/postal code."
    )

    def model_dump(self, **kwargs):
        """Serialize model, excluding None values to avoid sending empty fields."""
        return {k: v for k, v in super().model_dump(**kwargs).items() if v is not None}


class ThreeDSAuth(BaseModel):
    """3DS Authentication parameters.

    Contains URLs and preferences for the 3DS authentication process.
    Ref: Azul Docs "Paso 2: Iniciar un pago", Sub-Campos ThreeDSAuth
    """

    TermUrl: str = Field(
        ..., description="Merchant URL for ACS authentication results."
    )
    MethodNotificationUrl: str = Field(
        ..., description="Merchant URL for 3DS Method iframe notification."
    )
    RequestChallengeIndicator: ChallengeIndicator = Field(
        ChallengeIndicator.CHALLENGE,
        description="Merchant preference regarding authentication challenge.",
    )

    @field_validator("TermUrl", "MethodNotificationUrl")
    def validate_url(cls, v: str) -> str:
        """Validate URL format."""
        v_str = str(v)
        if not v_str.startswith(("http://", "https://")):
            raise ValueError(f"Invalid URL: {v_str}")
        return v_str

    def model_dump(self, **kwargs):
        """Serialize model, ensuring URLs and enums are strings."""
        data = super().model_dump(**kwargs)
        return {
            "TermUrl": str(data["TermUrl"]),
            "MethodNotificationUrl": str(data["MethodNotificationUrl"]),
            "RequestChallengeIndicator": (
                data["RequestChallengeIndicator"].value
                if hasattr(data["RequestChallengeIndicator"], "value")
                else str(data["RequestChallengeIndicator"])
            ),
        }


class SecureSale(BaseModel):
    """Secure sale transaction request with 3DS data.

    Ref: Azul Docs "SALE: Transacción de venta" & "Vista general 3D-Secure 2.0"
    """

    # Core Sale Fields
    Channel: str = Field(
        default="EC", description="Payment channel (e.g., 'EC'). (X(3))"
    )
    Store: str = Field(..., description="Unique merchant ID (MID). (X(11))")
    PosInputMode: str = Field(
        default="E-Commerce", description="Transaction entry mode. (A(10))"
    )
    Amount: str = Field(  # In cents
        ...,
        description="Total amount in cents (e.g. 1000 for $10.00). Serialized to str.",
    )
    Itbis: str = Field(  # In cents
        ...,
        description="ITBIS tax in cents (e.g. 180 for $1.80, 0 if exempt). To str.",
    )
    OrderNumber: str = Field(
        ..., description="Merchant order number. Empty if not applicable. (X(15))"
    )
    TrxType: str = Field(
        default="Sale",
        pattern="^Sale$",
        description="Transaction type, must be 'Sale'. (A(16))",
    )
    CardNumber: str = Field(
        ..., description="Card number, no special characters. (N(19))"
    )
    Expiration: str = Field(..., description="Expiration date in YYYYMM format. (N(6))")
    CVC: str = Field(..., description="Card security code (CVV2 or CVC). (N(3))")
    AcquirerRefData: str = Field(
        default="1",
        description="Acquirer reference. Fixed '1' (AZUL internal use). (N(1))",
    )
    CustomOrderId: Optional[str] = Field(
        default=None,
        description="Custom merchant order ID. Used for VerifyPayment. (X(75))",
    )
    SaveToDataVault: Optional[str] = Field(
        default="0", description="'1' to save to DataVault, '0' not to. (N(1))"
    )

    # 3DS Specific Fields
    ForceNo3DS: str = Field(
        default="0",
        pattern=r"^[01]$",
        description="'1' to force no 3DS, '0' to use 3DS if configured.",
    )
    CardHolderInfo: CardHolderInfo
    ThreeDSAuth: ThreeDSAuth

    _validate_amount_values = field_validator("Amount", mode="before")(
        _validate_amount_field
    )
    _validate_itbis_values = field_validator("Itbis", mode="before")(
        _validate_itbis_field
    )


class SecureTokenSale(BaseModel):
    """Secure token sale transaction with 3DS data.

    Ref: Azul Docs "Venta utilizando el Token" & "Vista general 3D-Secure 2.0"

    Note: Despite documentation stating Expiration should not be sent for token sales,
    the 3DS API implementation requires it to be sent as empty string.
    This is a known discrepancy between docs and API implementation.
    """

    # Core Token Sale Fields
    Channel: str = Field(
        default="EC", description="Payment channel (e.g., 'EC'). (X(3))"
    )
    Store: str = Field(..., description="Unique merchant ID (MID). (X(11))")
    PosInputMode: str = Field(
        default="E-Commerce", description="Transaction entry mode. (A(10))"
    )
    Amount: str = Field(  # In cents
        ...,
        description="Total amount in cents (e.g. 1000 for $10.00). Serialized to str.",
    )
    DataVaultToken: str = Field(
        ...,
        pattern=r"^[A-Fa-f0-9\-]{30,40}$",
        description="DataVault token for the transaction. (A(100))",
    )
    OrderNumber: str = Field(..., description="Merchant order number. (X(15))")
    TrxType: str = Field(
        default="Sale",
        pattern="^Sale$",
        description="Transaction type, must be 'Sale'. (A(16))",
    )
    CardNumber: Optional[str] = Field(
        default=None,
        description="Card number. May be required for 3DS despite using token. (N(19))",
    )
    Expiration: str = Field(
        default="",
        description="Expiration date. Must be empty string for token sales. (N(6))",
    )

    # Optional fields for Token Sale
    Itbis: Optional[str] = Field(  # In cents
        default=None,
        description="ITBIS in cents (optional for TokenSale). Serialized to str.",
    )
    CVC: Optional[str] = Field(
        default=None,
        description="CVC (optional with token, E-comm mandatory if configured). (N(3))",
        min_length=3,
        max_length=4,
    )
    CustomOrderId: Optional[str] = Field(
        default=None, description="Custom merchant order ID. (X(75))"
    )
    AcquirerRefData: Optional[str] = Field(
        default="1",
        description="Acquirer reference. Fixed '1' (AZUL internal use). (N(1))",
    )

    # 3DS Specific Fields
    ForceNo3DS: str = Field(
        default="0",
        pattern=r"^[01]$",
        description="'1' to force no 3DS, '0' to use 3DS if configured.",
    )
    CardHolderInfo: CardHolderInfo
    ThreeDSAuth: ThreeDSAuth

    _validate_amount_values = field_validator("Amount", mode="before")(
        _validate_amount_field
    )
    _validate_itbis_values = field_validator("Itbis", mode="before")(
        _validate_itbis_field
    )


class ChallengeRequest(BaseModel):
    """Model for 3DS challenge requests."""

    AzulOrderId: str = Field(..., description="Transaction ID from initial request.")
    CRes: str = Field(..., description="Challenge response from ACS.")


class SessionID(BaseModel):
    """Model for 3DS method notification requests."""

    AzulOrderId: str = Field(..., description="Azul order ID from initial transaction.")
    MethodNotificationStatus: str = Field(
        ..., description="Status of method notification."
    )
