"""Tests for hold transaction functionalities of the PyAzul SDK."""

import pytest

from pyazul.models.schemas import HoldTransactionModel
from tests.fixtures.cards import get_card
from tests.fixtures.order import generate_order_number


@pytest.fixture
def hold_transaction_data(settings):
    """
    Provide test data for a hold transaction.

    Includes card details, amount, and other necessary fields for creating
    a hold (pre-authorization) on a card.
    """
    card = get_card("MASTERCARD_2")  # Using a standard card
    return {
        # AzulBaseModel fields
        "Store": settings.MERCHANT_ID,
        "Channel": settings.CHANNEL,
        # BaseTransactionAttributes (defaults for PosInputMode, AcquirerRefData)
        "OrderNumber": generate_order_number(),
        "CustomOrderId": f"hold-test-{generate_order_number()}",
        "ForceNo3DS": "1",  # Test specific
        # CardPaymentAttributes (default for SaveToDataVault)
        "Amount": "1000",
        "Itbis": "180",
        "CardNumber": card["number"],
        "Expiration": card["expiration"],
        "CVC": card["cvv"],
        # HoldTransactionModel specific fields
        "TrxType": "Hold",
    }


@pytest.mark.asyncio
async def test_hold_transaction(transaction_service_integration, hold_transaction_data):
    """
    Test creating a hold transaction.

    Verifies that a hold can be successfully placed on a card,
    resulting in an IsoCode of '00' (success).
    """
    payment = HoldTransactionModel(**hold_transaction_data)
    response = await transaction_service_integration.hold(payment)

    print("Hold Response:", response)

    # Verify the hold was successful
    assert response.get("IsoCode") == "00", "Hold transaction should be approved"

    # Verify we got required reference numbers
    assert response.get("AuthorizationCode"), "Should receive authorization code"
    assert response.get("RRN"), "Should receive reference number"
