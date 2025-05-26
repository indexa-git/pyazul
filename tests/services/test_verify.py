"""Tests for transaction verification functionalities of the PyAzul SDK."""

import pytest

from pyazul.api.client import AzulAPI
from pyazul.models.schemas import VerifyTransactionModel
from pyazul.services.transaction import TransactionService


@pytest.fixture
def transaction_service(settings):
    """Provide a TransactionService instance for testing verifications."""
    api_client = AzulAPI(settings)
    return TransactionService(api_client)


@pytest.fixture
def verify_transaction_data(settings):
    """
    Provide test data for a transaction verification.

    Includes a custom order ID to identify the transaction to verify.
    """
    return {
        "CustomOrderId": "sale-test-001",
        "Store": settings.MERCHANT_ID,
        "Channel": settings.CHANNEL,
    }


@pytest.mark.asyncio
async def test_verify_transaction(transaction_service, verify_transaction_data):
    """Test verifying an existing transaction."""
    payment = VerifyTransactionModel(**verify_transaction_data)
    result = await transaction_service.verify(payment)
    assert result is not None
    assert result["IsoCode"] == "00", "Transaction should be verified successfully"
    assert result["Found"], "Transaction should be found"
    return result
