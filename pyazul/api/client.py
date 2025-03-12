import json
import logging
import ssl
from typing import Any, Dict

import httpx
from pyazul.core.config import get_azul_settings
from pyazul.core.exceptions import APIError, AzulResponseError, SSLError
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
        self.ssl_context = self._load_certificates()
        self.ENVIRONMENT = Environment(self.settings.ENVIRONMENT)
        self.url = self._get_base_url()
        if self.ENVIRONMENT == Environment.PROD:
            self.ALT_URL = AzulEndpoints.ALT_PROD_URL

    def _load_certificates(self) -> ssl.SSLContext:
        """Load and validate certificates into an SSL context"""
        try:
            cert_path, key_path = self.settings._load_certificates()
            if not all((cert_path, key_path)):
                raise SSLError("Invalid certificate configuration")
            
            ssl_context = ssl.create_default_context()
            ssl_context.load_cert_chain(cert_path, key_path)
            return ssl_context
        except Exception as e:
            raise SSLError(f"Error loading certificates: {str(e)}")

    def _init_client_config(self) -> None:
        """Initialize HTTP client configuration"""
        self.timeout = httpx.Timeout(30.0, read=30.0)
        self.base_headers = {
            'Content-Type': 'application/json',
        }

    def _get_base_url(self) -> str:
        """Get the base URL based on environment"""
        if self.settings.CUSTOM_URL:
            return self.settings.CUSTOM_URL
        return AzulEndpoints.get_url(self.ENVIRONMENT)

    def _get_request_headers(self, is_secure: bool = False) -> Dict[str, Any]:
        """
        Get request headers based on whether it's a secure (3DS) request or not.
        
        Args:
            is_secure (bool): Whether this is a secure (3DS) request
            
        Returns:
            Dict[str, Any]: Headers dictionary with appropriate authentication
        """
        headers = self.base_headers.copy()
        if is_secure:
            headers['Auth1'] = self.settings.AUTH1_3D
            headers['Auth2'] = self.settings.AUTH2_3D
        else:
            headers['Auth1'] = self.auth1
            headers['Auth2'] = self.auth2
        return headers

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
            _logger.debug(f"Received response: {json.dumps(data, indent=2)}")
            self._check_for_errors(data)
            return data
        except (httpx.HTTPStatusError, json.JSONDecodeError) as e:
            self._log_and_raise_api_error(e, response)

    def _check_for_errors(self, data: Dict[str, Any]) -> None:
        """Check for errors in API response data"""
        error_indicators = [
            ('ErrorMessage', data.get('ErrorMessage')),
            ('ErrorDescription', data.get('ErrorDescription')),
            ('ResponseCode', data.get('ResponseCode') == 'Error')
        ]
        for field, value in error_indicators:
            if value:
                error_msg = data.get('ErrorMessage') or data.get('ErrorDescription', 'Unknown error')
                error_code = data.get('IsoCode', '')
                _logger.error(f"API Error: {error_msg} - {error_code}")
                raise AzulResponseError(
                    f"API Error: {error_msg} - {error_code}",
                    response_data=data
                )

    def _log_and_raise_api_error(self, error: Exception, response: httpx.Response) -> None:
        """Log and raise API error"""
        if isinstance(error, httpx.HTTPStatusError):
            _logger.error(f"HTTP error occurred: {response.text}")
            raise APIError(f"HTTP {response.status_code}: {response.text}")
        elif isinstance(error, json.JSONDecodeError):
            _logger.error(f"Invalid JSON response: {error}")
            raise APIError("Invalid JSON response from API")

    def _get_request_config(self, is_secure: bool = False) -> Dict[str, Any]:
        """Get common request configuration"""
        return {
            'headers': self._get_request_headers(is_secure),
            'timeout': self.timeout
        }

    async def _async_request(
        self, 
        data: Dict[str, Any], 
        operation: str = '',
        retry_on_fail: bool = True,
        is_secure: bool = False
    ) -> Dict[str, Any]:
        """
        Make async request to Azul API.
        
        Args:
            data: Request data to send
            operation: Optional operation name to append to URL
            retry_on_fail: Whether to retry with alternate URL on failure (production only)
            is_secure: Whether this is a secure (3DS) request
            
        Returns:
            Dict with API response
            
        Raises:
            APIError: If request fails
        """
        parameters = self._prepare_request(data)
        endpoint = self._build_endpoint(operation)
        
        _logger.debug(f"Making request to {endpoint} with data: {parameters}")
        
        try:
            async with httpx.AsyncClient(verify=self.ssl_context) as client:
                try:
                    response = await client.post(
                        endpoint,
                        json=parameters,
                        **self._get_request_config(is_secure)
                    )
                    return self._handle_response(response)
                except (httpx.HTTPError, APIError) as e:
                    if retry_on_fail and self.ENVIRONMENT == Environment.PROD:
                        _logger.info("Retrying request with alternate URL")
                        alt_endpoint = f"{self.ALT_URL}?{operation}"
                        response = await client.post(
                            alt_endpoint,
                            json=parameters,
                            **self._get_request_config(is_secure)
                        )
                        return self._handle_response(response)
                    raise APIError(f"Request failed: {str(e)}")
        except Exception as err:
            _logger.error(f"Request failed: {str(err)}")
            raise APIError(f"Request failed: {str(err)}")
