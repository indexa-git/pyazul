import asyncio
from pyazul.models.schemas import SaleTransactionModel, RefundTransactionModel
from pyazul.services.transaction import TransactionService
from pyazul.core.config import get_azul_settings

async def test_refund():
    """
    Example demonstrating a complete payment and refund flow.
    
    This example shows how to:
    1. Make an initial payment
    2. Get the AzulOrderId from the payment
    3. Process a refund using that ID
    4. Handle the refund response
    
    Note: Refunds can only be processed for valid transactions
    and the refund amount must match the original payment.
    """
    # Initialize service
    settings = get_azul_settings()
    transaction_service = TransactionService(settings)
    
    try:
        # 1. First make a payment
        print("\n1. Making initial payment...")
        payment_data = {
            "Channel": "EC",
            "PosInputMode": "E-Commerce",
            "Amount": "1000",  # $10.00
            "Itbis": "180",    # $1.80 tax
            "TrxType": "Sale",
            "CardNumber": "5413330089600119",  # Test card
            "Expiration": "202812",
            "CVC": "979",
            "CustomOrderId": "refund-test-001",
            "SaveToDataVault": "1"
        }
        
        payment = SaleTransactionModel(**payment_data)
        payment_response = await transaction_service.sale(payment)
        
        if payment_response.get('IsoCode') != '00':
            raise Exception("Initial payment failed")
            
        azul_order_id = payment_response.get('AzulOrderId')
        print(f"Payment successful. AzulOrderId: {azul_order_id}")

        # 2. Process refund
        print("\n2. Processing refund...")
        refund_data = {
            "Channel": "EC",
            "PosInputMode": "E-Commerce",
            "Amount": "1000",  # Must match original amount
            "Itbis": "180",    # Must match original tax
            "AzulOrderId": azul_order_id,
            "TrxType": "Refund"
        }
        
        refund = RefundTransactionModel(**refund_data)
        refund_response = await transaction_service.refund(refund)
        
        # Display refund results
        print("\nRefund Response:")
        print("-" * 50)
        print(f"ISO Code: {refund_response.get('IsoCode')}")
        print(f"RRN: {refund_response.get('RRN')}")
        print(f"AzulOrderId: {refund_response.get('AzulOrderId')}")
        print("-" * 50)
        
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_refund()) 