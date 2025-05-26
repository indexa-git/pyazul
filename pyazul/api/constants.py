"""
This module contains constants and enums used throughout the Azul API client.

It defines environment types (DEV/PROD) and endpoint URLs for different environments.
The constants are used to configure the API client's behavior and routing.
"""

from enum import Enum


class Environment(str, Enum):
    """Represents the API environment (dev or prod)."""

    DEV = "dev"
    PROD = "prod"


class AzulEndpoints:
    """Holds the API endpoint URLs for different environments."""

    DEV_URL = "https://pruebas.azul.com.do/webservices/JSON/Default.aspx"
    PROD_URL = "https://pagos.azul.com.do/webservices/JSON/Default.aspx"
    ALT_PROD_URL = "https://contpagos.azul.com.do/Webservices/JSON/default.aspx"
    DEV_URL_PAYMEMT = "https://pruebas.azul.com.do/PaymentPage/"
    PROD_URL_PAYMEMT = "https://pagos.azul.com.do/PaymentPage/Default.aspx"
    ALT_PROD_URL_PAYMEMT = "https://contpagos.azul.com.do/PaymentPage/Default.aspx"

    @classmethod
    def get_url(cls, environment: Environment) -> str:
        """Get the base URL for the specified environment."""
        return cls.DEV_URL if environment == Environment.DEV else cls.PROD_URL
