"""Tests for post-authorization (capture) transaction functionalities."""

import pytest

from pyazul.models.schemas import HoldTransactionModel, PostSaleTransactionModel
from tests.fixtures.cards import get_card
from tests.fixtures.order import generate_order_number


@pytest.fixture
async def completed_hold(transaction_service_integration, settings):
    """Perform a hold transaction and return its details for posting."""
    order_num = generate_order_number()
    custom_order_id = f"custom-hold-{order_num}"
    card = get_card("MASTERCARD_2")

    hold_data_dict = {
        # AzulBaseModel fields
        "Store": settings.MERCHANT_ID,
        "Channel": settings.CHANNEL,
        # BaseTransactionAttributes (defaults for PosInputMode, AcquirerRefData)
        "OrderNumber": order_num,
        "CustomOrderId": custom_order_id,
        "ForceNo3DS": "1",  # Test specific
        # CardPaymentAttributes (default for SaveToDataVault)
        "Amount": "1000",
        "Itbis": "100",
        "CardNumber": card["number"],
        "Expiration": card["expiration"],
        "CVC": card["cvv"],
        # HoldTransactionModel specific fields
        "TrxType": "Hold",
    }
    payment = HoldTransactionModel(**hold_data_dict)
    print(f"Payload for hold in fixture: {payment.model_dump(exclude_none=True)}")
    hold_result = await transaction_service_integration.hold(payment)
    assert hold_result.get("IsoCode") == "00", "Hold in completed_hold fixture failed"
    return hold_result


@pytest.fixture
def post_transaction_data(completed_hold, settings):
    """Provide data for a post-authorization transaction, using a prior hold."""
    return {
        # AzulBaseModel fields
        "Store": settings.MERCHANT_ID,
        "Channel": settings.CHANNEL,
        # PostSaleTransactionModel specific fields
        "AzulOrderId": completed_hold["AzulOrderId"],
        "Amount": "1000",
        "Itbis": "100",
    }


@pytest.mark.asyncio
async def test_post_transaction(transaction_service_integration, post_transaction_data):
    """Test a post-authorization (capture) transaction."""
    payment = PostSaleTransactionModel(**post_transaction_data)
    post_result = await transaction_service_integration.post_sale(payment)
    print(post_result)
    assert (
        post_result["IsoCode"] == "00"
    ), "Post transaction should be processed successfully"
