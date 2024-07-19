import logging
from typing import Optional, Literal
from pydantic import BaseModel, HttpUrl, Field
import httpx

from .models import (
    SaleTransactionModel,
    HoldTransactionModel,
    PostSaleTransactionModel,
    RefundTransactionModel,
    VoidTransactionModel,
    VerifyTransactionModel,
    DataVaultCreateModel,
    DataVaultDeleteModel,
)

_logger = logging.getLogger(__name__)

class AzulAPIConfig(BaseModel):
    auth1: str
    auth2: str
    certificate_path: Optional[str] = Field(default=None) # This is mandatory, but made it optional for unit tests
    custom_url: Optional[HttpUrl] = None
    environment: Literal["dev", "prod"] = "dev"

class AzulAPI:
    def __init__(self, config: AzulAPIConfig):
        self.config = config
        self.url = config.custom_url or self._get_default_url()

    def _get_default_url(self) -> str:
        if self.config.environment == "dev":
            return "https://pruebas.azul.com.do/webservices/JSON/Default.aspx"
        return "https://pagos.azul.com.do/webservices/JSON/Default.aspx"

    async def azul_request(self, data: BaseModel, operation: str = ""):
        azul_endpoint = f"{self.url}?{operation}"
        headers = {
            "Content-Type": "application/json",
            "Auth1": self.config.auth1,
            "Auth2": self.config.auth2,
        }
        _logger.debug(f"azul_request: called with data:\n{data.model_dump_json()}")

        client_kwargs = {}
        if self.config.certificate_path:
            client_kwargs["cert"] = self.config.certificate_path

        try:
            async with httpx.AsyncClient(**client_kwargs) as client:
                r = await client.post(
                    azul_endpoint,
                    json=data.model_dump(),
                    headers=headers,
                    timeout=30,
                )
                await r.raise_for_status()
        except httpx.HTTPStatusError as err:
            if self.config.environment == "prod" and not self.config.custom_url:
                alt_url = "https://contpagos.azul.com.do/Webservices/JSON/default.aspx"
                azul_endpoint = f"{alt_url}?{operation}"
                r = await client.post(
                    azul_endpoint,
                    json=data.model_dump(),
                    headers=headers,
                    timeout=30,
                )
                await r.raise_for_status()
            else:
                raise
        except Exception as err:
            _logger.error(f"azul_request: Got the following error\n{err}")
            raise

        response = r.json()
        _logger.debug(f"azul_request: Values received\n{response}")
        return response

    async def sale_transaction(self, data: SaleTransactionModel):
        return await self.azul_request(data)

    async def hold_transaction(self, data: HoldTransactionModel):
        return await self.azul_request(data)

    async def refund_transaction(self, data: RefundTransactionModel):
        return await self.azul_request(data)

    async def void_transaction(self, data: VoidTransactionModel):
        return await self.azul_request(data, operation="ProcessVoid")

    async def post_sale_transaction(self, data: PostSaleTransactionModel):
        return await self.azul_request(data, operation="ProcessPost")

    async def verify_transaction(self, data: VerifyTransactionModel):
        return await self.azul_request(data, operation="VerifyPayment")

    async def datavault_create(self, data: DataVaultCreateModel):
        return await self.azul_request(data, operation="ProcessDatavault")

    async def datavault_delete(self, data: DataVaultDeleteModel):
        return await self.azul_request(data, operation="ProcessDatavault")