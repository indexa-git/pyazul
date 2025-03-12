"""
Core module for PyAzul package.
Contains configuration and base functionality.
"""

from .config import get_azul_settings, AzulSettings
from .exceptions import AzulError
from .base import BaseService

__all__ = [
    'get_azul_settings',
    'AzulSettings',
    'AzulError',
    'BaseService'
] 