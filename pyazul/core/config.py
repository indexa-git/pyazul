from typing import Optional, Any
from pydantic_settings import BaseSettings, SettingsConfigDict
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
    CHANNEL: str = "EC"

    # Certificate Settings
    AZUL_CERT: str
    AZUL_KEY: str

    # Optional Settings
    ENVIRONMENT: str = "dev"
    CUSTOM_URL: Optional[str] = None

    # Service URLs
    DEV_URL: str 
    PROD_URL: str 
    ALT_PROD_URL: str 

    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        case_sensitive=True,
        extra='allow'
    )

    @classmethod
    def parse_env_var(cls, field_name: str, raw_val: str) -> Any:
        if field_name == "MERCHANT_ID":
            return str(raw_val.strip("'\""))
        return raw_val

@lru_cache()
def get_azul_settings() -> AzulSettings:
    return AzulSettings() 