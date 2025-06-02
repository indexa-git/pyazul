"""
Core payment models for PyAzul.

This module defines Pydantic models for basic payment operations with Azul,
including sales, holds, refunds, voids, and post-authorization transactions.
"""

from typing import Optional

from pydantic import Field, field_validator

from ..schemas import AzulBase, _validate_amount_field, _validate_itbis_field


class BaseTransaction(AzulBase):
    """Base attributes common to many transaction types."""

    PosInputMode: str = Field(
        default="E-Commerce",
        description="Transaction entry mode (e.g., 'E-Commerce'), by AZUL. (A(10))",
    )
    OrderNumber: str = Field(
        ..., description="Merchant order number. Empty if not applicable. (X(15))"
    )
    CustomOrderId: Optional[str] = Field(
        default=None,
        description="Custom merchant order ID. Used for VerifyPayment. (X(75))",
    )
    CustomerServicePhone: Optional[str] = Field(
        default=None, description="Merchant customer service phone. (X(32))"
    )
    ECommerceURL: Optional[str] = Field(
        default=None, description="Merchant e-commerce URL. (X(32))"
    )
    AltMerchantName: Optional[str] = Field(
        default=None,
        description="Alternate merchant name for statements (max 25c). (X(30))",
    )
    ForceNo3DS: Optional[str] = Field(
        default=None,
        description="'1' to force no 3DS, '0'/omit to use 3DS if configured. (N(1))",
    )
    AcquirerRefData: Optional[str] = Field(
        default="1",
        description="Acquirer reference. Fixed '1' (AZUL internal use). (N(1))",
    )


class CardPayment(BaseTransaction):
    """Base attributes for payments made with actual card numbers."""

    Amount: str = Field(  # Represented in cents
        ...,
        description="Total amount in cents (e.g., 1000 for $10.00). Serialized to str.",
    )
    Itbis: str = Field(  # Represented in cents
        ...,
        description="ITBIS tax in cents (e.g., 180 for $1.80, 0 if exempt). To str.",
    )
    CardNumber: str = Field(
        ..., description="Card number, no special characters. (N(19))"
    )
    Expiration: str = Field(..., description="Expiration date in YYYYMM format. (N(6))")
    CVC: str = Field(..., description="Card security code (CVV2 or CVC). (N(3))")
    SaveToDataVault: Optional[str] = Field(
        default="0", description="'1' to save to DataVault, '0' not to. (N(1))"
    )

    _validate_card_amount_values = field_validator("Amount", mode="before")(
        _validate_amount_field
    )
    _validate_card_itbis_values = field_validator("Itbis", mode="before")(
        _validate_itbis_field
    )


class Sale(CardPayment):
    """Model for sale transactions."""

    TrxType: str = Field(
        default="Sale",
        pattern="^Sale$",
        description="Transaction type, must be 'Sale'.",
    )
    DataVaultToken: Optional[str] = Field(
        default=None,
        pattern=r"^[A-Fa-f0-9\-]{30,40}$",
        description="DataVault token to use instead of PAN/Expiry. (A(100))",
    )
    # All other fields inherited from CardPayment


class Hold(CardPayment):
    """Model for hold transactions."""

    TrxType: str = Field(
        default="Hold",
        pattern="^Hold$",
        description="Transaction type, must be 'Hold'.",
    )
    DataVaultToken: Optional[str] = Field(
        default=None,
        pattern=r"^[A-Fa-f0-9\-]{30,40}$",
        description="DataVault token to use instead of PAN/Expiry. (A(100))",
    )
    # All other fields inherited from CardPayment


class Refund(BaseTransaction):
    """Model for refund transactions."""

    AzulOrderId: str = Field(
        ..., description="AzulOrderId of the original transaction to refund. (N(8))"
    )
    TrxType: str = Field(
        default="Refund",
        pattern="^Refund$",
        description="Transaction type, must be 'Refund'.",
    )
    Amount: str = Field(  # Represented in cents
        ...,
        description="Total amount in cents (e.g., 1000 for $10.00). Serialized to str.",
    )
    Itbis: str = Field(  # Represented in cents
        ...,
        description="ITBIS tax in cents (e.g., 180 for $1.80, 0 if exempt). To str.",
    )
    AcquirerRefData: Optional[str] = None  # Override to None for refunds

    _validate_refund_amount_values = field_validator("Amount", mode="before")(
        _validate_amount_field
    )
    _validate_refund_itbis_values = field_validator("Itbis", mode="before")(
        _validate_itbis_field
    )
    # Inherits OrderNumber, CustomOrderId, etc. from BaseTransaction


class Post(AzulBase):
    """Model for post-authorization (capture) transactions (ProcessPost)."""

    AzulOrderId: str = Field(
        ...,
        description="AzulOrderId of the original Hold transaction to capture. (N(8))",
    )
    Amount: str = Field(  # Represented in cents
        ...,
        description="Total amount to capture in cents. Serialized to str. (N(12))",
    )
    Itbis: str = Field(  # Represented in cents
        ...,
        description="ITBIS of amount to capture in cents. Serialized to str. (N(12))",
    )

    _validate_post_sale_amount_values = field_validator("Amount", mode="before")(
        _validate_amount_field
    )
    _validate_post_sale_itbis_values = field_validator("Itbis", mode="before")(
        _validate_itbis_field
    )


class Void(AzulBase):
    """Model for void transactions (ProcessVoid)."""

    AzulOrderId: str = Field(
        ...,
        description="AzulOrderId of the original transaction to void. (N(999))",
    )
