"""Example demonstrating the DataVault tokenization flow with PyAzul."""

import asyncio

from pyazul import PyAzul


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
    # Initialize PyAzul facade
    azul = PyAzul()
    settings = azul.settings

    # Card data for tokenization
    card_details = {
        "CardNumber": "5413330089600119",
        "Expiration": "202812",
    }
    common_datavault_params = {
        "Channel": "EC",
        "Store": settings.MERCHANT_ID,
    }

    try:
        # 1. Create token
        print("\n1. Creating token...")
        create_payload_dict = {
            **common_datavault_params,
            **card_details,
            "TrxType": "CREATE",
        }
        token_response = await azul.create_token(create_payload_dict)
        print(f"Full token_response from create_token: {token_response}")

        if token_response.get("ResponseMessage") != "APROBADA":
            err_desc = token_response.get(
                "ErrorDescription", token_response.get("ResponseMessage")
            )
            raise Exception(f"Token creation failed: {err_desc}")

        token = token_response.get("DataVaultToken")
        print(f"Token created: {token}")

        # 2. Use token for payment
        print("\n2. Making payment with token...")
        token_sale_data = {
            "Channel": "EC",
            "Store": settings.MERCHANT_ID,
            "PosInputMode": "E-Commerce",
            "Amount": "1000",
            "Itbis": "180",
            "DataVaultToken": token,
            "OrderNumber": "003004005006007",
            "CVC": "123",
            "ForceNo3DS": "1",
        }
        sale_response = await azul.token_sale(token_sale_data)
        print(f"Sale response: {sale_response}")
        if sale_response.get("ResponseMessage") != "APROBADA":
            err_desc = sale_response.get(
                "ErrorDescription", sale_response.get("ResponseMessage")
            )
            raise Exception(f"Token Sale failed: {err_desc}")

        # 3. Delete token
        print("\n3. Deleting token...")
        delete_payload_dict = {
            **common_datavault_params,
            "DataVaultToken": token,
            "TrxType": "DELETE",
        }
        delete_response = await azul.delete_token(delete_payload_dict)
        print(f"Delete response: {delete_response}")
        if delete_response.get("ResponseMessage") != "APROBADA":
            err_desc = delete_response.get(
                "ErrorDescription", delete_response.get("ResponseMessage")
            )
            raise Exception(f"Token deletion failed: {err_desc}")

        # 4. Verify token is invalid
        print("\n4. Verifying deleted token...")
        try:
            verify_token_sale_data = {
                "Channel": "EC",
                "Store": settings.MERCHANT_ID,
                "PosInputMode": "E-Commerce",
                "Amount": "1000",
                "Itbis": "180",
                "DataVaultToken": token,
                "OrderNumber": "003004005006007",
                "CVC": "123",
                "ForceNo3DS": "1",
            }
            await azul.token_sale(verify_token_sale_data)
            print("Warning: Payment with deleted token succeeded unexpectedly")
        except Exception as e:
            print(f"Expected error when using deleted token: {str(e)}")

    except Exception as e:
        print(f"Error in DataVault flow: {str(e)}")


if __name__ == "__main__":
    asyncio.run(test_datavault_flow())
