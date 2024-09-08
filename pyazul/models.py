from pydantic import BaseModel, Field, field_validator
from typing import Optional
from decimal import Decimal


def clean_amount(amount: str) -> int:
    if not isinstance(amount, str) or not amount.replace(".", "", 1).isdigit():
        raise ValueError("Invalid amount format")

    return int(round(Decimal(amount) * 100, 0))


class AzulBaseModel(BaseModel):
    Channel: str
    Store: str


class TransactionWithAmountModel(AzulBaseModel):
    Amount: str
    Itbis: Optional[str] = Field(default=None)

    @field_validator("Amount", "Itbis", mode="before")
    @classmethod
    def clean_amounts(cls, v):
        return str(clean_amount(v)) if v is not None else v

    @field_validator("Itbis", mode="after")
    @classmethod
    def set_itbis(cls, v):
        if v is None or v == "0":
            return None
        return v

    # This function makes sure to not add 'Itbis' in the dict, unless there's a value.
    # Azul documentation doesn't specify that it will fail if sent empty.
    def model_dump(self, *args, **kwargs):
        data = super().model_dump(*args, **kwargs)
        if data.get("Itbis") is None:
            data.pop("Itbis", None)
        return data


class DataVaultCreateModel(AzulBaseModel):
    CardNumber: str
    Expiration: str
    CVC: str
    TrxType: str = Field(default="CREATE", frozen=True)


class DataVaultDeleteModel(AzulBaseModel):
    DataVaultToken: str
    TrxType: str = Field(default="DELETE", frozen=True)


class SaleTransactionModel(TransactionWithAmountModel):
    CardNumber: str = ""
    Expiration: str = ""
    CVC: str = ""
    PosInputMode: str = "E-Commerce"
    TrxType: str = Field(default="Sale", frozen=True)
    Payments: str = "1"
    Plan: str = "0"
    CurrencyPosCode: str
    AcquirerRefData: str = "1"
    CustomerServicePhone: str
    OrderNumber: str
    EcommerceURL: str
    CustomOrderID: str


class HoldTransactionModel(TransactionWithAmountModel):
    CardNumber: str = ""
    Expiration: str = ""
    CVC: str = ""
    PosInputMode: str = "E-Commerce"
    TrxType: str = Field(default="Hold", frozen=True)
    Payments: str = "1"
    Plan: str = "0"
    CurrencyPosCode: str
    OrderNumber: str


class PostSaleTransactionModel(TransactionWithAmountModel):
    AzulOrderId: str


class NullifyTransactionModel(SaleTransactionModel):
    pass


class RefundTransactionModel(SaleTransactionModel):
    TrxType: str = Field(default="Refund", frozen=True)
    OriginalDate: str
    OriginalTrxTicketNr: str
    AzulOrderId: str


class VoidTransactionModel(AzulBaseModel):
    AzulOrderId: str


class DataVaultSaleTransactionModel(TransactionWithAmountModel):
    PosInputMode: str = "E-Commerce"
    TrxType: str = Field(default="Sale", frozen=True)
    CurrencyPosCode: str
    Payments: str = "1"
    Plan: str = "0"
    AcquirerRefData: str = "1"
    OrderNumber: str
    DataVaultToken: str


class VerifyTransactionModel(AzulBaseModel):
    CustomOrderId: str
