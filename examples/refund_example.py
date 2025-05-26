"""Example demonstrating how to perform a refund transaction with PyAzul."""

import asyncio

from pyazul import PyAzul


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
    # Initialize PyAzul facade
    azul = PyAzul()
    settings = azul.settings

    try:
        # 1. First make a payment
        print("\n1. Making initial payment...")
        payment_data = {
            "Store": settings.MERCHANT_ID,
            "Channel": "EC",
            "PosInputMode": "E-Commerce",
            "Amount": "1000",  # $10.00
            "Itbis": "180",  # $1.80 tax
            "CardNumber": "5413330089600119",  # Test card
            "Expiration": "202812",
            "CVC": "979",
            "OrderNumber": "SALE-FOR-REFUND-001",
            "CustomOrderId": "refund-test-001",
            "SaveToDataVault": "1",
        }

        payment_response = await azul.sale(payment_data)

        if payment_response.get("ResponseMessage") != "APROBADA":
            err_desc = payment_response.get(
                "ErrorDescription", payment_response.get("ResponseMessage")
            )
            raise Exception(f"Initial payment failed: {err_desc}")

        azul_order_id = payment_response.get("AzulOrderId")
        original_order_number = payment_data["OrderNumber"]
        print(f"Payment successful. AzulOrderId: {azul_order_id}")

        # 2. Process refund
        print("\n2. Processing refund...")
        refund_data = {
            "Store": settings.MERCHANT_ID,
            "Channel": "EC",
            "PosInputMode": "E-Commerce",
            "Amount": "1000",
            "Itbis": "180",
            "AzulOrderId": azul_order_id,
            "OrderNumber": original_order_number,
        }

        refund_response = await azul.refund(refund_data)

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
