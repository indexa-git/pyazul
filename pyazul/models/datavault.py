from pydantic import BaseModel, Field
from .base import BaseTransaction, CardData
from .payment import PaymentTransaction


class DataVaultCreate(BaseTransaction):
    Card: CardData
    CustomerId: str = Field(..., description="Customer identifier")
    TrxType: str = Field("CREATE", const=True)

class DataVaultDelete(BaseTransaction):
    CustomerId: str
    DataVaultToken: str
    TrxType: str = Field("DELETE", const=True)

class DataVaultSaleTransaction(PaymentTransaction):
    DataVaultToken: str
    TrxType: str = Field("Sale", const=True)

class VerifyTransaction(BaseModel):
    CustomOrderId: str 