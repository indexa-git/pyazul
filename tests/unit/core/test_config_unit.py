"""Unit tests for pyazul.core.config."""

import os
from unittest.mock import patch

import pytest

from pyazul.core.config import AzulSettings


@pytest.fixture(scope="session", autouse=True)
def mock_load_dotenv_session_wide():
    """Patch dotenv.load_dotenv session-wide to reduce .env influence.

    Note: This might not prevent an initial load if .env is loaded at module import time
    before this patch takes effect for all code paths. Tests should be robust to this.
    """
    with patch("pyazul.core.config.load_dotenv", return_value=False) as mock_load:
        yield mock_load


@pytest.fixture
def azul_settings_test_factory(monkeypatch):
    """Provide a factory to create AzulSettings for testing.

    Clears OS environ vars. Caller is responsible for passing initial values,
    including None for fields intended to be tested as missing.
    """

    def factory(**initial_values_for_test):
        vars_to_manage = list(AzulSettings.model_fields.keys())
        original_os_environ = {}

        for var in vars_to_manage:
            if var in os.environ:
                original_os_environ[var] = os.environ[var]
            monkeypatch.delenv(var, raising=False)

        settings = AzulSettings(**initial_values_for_test)

        # Restore original os.environ values
        for var, val in original_os_environ.items():
            monkeypatch.setenv(var, val)
        for var in vars_to_manage:
            if var not in original_os_environ:
                monkeypatch.delenv(var, raising=False)
        return settings

    return factory


def test_azul_settings_model_field_defaults(azul_settings_test_factory):
    """Test AzulSettings field defaults when explicitly set to None or not provided."""
    settings = azul_settings_test_factory(
        AUTH1="test_auth1",
        AUTH2="test_auth2",
        MERCHANT_ID="test_merchant_id",
        AZUL_CERT="dummy_cert.pem",
        AZUL_KEY="dummy_key.key",
        ALT_PROD_URL=None,
        ALT_PROD_URL_PAYMENT=None,
        AZUL_AUTH_KEY=None,
        MERCHANT_NAME=None,
        MERCHANT_TYPE=None,
        CUSTOM_URL=None,
    )
    assert settings.ENVIRONMENT == "dev"
    assert settings.CHANNEL == "EC"
    assert settings.ALT_PROD_URL is None
    assert settings.AZUL_AUTH_KEY is None
    assert settings.MERCHANT_NAME is None
    assert settings.MERCHANT_TYPE is None
    assert settings.CUSTOM_URL is None


def test_custom_validator_missing_auth_dev_url(azul_settings_test_factory):
    """Test custom validator: missing AUTH1/2, M_ID."""
    match_str = "The following required settings are missing or not set"
    with pytest.raises(ValueError, match=match_str) as exc_info:
        azul_settings_test_factory(
            AZUL_CERT="dummy.pem",
            AZUL_KEY="dummy.key",
            AUTH1=None,
            AUTH2=None,
            MERCHANT_ID=None,
            ENVIRONMENT="dev",
        )
    error_msg = str(exc_info.value)
    assert "AUTH1" in error_msg
    assert "AUTH2" in error_msg
    assert "MERCHANT_ID" in error_msg


def test_environment_setting_works(azul_settings_test_factory):
    """Test that environment setting works correctly."""
    settings = azul_settings_test_factory(
        AUTH1="test_auth1",
        AUTH2="test_auth2",
        MERCHANT_ID="test_merchant_id",
        AZUL_CERT="dummy_cert.pem",
        AZUL_KEY="dummy_key.key",
        ENVIRONMENT="prod",
    )
    assert settings.ENVIRONMENT == "prod"


def test_alt_prod_url_setting_works(azul_settings_test_factory):
    """Test that ALT_PROD_URL setting works correctly."""
    custom_alt_url = "http://custom.alt.url"

    settings = azul_settings_test_factory(
        AUTH1="test_auth1",
        AUTH2="test_auth2",
        MERCHANT_ID="test_merchant_id",
        AZUL_CERT="dummy_cert.pem",
        AZUL_KEY="dummy_key.key",
        ENVIRONMENT="prod",
        ALT_PROD_URL=custom_alt_url,
    )
    assert settings.ENVIRONMENT == "prod"
    assert settings.ALT_PROD_URL == custom_alt_url
