"""Pytest configuration and fixtures for PyAzul tests."""

import pytest

from pyazul.core.config import get_azul_settings


@pytest.fixture(scope="session")
def settings():
    """Provide AzulSettings for tests, loaded once per session."""
    return get_azul_settings()
