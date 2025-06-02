"""Integration tests for void operations."""

import asyncio

import pytest

from pyazul.models.payment import Hold, Void
from tests.fixtures.cards import get_card
from tests.fixtures.order import generate_order_number


@pytest.fixture
async def completed_hold_for_void(transaction_service_integration, settings):
    """Perform a hold transaction and return its details for voiding."""
    order_num = generate_order_number()
    card = get_card("MASTERCARD_2")

    payment = Hold(
        Store=settings.MERCHANT_ID,
        OrderNumber=order_num,
        CustomOrderId=f"custom-void-{order_num}",
        ForceNo3DS="1",  # Test specific
        Amount="1000",
        Itbis="100",
        CardNumber=card["number"],
        Expiration=card["expiration"],
        CVC=card["cvv"],
    )

    hold_result = await transaction_service_integration.process_hold(payment)
    assert (
        hold_result.get("IsoCode") == "00"
    ), f"Hold transaction in fixture failed: {hold_result.get('ResponseMessage')}"
    assert (
        hold_result.get("AzulOrderId") is not None
    ), "AzulOrderId not found in fixture hold result"
    return hold_result


@pytest.mark.asyncio
async def test_void_transaction(
    transaction_service_integration, completed_hold_for_void, settings
):
    """Test voiding a previously authorized (held) transaction."""
    await asyncio.sleep(5)  # Ensure transaction is processed by backend

    void_payment_request = Void(
        Store=settings.MERCHANT_ID,
        AzulOrderId=completed_hold_for_void.get("AzulOrderId"),
    )

    result = await transaction_service_integration.process_void(void_payment_request)
    assert (
        result.get("IsoCode") == "00"
    ), f"Transaction void failed: {result.get('ResponseMessage')}"
