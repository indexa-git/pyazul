from enum import Enum
"""
This module contains constants and enums used throughout the Azul API client.
It defines environment types (DEV/PROD) and endpoint URLs for different environments.
The constants are used to configure the API client's behavior and routing.
"""


class Environment(str, Enum):
    DEV = "dev"
    PROD = "prod"

class AzulEndpoints:
    DEV_URL = "https://pruebas.azul.com.do/webservices/JSON/Default.aspx"
    PROD_URL = "https://pagos.azul.com.do/webservices/JSON/Default.aspx"
    ALT_PROD_URL = "https://contpagos.azul.com.do/Webservices/JSON/default.aspx"
    DEV_URL_PAYMEMT = "https://pruebas.azul.com.do/PaymentPage/"
    PROD_URL_PAYMEMT = "https://pagos.azul.com.do/PaymentPage/"

    @classmethod
    def get_url(cls, environment: Environment) -> str:
        return cls.DEV_URL if environment == Environment.DEV else cls.PROD_URL