from typing import Optional, Union, Literal
from pydantic import BaseModel, Field, RootModel, HttpUrl, field_validator, ConfigDict
from datetime import datetime
"""
This module defines the data models and schemas for the Azul payment gateway integration.
It contains Pydantic models that handle:
- Payment transactions (sales, holds, refunds, Post, Void, Verify)
- DataVault operations (token creation and deletion)
- Card tokenization
- Input validation and type checking
- Payment Page transactions

These models ensure data consistency and proper formatting when communicating with 
the Azul API endpoints. Each model includes field validations and descriptions
to maintain compliance with Azul's API specifications.
"""

class AzulBaseModel(BaseModel):
    """
    Base model for all Azul payment operations.
    """
    Channel: str = Field("EC", description="Payment channel provided by AZUL")
    PosInputMode: str = Field("E-Commerce", description="Entry mode provided by AZUL")
    Amount: str = Field('', description="Total amount (including taxes). Format: no decimals, e.g., 1000 = $10.00")
    Itbis: Optional[str] = Field(None, description="Tax value (ITBIS). Same format as amount")

class SaleTransactionModel(AzulBaseModel):
    """
    Model for processing sales transactions.
    """
    CardNumber: str = Field(..., description="Card number without special characters")
    Expiration: str = Field(..., description="Expiration date in YYYYMM format")
    CVC: str = Field(..., description="Security code")
    TrxType: Literal["Sale"] = "Sale"
    AcquirerRefData: str = Field("1", description="AZUL Internal Use")
    CustomOrderId: Optional[str] = Field("", description="Merchant-provided identifier")
    SaveToDataVault: str = Field("2", description="1 = save to vault, 2 = don't save")

class HoldTransactionModel(AzulBaseModel):
    """
    Model for processing hold transactions.
    """
    CardNumber: str = Field(..., description="Card number without special characters")
    Expiration: str = Field(..., description="Expiration date in YYYYMM format")
    CVC: str = Field(..., description="Security code")
    TrxType: Literal["Hold"] = "Hold"
    AcquirerRefData: str = Field("1", description="AZUL Internal Use")
    CustomOrderId: Optional[str] = Field("", description="Merchant-provided identifier")

class RefundTransactionModel(AzulBaseModel):
    """
    Model for processing refund transactions.
    """
    AzulOrderId: str = Field(..., description="Order number provided by AZUL")
    TrxType: Literal["Refund"] = "Refund"

class DataVaultCreateModel(AzulBaseModel):
    """
    Model for creating DataVault tokens.
    """
    CardNumber: str = Field(..., description="Card number without special characters")
    Expiration: str = Field(..., description="Expiration date in YYYYMM format")
    store: str = Field(..., description="Merchant ID provided by AZUL")
    CustomOrderId: Optional[str] = Field("", description="Merchant-provided identifier")
    TrxType: Literal["CREATE"] = "CREATE"

class DataVaultDeleteModel(AzulBaseModel):
    """
    Model for deleting DataVault tokens.
    """
    DataVaultToken: str = Field(..., description="DataVault token to delete")
    TrxType: Literal["DELETE"] = "DELETE"
    store: str = Field(..., description="Merchant ID provided by AZUL")

class TokenSaleModel(AzulBaseModel):
    """
    Model for processing token sales.
    """
    DataVaultToken: str = Field(..., description="DataVault token for the transaction")
    Expiration: str = Field("", description="Expiration date in YYYYMM format")
    CardNumber: str = Field("", description="Card number (optional when using token)")
    CVC: str = Field("", description="Security code (optional when using token)")
    TrxType: Literal["Sale"] = "Sale"
    CustomOrderId: Optional[str] = Field("", description="Merchant-provided identifier")
    AcquirerRefData: str = Field("1", description="AZUL Internal Use")

class PostSaleTransactionModel(HoldTransactionModel):
    """
    Model for processing post sale transactions.
    """
    TrxType: Literal["Post"] = "Post"
    AzulOrderId: str = Field(..., description="Order number provided by AZUL")
    ApprovedUrl: str = Field(..., description="URL to redirect to when transaction is approved")
    DeclinedUrl: str = Field(..., description="URL to redirect to when transaction is declined")
    CancelUrl: str = Field(..., description="URL to redirect to when transaction is cancelled")
    UseCustomField1: str = Field("1", description="1 = use custom field 1, 0 = don't use")

class VerifyTransactionModel(AzulBaseModel):
    """
    Model for verifying transactions.
    """
    CustomOrderId: str = Field(..., description="identifier merge with transaction to verify")
   
class VoidTransactionModel(AzulBaseModel):
    """
    Model for voiding transactions.
    """
    AzulOrderId: str = Field(..., description="Order number provided by AZUL")
    store: str = Field(..., description="Merchant ID provided by AZUL")
   
