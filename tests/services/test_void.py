"""Tests for void transaction functionalities of the PyAzul SDK."""

import asyncio

# import uuid # Removed unused import
from datetime import datetime

import pytest

from pyazul.api.client import AzulAPI
from pyazul.core.config import get_azul_settings
from pyazul.models.schemas import HoldTransactionModel, VoidTransactionModel
from pyazul.services.transaction import TransactionService


@pytest.fixture
def transaction_service():
    """Provide a TransactionService instance for testing void operations."""
    settings = get_azul_settings()
    api_client = AzulAPI(settings)
    return TransactionService(api_client)


@pytest.fixture
async def completed_hold_for_void(transaction_service):
    """Perform a hold transaction and return its details for voiding.

    This fixture creates a HOLD transaction that can be subsequently used in
    tests that need to void a transaction.

    Returns:
        dict: The API response from the hold transaction.
    """
    store_id = transaction_service.api.settings.MERCHANT_ID
    unique_order_id = datetime.now().strftime("%Y%m%d%H%M%S%f")[:15]

    # Fields required by Pydantic model (no default or Optional without default)
    hold_data = HoldTransactionModel(
        Store=store_id,
        OrderNumber=unique_order_id,
        CardNumber="5413330089600119",
        Expiration="202812",
        CVC="979",
        Amount="1000",
        Itbis="100",
        # Fields with defaults in Pydantic model, specified as required by docs, or to satisfy strict linter # noqa: E501
        Channel="EC",
        PosInputMode="E-Commerce",
        TrxType="Hold",
        AcquirerRefData="1",
        CustomOrderId=f"custom-void-{unique_order_id}",
        # Explicitly providing remaining Optional fields or fields with defaults that linter flags # noqa: E501
        DataVaultToken=None,
        SaveToDataVault="0",  # Model default is "0"
        CustomerServicePhone=None,
        ECommerceURL=None,
        AltMerchantName=None,
        ForceNo3DS="1",
    )
    hold_result = await transaction_service.hold(hold_data)
    assert hold_result is not None, "Hold result from fixture should not be None"
    assert (
        hold_result.get("IsoCode") == "00"
    ), f"Hold transaction in fixture failed: {hold_result.get('ResponseMessage')}"
    assert (
        hold_result.get("AzulOrderId") is not None
    ), "AzulOrderId not found in fixture hold result"
    return hold_result


@pytest.mark.asyncio
async def test_void_transaction(transaction_service, completed_hold_for_void):
    """Test voiding a previously authorized (held) transaction."""
    store_id = transaction_service.api.settings.MERCHANT_ID
    azul_order_id_to_void = completed_hold_for_void.get("AzulOrderId")

    await asyncio.sleep(2)  # Ensure transaction is processed by backend

    # VoidTransactionModel requires AzulOrderId, Channel, and Store.
    # Channel has a default in its model definition if not provided from AzulBaseModel inheritance. # noqa: E501
    # Checking VoidTransactionModel definition in schemas.py:
    # class VoidTransactionModel(BaseModel):
    #     Channel: str = Field("EC", ...)
    #     Store: str = Field(...)
    #     AzulOrderId: str = Field(...)
    # So, Channel default is "EC". Store and AzulOrderId are needed.
    void_payment_request = VoidTransactionModel(
        AzulOrderId=azul_order_id_to_void,
        Store=store_id,
        Channel="EC",  # Explicitly provide Channel as linter was strict
    )

    result = await transaction_service.void(void_payment_request)
    assert result is not None, "Void result should not be None"
    assert (
        result.get("IsoCode") == "00"
    ), f"Transaction void failed: {result.get('ResponseMessage')}"
