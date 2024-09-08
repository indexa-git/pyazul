import json
import logging
from typing import Dict, Any, Optional

import httpx
from . import models

_logger = logging.getLogger(__name__)


class AzulAPI:
    def __init__(
        self,
        auth1: str,
        auth2: str,
        certificate_path: str,
        custom_url: Optional[str] = None,
        environment: str = "dev",
    ):
        """
        :param auth1: str
        :param auth2: str
        :param certificate_path: str (path to your .p12 certificate)
        :param environment: str (defaults 'dev' can also be set to 'prod')
        :param custom_url: Optional[str] (defaults None, custom azul webservice url)
        """
        self.certificate_path: str = certificate_path
        self.auth1: str = auth1
        self.auth2: str = auth2
        self.ENVIRONMENT: str = environment

        if custom_url:
            self.url: str = custom_url
        else:
            if environment == "dev":
                self.url: str = (
                    "https://pruebas.azul.com.do/webservices/JSON/Default.aspx"
                )
            else:
                self.url: str = (
                    "https://pagos.azul.com.do/webservices/JSON/Default.aspx"
                )
                self.ALT_URL: str = (
                    "https://contpagos.azul.com.do/Webservices/JSON/default.aspx"
                )

        self.client: httpx.Client = httpx.Client(cert=self.certificate_path)

    def __del__(self) -> None:
        self.client.close()

    def azul_request(self, data: Dict[str, Any], operation: str = "") -> Dict[str, Any]:
        #  Required parameters for all transactions
        parameters: Dict[str, str] = {
            "Channel": data.get("Channel", ""),
            "Store": data.get("Store", ""),
        }

        # Updating parameters with the extra parameters
        parameters.update(data)

        azul_endpoint: str = self.url + f"?{operation}"

        headers: Dict[str, str] = {
            "Content-Type": "application/json",
            "Auth1": self.auth1,
            "Auth2": self.auth2,
        }
        r: httpx.Response = {}
        _logger.debug("azul_request: called with data:\n%s", data)

        try:
            r = self.client.post(
                azul_endpoint,
                json=parameters,
                headers=headers,
                timeout=30,
            )
            if r.raise_for_status() and self.ENVIRONMENT == "prod":
                azul_endpoint = self.ALT_URL + f"?{operation}"
                r = self.client.post(
                    azul_endpoint,
                    json=parameters,
                    headers=headers,
                    timeout=30,
                )
        except Exception as err:
            _logger.error("azul_request: Got the following error\n%s", str(err))
            raise Exception(str(err))

        response: Dict[str, Any] = json.loads(r.text)
        _logger.debug("azul_request: Values received\n%s", json.loads(r.text))

        return response

    def sale_transaction(self, data: Dict[str, Any]) -> Dict[str, Any]:
        validated_data: Dict[str, Any] = models.SaleTransactionModel(**data).model_dump(
            exclude_none=True
        )
        return self.azul_request(validated_data)

    def hold_transaction(self, data: Dict[str, Any]) -> Dict[str, Any]:
        validated_data: Dict[str, Any] = models.HoldTransactionModel(**data).model_dump(
            exclude_none=True
        )
        return self.azul_request(validated_data)

    def refund_transaction(self, data: Dict[str, Any]) -> Dict[str, Any]:
        validated_data: Dict[str, Any] = models.RefundTransactionModel(
            **data
        ).model_dump(exclude_none=True)
        return self.azul_request(validated_data)

    def void_transaction(self, data: Dict[str, Any]) -> Dict[str, Any]:
        validated_data: Dict[str, Any] = models.VoidTransactionModel(**data).model_dump(
            exclude_none=True
        )
        return self.azul_request(validated_data, operation="ProcessVoid")

    def post_sale_transaction(self, data: Dict[str, Any]) -> Dict[str, Any]:
        validated_data: Dict[str, Any] = models.PostSaleTransactionModel(
            **data
        ).model_dump(exclude_none=True)
        return self.azul_request(validated_data, operation="ProcessPost")

    def verify_transaction(self, data: Dict[str, Any]) -> Dict[str, Any]:
        validated_data: Dict[str, Any] = models.VerifyTransactionModel(
            **data
        ).model_dump(exclude_none=True)
        return self.azul_request(validated_data, operation="VerifyPayment")

    def nulify_transaction(self, data: Dict[str, Any]) -> Dict[str, Any]:
        validated_data: Dict[str, Any] = models.NullifyTransactionModel(
            **data
        ).model_dump(exclude_none=True)
        return self.azul_request(validated_data)

    def datavault_create(self, data: Dict[str, Any]) -> Dict[str, Any]:
        validated_data: Dict[str, Any] = models.DataVaultCreateModel(**data).model_dump(
            exclude_none=True
        )
        return self.azul_request(validated_data, operation="ProcessDatavault")

    def datavault_delete(self, data: Dict[str, Any]) -> Dict[str, Any]:
        validated_data: Dict[str, Any] = models.DataVaultDeleteModel(**data).model_dump(
            exclude_none=True
        )
        return self.azul_request(validated_data, operation="ProcessDatavault")


