"""Unit test configurations."""

from unittest.mock import AsyncMock, Mock

import pytest

from pyazul.api.client import AzulAPI
from pyazul.core.config import AzulSettings


@pytest.fixture
def mock_azul_settings() -> AzulSettings:
    """Return a mock AzulSettings instance."""
    settings = Mock(spec=AzulSettings)
    settings.MERCHANT_ID = "123456789"
    settings.AUTH1 = "test_auth1"
    settings.AUTH2 = "test_auth2"
    settings.AZUL_CERT = "dummy_cert_path.pem"
    settings.AZUL_KEY = "dummy_key_path.key"
    settings.ENVIRONMENT = "dev"

    settings.CHANNEL = "EC"
    # Add other necessary mock attributes as needed
    return settings


@pytest.fixture
def mock_api_client(mock_azul_settings) -> AzulAPI:
    """Return a mock AzulAPI client instance."""
    client = Mock(spec=AzulAPI)
    client.settings = mock_azul_settings
    # Mock private methods using spec to avoid protected access warnings
    client.configure_mock(
        **{
            "post.return_value": AsyncMock(),
        }
    )
    # Set additional attributes that may not be in the spec
    client._get_ssl_context = Mock(return_value=None)
    client._generate_auth_headers = Mock(
        return_value={("Auth1", "test_auth1"), ("Auth2", "test_auth2")}
    )
    client._prepare_payload = Mock(side_effect=lambda data, **kwargs: data)
    return client
