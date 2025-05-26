"""
3D Secure authentication models and validation for PyAzul.

This module provides Pydantic models for handling 3D Secure (3DS) transactions,
including cardholder information, authentication parameters, and challenge indicators.
It ensures data integrity and compliance with 3DS protocols.
"""

from enum import Enum
from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator

from .schemas import _validate_amount_field, _validate_itbis_field


class ChallengeIndicator(str, Enum):
    """Challenge indicator values for 3DS authentication."""

    NO_PREFERENCE = "01"  # No preference for challenge
    NO_CHALLENGE = "02"  # Prefer no challenge
    CHALLENGE = "03"  # Request Challenge (default preference)
    MANDATE_CHALLENGE = "04"  # Challenge required by mandate


class CardHolderInfo(BaseModel):
    """Cardholder information for 3DS authentication.

    Helps issuing bank assess transaction risk.
    All fields are optional - omit fields if information is not available.
    Ref: Azul Docs "Sub-campos CardHolderInfo"
    """

    BillingAddressCity: Optional[str] = Field(None, description="Billing address city.")
    BillingAddressCountry: Optional[str] = Field(
        None, description="Billing address country (e.g., 'DO')."
    )
    BillingAddressLine1: Optional[str] = Field(
        None, description="Billing address line 1."
    )
    BillingAddressLine2: Optional[str] = Field(
        None, description="Billing address line 2."
    )
    BillingAddressLine3: Optional[str] = Field(
        None, description="Billing address line 3."
    )
    BillingAddressState: Optional[str] = Field(
        None, description="Billing address state/province."
    )
    BillingAddressZip: Optional[str] = Field(
        None, description="Billing address ZIP/postal code."
    )
    Email: Optional[str] = Field(None, description="Cardholder email address.")
    Name: Optional[str] = Field(None, description="Cardholder full name.")
    PhoneHome: Optional[str] = Field(None, description="Cardholder home phone number.")
    PhoneMobile: Optional[str] = Field(
        None, description="Cardholder mobile phone number."
    )
    PhoneWork: Optional[str] = Field(None, description="Cardholder work phone number.")
    ShippingAddressCity: Optional[str] = Field(
        None, description="Shipping address city."
    )
    ShippingAddressCountry: Optional[str] = Field(
        None, description="Shipping address country (e.g., 'DO')."
    )
    ShippingAddressLine1: Optional[str] = Field(
        None, description="Shipping address line 1."
    )
    ShippingAddressLine2: Optional[str] = Field(
        None, description="Shipping address line 2."
    )
    ShippingAddressLine3: Optional[str] = Field(
        None, description="Shipping address line 3."
    )
    ShippingAddressState: Optional[str] = Field(
        None, description="Shipping address state/province."
    )
    ShippingAddressZip: Optional[str] = Field(
        None, description="Shipping address ZIP/postal code."
    )

    def model_dump(self, **kwargs):
        """Serialize model, excluding None values as recommended by Azul docs."""
        data = super().model_dump(**kwargs)
        # Remove None values to follow Azul's recommendation to omit blank fields
        return {k: v for k, v in data.items() if v is not None}


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
            "RequestChallengeIndicator": data["RequestChallengeIndicator"].value,
        }


class SecureSaleRequest(BaseModel):
    """Secure sale transaction request with 3DS data.

    Ref: Azul Docs "SALE: Transacción de venta" & "Vista general 3D-Secure 2.0"
    """

    # Core Sale Fields
    Channel: str = Field("EC", description="Payment channel (e.g., 'EC'). (X(3))")
    Store: str = Field(..., description="Unique merchant ID (MID). (X(11))")
    PosInputMode: str = Field(
        "E-Commerce", description="Transaction entry mode. (A(10))"
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
    CardNumber: str = Field(
        ..., description="Card number, no special characters. (N(19))"
    )
    Expiration: str = Field(..., description="Expiration date in YYYYMM format. (N(6))")
    CVC: str = Field(..., description="Card security code (CVV2 or CVC). (N(3))")
    AcquirerRefData: str = Field(
        "1", description="Acquirer reference. Fixed '1' (AZUL internal use). (N(1))"
    )
    CustomOrderId: Optional[str] = Field(
        None, description="Custom merchant order ID. Used for VerifyPayment. (X(75))"
    )
    SaveToDataVault: Optional[str] = Field(
        "0", description="'1' to save to DataVault, '0' not to. (N(1))"
    )

    # 3DS Specific Fields
    forceNo3DS: Literal["0", "1"] = Field(
        "0", description="'1' to force no 3DS, '0' to use 3DS if configured."
    )
    cardHolderInfo: CardHolderInfo
    threeDSAuth: ThreeDSAuth

    _validate_amount_values = field_validator("Amount", mode="before")(
        _validate_amount_field
    )
    _validate_itbis_values = field_validator("Itbis", mode="before")(
        _validate_itbis_field
    )


class SecureTokenSale(BaseModel):
    """Secure token sale transaction with 3DS data.

    Ref: Azul Docs "Venta utilizando el Token" & "Vista general 3D-Secure 2.0"
    """

    # Core Token Sale Fields
    Channel: str = Field("EC", description="Payment channel (e.g., 'EC'). (X(3))")
    Store: str = Field(..., description="Unique merchant ID (MID). (X(11))")
    PosInputMode: str = Field(
        "E-Commerce", description="Transaction entry mode. (A(10))"
    )
    Amount: str = Field(  # In cents
        ...,
        description="Total amount in cents (e.g. 1000 for $10.00). Serialized to str.",
    )
    DataVaultToken: str = Field(
        ..., description="DataVault token for the transaction. (A(100))"
    )
    OrderNumber: str = Field(..., description="Merchant order number. (X(15))")
    TrxType: Literal["Sale"] = Field(
        "Sale", description="Transaction type, fixed 'Sale'. (A(16))"
    )

    # Optional fields for Token Sale
    Itbis: Optional[str] = Field(  # In cents
        None, description="ITBIS in cents (optional for TokenSale). Serialized to str."
    )
    CVC: Optional[str] = Field(
        None,
        description="CVC (optional with token, E-comm mandatory if configured). (N(3))",
        min_length=3,
        max_length=4,
    )
    CustomOrderId: Optional[str] = Field(
        None, description="Custom merchant order ID. (X(75))"
    )
    AcquirerRefData: Optional[str] = Field(
        "1", description="Acquirer reference. Fixed '1' (AZUL internal use). (N(1))"
    )

    # 3DS Specific Fields
    forceNo3DS: Literal["0", "1"] = Field(
        "0", description="'1' to force no 3DS, '0' to use 3DS if configured."
    )
    cardHolderInfo: CardHolderInfo
    threeDSAuth: ThreeDSAuth

    _validate_amount_values = field_validator("Amount", mode="before")(
        _validate_amount_field
    )
    _validate_itbis_values = field_validator("Itbis", mode="before")(
        _validate_itbis_field
    )


class SecureSessionID(BaseModel):
    """Model for requests needing only a secure session ID."""

    session_id: str = Field(..., description="Secure session identifier.")


class SecureChallengeRequest(BaseModel):
    """Model for the 3DS challenge response (CRes)."""

    session_id: str = Field(..., description="Secure session identifier.")
    cres: str = Field(..., description="Challenge Response (CRes) from ACS.")
