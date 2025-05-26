"""Example demonstrating how to perform a card verification with PyAzul."""

import asyncio

from pyazul import PyAzul


async def main():
    """Perform a card verification transaction."""
    azul = PyAzul()
    settings = azul.settings

    # Create a verify transaction data
    verify_data = {
        "Store": settings.MERCHANT_ID,
        "Channel": "EC",
        "CustomOrderId": "sale-test-001",  # Assumes this CustomOrderId exists
    }
    verify_result = await azul.verify_transaction(verify_data)
    print("Verify Result:", verify_result)
    if (
        verify_result.get("ResponseMessage") == "APROBADA"
        and verify_result.get("Found") == "Yes"
    ):
        print("Transaction verified successfully and found")
    elif verify_result.get("Found") == "No":
        print("Transaction not found.")
    else:
        err_desc = verify_result.get(
            "ErrorDescription", verify_result.get("ResponseMessage")
        )
        print(f"Transaction verification failed or not found: {err_desc}")


if __name__ == "__main__":
    asyncio.run(main())
