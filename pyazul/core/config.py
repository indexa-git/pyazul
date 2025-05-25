"""
Configuration management for PyAzul.

This module defines the `AzulSettings` class, which loads configuration
from environment variables and .env files. It also provides utility
functions for accessing these settings.
"""

import base64
import os
from functools import lru_cache
from pathlib import Path
from typing import Any, Optional, Self, Tuple

from dotenv import load_dotenv
from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Load .env file with override=True to ensure values are loaded
load_dotenv(override=True)


class AzulSettings(BaseSettings):
    """
    Manages configuration settings for the PyAzul library.

    Loads settings from environment variables and a .env file.
    It includes credentials, API endpoints, and certificate configurations.
    """

    # Payment Page Settings
    AZUL_MERCHANT_ID: Optional[str] = None
    AZUL_AUTH_KEY: Optional[str] = None
    MERCHANT_NAME: Optional[str] = None
    MERCHANT_TYPE: Optional[str] = None

    # Authentication Settings
    AUTH1: Optional[str] = None
    AUTH2: Optional[str] = None
    AUTH1_3D: str = ""
    AUTH2_3D: str = ""
    MERCHANT_ID: Optional[str] = None
    CHANNEL: str = "EC"

    # Certificate Settings
    AZUL_CERT: Optional[str] = None
    AZUL_KEY: Optional[str] = None

    # Optional Settings
    ENVIRONMENT: str = "dev"
    CUSTOM_URL: Optional[str] = None

    # Service URLs
    DEV_URL: Optional[str] = None
    PROD_URL: Optional[str] = None
    ALT_PROD_URL: Optional[str] = None
    ALT_PROD_URL_PAYMENT: Optional[str] = None

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=True, extra="allow"
    )

    @classmethod
    def parse_env_var(cls, field_name: str, raw_val: str) -> Any:
        """Parse specific environment variables."""
        if field_name in ["MERCHANT_ID", "AZUL_CERT", "AZUL_KEY"]:
            return str(raw_val.strip("'\""))
        return raw_val

    def _load_certificates(self) -> Tuple[str, str]:
        """
        Load SSL certificates from environment variables.

        Certificates can be provided as file paths, direct PEM content,
        or base64 encoded PEM content. They are loaded and written to
        temporary files if necessary.
        """
        cert_value = os.getenv("AZUL_CERT", "").strip("'\"")
        key_value = os.getenv("AZUL_KEY", "").strip("'\"")

        temp_dir = Path.home() / ".pyazul" / "certs"
        temp_dir.mkdir(mode=0o700, parents=True, exist_ok=True)

        def is_valid_file_path(path_str: str) -> bool:
            """Check if a string is a valid and existing file path."""
            try:
                path = Path(path_str)
                return path.is_file() and path.exists()
            except Exception:
                return False

        def is_pem_content(content: str, cert_type: str = "CERTIFICATE") -> bool:
            """Check if a string contains PEM markers for certificates or keys."""
            begin = f"-----BEGIN {cert_type}-----"
            end = f"-----END {cert_type}-----"
            return begin in content and end in content

        def is_base64(s: str) -> bool:
            """Check if a string is a base64 encoded PEM content."""
            try:
                decoded = base64.b64decode(s.rstrip("%")).decode("utf-8")
                return is_pem_content(decoded) or is_pem_content(decoded, "PRIVATE KEY")
            except Exception:
                return False

        def write_cert(path: Path, content: str, is_base64: bool = False) -> None:
            """Write certificate content to a file with restricted permissions."""
            try:
                data = (
                    base64.b64decode(content.rstrip("%"))
                    if is_base64
                    else content.encode("utf-8")
                )
                with open(path, "wb") as f:
                    f.write(data)
                path.chmod(0o600)
            except Exception as e:
                raise ValueError(f"Error writing certificate: {str(e)}") from e

        # Process certificate
        cert_path = temp_dir / "azul_cert.crt"
        if is_valid_file_path(cert_value):
            cert_path = Path(cert_value)
        elif is_pem_content(cert_value):
            write_cert(cert_path, cert_value)
        else:
            raise ValueError(
                "Invalid certificate format: Must be a valid file path, PEM content, "
                "or base64 encoded PEM."
            )

        # Process key
        key_path = temp_dir / "azul_key.key"
        if is_valid_file_path(key_value):
            key_path = Path(key_value)
        elif is_pem_content(key_value, "PRIVATE KEY"):
            write_cert(key_path, key_value)
        elif is_base64(key_value):
            write_cert(key_path, key_value, True)
        else:
            raise ValueError(
                "Invalid key format: Must be a valid file path, PEM content, "
                "or base64 encoded PEM."
            )

        return str(cert_path), str(key_path)

    @model_validator(mode="after")
    def _ensure_required_fields_are_set(self) -> Self:
        """Validate that all required configuration fields are set."""
        # Always required fields
        always_required_fields = {
            "AZUL_MERCHANT_ID": self.AZUL_MERCHANT_ID,
            "AZUL_AUTH_KEY": self.AZUL_AUTH_KEY,
            "MERCHANT_NAME": self.MERCHANT_NAME,
            "MERCHANT_TYPE": self.MERCHANT_TYPE,
            "AUTH1": self.AUTH1,
            "AUTH2": self.AUTH2,
            "MERCHANT_ID": self.MERCHANT_ID,
        }

        missing_fields = [
            name for name, value in always_required_fields.items() if value is None
        ]

        # Environment-specific URL requirements
        if self.ENVIRONMENT == "dev":
            if self.DEV_URL is None:
                missing_fields.append("DEV_URL")
        elif self.ENVIRONMENT == "prod":
            if self.PROD_URL is None:
                missing_fields.append("PROD_URL")
            # ALT_PROD_URL is optional. If set, it overrides the default alternate URL
            # for 'prod' environment retries used by the API client.
            # ALT_PROD_URL_PAYMENT is optional and allows overriding the constant
            # defined in AzulEndpoints. The PaymentPageService should be designed
            # to allow selection between primary and this alternate URL.
        # else:
        # ENVIRONMENT has a default ('dev'), and pydantic would typically handle
        # validation if it were an Enum. If it can be other values,
        # one might add a warning here, but for 'dev'/'prod' this is sufficient.

        if missing_fields:
            raise ValueError(
                "The following required settings are missing or not set in the "
                f"environment: {', '.join(missing_fields)}"
            )
        return self


@lru_cache()
def get_azul_settings() -> AzulSettings:
    """Return a cached instance of AzulSettings."""
    return AzulSettings()
