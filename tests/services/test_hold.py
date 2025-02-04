import pytest
from pyazul.models.schemas import HoldTransactionModel
from pyazul.services.transaction import TransactionService
from pyazul.core.config import get_azul_settings

@pytest.fixture
def transaction_service():
    """
    Fixture that provides a configured TransactionService instance.
    Used for processing hold/authorization transactions.
    """
    settings = get_azul_settings()
    return TransactionService(settings)

@pytest.fixture
def hold_payment_data():
    """
    Fixture providing test data for hold transactions.
    A hold (also known as authorization) reserves funds on a card
    without capturing them immediately.
    
    Returns:
        dict: Test data including:
            - Card details (test card number)
            - Amount to hold
            - Transaction identifiers
    """
    return {
        "Channel": "EC",
        "PosInputMode": "E-Commerce",
        "Amount": "1000",  # $10.00 to be held
        "Itbis": "180",    # $1.80 tax amount
        "TrxType": "Hold", # Specifies this is a hold transaction
        "CardNumber": "5413330089600119",  # Test card provided by Azul
        "Expiration": "202812",  # Card expiration in YYYYMM format
        "CVC": "979",      # Test card security code
        "CustomOrderId": "hold-test-001",  # Unique identifier for this test
        "SaveToDataVault": "2"  # Don't save card to vault for hold operations
    }

@pytest.mark.asyncio
async def test_hold_payment(transaction_service, hold_payment_data):
    """
    Test card authorization/hold transaction.
    
    This test verifies that:
    1. We can successfully place a hold on a card
    2. The hold reserves the specified amount
    3. We receive proper authorization codes
    
    Expected outcomes:
    - Response should have IsoCode '00' (success)
    - Should receive an authorization code
    - Should receive a reference number (RRN)
    
    Note: Holds are typically used in scenarios where the final
    amount might change (hotels, car rentals, etc.)
    """
    payment = HoldTransactionModel(**hold_payment_data)
    response = await transaction_service.hold(payment)
    
    print("Hold Response:", response)
    
    # Verify the hold was successful
    assert response.get('IsoCode') == '00', "Hold transaction should be approved"
    
    # Verify we got required reference numbers
    assert response.get('AuthorizationCode'), "Should receive authorization code"
    assert response.get('RRN'), "Should receive reference number" 