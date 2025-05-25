"""Tests for post-authorization (capture) transaction functionalities."""

import pytest

from pyazul.models.schemas import PostSaleTransactionModel
from pyazul.services.transaction import TransactionService


@pytest.fixture
def transaction_service(settings):
    """Provide a TransactionService instance for testing post-auths."""
    return TransactionService(settings)


@pytest.fixture
def post_transaction_data(completed_hold):
    """Provide data for a post-authorization transaction, using a prior hold."""
    return {
        "AzulOrderId": completed_hold["AzulOrderId"],
        "ApprovedUrl": "https://example.com/approved",
        "DeclinedUrl": "https://example.com/declined",
        "CancelUrl": "https://example.com/cancelled",
        "UseCustomField1": "0",
        "CardNumber": "5413330089600119",
        "Expiration": "202812",
        "CVC": "979",
        "Amount": "1000",
        "Itbis": "100",
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
