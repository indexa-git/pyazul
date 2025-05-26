"""Tests for transaction verification functionalities of the PyAzul SDK."""

import pytest

from pyazul.models.schemas import VerifyTransactionModel


@pytest.fixture
def verify_transaction_data(settings):
    """
    Provide test data for a transaction verification.

    Includes a custom order ID to identify the transaction to verify.
    """
    return {
        # AzulBaseModel fields
        "Store": settings.MERCHANT_ID,
        "Channel": settings.CHANNEL,
        # VerifyTransactionModel specific fields
        "CustomOrderId": "sale-test-001",
    }


@pytest.mark.asyncio
async def test_verify_transaction(
    transaction_service_integration, verify_transaction_data
):
    """Test verifying an existing transaction."""
    payment = VerifyTransactionModel(**verify_transaction_data)
    result = await transaction_service_integration.verify(payment)
    assert result is not None
    assert result["IsoCode"] == "00", "Transaction should be verified successfully"
    assert result["Found"], "Transaction should be found"
    return result
