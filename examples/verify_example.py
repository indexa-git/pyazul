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
    try:
        verify_result = await azul.verify_transaction(verify_data)
        print("Verify Result:", verify_result)

        found_status = verify_result.get("Found")
        iso_code = verify_result.get("IsoCode")

        if found_status is True and iso_code == "00":
            print("Transaction verified successfully and found.")
            print(f"  AzulOrderId: {verify_result.get('AzulOrderId')}")
            print(f"  Amount: {verify_result.get('Amount')}")
            print(f"  TransactionType: {verify_result.get('TransactionType')}")
        elif found_status is True and iso_code != "00":
            # Found, but not in an 'approved' state, or some other issue
            err_msg = (
                verify_result.get("ErrorDescription")
                or verify_result.get("ResponseMessage")
                or f"Found but IsoCode is {iso_code}"
            )
            print(f"Transaction found but has an issue: {err_msg}")
        elif found_status is False or (
            isinstance(found_status, str) and found_status.lower() == "no"
        ):
            print("Transaction not found.")
        else:
            # Fallback for unexpected 'Found' status or other errors
            err_msg = (
                verify_result.get("ErrorDescription")
                or verify_result.get("ResponseMessage")
                or "Unknown verification status."
            )
            print(f"Transaction verification failed or status unknown: {err_msg}")
            print(f"Full Verify Result: {verify_result}")

    except Exception as e:
        print(f"An error occurred during verification: {str(e)}")


if __name__ == "__main__":
    asyncio.run(main())
