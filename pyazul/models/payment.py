from typing import Optional
from pydantic import BaseModel, Field, field_validator, model_validator
from .base import BaseTransaction, CardData
from decimal import Decimal
from . import utils

class PaymentTransaction(BaseTransaction):
    Amount: Decimal = Field(..., gt=0)
    Itbis: Optional[Decimal] = Field(None, ge=0)
    Payments: str = Field("1")
    Plan: str = Field("0")
    EcommerceURL: Optional[str] = None
    CustomOrderID: Optional[str] = None
    
    @model_validator(mode='before')
    def clean_amount(cls, values):
        if 'Amount' in values:
            values['Amount'] = utils.clean_amount(values['Amount'])
        if 'Itbis' in values and values['Itbis']:
            values['Itbis'] = utils.clean_amount(values['Itbis'])
        return values

class SaleTransaction(PaymentTransaction):
    Card: CardData
    TrxType: str = Field("Sale", const=True)
    
    class Config:
        json_schema_extra = {
            "example": {
                "Channel": "EC",
                "Store": "39038540035",
                "Merchant": "39038540035",
                "Amount": "100.00",
                "Itbis": "18.00",
                "CurrencyPosCode": "$",
                "Card": {
                    "CardNumber": "4111111111111111",
                    "Expiration": "12/25",
                    "CVC": "123"
                }
            }
        }

class HoldTransaction(PaymentTransaction):
    Card: CardData
    TrxType: str = Field("Hold", const=True)

class RefundTransaction(PaymentTransaction):
    Card: CardData
    TrxType: str = Field("Refund", const=True)
    OriginalDate: str = Field(..., pattern=r"^\d{2}/\d{2}/\d{4}$")
    OriginalTrxTicket: str
    AzulOrderId: str
    
    @field_validator('OriginalDate')
    def validate_date(cls, v):
        from datetime import datetime
        try:
            datetime.strptime(v, '%d/%m/%Y')
        except ValueError:
            raise ValueError('Invalid date format')
        return v

class VoidTransaction(BaseTransaction):
    AzulOrderId: str
    TrxType: str = Field("Void", const=True)

class PostSaleTransaction(BaseModel):
    AzulOrderId: str
    Amount: Decimal
    Itbis: Optional[Decimal] = None
    
    @model_validator(mode='before')
    def clean_amounts(cls, values):
        if 'Amount' in values:
            values['Amount'] = utils.clean_amount(values['Amount'])
        if 'Itbis' in values and values['Itbis']:
            values['Itbis'] = utils.clean_amount(values['Itbis'])
        return values