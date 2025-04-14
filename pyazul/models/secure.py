"""
feat(models): Implement 3DS authentication models and validation

- Created SecureSaleRequest model for 3DS transactions with validation
- Implemented CardHolderInfo model with optional fields and documentation
- Added ThreeDSAuth model with URL validation and serialization
- Added ChallengeIndicator enum for authentication preferences
- Implemented custom validation for URLs and critical fields
- Improved data type handling and serialization formats
"""

from typing import Optional, Literal
from pydantic import BaseModel, Field, field_validator
from enum import Enum


class ChallengeIndicator(str,Enum):

        """

        Challenge indicator values for 3DS authentication
        These values indicate the merchant's preference for challenges during authentication.

        """
    
        NO_PREFERENCE = "01"  # No preference for challenge
        NO_CHALLENGE = "02"  # Prefer no challenge
        CHALLENGE = "03"  # Request Challenge
        MANDATE_CHALLENGE = "04"  # Challenge required by mandate


class CardHolderInfo(BaseModel):
    """
    Cardholder information model for 3DS authentication.
    This information helps the issuing bank assess transaction risk.
    """
    BillingAddressCity: str = Field(..., description="Billing address city")
    BillingAddressCountry: str = Field(..., description="Billing address country")
    BillingAddressLine1: str = Field(..., description="Billing address line 1")
    BillingAddressLine2: Optional[str] = Field(None, description="Billing address line 2")
    BillingAddressLine3: Optional[str] = Field(None, description="Billing address line 3")
    BillingAddressState: str = Field(..., description="Billing address state")
    BillingAddressZip: str = Field(..., description="Billing address ZIP/postal code")
    Email: str = Field(..., description="Cardholder email address")
    Name: str = Field(..., description="Cardholder name")
    PhoneHome: Optional[str] = Field(None, description="Home phone number")
    PhoneMobile: Optional[str] = Field(None, description="Mobile phone number")
    PhoneWork: Optional[str] = Field(None, description="Work phone number")
    ShippingAddressCity: str = Field(..., description="Shipping address city")
    ShippingAddressCountry: str = Field(..., description="Shipping address country")
    ShippingAddressLine1: str = Field(..., description="Shipping address line 1")
    ShippingAddressLine2: Optional[str] = Field(None, description="Shipping address line 2")
    ShippingAddressLine3: Optional[str] = Field(None, description="Shipping address line 3")
    ShippingAddressState: str = Field(..., description="Shipping address state/province")
    ShippingAddressZip: str = Field(..., description="Shipping address ZIP/postal code")


class ThreeDSAuth(BaseModel):

    """
        3DS Authentication parameters model.
        Contains URLs and preferences for 3DS authentication process.
    """
    
    TermUrl: str = Field(..., description="URL for receiving authentication results")
    MethodNotificationUrl: str = Field(..., description="URL for receiving 3DS method notifications")
    RequestChallengeIndicator: ChallengeIndicator = Field(
         ChallengeIndicator.CHALLENGE,
         description="Merchant's challenge preference"
    )

    @field_validator('TermUrl', 'MethodNotificationUrl')
    def validate_url(cls, v:str) -> str:
        """Validate URL format"""
        v_str = str(v)
        if not v_str.startswith(('http://', 'https://')):
            raise ValueError(f"Invalid URL: {v_str}")
        return v_str

    def model_dump(self, **kwargs):
        """Custom serialization method"""
        data = super().model_dump(**kwargs)
        return {
            "TermUrl": str(data["TermUrl"]),
            "MethodNotificationUrl": str(data["MethodNotificationUrl"]),
            "RequestChallengeIndicator": str(data["RequestChallengeIndicator"])
        }
  
class SecureSaleRequest(BaseModel):
     
     """
      Secure sale transaction request model.
      Combines payment information with 3DS authentication data.
     """
     Amount: int = Field(..., description="Transaction amount in cents")
     ITBIS: int = Field(..., description="Tax amount in cents")
     CardNumber: str = Field(..., description="Card number")
     CVC: str = Field(..., description="Card security code")
     Expiration: str = Field(..., description="Card expiration in YYYYMM format")
     OrderNumber: str = Field(..., description="Unique order identifier")
     Channel: str = Field("EC",description="Transaction channel")
     PosInputMode: str = Field("E-commerce",description="Entry mode")
     AcquirerRefData: Literal["0", "1"] = Field("1", description="Acquirer reference data")
     forceNo3DS: Literal["0", "1"] = Field("0", description="Force no 3DS flag")
     cardHolderInfo: CardHolderInfo
     threeDSAuth: ThreeDSAuth
class SecureTokenSale(BaseModel):
    """
    Model for processing token sales.
    """
    Amount: int = Field(..., description="Transaction amount in cents")
    ITBIS: int = Field(..., description="Tax amount in cents")
    Channel: str = Field("EC",description="Transaction channel")
    PosInputMode: str = Field("E-commerce",description="Entry mode")
    DataVaultToken: str = Field(..., description="DataVault token for the transaction")
    Expiration: str = Field("", description="Expiration date in YYYYMM format (required even with token)")
    CardNumber: str= Field("", description="Card number (optional when using token)")
    OrderNumber: str = Field(..., description="Unique order identifier")
    CVC: str = Field("", description="Security code (optional when using token)")
    TrxType: Literal["Sale"] = "Sale"
    CustomOrderId: Optional[str] = Field("", description="Merchant-provided identifier")
    AcquirerRefData: str = Field("1", description="AZUL Internal Use")
    forceNo3DS: Literal["0", "1"] = Field("0", description="Force no 3DS flag")
    cardHolderInfo: CardHolderInfo
    threeDSAuth: ThreeDSAuth 