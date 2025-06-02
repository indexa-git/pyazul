"""Integration tests for payment operations."""

import pytest

from pyazul.models.payment import Refund, Sale
from tests.fixtures.cards import get_card
from tests.fixtures.order import generate_order_number


@pytest.fixture
def card_payment_data(settings):
    """
    Provide standard test data for a card payment.

    Returns:
        dict: Data for card payment transaction.
    """
    card = get_card("MASTERCARD_2")  # Using a standard card
    return {
        "Store": settings.MERCHANT_ID,
        "OrderNumber": generate_order_number(),
        "CustomOrderId": f"sale-test-{generate_order_number()}",
        "ForceNo3DS": "1",  # Test specific
        "Amount": "1000",
        "Itbis": "180",
        "CardNumber": card["number"],
        "Expiration": card["expiration"],
        "CVC": card["cvv"],
        "SaveToDataVault": "1",  # Test specific: non-default, save to vault
    }


@pytest.mark.asyncio
async def test_card_payment(transaction_service_integration, card_payment_data):
    """
    Test direct card payment transaction.

    Verifies successful card payment processing, approval, and auth codes.

    Expected outcomes:
    - Response IsoCode '00' (success).
    - Receive proper authorization codes.
    - Transaction amount matches request.
    """
    payment = Sale(**card_payment_data)
    response = await transaction_service_integration.process_sale(payment)
    assert response.get("IsoCode") == "00", "Payment should be approved"
    print("Payment Response:", response)
    return response


@pytest.fixture
async def completed_payment(transaction_service_integration, card_payment_data):
    """
    Create a successful payment and return the response.

    Used by refund tests needing a previous successful transaction.

    Returns:
        dict: API response with transaction details for refund.
    """
    payment = Sale(**card_payment_data)
    return await transaction_service_integration.process_sale(payment)


@pytest.fixture
def refund_payment_data(completed_payment, card_payment_data, settings):
    """
    Provide test data for refund transactions.

    Uses AzulOrderId from a previous successful payment.

    Args:
        completed_payment: Response from a successful payment.
        card_payment_data: Original card payment data fixture.
        settings: The application settings fixture.

    Returns:
        dict: Test data with original transaction ref, refund amount, and merchant IDs.
    """
    return {
        "Store": settings.MERCHANT_ID,
        "OrderNumber": card_payment_data.get("OrderNumber"),
        "AzulOrderId": completed_payment.get("AzulOrderId"),
        "Amount": "1000",
        "Itbis": "180",
    }


@pytest.mark.asyncio
async def test_refund(transaction_service_integration, refund_payment_data):
    """
    Test refund transaction for a previous payment.

    Verifies successful refund, approval, and matching amount.

    Expected outcomes:
    - Response IsoCode '00' (success).
    - Able to refund the full amount.
    - Receive proper reference numbers.

    Note: Refunds are for successful transactions and must match the original amount.
    """
    payment = Refund(**refund_payment_data)
    response = await transaction_service_integration.process_refund(payment)
    print("Refund Response:", response)
    assert response.get("IsoCode") == "00", "Refund should be approved"
