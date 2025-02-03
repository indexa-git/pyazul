from models.datavault import DataVaultCreate, DataVaultDelete, DataVaultSaleTransaction
from api.client import AzulAPI
from typing import Dict, Any

class DataVaultService:
    """
    DataVaultService is a service that provides methods to interact with the Azul API.    
    It handles the validation and formatting of transaction data before sending it to the API, because using pydantic we can validate the data before sending it to the API.

      This aproach is more secure and easier to maintain because we can adding more methods to the service without breaking the API.
    """

    def __init__(self, client: AzulAPI):
        self.client = client    

    async def create(self, data: DataVaultCreate) -> Dict[str, Any]:
        validated_date = DataVaultCreate(**data).model_dump()
        return await self.client._async_request(validated_date)
    
    async def delete(self, data: DataVaultDelete) -> Dict[str, Any]:
        validated_date = DataVaultDelete(**data).model_dump()
        return await self.client._async_request(validated_date)
    
    async def sale(self, data: DataVaultSaleTransaction) -> Dict[str, Any]:
        validated_date = DataVaultSaleTransaction(**data).model_dump()
        return await self.client._async_request(validated_date)