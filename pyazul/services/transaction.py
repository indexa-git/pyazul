from typing import Dict, Any
from models.payment import SaleTransaction, HoldTransaction, RefundTransaction, VoidTransaction, PostSaleTransaction
from models.datavault import VerifyTransaction
from api.client import AzulAPI

class TransactionService:

    """
    TransactionService is a service that provides methods to interact with the Azul API.    
    It handles the validation and formatting of transaction data  because using pydantic we can validate the data before sending it to the API.

    This aproach is more secure and easier to maintain because we can adding more methods to the service without breaking the API.
    """


    def __init__(self, client: AzulAPI):
        self.client = client

    async def sale(self, data: Dict[str, Any]) -> Dict[str, Any]:
        validated_data = SaleTransaction(**data).model_dump()
        return await self.client._async_request(validated_data)

    async def hold(self, data: Dict[str, Any]) -> Dict[str, Any]:
        validated_data = HoldTransaction(**data).model_dump()
        return await self.client._async_request(validated_data)

    async def refund(self, data: Dict[str, Any]) -> Dict[str, Any]:
        validated_data = RefundTransaction(**data).model_dump()
        return await self.client._async_request(validated_data) 
    
    async def void(self, data:Dict[str, Any]) -> Dict[str, Any]:
        validated_data = VoidTransaction(**data).model_dump()
        return await self.client._async_request(validated_data)
    
    async def post_sale(self, data: Dict[str, Any]) -> Dict[str, Any]:
        validated_data = PostSaleTransaction(**data).model_dump()
        return await self.client._async_request(validated_data)
    
    async def verify(self, data: Dict[str, Any]) -> Dict[str, Any]:
        validated_data = VerifyTransaction(**data).model_dump()
        return await self.client._async_request(validated_data)
    
    
        