class AzulAPIAsync(AzulAPI):
    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self.client: httpx.AsyncClient = httpx.AsyncClient(cert=self.certificate_path)

    async def __aenter__(self) -> "AzulAPIAsync":
        return self

    async def __aexit__(
        self,
        exc_type: Optional[type],
        exc_value: Optional[Exception],
        traceback: Optional[Any],
    ) -> None:
        await self.client.aclose()

    async def azul_request(
        self, data: Dict[str, Any], operation: str = ""
    ) -> Dict[str, Any]:
        #  Required parameters for all transactions
        parameters: Dict[str, str] = {
            "Channel": data.get("Channel", ""),
            "Store": data.get("Store", ""),
        }

        # Updating parameters with the extra parameters
        parameters.update(data)

        azul_endpoint: str = self.url + f"?{operation}"

        headers: Dict[str, str] = {
            "Content-Type": "application/json",
            "Auth1": self.auth1,
            "Auth2": self.auth2,
        }
        r: httpx.Response = {}
        _logger.debug("azul_request: called with data:\n%s", data)

        try:
            r = await self.client.post(
                azul_endpoint,
                json=parameters,
                headers=headers,
                timeout=30,
            )
            if r.raise_for_status() and self.ENVIRONMENT == "prod":
                azul_endpoint = self.ALT_URL + f"?{operation}"
                r = await self.client.post(
                    azul_endpoint,
                    json=parameters,
                    headers=headers,
                    timeout=30,
                )
        except Exception as err:
            _logger.error("azul_request: Got the following error\n%s", str(err))
            raise Exception(str(err))

        response: Dict[str, Any] = json.loads(r.text)
        _logger.debug("azul_request: Values received\n%s", json.loads(r.text))

        return response

    async def sale_transaction(self, data: Dict[str, Any]) -> Dict[str, Any]:
        validated_data: Dict[str, Any] = models.SaleTransactionModel(**data).model_dump(
            exclude_none=True
        )
        return await self.azul_request(validated_data)

    async def hold_transaction(self, data: Dict[str, Any]) -> Dict[str, Any]:
        validated_data: Dict[str, Any] = models.HoldTransactionModel(**data).model_dump(
            exclude_none=True
        )
        return await self.azul_request(validated_data)

    async def refund_transaction(self, data: Dict[str, Any]) -> Dict[str, Any]:
        validated_data: Dict[str, Any] = models.RefundTransactionModel(
            **data
        ).model_dump(exclude_none=True)
        return await self.azul_request(validated_data)

    async def void_transaction(self, data: Dict[str, Any]) -> Dict[str, Any]:
        validated_data: Dict[str, Any] = models.VoidTransactionModel(**data).model_dump(
            exclude_none=True
        )
        return await self.azul_request(validated_data, operation="ProcessVoid")

    async def post_sale_transaction(self, data: Dict[str, Any]) -> Dict[str, Any]:
        validated_data: Dict[str, Any] = models.PostSaleTransactionModel(
            **data
        ).model_dump(exclude_none=True)
        return await self.azul_request(validated_data, operation="ProcessPost")

    async def verify_transaction(self, data: Dict[str, Any]) -> Dict[str, Any]:
        validated_data: Dict[str, Any] = models.VerifyTransactionModel(
            **data
        ).model_dump(exclude_none=True)
        return await self.azul_request(validated_data, operation="VerifyPayment")

    async def nulify_transaction(self, data: Dict[str, Any]) -> Dict[str, Any]:
        validated_data: Dict[str, Any] = models.NullifyTransactionModel(
            **data
        ).model_dump(exclude_none=True)
        return await self.azul_request(validated_data)

    async def datavault_create(self, data: Dict[str, Any]) -> Dict[str, Any]:
        validated_data: Dict[str, Any] = models.DataVaultCreateModel(**data).model_dump(
            exclude_none=True
        )
        return await self.azul_request(validated_data, operation="ProcessDatavault")

    async def datavault_delete(self, data: Dict[str, Any]) -> Dict[str, Any]:
        validated_data: Dict[str, Any] = models.DataVaultDeleteModel(**data).model_dump(
            exclude_none=True
        )
        return await self.azul_request(validated_data, operation="ProcessDatavault")
