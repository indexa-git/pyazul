from pydantic import BaseModel
from typing import Optional, Literal
from datetime import date

class AzulBaseModel(BaseModel):
    Channel: str
    Store: str

class SaleTransactionModel(AzulBaseModel):
    CardNumber: str
    Expiration: str
    CVC: str
    PosInputMode: str = "E-Commerce"
    TrxType: Literal["Sale"] = "Sale"
    Payments: str = "1"
    Plan: str = "0"
    Amount: int
    CurrencyPosCode: str
    AcquirerRefData: str = "1"
    CustomerServicePhone: str
    OrderNumber: str
    EcommerceURL: str
    CustomOrderID: str
    Itbis: Optional[int] = None

class HoldTransactionModel(AzulBaseModel):
    CardNumber: str
    Expiration: str
    CVC: str
    PosInputMode: str = "E-Commerce"
    TrxType: Literal["Hold"] = "Hold"
    Payments: str = "1"
    Plan: str = "0"
    Amount: int
    CurrencyPosCode: str
    OrderNumber: str
    Itbis: Optional[int] = None

class PostSaleTransactionModel(AzulBaseModel):
    AzulOrderId: str
    Amount: int
    Itbis: Optional[int] = None

class RefundTransactionModel(AzulBaseModel):
    CardNumber: str
    Expiration: str
    CVC: str
    PosInputMode: str = "E-Commerce"
    TrxType: Literal["Refund"] = "Refund"
    Payments: str = "1"
    Plan: str = "0"
    Amount: int
    CurrencyPosCode: str
    OriginalDate: date
    OriginalTrxTicketNr: str
    AcquirerRefData: str = "1"
    CustomerServicePhone: str
    OrderNumber: str
    EcommerceURL: str
    CustomOrderID: str
    AzulOrderId: str
    Itbis: Optional[int] = None

class VoidTransactionModel(AzulBaseModel):
    AzulOrderId: str

class VerifyTransactionModel(AzulBaseModel):
    CustomOrderId: str

class DataVaultCreateModel(AzulBaseModel):
    CardNumber: str
    Expiration: str
    CVC: str
    TrxType: Literal["CREATE"] = "CREATE"

class DataVaultDeleteModel(AzulBaseModel):
    DataVaultToken: str
    TrxType: Literal["DELETE"] = "DELETE"