"""
Payment Page models for PyAzul.

This module defines Pydantic models for Azul's hosted Payment Page functionality,
including form generation, validation, and data formatting.
"""

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator

from ..schemas import _validate_amount_field, _validate_itbis_field


class PaymentPage(BaseModel):
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
        payment = PaymentPage(
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
        default=None,
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
