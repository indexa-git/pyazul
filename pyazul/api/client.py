import json
import logging
from typing import Any, Dict

import httpx
from pyazul.core.config import get_azul_settings
from pyazul.core.exceptions import APIError, AzulResponseError
from pyazul.api.constants import Environment, AzulEndpoints

_logger = logging.getLogger(__name__)

class AzulAPI:
    """
    AzulAPI is the main client class for interacting with the Azul payment gateway.
    
    It handles all HTTP communication with Azul's API endpoints, including:
    - Payment processing (sales, refunds, voids)
    - DataVault operations (tokenization)
    - Authentication and request signing
    - Certificate management
    - Environment-specific configuration
    
    The client automatically loads configuration from environment variables
    and handles all the low-level details of making secure API requests.
    """
    def __init__(self):
        """Initialize AzulAPI using configuration from environment variables"""
        self.settings = get_azul_settings()
        self._init_configuration()
        self._init_client_config()

    def _init_configuration(self) -> None:
        """Initialize basic configuration from settings"""
        self.auth1 = self.settings.AUTH1
        self.auth2 = self.settings.AUTH2
        self.certificate = (self.settings.AZUL_CERT, self.settings.AZUL_KEY)
        self.ENVIRONMENT = Environment(self.settings.ENVIRONMENT)
        # URL Configuration
        self.url = self._get_base_url()
        if self.ENVIRONMENT == Environment.PROD:
            self.ALT_URL = AzulEndpoints.ALT_PROD_URL

    def _init_client_config(self) -> None:
        """Initialize HTTP client configuration"""
        self.timeout = httpx.Timeout(30.0, read=30.0)
        self.headers = {
            'Content-Type': 'application/json',
            'Auth1': self.auth1,
            'Auth2': self.auth2,
        }

    def _get_base_url(self) -> str:
        """Get the base URL based on environment"""
        if self.settings.CUSTOM_URL:
            return self.settings.CUSTOM_URL
        return AzulEndpoints.get_url(self.ENVIRONMENT)

    def _build_endpoint(self, operation: str = '') -> str:
        """Build the full endpoint URL"""
        return f"{self.url}?{operation}" if operation else self.url

    def _prepare_request(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Prepare request data with required parameters
        
        Args:
            data: Request data dictionary
            
        Returns:
            Dict with prepared parameters
        """
        required_params = {
            'Channel': self.settings.CHANNEL,
            'Store': self.settings.MERCHANT_ID,
        }
        return {**required_params, **data}

    def _handle_response(self, response: httpx.Response) -> Dict[str, Any]:
        """
        Handle API response and check for errors
        
        Args:
            response: HTTPX response object
            
        Returns:
            Dict with API response
            
        Raises:
            AzulResponseError: If API returns an error
        """
        try:
            response.raise_for_status()
            data = response.json()
            print(data)
            
            if ('ErrorMessage' in data and data['ErrorMessage']) or \
               ('ErrorDescription' in data and data['ErrorDescription']) or \
               ('ResponseCode' in data and data['ResponseCode'] == 'Error'):
                error_msg = data.get('ErrorMessage') or data.get('ErrorDescription', 'Unknown error')
                error_code = data.get('IsoCode', '')
                raise AzulResponseError(
                    f"API Error: {error_msg} - {error_code}",
                    response_data=data
                )
            
            return data
            
        except httpx.HTTPStatusError as e:
            _logger.error(f"HTTP error occurred: {e.response.text}")
            raise APIError(f"HTTP {e.response.status_code}: {e.response.text}")
        except json.JSONDecodeError as e:
            _logger.error(f"Invalid JSON response: {e}")
            raise APIError("Invalid JSON response from API")

    def _get_request_config(self) -> Dict[str, Any]:
        """Get common request configuration"""
        return {
            'headers': self.headers,
            'timeout': self.timeout
        }

    async def _make_request(
        self,
        client: httpx.AsyncClient,
        endpoint: str,
        parameters: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Make request and handle response"""
        _logger.debug(f"Making request to {endpoint} with data: {parameters}")
        
        # Configurar el cliente con los certificados
        client.cert = self.certificate[0]  # Certificado
        client.private_key = self.certificate[1]  # Llave privada
        
        response = await client.post(
            endpoint,
            json=parameters,
            **self._get_request_config()
        )
        return self._handle_response(response)

    async def _async_request(
        self, 
        data: Dict[str, Any], 
        operation: str = '',
        retry_on_fail: bool = True
    ) -> Dict[str, Any]:
        """Make async request to Azul API"""
        parameters = self._prepare_request(data)
        endpoint = self._build_endpoint(operation)
        
        try:
            async with httpx.AsyncClient(
                verify=False,  # Temporalmente para pruebas
                cert=(self.settings.AZUL_CERT, self.settings.AZUL_KEY)
            ) as client:
                try:
                    return await self._make_request(client, endpoint, parameters)
                except APIError as e:
                    if retry_on_fail and self.ENVIRONMENT == Environment.PROD:
                        _logger.info("Retrying request with alternate URL")
                        alt_endpoint = f"{self.ALT_URL}?{operation}"
                        return await self._make_request(client, alt_endpoint, parameters)
                    raise APIError(f"Request failed: {str(e)}")
        except Exception as err:
            _logger.error(f"Request failed: {str(err)}")
            raise APIError(f"Request failed: {str(err)}")
