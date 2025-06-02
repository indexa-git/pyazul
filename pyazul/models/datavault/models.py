"""
DataVault (tokenization) models for PyAzul.

This module defines Pydantic models for card tokenization operations,
including token creation, deletion, and token-based payments.
"""

from typing import Literal, Optional, Union

from pydantic import BaseModel, Field, field_validator

from ..payment.models import BaseTransaction
from ..schemas import AzulBase, _validate_amount_field, _validate_itbis_field


class TokenRequest(AzulBase):
    """Model for DataVault token creation and deletion requests."""

    TrxType: str = Field(
        ...,
        pattern="^(CREATE|DELETE)$",
        description="Transaction type: 'CREATE' or 'DELETE'.",
    )
    CardNumber: Optional[str] = Field(
        default=None,
        pattern=r"^[0-9]{13,19}$",
        description="Card number for CREATE. (N(19))",
    )
    Expiration: Optional[str] = Field(
        default=None,
        pattern=r"^(20[2-9][0-9]|2[1-9][0-9]{2})(0[1-9]|1[0-2])$",
        description="Expiration date in YYYYMM format for CREATE. (N(6))",
    )
    CVC: Optional[str] = Field(
        default=None,
        pattern=r"^[0-9]{3,4}$",
        description="Card security code for CREATE. (N(3-4))",
    )
    DataVaultToken: Optional[str] = Field(
        default=None,
        pattern=r"^[A-Fa-f0-9\-]{30,40}$",
        description="Token to delete for DELETE operations. (A(100))",
    )


class TokenSuccess(BaseModel):
    """Model for successful DataVault responses."""

    CardNumber: str = Field(..., description="Masked card number")
    DataVaultToken: str = Field(..., description="Generated token")
    DataVaultBrand: str = Field(..., description="Card brand (e.g., 'VISA')")
    DataVaultExpiration: str = Field(..., description="Token expiration YYYYMM")
    ErrorDescription: str = Field("", description="Empty for success")
    HasCVV: bool = Field(..., description="Whether token includes CVV")
    IsoCode: str = Field(..., description="'00' for success")
    ResponseMessage: str = Field(..., description="Success message")
    type: Literal["success"] = Field("success", description="Response type indicator")

    @classmethod
    def from_api_response(cls, data: dict) -> "TokenSuccess":
        """Create a TokenSuccess from API response data."""
        return cls(
            CardNumber=data.get("CardNumber", ""),
            DataVaultToken=data.get("DataVaultToken", ""),
            DataVaultBrand=data.get(
                "Brand", ""
            ),  # API uses 'Brand', not 'DataVaultBrand'
            DataVaultExpiration=data.get("Expiration", ""),  # API uses 'Expiration'
            ErrorDescription="",
            HasCVV=data.get("HasCVV", False),
            IsoCode=data.get("ISOCode", "00"),
            ResponseMessage=data.get("ResponseMessage", ""),
            type="success",
        )


class TokenError(BaseModel):
    """Model for failed DataVault responses."""

    CardNumber: str = Field("", description="Empty card number for errors")
    DataVaultToken: str = Field("", description="Empty token for errors")
    DataVaultBrand: str = Field("", description="Empty brand for errors")
    DataVaultExpiration: str = Field("", description="Empty expiration for errors")
    ErrorDescription: str = Field(..., description="Error description")
    HasCVV: bool = Field(False, description="False for errors")
    IsoCode: str = Field(..., description="Error ISO code (not '00')")
    ResponseMessage: str = Field(..., description="Error response message")
    type: Literal["error"] = Field("error", description="Response type indicator")

    @classmethod
    def from_api_response(cls, data: dict) -> "TokenError":
        """Create a TokenError from API response data."""
        return cls(
            CardNumber="",
            DataVaultToken="",
            DataVaultBrand="",
            DataVaultExpiration="",
            ErrorDescription=data.get("ErrorDescription", "Unknown error"),
            HasCVV=False,
            IsoCode=data.get("IsoCode", "99"),
            ResponseMessage=data.get("ResponseMessage", "ERROR"),
            type="error",
        )


# Union type for DataVault responses
TokenResponse = Union[TokenSuccess, TokenError]


class TokenSale(BaseTransaction):
    """Model for sales transactions using a DataVault token."""

    Amount: str = Field(  # Represented in cents
        ...,
        pattern=r"^[1-9][0-9]{0,11}$",
        description="Total amount in cents (e.g., 1000 for $10.00). Serialized to str.",
    )
    Itbis: Optional[str] = Field(  # Represented in cents
        default="000",
        pattern=r"^[0-9]{1,12}$",
        description="ITBIS in cents (optional for TokenSale). Serialized to str.",
    )
    DataVaultToken: str = Field(
        ...,
        pattern=r"^[A-Fa-f0-9\-]{30,40}$",
        description="DataVault token for the transaction. (A(100))",
    )
    TrxType: str = Field(
        default="Sale",
        pattern="^Sale$",
        description="Transaction type, must be 'Sale'. (A(16))",
    )
    CVC: Optional[str] = Field(
        default=None,
        min_length=3,
        max_length=4,
        pattern=r"^[0-9]{3,4}$",
        description="CVC (optional with token, E-comm mandatory). (N(3-4))",
    )
    CardNumber: Optional[str] = Field(
        default="", description="Card number, empty for token sales. (N(19))"
    )
    Expiration: Optional[str] = Field(
        default="",
        description="Expiration date (YYYYMM), empty for token sales. (N(6))",
    )

    _validate_token_sale_amount_values = field_validator("Amount", mode="before")(
        _validate_amount_field
    )
    _validate_token_sale_itbis_values = field_validator("Itbis", mode="before")(
        _validate_itbis_field
    )
