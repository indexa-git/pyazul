from typing import Optional, Any
from pydantic_settings import BaseSettings
from functools import lru_cache
from dotenv import load_dotenv

# Load .env file
load_dotenv()

class AzulSettings(BaseSettings):
    # Payment Page Settings
    AZUL_MERCHANT_ID: str
    AZUL_AUTH_KEY: str

    # Authentication Settings
    AUTH1: str
    AUTH2: str
    AUTH1_3D: str = "3dsecure"
    AUTH2_3D: str = "3dsecure"
    MERCHANT_ID: str

    # Certificate Settings
    AZUL_CERT: str
    AZUL_KEY: str

    # Optional Settings
    ENVIRONMENT: str = "dev"
    CUSTOM_URL: Optional[str] = None

    # Service URLs
    DEV_URL: str = "https://pruebas.azul.com.do/webservices/JSON/Default.aspx"
    PROD_URL: str = "https://pagos.azul.com.do/webservices/JSON/Default.aspx"
    ALT_PROD_URL: str = "https://contpagos.azul.com.do/Webservices/JSON/default.aspx"

    class Config:
        env_file = '.env'
        env_file_encoding = 'utf-8'
        case_sensitive = True

        @classmethod
        def parse_env_var(cls, field_name: str, raw_val: str) -> Any:
            if field_name == "MERCHANT_ID":
                # Remove quotes if present and ensure it's treated as string
                return str(raw_val.strip("'\""))
            return raw_val

@lru_cache()
def get_azul_settings() -> AzulSettings:
    return AzulSettings() 