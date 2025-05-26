"""
Data models and schemas for Azul payment gateway integration.

This module defines Pydantic models for various Azul API operations,
ensuring data validation and consistency.
"""

from datetime import datetime
from typing import Literal, Optional, Union

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    HttpUrl,
    RootModel,
    field_validator,
    model_validator,
)


# Helper validator functions
def _validate_amount_field(v: Union[str, int, float], info) -> str:
    """
    Validate and normalize amount fields to string representation in cents.

    Accepts int, float, or str input and ensures non-negative integer value.
    Converts float/int inputs to string format required by Azul API.

    Args:
        v: Input value (str, int, or float representing cents)
        info: Pydantic field info

    Returns:
        str: Validated amount as string of digits

    Raises:
        ValueError: If value is negative or not a valid number
    """
    if isinstance(v, float):  # Convert float to int (cents) then to str
        v = str(int(v))
    elif isinstance(v, int):
        v = str(v)

    if not v.isdigit():
        raise ValueError(
            f"{info.field_name} ('{v}') must be a string of digits representing cents."
        )

    numeric_val = int(v)
    if numeric_val < 0:
        raise ValueError(f"{info.field_name} ('{v}') must be non-negative.")

    return str(numeric_val)


def _validate_itbis_field(v: Union[str, int, float, None], info) -> Optional[str]:
    """
    Validate and normalize ITBIS fields to string representation in cents.

    Similar to _validate_amount_field but with special handling:
    - Returns None for Optional fields when input is None
    - Formats zero values as "000" per Azul documentation requirement

    Args:
        v: Input value (str, int, float, or None for optional fields)
        info: Pydantic field info

    Returns:
        Optional[str]: Validated ITBIS as string, "000" for zero, or None for optional

    Raises:
        ValueError: If value is negative or not a valid number
    """
    if v is None:  # Handles Optional fields like TokenSaleModel.Itbis
        return (
            None  # Pydantic handles None for non-optional fields before this validator.
        )

    # At this point, v is not None. It can be str, int, or float.
    if isinstance(v, float):
        v = str(int(v))
    elif isinstance(v, int):
        v = str(v)

    if (
        not v.isdigit()
    ):  # Now v is guaranteed to be a str if it passed initial type checks
        raise ValueError(
            f"{info.field_name} ('{v}') must be a string of digits representing cents."
        )

    numeric_val = int(v)
    if numeric_val < 0:
        raise ValueError(f"{info.field_name} ('{v}') must be non-negative.")

    if numeric_val == 0:
        return "000"

    return str(numeric_val)


class AzulBaseModel(BaseModel):
    """Base model for Azul payment operations."""

    Channel: Optional[str] = Field(
        None, description="Payment channel (e.g., 'EC'), provided by AZUL. (X(3))"
    )
    Store: Optional[str] = Field(
        None, description="Unique merchant ID (MID), provided by AZUL. (X(11))"
    )
    PosInputMode: str = Field(
        "E-Commerce",
        description="Transaction entry mode (e.g., 'E-Commerce'), by AZUL. (X(11))",
    )
    Amount: str = Field(  # Represented in cents
        ...,
        description="Total amount in cents (e.g., 1000 for $10.00). Serialized to str.",
    )
    Itbis: str = Field(  # Represented in cents
        ...,
        description="ITBIS tax in cents (e.g., 180 for $1.80, 0 if exempt). To str.",
    )

    _validate_amount_values = field_validator("Amount", mode="before")(
        _validate_amount_field
    )
    _validate_itbis_values = field_validator("Itbis", mode="before")(
        _validate_itbis_field
    )


class SaleTransactionModel(AzulBaseModel):
    """Model for sales transactions."""

    CardNumber: str = Field(
        ..., description="Card number, no special characters. (N(19))"
    )
    Expiration: str = Field(..., description="Expiration date in YYYYMM format. (N(6))")
    CVC: str = Field(..., description="Card security code (CVV2 or CVC). (N(3))")
    TrxType: Literal["Sale"] = "Sale"
    OrderNumber: str = Field(
        ..., description="Merchant order number. Empty if not applicable. (X(15))"
    )
    AcquirerRefData: str = Field(
        "1", description="Acquirer reference. Fixed '1' (AZUL internal use). (N(1))"
    )
    CustomOrderId: Optional[str] = Field(
        None, description="Custom merchant order ID. Used for VerifyPayment. (X(75))"
    )
    SaveToDataVault: Optional[str] = Field(
        "0", description="'1' to save to DataVault, '0' not to. (N(1))"
    )
    CustomerServicePhone: Optional[str] = Field(
        None, description="Merchant customer service phone. (X(32))"
    )
    ECommerceURL: Optional[str] = Field(
        None, description="Merchant e-commerce URL. (X(32))"
    )
    AltMerchantName: Optional[str] = Field(
        None, description="Alternate merchant name for statements (max 25c). (X(30))"
    )
    ForceNo3DS: Optional[str] = Field(
        None,
        description="'1' to force no 3DS, '0'/omit to use 3DS if configured. (N(1))",
    )


