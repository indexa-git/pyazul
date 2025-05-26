"""Tests for transaction verification functionalities of the PyAzul SDK."""

import pytest

from pyazul.models.schemas import SaleTransactionModel, VerifyTransactionModel
from tests.fixtures.cards import get_card
from tests.fixtures.order import generate_order_number


@pytest.fixture
async def sale_for_verification(transaction_service_integration, settings):
    """Create a sale transaction to be used for verification tests."""
    card = get_card("MASTERCARD_2")
    order_num = generate_order_number()
    custom_order_id = f"verify-sale-{order_num}"

    payment_data = {
        "Store": settings.MERCHANT_ID,
        "Channel": settings.CHANNEL,
        "OrderNumber": order_num,
        "CustomOrderId": custom_order_id,
        "ForceNo3DS": "1",
        "Amount": "500",  # Small amount for verification test
        "Itbis": "0",
        "CardNumber": card["number"],
        "Expiration": card["expiration"],
        "CVC": card["cvv"],
        "TrxType": "Sale",
    }
    payment_model = SaleTransactionModel(**payment_data)
    response = await transaction_service_integration.sale(payment_model)
    assert response.get("IsoCode") == "00", "Sale for verification fixture failed"
    return response  # Returns the full response, which includes CustomOrderId


@pytest.fixture
def verify_transaction_data(settings, sale_for_verification):
    """
    Provide test data for a transaction verification.

    Uses CustomOrderId from a previously created sale transaction.
    """
    return {
        # AzulBaseModel fields
        "Store": settings.MERCHANT_ID,
        "Channel": settings.CHANNEL,
        # VerifyTransactionModel specific fields
        "CustomOrderId": sale_for_verification["CustomOrderId"],
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
    # Optionally, assert more details from sale_for_verification match result
    # For example: assert result["Amount"] == sale_for_verification["Amount"]
    return result
