from typing import Optional, Any, Tuple
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache
from dotenv import load_dotenv
import os
import base64
from pathlib import Path

# Load .env file with override=True to ensure values are loaded
load_dotenv(override=True)

class AzulSettings(BaseSettings):
    # Payment Page Settings
    AZUL_MERCHANT_ID: str
    AZUL_AUTH_KEY: str
    MERCHANT_NAME: str
    MERCHANT_TYPE: str

    # Authentication Settings
    AUTH1: str
    AUTH2: str
    AUTH1_3D: str = ""
    AUTH2_3D: str = ""
    MERCHANT_ID: str
    CHANNEL: str = "EC"

    # Certificate Settings
    AZUL_CERT: Optional[str] = None
    AZUL_KEY: Optional[str] = None

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
        if field_name in ["MERCHANT_ID", "AZUL_CERT", "AZUL_KEY"]:
            return str(raw_val.strip("'\""))
        return raw_val

    def _load_certificates(self) -> Tuple[str, str]:
        """
        Load certificates from environment variables.
        Supports three formats:
        1. File paths
        2. Direct PEM content
        """
        cert_value = os.getenv('AZUL_CERT', '').strip("'\"")
        key_value = os.getenv('AZUL_KEY', '').strip("'\"")
        
        temp_dir = Path.home() / '.pyazul' / 'certs'
        temp_dir.mkdir(mode=0o700, parents=True, exist_ok=True)
        
        def is_valid_file_path(path_str: str) -> bool:
            """Check if string is a valid file path"""
            try:
                path = Path(path_str)
                return path.is_file() and path.exists()
            except Exception:
                return False
        
        def is_pem_content(content: str, cert_type: str = 'CERTIFICATE') -> bool:
            """Check if string contains PEM markers"""
            begin = f"-----BEGIN {cert_type}-----"
            end = f"-----END {cert_type}-----"
            return begin in content and end in content
        
        def is_base64(s: str) -> bool:
            """Check if string is base64 encoded"""
            try:
                decoded = base64.b64decode(s.rstrip('%')).decode('utf-8')
                return is_pem_content(decoded) or is_pem_content(decoded, 'PRIVATE KEY')
            except Exception:
                return False
            
        def write_cert(path: Path, content: str, is_base64: bool = False) -> None:
            """Write certificate content to file"""
            try:
                data = base64.b64decode(content.rstrip('%')) if is_base64 else content.encode('utf-8')
                with open(path, 'wb') as f:
                    f.write(data)
                path.chmod(0o600)
            except Exception as e:
                raise ValueError(f"Error writing certificate: {str(e)}")
        
        # Process certificate
        cert_path = temp_dir / 'azul_cert.crt'
        if is_valid_file_path(cert_value):
            cert_path = Path(cert_value)
        elif is_pem_content(cert_value):
            write_cert(cert_path, cert_value)
        else:
            raise ValueError("Invalid certificate format: Must be a valid file path, PEM content, or base64 encoded PEM")
        
        # Process key
        key_path = temp_dir / 'azul_key.key'
        if is_valid_file_path(key_value):
            key_path = Path(key_value)
        elif is_pem_content(key_value, 'PRIVATE KEY'):
            write_cert(key_path, key_value)
        elif is_base64(key_value):
            write_cert(key_path, key_value, True)
        else:
            raise ValueError("Invalid key format: Must be a valid file path, PEM content, or base64 encoded PEM")
        
        return str(cert_path), str(key_path)

@lru_cache()
def get_azul_settings() -> AzulSettings:
    return AzulSettings() 