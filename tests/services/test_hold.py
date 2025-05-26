"""Tests for hold transaction functionalities of the PyAzul SDK."""

import pytest

from pyazul.api.client import AzulAPI
from pyazul.models.schemas import HoldTransactionModel
from pyazul.services.transaction import TransactionService


@pytest.fixture
def transaction_service(settings):
    """
    Provide a TransactionService instance for testing.

    This fixture is scoped to the session to reuse the same service instance
    across multiple tests, improving efficiency.
    """
    api_client = AzulAPI(settings)
    return TransactionService(api_client)


@pytest.fixture
def hold_transaction_data():
    """
    Provide test data for a hold transaction.

    Includes card details, amount, and other necessary fields for creating
    a hold (pre-authorization) on a card.
    """
    return {
        "Channel": "EC",
        "PosInputMode": "E-Commerce",
        "Amount": "1000",  # $10.00 to be held
        "Itbis": "180",  # $1.80 tax amount
        "TrxType": "Hold",  # Specifies this is a hold transaction
        "CardNumber": "5413330089600119",  # Test card provided by Azul
        "Expiration": "202812",  # Card expiration in YYYYMM format
        "CVC": "979",  # Test card security code
        "OrderNumber": "order-123",
        "CustomOrderId": "hold-test-001",  # Unique identifier for this test
        "SaveToDataVault": "0",  # Changed from "2" to "0"
        "AcquirerRefData": "1",
        "ForceNo3DS": "1",  # Added to bypass 3DS for this test
    }


@pytest.mark.asyncio
async def test_hold_transaction(transaction_service, hold_transaction_data):
    """
    Test creating a hold transaction.

    Verifies that a hold can be successfully placed on a card,
    resulting in an IsoCode of '00' (success).
    """
    payment = HoldTransactionModel(**hold_transaction_data)
    response = await transaction_service.hold(payment)

    print("Hold Response:", response)

    # Verify the hold was successful
    assert response.get("IsoCode") == "00", "Hold transaction should be approved"

    # Verify we got required reference numbers
    assert response.get("AuthorizationCode"), "Should receive authorization code"
    assert response.get("RRN"), "Should receive reference number"
