"""Example demonstrating how to perform a post-authorization transaction with PyAzul."""

import asyncio

from pyazul import PyAzul


async def main():
    """Demonstrates posting a previously authorized transaction."""
    azul = PyAzul()
    settings = azul.settings

    # Step 1: Create a hold transaction
    hold_transaction_data = {
        "Store": settings.MERCHANT_ID,
        "Channel": "EC",
        "PosInputMode": "E-Commerce",
        "CardNumber": "5413330089600119",
        "Expiration": "202812",
        "CVC": "979",
        "Amount": "1000",
        "Itbis": "100",
        "OrderNumber": "HOLD-FOR-POST-001",
        "CustomOrderId": "hold_test_to_post",
    }
    hold_result = await azul.hold(hold_transaction_data)
    print("Hold Result:", hold_result)
    if hold_result.get("ResponseMessage") != "APROBADA":
        err_desc = hold_result.get(
            "ErrorDescription", hold_result.get("ResponseMessage")
        )
        print(f"Hold transaction failed: {err_desc}")
        return
    azul_order_id = hold_result["AzulOrderId"]

    # Step 2: Use the AzulOrderId from hold for the post transaction
    post_transaction_data = {
        "Store": settings.MERCHANT_ID,
        "Channel": "EC",
        "AzulOrderId": azul_order_id,
        "Amount": "1000",
        "Itbis": "100",
    }
    post_result = await azul.post_auth(post_transaction_data)
    print("Post Result:", post_result)
    if post_result.get("ResponseMessage") == "APROBADA":
        print("Post transaction processed successfully")
    else:
        err_desc = post_result.get(
            "ErrorDescription", post_result.get("ResponseMessage")
        )
        print(f"Post transaction failed: {err_desc}")


if __name__ == "__main__":
    asyncio.run(main())
