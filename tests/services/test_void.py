"""Tests for void transaction functionalities of the PyAzul SDK."""

import asyncio

import pytest

from pyazul.models.schemas import HoldTransactionModel, VoidTransactionModel
from pyazul.services.transaction import TransactionService


@pytest.fixture
def transaction_service(settings):
    """Provide a TransactionService instance for testing void operations."""
    return TransactionService(settings)


@pytest.fixture
def void_transaction_data(completed_payment):
    """
    Provide test data for a void transaction.

    Uses AzulOrderId from a previously completed payment.
    """
    return {
        "AzulOrderId": completed_payment["AzulOrderId"],
        "store": completed_payment["store"],
    }


@pytest.mark.asyncio
async def test_void_transaction(transaction_service, void_transaction_data):
    """Test voiding a previously authorized transaction."""
    payment = VoidTransactionModel(**void_transaction_data)

    # First, we perform a hold transaction
    hold_transaction = HoldTransactionModel(
        CardNumber="5413330089600119",
        Expiration="202812",
        CVC="979",
        Amount="1000",
        Itbis="100",
        TrxType="Hold",
        CustomOrderId="hold_test_to_post",
    )
    hold_result = await transaction_service.hold(hold_transaction)
    assert hold_result["IsoCode"] == "00", "Hold transaction should be successful"
    # azul_order_id = hold_result["AzulOrderId"]

    # We wait for 2 seconds to ensure the hold transaction is fully processed
    await asyncio.sleep(2)

    # Then we attempt to void the transaction
    result = await transaction_service.void(payment)
    assert result is not None
    assert result["IsoCode"] == "00", "Transaction should be voided successfully"