class HoldTransactionModel(AzulBaseModel):
    """Model for hold transactions."""

    CardNumber: str = Field(
        ..., description="Card number, no special characters. (N(19))"
    )
    Expiration: str = Field(..., description="Expiration date in YYYYMM format. (N(6))")
    CVC: str = Field(..., description="Card security code (CVV2 or CVC). (N(3))")
    TrxType: Literal["Hold"] = Field(
        "Hold", description="Transaction type, fixed Hold."
    )
    OrderNumber: str = Field(
        ..., description="Merchant order number. Empty if not applicable. (X(15))"
    )
    AcquirerRefData: str = Field(  # Documented as Obligatorio: Si for HOLD
        "1", description="Acquirer reference. Fixed '1' (AZUL internal use). (N(1))"
    )
    CustomOrderId: Optional[str] = Field(
        None, description="Custom merchant order ID. Used for VerifyPayment. (X(75))"
    )
    DataVaultToken: Optional[str] = Field(
        None, description="DataVault token to use instead of PAN/Expiry. (A(100))"
    )
    SaveToDataVault: Optional[str] = Field(
        "0", description="'1' to save to DataVault, '0' not to. (N(1))"
    )
    CustomerServicePhone: Optional[str] = Field(
        None, description="Merchant customer service phone. (X(32))"
    )
    ECommerceURL: Optional[str] = Field(
        None, description="Merchant e-commerce URL. (X(32))"
    )
    AltMerchantName: Optional[str] = Field(
        None, description="Alternate merchant name for statements (max 25c). (X(30))"
    )
    ForceNo3DS: Optional[str] = Field(
        None,
        description="'1' to force no 3DS, '0'/omit to use 3DS if configured. (N(1))",
    )


class RefundTransactionModel(AzulBaseModel):
    """Model for refund transactions."""

    AzulOrderId: str = Field(
        ..., description="AzulOrderId of the original transaction to refund. (N(8))"
    )
    OrderNumber: str = Field(
        ...,
        description="Original merchant order number for the transaction. (X(15))",
    )
    TrxType: Literal["Refund"] = "Refund"
    CustomOrderId: Optional[str] = Field(
        None, description="Original custom merchant order ID. (X(75))"
    )
    CustomerServicePhone: Optional[str] = Field(
        None, description="Merchant customer service phone. (X(32))"
    )
    ECommerceURL: Optional[str] = Field(
        None, description="Merchant e-commerce URL. (X(32))"
    )
    AltMerchantName: Optional[str] = Field(
        None, description="Alternate merchant name (max 25c). (X(30))"
    )


class DataVaultRequestModel(BaseModel):
    """Model for DataVault operations (CREATE or DELETE token)."""

    Channel: str = Field(
        "EC", description="Payment channel (e.g., 'EC'), provided by AZUL. (X(3))"
    )
    Store: str = Field(
        ..., description="Unique merchant ID (MID), provided by AZUL. (X(11))"
    )
    TrxType: Literal["CREATE", "DELETE"] = Field(
        ..., description="Transaction type: 'CREATE' or 'DELETE'. (A(10))"
    )
    CardNumber: Optional[str] = Field(
        None, description="Card number to tokenize (for CREATE). (N(19))"
    )
    Expiration: Optional[str] = Field(
        None, description="Expiration date YYYYMM (for CREATE). (N(6))"
    )
    CVC: Optional[str] = Field(
        None,
        description="Security code. Optional for CREATE, not used for DELETE. (N(3))",
        min_length=3,
        max_length=4,
    )
    DataVaultToken: Optional[str] = Field(
        None, description="DataVault token to be deleted (for DELETE). (X(30))"
    )

    @model_validator(mode="after")
    def check_fields_for_trxtype(cls, data):
        """Validate fields based on TrxType."""
        if data.TrxType == "CREATE":
            if not data.CardNumber or not data.Expiration:
                raise ValueError("CardNumber and Expiration are required for CREATE")
            if data.DataVaultToken:
                raise ValueError("DataVaultToken not allowed for CREATE")
        elif data.TrxType == "DELETE":
            if not data.DataVaultToken:
                raise ValueError("DataVaultToken is required for DELETE")
            if data.CardNumber or data.Expiration or data.CVC:
                raise ValueError("Card/Expiry/CVC not allowed for DELETE")
        return data


