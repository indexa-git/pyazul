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
            "Amount": "1000",
            "Itbis": "180",
            "CardNumber": "5413330089600119",
            "Expiration": "202812",
            "CVC": "979",
            "OrderNumber": "002003004005006",  # Numeric OrderNumber
            "CustomOrderId": "refund-test-001",
            "SaveToDataVault": "1",
            "ForceNo3DS": "1",  # Bypass 3D Secure for the initial sale
        }

        payment_response = await azul.sale(payment_data)
        print(f"Initial Payment Response: {payment_response}")

        if payment_response.get("ResponseMessage") != "APROBADA":
            err_desc = payment_response.get(
                "ErrorDescription",
                payment_response.get(
                    "ResponseMessage", "Unknown error during payment."
                ),
            )
            raise Exception(f"Initial payment failed: {err_desc}")

        azul_order_id = payment_response.get("AzulOrderId")
        original_order_number = payment_data["OrderNumber"]
        if not azul_order_id:
            raise Exception("AzulOrderId not found in successful payment response.")
        print(f"Payment successful. AzulOrderId: {azul_order_id}")

        # 2. Process refund
        print("\n2. Processing refund...")
        refund_data = {
            "Store": settings.MERCHANT_ID,
            "Channel": "EC",
            "Amount": "1000",
            "Itbis": "180",
            "AzulOrderId": azul_order_id,
            "OrderNumber": original_order_number,
            "PosInputMode": "E-Commerce",
        }

        refund_response = await azul.refund(refund_data)
        print(f"Refund Attempt Response: {refund_response}")

        if (
            refund_response.get("ResponseMessage") == "APROBADA"
            and refund_response.get("IsoCode") == "00"
        ):
            print("\nRefund Processed Successfully:")
            print("-" * 50)
            print(f"ISO Code: {refund_response.get('IsoCode')}")
            print(f"RRN: {refund_response.get('RRN')}")
            print(f"AzulOrderId (Refund): {refund_response.get('AzulOrderId')}")
            print("-" * 50)
        else:
            err_desc_refund = refund_response.get(
                "ErrorDescription",
                refund_response.get("ResponseMessage", "Unknown error during refund."),
            )
            print(f"Refund failed or was not approved. Details: {err_desc_refund}")
            print(f"Full refund response: {refund_response}")

    except Exception as e:
        print(f"An error occurred: {str(e)}")
        # For deeper debugging, you might want to print the full traceback
        # import traceback
        # traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_refund())
