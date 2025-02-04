from typing import Optional, Union, Literal
from pydantic import BaseModel, Field, RootModel
"""
This module defines the data models and schemas for the Azul payment gateway integration.
It contains Pydantic models that handle:
- Payment transactions (sales, holds, refunds)
- DataVault operations (token creation and deletion)
- Card tokenization
- Input validation and type checking

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
    Amount: str = Field(..., description="Total amount (including taxes). Format: no decimals, e.g., 1000 = $10.00")
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