class TokenSaleModel(BaseModel):
    """Model for sales transactions using a DataVault token."""

    Channel: str = Field(
        "EC", description="Payment channel (e.g., 'EC'), provided by AZUL. (X(3))"
    )
    Store: str = Field(
        ..., description="Unique merchant ID (MID), provided by AZUL. (X(11))"
    )
    PosInputMode: str = Field(
        "E-Commerce",
        description="Transaction entry mode (e.g., 'E-Commerce'), by AZUL. (A(10))",
    )
    Amount: str = Field(  # Represented in cents
        ...,
        description="Total amount in cents (e.g., 1000 for $10.00). Serialized to str.",
    )
    Itbis: Optional[str] = Field(  # Represented in cents
        None,
        description="ITBIS in cents (optional for TokenSale). Serialized to str.",
    )
    DataVaultToken: str = Field(
        ..., description="DataVault token for the transaction. (A(100))"
    )
    TrxType: Literal["Sale"] = Field(
        "Sale", description="Transaction type, fixed 'Sale'. (A(16))"
    )
    OrderNumber: str = Field(..., description="Merchant order number. (X(15))")
    CVC: Optional[str] = Field(
        None,
        description="CVC (optional with token, E-comm mandatory if configured). (N(3))",
        min_length=3,
        max_length=4,
    )
    CardNumber: Optional[str] = Field(
        default="", description="Card number, empty for token sales. (N(19))"
    )
    Expiration: Optional[str] = Field(
        default="",
        description="Expiration date (YYYYMM), empty for token sales. (N(6))",
    )
    CustomOrderId: Optional[str] = Field(
        None, description="Custom merchant order ID. (X(75))"
    )
    AcquirerRefData: Optional[str] = Field(
        "1", description="Acquirer reference. Fixed '1' (AZUL internal use). (N(1))"
    )
    CustomerServicePhone: Optional[str] = Field(
        None, description="Merchant customer service phone. (X(32))"
    )
    ECommerceURL: Optional[str] = Field(
        None, description="Merchant e-commerce URL. (X(32))"
    )
    AltMerchantName: Optional[str] = Field(
        None, description="Alternate merchant name (max 25c). (X(30))"
    )
    ForceNo3DS: Optional[str] = Field(
        None, description="'1' to force no 3DS, '0'/omit to use 3DS. (N(1))"
    )

    _validate_amount_values = field_validator("Amount", mode="before")(
        _validate_amount_field
    )
    _validate_itbis_values = field_validator("Itbis", mode="before")(
        _validate_itbis_field
    )


class PostSaleTransactionModel(BaseModel):
    """Model for post-authorization (capture) transactions (ProcessPost)."""

    Channel: str = Field(
        "EC", description="Payment channel (e.g., 'EC'), provided by AZUL. (X(3))"
    )
    Store: str = Field(
        ..., description="Unique merchant ID (MID), provided by AZUL. (X(11))"
    )
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

    _validate_amount_values = field_validator("Amount", mode="before")(
        _validate_amount_field
    )
    _validate_itbis_values = field_validator("Itbis", mode="before")(
        _validate_itbis_field
    )


class VerifyTransactionModel(BaseModel):
    """Model for verifying existing transactions using CustomOrderId (VerifyPayment)."""

    Channel: str = Field(
        "EC", description="Payment channel (e.g., 'EC'), provided by AZUL. (X(3))"
    )
    Store: str = Field(
        ..., description="Unique merchant ID (MID), provided by AZUL. (X(11))"
    )
    CustomOrderId: str = Field(
        ..., description="CustomOrderId of the original transaction to verify. (X(75))"
    )


class VoidTransactionModel(BaseModel):
    """Model for voiding transactions (ProcessVoid)."""

    Channel: str = Field(
        "EC", description="Payment channel (e.g., 'EC'), provided by AZUL. (X(3))"
    )
    Store: str = Field(
        ..., description="Unique merchant ID (MID), provided by AZUL. (X(11))"
    )
    AzulOrderId: str = Field(
        ..., description="AzulOrderId of the original transaction to void. (N(999))"
    )