class PaymentSchema(RootModel):
    """
    Root model for combining payment operations.
    """
    root: Union[SaleTransactionModel, HoldTransactionModel, RefundTransactionModel, DataVaultCreateModel, DataVaultDeleteModel, TokenSaleModel]
    
    @classmethod
    def validate(cls, value: dict) -> Union[SaleTransactionModel, HoldTransactionModel, RefundTransactionModel, DataVaultCreateModel]:
        if 'data_vault_token' in value and value['data_vault_token']:
            return DataVaultCreateModel(**value)
        return SaleTransactionModel(**value)

class PaymentPageModel(BaseModel):
    """
    Model for Azul Payment Page transactions.
    
    This model handles the payment form data and validation for Azul's Payment Page.
    It ensures all data is formatted according to Azul's specifications.
    
    Amount format:
    - All amounts must be sent without commas or decimal points
    - Last two digits represent decimals
    - Examples:
      * 1000 = $10.00
      * 1748321 = $17,483.21
      * 000 = $0.00 (for zero ITBIS)
    
    Usage example:
        payment = PaymentPageModel(
            Amount="100000",      # $1,000.00
            ITBIS="18000",       # $180.00
            ApprovedUrl="https://example.com/approved",
            DeclineUrl="https://example.com/declined",
            CancelUrl="https://example.com/cancel"
        )
    """
    model_config = ConfigDict(validate_assignment=True)

    # Basic transaction data
    CurrencyCode: Literal["$"] = "$"
    OrderNumber: str = Field(
        default_factory=lambda: datetime.now().strftime("%Y%m%d%H%M%S"),
        description="Unique order identifier. Defaults to current timestamp."
    )
    
    # Amount fields
    Amount: str = Field(
        ..., 
        pattern=r'^\d+$', 
        description="Total amount including taxes. Format: 1000 = $10.00"
    )
    ITBIS: str = Field(
        "", 
        pattern=r'^\d+$', 
        description="Tax amount. Format: 1000 = $10.00, use '000' for zero"
    )
    
    # URLs for transaction results
    ApprovedUrl: HttpUrl
    DeclineUrl: HttpUrl
    CancelUrl: HttpUrl
    
    # Custom fields
    UseCustomField1: Literal["0", "1"] = "0"
    CustomField1Label: Optional[str] = ""
    CustomField1Value: Optional[str] = ""
    UseCustomField2: Literal["0", "1"] = "0"
    CustomField2Label: Optional[str] = ""
    CustomField2Value: Optional[str] = ""
    
    # Additional settings
    ShowTransactionResult: Literal["0", "1"] = "1"
    Locale: Literal["ES", "EN"] = "ES"
    
    # DataVault settings (optional)
    SaveToDataVault: Optional[str] = None
    DataVaultToken: Optional[str] = None
    
    # Merchant settings
    AltMerchantName: Optional[str] = Field(
        None,
        max_length=25,
        pattern=r'^[a-zA-Z0-9\s.,]*$',
        description="Alternative merchant name to display (max 25 chars)"
    )

    @field_validator('Amount', 'ITBIS')
    def validate_amounts(cls, v: str, info) -> str:
        """
        Validate amount format.
        
        Rules:
        - Must be a valid number without decimals
        - For ITBIS = 0, must use "000"
        """
        # Si es número, convertirlo a string
        if isinstance(v, (int, float)):
            v = str(int(v))
        
        # Validar que sea un número válido
        if not v.isdigit():
            raise ValueError("Amount must be a number without decimals")
            
        # Para ITBIS cero, asegurar formato "000"
        if info.field_name == 'ITBIS' and int(v) == 0:
            return "000"
            
        return v

    @field_validator('CustomField1Label', 'CustomField1Value')
    def validate_custom_field1(cls, v: str, info) -> str:
        """Validate that custom field 1 values are provided when enabled"""
        if info.data.get('UseCustomField1') == '1' and not v:
            field_name = info.field_name
            raise ValueError(f'Custom field 1 {field_name} is required when UseCustomField1 is "1"')
        return v

    @field_validator('CustomField2Label', 'CustomField2Value')
    def validate_custom_field2(cls, v: str, info) -> str:
        """Validate that custom field 2 values are provided when enabled"""
        if info.data.get('UseCustomField2') == '1' and not v:
            field_name = info.field_name
            raise ValueError(f'Custom field 2 {field_name} is required when UseCustomField2 is "1"')
        return v

    def __str__(self) -> str:
        """
        String representation with formatted amounts in USD.
        Example: "Payment Request - Amount: $1,000.00, ITBIS: $180.00"
        """
        amount = float(self.Amount) / 100
        itbis = float(self.ITBIS) / 100 if self.ITBIS != "000" else 0.00
        return (
            f"Payment Request - "
            f"Amount: ${amount:.2f}, "
            f"ITBIS: ${itbis:.2f}"
        )