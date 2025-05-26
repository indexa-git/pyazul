"""Tests for post-authorization (capture) transaction functionalities."""

from datetime import datetime

import pytest

from pyazul.api.client import AzulAPI
from pyazul.models.schemas import HoldTransactionModel, PostSaleTransactionModel
from pyazul.services.transaction import TransactionService


@pytest.fixture
def transaction_service(settings):
    """Provide a TransactionService instance for testing post-auths."""
    api_client = AzulAPI(settings)
    return TransactionService(api_client)


@pytest.fixture
async def completed_hold(transaction_service):
    """Perform a hold transaction and return its details for posting."""
    unique_order_id = datetime.now().strftime("%Y%m%d%H%M%S%f")[:15]
    hold_data_dict = {
        "Store": transaction_service.api.settings.MERCHANT_ID,
        "Channel": transaction_service.api.settings.CHANNEL,
        "CardNumber": "5413330089600119",
        "Expiration": "202812",
        "CVC": "979",
        "Amount": "1000",
        "Itbis": "100",
        "OrderNumber": unique_order_id,
        "CustomOrderId": f"custom-{unique_order_id}",
        "AcquirerRefData": "1",
        "PosInputMode": "E-Commerce",
        "ForceNo3DS": "1",
    }
    payment = HoldTransactionModel(**hold_data_dict)  # type: ignore[arg-type]
    print(f"Payload for hold in fixture: {payment.model_dump(exclude_none=True)}")
    hold_result = await transaction_service.hold(payment)
    assert hold_result.get("IsoCode") == "00", "Hold in completed_hold fixture failed"
    return hold_result


@pytest.fixture
def post_transaction_data(completed_hold, transaction_service):
    """Provide data for a post-authorization transaction, using a prior hold."""
    return {
        "AzulOrderId": completed_hold["AzulOrderId"],
        "Amount": "1000",
        "Itbis": "100",
        "Store": transaction_service.api.settings.MERCHANT_ID,
        "Channel": transaction_service.api.settings.CHANNEL,
    }


@pytest.mark.asyncio
async def test_post_transaction(transaction_service, post_transaction_data):
    """Test a post-authorization (capture) transaction."""
    payment = PostSaleTransactionModel(**post_transaction_data)
    post_result = await transaction_service.post_sale(payment)
    print(post_result)
    assert (
        post_result["IsoCode"] == "00"
    ), "Post transaction should be processed successfully"
