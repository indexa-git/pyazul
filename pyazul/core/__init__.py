"""
Core module for PyAzul.

Contains base classes, configuration, exceptions, and session management.
"""

from .base import BaseService
from .config import AzulSettings, get_azul_settings
from .exceptions import AzulError

__all__ = ["get_azul_settings", "AzulSettings", "AzulError", "BaseService"]
