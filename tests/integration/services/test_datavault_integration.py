"""Tests for DataVault (tokenization) functionalities of the PyAzul SDK."""

from typing import Literal

import pytest

from pyazul.models import DataVaultRequestModel, TokenSaleModel

# Define Literal constants for TrxType to satisfy strict type checking
TRX_TYPE_CREATE: Literal["CREATE"] = "CREATE"
TRX_TYPE_DELETE: Literal["DELETE"] = "DELETE"


@pytest.fixture
def datavault_create_data(settings):
    """
    Provide test card data for DataVault token CREATION.

    Uses a test card number provided by Azul for integration testing.

    Returns:
        dict: Test data including card details and merchant information.
    """
    return {
        "Store": settings.MERCHANT_ID,
        "Channel": settings.CHANNEL,
        "TrxType": TRX_TYPE_CREATE,
        "CardNumber": "5413330089600119",
        "Expiration": "202812",
        "CVC": None,  # Optional for CREATE
    }


@pytest.mark.asyncio
async def test_create_datavault(datavault_service_integration, datavault_create_data):
    """
    Test token creation in DataVault.

    Verifies that a card can be successfully tokenized.

    Expected outcome:
    - Response should have IsoCode '00' (success).
    - Should receive a valid DataVaultToken.
    """
    payment = DataVaultRequestModel(**datavault_create_data)
    response = await datavault_service_integration.create(payment)
    assert response.get("IsoCode") == "00"
    print("Token created:", response.get("DataVaultToken"))
    print("Response:", response)
    return response


@pytest.fixture
async def completed_datavault_creation(
    datavault_service_integration, datavault_create_data
):
    """
    Create a token and return the creation response.

    Used by other tests that need a pre-existing token.

    Returns:
        dict: API response containing the created token.
    """
    payment = DataVaultRequestModel(**datavault_create_data)
    return await datavault_service_integration.create(payment)


@pytest.mark.asyncio
async def test_create_sale_datavault(
    transaction_service_integration, completed_datavault_creation, settings
):
    """
    Test sale transaction using a previously created token.

    Verifies that a token can be used for payment processing.
    """
    print(f"Completed Datavault for Sale: {completed_datavault_creation}")
    token = completed_datavault_creation.get("DataVaultToken")

    token_sale_data = {
        # AzulBaseModel fields
        "Store": settings.MERCHANT_ID,
        "Channel": settings.CHANNEL,
        # BaseTransactionAttributes (PosInputMode, AcquirerRefData use defaults)
        "OrderNumber": "TSALE-001",
        "CustomOrderId": "token-sale-test-001",
        "ForceNo3DS": "1",  # Test specific
        # TokenSaleModel specific fields (TrxType uses model default "Sale")
        "Amount": "1000",
        "Itbis": "180",
        "DataVaultToken": token,
        "CVC": None,
    }

    payment = TokenSaleModel(**token_sale_data)
    response = await transaction_service_integration.sale(payment)
    assert response.get("IsoCode") == "00"
    print("Token used:", token)
    print("Response:", response)
    return response


@pytest.mark.asyncio
async def test_delete_and_sale_datavault(
    datavault_service_integration,
    transaction_service_integration,
    completed_datavault_creation,
    settings,
):
    """Test the complete token lifecycle: Delete and then attempt sale."""
    token = completed_datavault_creation.get("DataVaultToken")
    store_id = completed_datavault_creation.get("Store", settings.MERCHANT_ID)

    # 1. Delete Token
    datavault_delete_data = {
        # AzulBaseModel fields
        "Store": store_id,
        "Channel": settings.CHANNEL,
        # DataVaultRequestModel specific fields for DELETE
        "TrxType": TRX_TYPE_DELETE,
        "DataVaultToken": token,
    }
    delete_payment = DataVaultRequestModel(**datavault_delete_data)
    delete_response = await datavault_service_integration.delete(delete_payment)
    print("Delete response:", delete_response)
    assert delete_response.get("IsoCode") == "00", "Token deletion should be successful"

    # 2. Attempt sale with deleted token
    token_sale_data_after_delete = {
        # AzulBaseModel fields
        "Store": store_id,
        "Channel": settings.CHANNEL,
        # BaseTransactionAttributes (PosInputMode, AcquirerRefData use defaults)
        "OrderNumber": "TSALE-002",
        "CustomOrderId": "token-sale-test-002",
        "ForceNo3DS": "1",  # Test specific
        # TokenSaleModel specific fields (TrxType uses model default "Sale")
        "Amount": "1000",
        "Itbis": "180",
        "DataVaultToken": token,  # The deleted token
        "CVC": None,
    }
    payment = TokenSaleModel(**token_sale_data_after_delete)
    try:
        sale_response = await transaction_service_integration.sale(payment)
        pytest.fail(
            f"Sale should not succeed with deleted token. Response: {sale_response}"
        )
    except Exception as e:
        print(f"Expected error with deleted token: {str(e)}")
        assert (
            "TokenId does not exist" in str(e)
            or "TokenId no existe" in str(e)
            or "INVALID_TOKEN" in str(e).upper()
        ), "Error message should indicate token is invalid or does not exist"