class PaymentSchema(RootModel):
    """Root model for combining payment operations."""

    root: Union[
        SaleTransactionModel,
        HoldTransactionModel,
        RefundTransactionModel,
        DataVaultRequestModel,
        TokenSaleModel,
        PostSaleTransactionModel,
        VerifyTransactionModel,
        VoidTransactionModel,
    ]

    @classmethod
    def validate_payment(cls, value: dict) -> Union[
        SaleTransactionModel,
        HoldTransactionModel,
        RefundTransactionModel,
        DataVaultRequestModel,
        TokenSaleModel,
        PostSaleTransactionModel,
        VerifyTransactionModel,
        VoidTransactionModel,
    ]:
        """Validate and determine the appropriate model for the payment data."""
        # Attempt to identify by unique fields for non-TrxType models first
        if (
            "CustomOrderId" in value
            and "AzulOrderId" not in value
            and "Amount" not in value
            and "TrxType" not in value
        ):
            return VerifyTransactionModel(**value)

        if "AzulOrderId" in value:
            # Check for PostSale: AzulOrderId, Amount, Itbis, Channel, Store (5 fields)
            if (
                "Amount" in value
                and "Itbis" in value
                and "Channel" in value
                and "Store" in value
                and len(value) <= 5  # Heuristic: check number of keys
                and "TrxType" not in value
            ):
                return PostSaleTransactionModel(**value)
            # Check for Void: AzulOrderId, Channel, Store (3 fields)
            elif (
                "Channel" in value
                and "Store" in value
                and len(value) <= 3  # Heuristic
                and "TrxType" not in value
                and "Amount" not in value  # Differentiate from Post/Refund
            ):
                return VoidTransactionModel(**value)

        trx_type = value.get("TrxType")

        if trx_type == "CREATE":
            return DataVaultRequestModel(**value)
        elif trx_type == "DELETE":
            return DataVaultRequestModel(**value)
        elif trx_type == "Hold":
            return HoldTransactionModel(**value)
        elif trx_type == "Refund":
            if "AzulOrderId" in value and "Amount" in value:
                return RefundTransactionModel(**value)
        elif trx_type == "Sale":
            if "DataVaultToken" in value:
                return TokenSaleModel(**value)
            elif "CardNumber" in value:
                return SaleTransactionModel(**value)

        raise ValueError(f"Could not determine transaction model for input: {value}")


class PaymentPageModel(BaseModel):
    """
    Define the model for Azul Payment Page transactions.

    This model handles the payment form data and validation for Azul's Payment Page.
    It ensures all data is formatted according to Azul's specifications.

    Amount format:
    - All amounts are in cents.
    - They will be serialized to strings for the payment page POST.
    - Examples:
      * 1000 = $10.00
      * 1748321 = $17,483.21

    Usage example:
        payment = PaymentPageModel(
            Amount=100000,      # $1,000.00 (in cents)
            ITBIS=18000,       # $180.00 (in cents)
            ApprovedUrl=HttpUrl("https://example.com/approved"),
            DeclineUrl=HttpUrl("https://example.com/declined"),
            CancelUrl=HttpUrl("https://example.com/cancel")
        )
    """

    model_config = ConfigDict(validate_assignment=True)

    CurrencyCode: Literal["$"] = "$"
    OrderNumber: str = Field(
        default_factory=lambda: datetime.now().strftime("%Y%m%d%H%M%S"),
        description="Unique order ID. Defaults to current timestamp.",
    )

    Amount: str = Field(  # Represented in cents
        ..., description="Total amount including taxes, in cents."
    )
    ITBIS: str = Field(  # Represented in cents
        ..., description="Tax amount in cents. Use 0 for zero/exempt."
    )

    ApprovedUrl: HttpUrl
    DeclineUrl: HttpUrl
    CancelUrl: HttpUrl

    UseCustomField1: Literal["0", "1"] = "0"
    CustomField1Label: Optional[str] = ""
    CustomField1Value: Optional[str] = ""
    UseCustomField2: Literal["0", "1"] = "0"
    CustomField2Label: Optional[str] = ""
    CustomField2Value: Optional[str] = ""

    ShowTransactionResult: Literal["0", "1"] = "1"
    Locale: Literal["ES", "EN"] = "ES"

    SaveToDataVault: Optional[str] = None
    DataVaultToken: Optional[str] = None

    AltMerchantName: Optional[str] = Field(
        None,
        max_length=25,
        pattern=r"^[a-zA-Z0-9\s.,]*$",
        description="Alternate merchant name for display (max 25 chars)",
    )

    _validate_amount_values = field_validator("Amount", mode="before")(
        _validate_amount_field
    )
    _validate_itbis_values = field_validator("ITBIS", mode="before")(
        _validate_itbis_field
    )

    @field_validator("CustomField1Label", "CustomField1Value")
    def validate_custom_field1(cls, v: str, info) -> str:
        """Validate that custom field 1 values are provided when enabled."""
        if info.data.get("UseCustomField1") == "1" and not v:
            field_name = info.field_name
            raise ValueError(
                f'Custom field 1 {field_name} is required when UseCustomField1 is "1"'
            )
        return v

    @field_validator("CustomField2Label", "CustomField2Value")
    def validate_custom_field2(cls, v: str, info) -> str:
        """Validate that custom field 2 values are provided when enabled."""
        if info.data.get("UseCustomField2") == "1" and not v:
            field_name = info.field_name
            raise ValueError(
                f'Custom field 2 {field_name} is required when UseCustomField2 is "1"'
            )
        return v

    def __str__(self) -> str:
        """Return a string representation with formatted amounts in USD."""
        amount = int(self.Amount) / 100
        itbis = int(self.ITBIS) / 100
        return f"Payment Request - Amount: ${amount:.2f}, ITBIS: ${itbis:.2f}"
