import pytest
from pyazul.models.schemas import SaleTransactionModel, RefundTransactionModel
from pyazul.services.transaction import TransactionService
from pyazul.core.config import get_azul_settings

@pytest.fixture
def transaction_service():
    """
    Fixture that provides a configured TransactionService instance.
    Used for processing direct card payments and refunds.
    """
    settings = get_azul_settings()
    return TransactionService(settings)

@pytest.fixture
def card_payment_data():
    """
    Fixture providing test data for card payment transactions.
    Uses a test card provided by Azul for integration testing.
    
    Returns:
        dict: Test data including:
            - Card details (test card number)
            - Transaction amount and tax
            - Merchant identifiers
    """
    return {
        "Channel": "EC",
        "PosInputMode": "E-Commerce",
        "Amount": "1000",  # $10.00 transaction amount
        "Itbis": "180",    # $1.80 tax amount
        "TrxType": "Sale", # Direct sale transaction
        "CardNumber": "5413330089600119",  # Test card provided by Azul
        "Expiration": "202812",  # Card expiration in YYYYMM format
        "CVC": "979",      # Test card security code
        "CustomOrderId": "sale-test-001",  # Unique identifier for this test
        "SaveToDataVault": "1"  # Save card to vault for future use
    }

@pytest.mark.asyncio
async def test_card_payment(transaction_service, card_payment_data):
    """
    Test direct card payment transaction.
    
    This test verifies that:
    1. We can successfully process a card payment
    2. The transaction is approved
    3. We receive proper authorization codes
    
    Expected outcomes:
    - Response should have IsoCode '00' (success)
    - Should receive proper authorization codes
    - Transaction amount should match request
    """
    payment = SaleTransactionModel(**card_payment_data)
    response = await transaction_service.sale(payment)
    assert response.get('IsoCode') == '00', "Payment should be approved"
    print("Payment Response:", response)
    return response

@pytest.fixture
async def completed_payment(transaction_service, card_payment_data):
    """
    Fixture that creates a successful payment and returns the response.
    Used by refund tests that need a previous successful transaction.
    
    Returns:
        dict: API response containing the transaction details needed for refund
    """
    payment = SaleTransactionModel(**card_payment_data)
    return await transaction_service.sale(payment)

@pytest.fixture
def refund_payment_data(completed_payment):
    """
    Fixture providing test data for refund transactions.
    Uses the AzulOrderId from a previous successful payment.
    
    Args:
        completed_payment: Response from a successful payment transaction
    
    Returns:
        dict: Test data including:
            - Original transaction reference
            - Refund amount (must match original payment)
            - Required merchant identifiers
    """
    return {
        "Channel": "EC",
        "PosInputMode": "E-Commerce",
        "Amount": "1000",  # Must match original payment amount
        "Itbis": "180",    # Must match original tax amount
        "AzulOrderId": completed_payment.get('AzulOrderId'),  # Reference to original transaction
        "TrxType": "Refund"  # Specifies this is a refund operation
    }

@pytest.mark.asyncio
async def test_refund(transaction_service, refund_payment_data):
    """
    Test refund transaction for a previous payment.
    
    This test verifies that:
    1. We can successfully refund a previous transaction
    2. The refund is approved
    3. The refund amount matches the original payment
    
    Expected outcomes:
    - Response should have IsoCode '00' (success)
    - Should be able to refund the full amount
    - Should receive proper reference numbers
    
    Note: Refunds can only be processed for successful transactions
    and must match the original amount.
    """
    payment = RefundTransactionModel(**refund_payment_data)
    response = await transaction_service.refund(payment)
    print("Refund Response:", response)
    assert response.get('IsoCode') == '00', "Refund should be approved"
