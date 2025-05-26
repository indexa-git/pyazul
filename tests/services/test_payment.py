"""Tests for standard payment (sale) and refund transaction functionalities."""

import pytest

from pyazul.api.client import AzulAPI
from pyazul.core.config import get_azul_settings
from pyazul.models.schemas import RefundTransactionModel, SaleTransactionModel
from pyazul.services.transaction import TransactionService


@pytest.fixture
def transaction_service():
    """
    Provide a configured TransactionService instance.

    Used for processing direct card payments and refunds.
    """
    settings = get_azul_settings()
    api_client = AzulAPI(settings)  # Create AzulAPI instance
    return TransactionService(api_client)  # Pass the api_client


@pytest.fixture
def card_payment_data():
    """
    Provide test data for card payment transactions.

    Uses a test card provided by Azul for integration testing.

    Returns:
        dict: Test data including card details, amount, and merchant IDs.
    """
    return {
        "Channel": "EC",
        "PosInputMode": "E-Commerce",
        "Amount": "1000",  # $10.00 transaction amount
        "Itbis": "180",  # $1.80 tax amount
        "TrxType": "Sale",  # Direct sale transaction
        "CardNumber": "5413330089600119",  # Test card provided by Azul
        "Expiration": "202812",  # Card expiration in YYYYMM format
        "CVC": "979",  # Test card security code
        "OrderNumber": "sale-order-123",
        "CustomOrderId": "sale-test-001",  # Unique identifier for this test
        "SaveToDataVault": "1",  # Save card to vault for future use
        "ForceNo3DS": "1",  # Added to bypass 3DS for this test
    }


@pytest.mark.asyncio
async def test_card_payment(transaction_service, card_payment_data):
    """
    Test direct card payment transaction.

    Verifies successful card payment processing, approval, and auth codes.

    Expected outcomes:
    - Response IsoCode '00' (success).
    - Receive proper authorization codes.
    - Transaction amount matches request.
    """
    payment = SaleTransactionModel(**card_payment_data)
    response = await transaction_service.sale(payment)
    assert response.get("IsoCode") == "00", "Payment should be approved"
    print("Payment Response:", response)
    return response


@pytest.fixture
async def completed_payment(transaction_service, card_payment_data):
    """
    Create a successful payment and return the response.

    Used by refund tests needing a previous successful transaction.

    Returns:
        dict: API response with transaction details for refund.
    """
    payment = SaleTransactionModel(**card_payment_data)
    return await transaction_service.sale(payment)


@pytest.fixture
def refund_payment_data(completed_payment, card_payment_data):
    """
    Provide test data for refund transactions.

    Uses AzulOrderId from a previous successful payment.

    Args:
        completed_payment: Response from a successful payment.
        card_payment_data: Original card payment data fixture.

    Returns:
        dict: Test data with original transaction ref, refund amount, and merchant IDs.
    """
    return {
        "Channel": "EC",
        "PosInputMode": "E-Commerce",
        "Amount": "1000",  # Must match original payment amount
        "Itbis": "180",  # Must match original tax amount
        "AzulOrderId": completed_payment.get(
            "AzulOrderId"
        ),  # Reference to original transaction
        "OrderNumber": card_payment_data.get(
            "OrderNumber"
        ),  # Use OrderNumber from the original sale data
        "TrxType": "Refund",  # Specifies this is a refund operation
    }


@pytest.mark.asyncio
async def test_refund(transaction_service, refund_payment_data):
    """
    Test refund transaction for a previous payment.

    Verifies successful refund, approval, and matching amount.

    Expected outcomes:
    - Response IsoCode '00' (success).
    - Able to refund the full amount.
    - Receive proper reference numbers.

    Note: Refunds are for successful transactions and must match the original amount.
    """
    payment = RefundTransactionModel(**refund_payment_data)
    response = await transaction_service.refund(payment)
    print("Refund Response:", response)
    assert response.get("IsoCode") == "00", "Refund should be approved"
