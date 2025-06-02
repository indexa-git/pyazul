"""Handles HTTP communication with the Azul payment gateway."""

import json
import logging
import ssl
from typing import Any, Dict, NoReturn

import httpx

from pyazul.api.constants import AzulEndpoints, Environment
from pyazul.core.config import AzulSettings
from pyazul.core.exceptions import APIError, AzulResponseError, SSLError

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

    def __init__(self, settings: AzulSettings):
        """Initialize AzulAPI using provided configuration."""
        self.settings = settings
        self._init_configuration()
        self._init_client_config()

    def _init_configuration(self) -> None:
        """Initialize basic configuration from settings."""
        if self.settings.AUTH1 is None:
            raise ValueError(
                "AUTH1 is not set in settings; essential for API authentication."
            )
        self.auth1 = self.settings.AUTH1

        if self.settings.AUTH2 is None:
            raise ValueError(
                "AUTH2 is not set in settings; essential for API authentication."
            )
        self.auth2 = self.settings.AUTH2
        self.ssl_context = self._load_certificates()
        self.ENVIRONMENT = Environment(self.settings.ENVIRONMENT)
        self.url = self._get_base_url()
        if self.ENVIRONMENT == Environment.PROD:
            # Prioritize user-defined ALT_PROD_URL from settings, fallback to constant
            self.ALT_URL = self.settings.ALT_PROD_URL or AzulEndpoints.ALT_PROD_URL

    def _load_certificates(self) -> ssl.SSLContext:
        """Load and validate certificates into an SSL context."""
        try:
            cert_path, key_path = self.settings._load_certificates()
            if not all((cert_path, key_path)):
                raise SSLError("Invalid certificate configuration")

            ssl_context = ssl.create_default_context()
            ssl_context.load_cert_chain(cert_path, key_path)
            return ssl_context
        except Exception as e:
            raise SSLError(f"Error loading certificates: {str(e)}") from e

    def _init_client_config(self) -> None:
        """Initialize HTTP client configuration."""
        self.timeout = httpx.Timeout(30.0, read=30.0)
        self.base_headers = {
            "Content-Type": "application/json",
        }

    def _get_base_url(self) -> str:
        """Get the base URL based on environment."""
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
        headers["Auth1"] = self.auth1
        headers["Auth2"] = self.auth2
        return headers

    def _prepare_request(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare request data with required parameters from settings.

        Ensures Channel & Store are always sourced from SDK settings.

        Args:
            data: The input dictionary representing the request payload.

        Returns:
            The modified dictionary with Channel and Store updated from settings.
        """
        # Always use Channel & Store from settings, overriding model values if present.
        data["Channel"] = self.settings.CHANNEL
        data["Store"] = self.settings.MERCHANT_ID
        return data  # Return the modified data, None filtering is handled by model_dump

    def _handle_response(self, response: httpx.Response) -> Dict[str, Any]:
        """
        Handle API response and check for errors.

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
        """Check for errors in API response data based on Azul documentation."""
        response_code = data.get("ResponseCode", "")
        iso_code = data.get("IsoCode", "")
        response_message = data.get("ResponseMessage", "")
        error_description = data.get("ErrorDescription", "")

        # Handle system errors (ResponseCode = "Error")
        if response_code == "Error":
            error_msg = error_description or "System error occurred"
            _logger.error(f"System Error: {error_msg}")
            raise AzulResponseError(f"System Error: {error_msg}", response_data=data)

        # Handle ISO8583 responses
        if response_code == "ISO8583":
            # Success case (IsoCode = "00")
            if iso_code == "00":
                _logger.debug("Transaction approved")
                return

            # 3DS special cases - these are processing states, not final results
            if iso_code in ["3D", "3D2METHOD"]:
                _logger.info(f"3DS processing required: {response_message}")
                return

            # All other ISO codes are declines - treat as normal responses
            if error_description and response_message:
                # Both available - use ResponseMessage as title,
                # ErrorDescription as detail
                decline_reason = f"{response_message}: {error_description}"
            elif error_description:
                # Only ErrorDescription available
                decline_reason = error_description
            elif response_message:
                # Only ResponseMessage available
                decline_reason = response_message
            else:
                # Neither available - use ISO code fallback
                decline_reason = f"Declined (ISO: {iso_code})"
            _logger.info(f"Transaction declined: {decline_reason}")
            return

        # Handle legacy error patterns and unexpected response structures
        if error_description and "SGS-" in error_description:
            # System gateway errors should be treated as exceptions
            system_error_types = [
                "timeout",
                "not been processed",
                "Internal Server Error",
                "Unauthorized",
                "Server Unavailable",
                "SSL/TLS",
                "connection",
            ]
            if any(
                error_type in error_description for error_type in system_error_types
            ):
                _logger.error(f"Gateway Error: {error_description}")
                raise AzulResponseError(
                    f"Gateway Error: {error_description}", response_data=data
                )
            else:
                # Business rule errors (like invalid card type) - treat as declines
                _logger.info(f"Transaction declined: {error_description}")
                return

        # If we have an ErrorMessage, it's typically a system error
        error_message = data.get("ErrorMessage")
        if error_message:
            _logger.error(f"API Error: {error_message}")
            raise AzulResponseError(f"API Error: {error_message}", response_data=data)

        # If we reach here with no clear response pattern, log and return
        # (avoid throwing exceptions for unknown but potentially valid responses)
        if response_code or iso_code or response_message:
            _logger.debug(
                f"Response received - Code: {response_code}, ISO: {iso_code}, "
                f"Message: {response_message}"
            )
        else:
            _logger.warning(
                "Received response with unclear structure",
                extra={"response_data": data},
            )

    def _log_and_raise_api_error(
        self, error: Exception, response: httpx.Response
    ) -> NoReturn:
        """Log and raise API error."""
        if isinstance(error, httpx.HTTPStatusError):
            _logger.error(f"HTTP error occurred: {response.text}")
            raise APIError(f"HTTP {response.status_code}: {response.text}")
        elif isinstance(error, json.JSONDecodeError):
            _logger.error(f"Invalid JSON response: {error}")
            raise APIError("Invalid JSON response from API")
        _logger.error(f"An unexpected error occurred: {error}")
        raise APIError(f"An unexpected error type was handled: {str(error)}")

    def _get_request_config(self, is_secure: bool = False) -> Dict[str, Any]:
        """Get common request configuration."""
        return {
            "headers": self._get_request_headers(is_secure),
            "timeout": self.timeout,
        }

    async def _async_request(
        self,
        data: Dict[str, Any],
        operation: str = "",
        retry_on_fail: bool = True,
        is_secure: bool = False,
    ) -> Dict[str, Any]:
        """
        Make async request to Azul API.

        Args:
            data: Request data to send
            operation: Optional operation name to append to URL
            retry_on_fail: Whether to retry with alternate URL on failure
                           (production only)
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
                        endpoint, json=parameters, **self._get_request_config(is_secure)
                    )
                    return self._handle_response(response)
                except (httpx.HTTPError, APIError) as e:
                    if retry_on_fail and self.ENVIRONMENT == Environment.PROD:
                        _logger.info("Retrying request with alternate URL")
                        alt_endpoint = f"{self.ALT_URL}?{operation}"
                        response = await client.post(
                            alt_endpoint,
                            json=parameters,
                            **self._get_request_config(is_secure),
                        )
                        return self._handle_response(response)
                    raise APIError(f"Request failed: {str(e)}") from e
        except Exception as err:
            _logger.error(f"Request failed: {str(err)}")
            raise APIError(f"Request failed: {str(err)}") from err

    def _build_endpoint(self, operation: str = "") -> str:
        """Build the full endpoint URL."""
        return f"{self.url}?{operation}" if operation else self.url

    async def post(
        self,
        endpoint: str,
        data: Dict[str, Any],
        is_secure: bool = False,
        retry_on_fail: bool = True,
    ) -> Dict[str, Any]:
        """
        Make a POST request to the Azul API.

        Args:
            endpoint: API endpoint (e.g., "/webservices/JSON/default.aspx")
            data: Request data to send
            is_secure: Whether this is a secure (3DS) request
            retry_on_fail: Whether to retry with alternate URL on failure

        Returns:
            Dict with API response

        Raises:
            APIError: If request fails
        """
        # Extract operation from endpoint query parameters
        operation = ""
        if "?" in endpoint:
            operation = endpoint.split("?", 1)[1]

        return await self._async_request(
            data=data,
            operation=operation,
            retry_on_fail=retry_on_fail,
            is_secure=is_secure,
        )
