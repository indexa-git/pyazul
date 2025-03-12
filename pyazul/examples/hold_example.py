import asyncio
from pyazul.models.schemas import HoldTransactionModel
from pyazul.services.transaction import TransactionService
from pyazul.core.config import get_azul_settings

async def test_hold():
    """
    Example demonstrating a card authorization hold.
    
    This example shows how to:
    1. Initialize the transaction service
    2. Create a hold request
    3. Place a hold on a card
    4. Handle the authorization response
    
    Use case: When you need to verify funds or reserve an amount
    without immediate capture, such as:
    - Hotel reservations
    - Car rentals
    - Pre-authorizations
    """
    # Initialize service
    settings = get_azul_settings()
    transaction_service = TransactionService(settings)
    
    # Hold transaction data
    hold_data = {
        # "Channel": "EC",
        # "PosInputMode": "E-Commerce",
        "Amount": "1000",  # Amount to hold
        "Itbis": "180",    # Tax amount
        "TrxType": "Hold",
        "CardNumber": "5413330089600119",
        "Expiration": "202812",
        "CVC": "979",
        "CustomOrderId": "hold-example-001",
        "SaveToDataVault": "0"  # Don't save card for holds
    }
    
    try:
        # Process hold request
        payment = HoldTransactionModel(**hold_data)
        response = await transaction_service.hold(payment)
        
        # Display hold results
        print("\nHold Response:")
        print("-" * 50)
        print(f"ISO Code: {response.get('IsoCode')}")
        print(f"Authorization: {response.get('AuthorizationCode')}")
        print(f"RRN: {response.get('RRN')}")
        print(f"Order ID: {response.get('CustomOrderId')}")
        print(f"Azul Order ID: {response.get('AzulOrderId')}")
        print("-" * 50)
        
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_hold()) 