import pytest
from pyazul.core.config import get_azul_settings
from pyazul.services.transaction import TransactionService
# from pyazul.services.datavault import DataVaultService

pytest.ini_options = {
    "asyncio_mode": "auto",
    "asyncio_default_fixture_loop_scope": "function"
}

@pytest.fixture(scope="session")
def settings():
    return get_azul_settings()

@pytest.fixture(scope="session")
def transaction_service(settings):
    return TransactionService(settings)
