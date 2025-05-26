"""Tests for void transaction functionalities of the PyAzul SDK."""

import asyncio
from datetime import datetime

import pytest

from pyazul.models.schemas import HoldTransactionModel, VoidTransactionModel


@pytest.fixture
async def completed_hold_for_void(transaction_service_integration, settings):
    """Perform a hold transaction and return its details for voiding.

    This fixture creates a HOLD transaction that can be subsequently used in
    tests that need to void a transaction.

    Returns:
        dict: The API response from the hold transaction.
    """
    store_id = settings.MERCHANT_ID
    channel_id = settings.CHANNEL
    unique_order_id = datetime.now().strftime("%Y%m%d%H%M%S%f")[:15]

    # Define as a dictionary first, omitting fields to rely on defaults
    hold_data_dict = {
        # AzulBaseModel fields
        "Store": store_id,
        "Channel": channel_id,
        # BaseTransactionAttributes (PosInputMode, AcquirerRefData will use defaults)
        "OrderNumber": unique_order_id,
        "CustomOrderId": f"custom-void-{unique_order_id}",
        "ForceNo3DS": "1",  # Test specific
        # CardPaymentAttributes (SaveToDataVault will use default)
        "Amount": "1000",
        "Itbis": "100",
        "CardNumber": "5413330089600119",
        "Expiration": "202812",
        "CVC": "979",
        # HoldTransactionModel specific fields
        "TrxType": "Hold",
        # Optional fields with None defaults (like DataVaultToken) are omitted
        # and will be correctly defaulted by Pydantic.
    }
    payment = HoldTransactionModel(**hold_data_dict)
    hold_result = await transaction_service_integration.hold(payment)
    assert hold_result is not None, "Hold result from fixture should not be None"
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
    store_id = settings.MERCHANT_ID
    channel_id = settings.CHANNEL
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
        Store=store_id,
        Channel=channel_id,
        AzulOrderId=azul_order_id_to_void,
    )

    result = await transaction_service_integration.void(void_payment_request)
    assert result is not None, "Void result should not be None"
    assert (
        result.get("IsoCode") == "00"
    ), f"Transaction void failed: {result.get('ResponseMessage')}"
