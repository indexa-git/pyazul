"""Example demonstrating a standard payment transaction with PyAzul."""

import asyncio

from pyazul import PyAzul


async def test_payment():
    """
    Example demonstrating a direct card payment transaction.

    This example shows how to:
    1. Initialize the transaction service
    2. Create a payment request with card data
    3. Process the payment
    4. Handle the response

    Use case: Direct card payment where you need to charge
    a customer's card immediately.
    """
    # Initialize PyAzul facade
    azul = PyAzul()
    settings = azul.settings

    # Test payment data
    payment_data = {
        "Store": settings.MERCHANT_ID,
        "Channel": "EC",
        "PosInputMode": "E-Commerce",
        "Amount": "1000",  # $10.00
        "Itbis": "180",  # $1.80 tax
        "CardNumber": "5413330089600119",  # Test card
        "Expiration": "202812",
        "CVC": "979",
        "OrderNumber": "SALE-001",
        "CustomOrderId": "example-001",
        "SaveToDataVault": "1",  # Save card for future use
    }

    try:
        # Create and process payment
        response = await azul.sale(payment_data)

        # Display transaction results
        print("\nPayment Response:")
        print("-" * 50)
        print(f"ISO Code: {response.get('IsoCode')}")  # '00' means success
        print(f"Authorization: {response.get('AuthorizationCode')}")
        print(f"RRN: {response.get('RRN')}")  # Reference number
        print(f"Order ID: {response.get('CustomOrderId')}")
        print(f"Azul Order ID: {response.get('AzulOrderId')}")  # Keep for refunds
        print("-" * 50)

    except Exception as e:
        print(f"Error: {str(e)}")


if __name__ == "__main__":
    asyncio.run(test_payment())
