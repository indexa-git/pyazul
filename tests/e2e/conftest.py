"""Pytest configuration and fixtures for PyAzul integration tests."""

import pytest

from pyazul.api.client import AzulAPI
from pyazul.core.config import AzulSettings
from pyazul.services.datavault import DataVaultService
from pyazul.services.payment_page import PaymentPageService
from pyazul.services.transaction import TransactionService


@pytest.fixture(scope="session")
def transaction_service_integration(settings: AzulSettings) -> TransactionService:
    """Provide a TransactionService instance for integration tests."""
    api_client = AzulAPI(settings=settings)
    return TransactionService(client=api_client, settings=settings)


@pytest.fixture(scope="session")
def datavault_service_integration(settings: AzulSettings) -> DataVaultService:
    """Provide a DataVaultService instance for integration tests."""
    api_client = AzulAPI(settings=settings)
    return DataVaultService(client=api_client, settings=settings)


@pytest.fixture(scope="session")
def payment_page_service_integration(settings: AzulSettings) -> PaymentPageService:
    """Provide a PaymentPageService instance for integration tests."""
    return PaymentPageService(settings=settings)
