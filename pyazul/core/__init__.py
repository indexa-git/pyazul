"""
Core module for PyAzul package.
Contains configuration and base functionality.
"""

from .base import BaseService
from .config import AzulSettings, get_azul_settings
from .exceptions import AzulError

__all__ = ["get_azul_settings", "AzulSettings", "AzulError", "BaseService"]
