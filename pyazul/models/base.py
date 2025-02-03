from typing import Optional
from pydantic import BaseModel, Field, field_validator

class BaseTransaction(BaseModel):
    Channel: str = Field(..., description="Channel identifier")
    Store: str = Field(..., description="Store identifier")
    Merchant: str = Field(..., description="Merchant identifier")
    PosInputMode: str = Field("E-Commerce", description="Input mode")
    CurrencyPosCode: str = Field("$", description="Currency symbol")
    OrderNumber: Optional[str] = None
    CustomerServicePhone: Optional[str] = None
    AcquirerRefData: str = Field("1")
    
    @field_validator('Store', 'Merchant')
    def validate_numeric_string(cls, v):
        if not v.isdigit():
            raise ValueError('Must be a numeric string')
        return v

class CardData(BaseModel):
    CardNumber: str = Field(..., min_length=13, max_length=19)
    Expiration: str = Field(..., pattern=r"^(0[1-9]|1[0-2])/([0-9]{2})$")
    CVC: str = Field(..., min_length=3, max_length=4)
    
    @field_validator('CardNumber')
    def validate_card_number(cls, v):
        if not v.isdigit():
            raise ValueError('Card number must contain only digits')
        return v