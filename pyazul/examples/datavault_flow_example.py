import asyncio
from pyazul.models.schemas import DataVaultCreateModel, DataVaultDeleteModel, TokenSaleModel
from pyazul.services.datavault import DataVaultService
from pyazul.services.transaction import TransactionService
from pyazul.core.config import get_azul_settings

async def test_datavault_flow():
    """
    Example demonstrating the complete DataVault token lifecycle.
    
    This example shows how to:
    1. Create a token from card data
    2. Use the token for a payment
    3. Delete the token
    4. Handle token-related errors
    
    Use case: When you need to securely store card data for future use,
    such as:
    - Subscription payments
    - One-click checkouts
    - Recurring billing
    
    Security note: Using tokens instead of storing card data helps
    with PCI compliance by reducing the scope of sensitive data
    handling in your system.
    """
    # Initialize services
    settings = get_azul_settings()
    datavault_service = DataVaultService(settings)
    transaction_service = TransactionService(settings)
    
    # Card data for tokenization
    datavault_data = {
        "Channel": "EC",
        "PosInputMode": "E-Commerce",
        "Amount": "1000",
        "Itbis": "180",
        "CardNumber": "5413330089600119",
        "Expiration": "202812",
        "CustomOrderId": "datavault-example-001",
        "store": "39038540035"
    }
    
    try:
        # 1. Create token
        print("\n1. Creating token...")
        create_token = DataVaultCreateModel(**datavault_data)
        token_response = await datavault_service.create(create_token)
        
        if token_response.get('IsoCode') != '00':
            raise Exception("Token creation failed")
            
        token = token_response.get('DataVaultToken')
        print(f"Token created: {token}")

        # 2. Use token for payment
        print("\n2. Making payment with token...")
        token_sale_data = {
            "Channel": "EC",
            "PosInputMode": "E-Commerce",
            "Amount": "1000",
            "Itbis": "180",
            "DataVaultToken": token,
            "CustomOrderId": "token-sale-example-001"
        }
        token_payment = TokenSaleModel(**token_sale_data)
        sale_response = await transaction_service.sale(token_payment)
        print(f"Sale response: {sale_response}")
        assert sale_response.get('IsoCode') == '00', "Sale should be successful"

        # 3. Delete token
        print("\n3. Deleting token...")
        delete_data = {
            "Channel": "EC",
            "PosInputMode": "E-Commerce",
            "store": "39038540035",
            "DataVaultToken": token,
            "Amount": "1000",
            "Itbis": "180"
        }
        delete_token = DataVaultDeleteModel(**delete_data)
        delete_response = await datavault_service.delete(delete_token)
        print(f"Delete response: {delete_response}")

        # 4. Verify token is invalid
        print("\n4. Verifying deleted token...")
        try:
            await transaction_service.sale(token_payment)
            print("Warning: Payment with deleted token succeeded")
        except Exception as e:
            print(f"Expected error: {str(e)}")
            
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_datavault_flow()) 