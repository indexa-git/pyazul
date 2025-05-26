"""Tests for DataVault (tokenization) functionalities of the PyAzul SDK."""

from typing import Literal

import pytest

from pyazul.api.client import AzulAPI
from pyazul.core.config import get_azul_settings
from pyazul.models import DataVaultRequestModel, TokenSaleModel
from pyazul.services.datavault import DataVaultService
from pyazul.services.transaction import TransactionService

# Define Literal constants for TrxType to satisfy strict type checking
TRX_TYPE_CREATE: Literal["CREATE"] = "CREATE"
TRX_TYPE_DELETE: Literal["DELETE"] = "DELETE"


@pytest.fixture
def transaction_service():
    """
    Provide a configured TransactionService instance.

    Used for processing payments and token-based transactions.
    """
    settings = get_azul_settings()
    api_client = AzulAPI(settings)
    return TransactionService(api_client)


@pytest.fixture
def datavault_service():
    """
    Provide a configured DataVaultService instance.

    Used for token creation and management operations.
    """
    settings = get_azul_settings()
    api_client = AzulAPI(settings)
    return DataVaultService(api_client)


@pytest.fixture
def datavault_payment_data():
    """
    Provide test card data for DataVault operations.

    Uses a test card number provided by Azul for integration testing.

    Returns:
        dict: Test data including card details and merchant information.
    """
    return {
        "Channel": "EC",
        "PosInputMode": "E-Commerce",
        "Amount": "1000",  # $10.00
        "Itbis": "180",  # $1.80 (tax)
        "CardNumber": "5413330089600119",  # Test card provided by Azul
        "Expiration": "202812",
        "CustomOrderId": "datavault-test-001",  # Unique identifier for this test
        "Store": "39038540035",
        "DataVaultToken": "",
        "TrxType": TRX_TYPE_CREATE,
    }


@pytest.mark.asyncio
async def test_create_datavault(datavault_service, datavault_payment_data):
    """
    Test token creation in DataVault.

    Verifies that a card can be successfully tokenized.

    Expected outcome:
    - Response should have IsoCode '00' (success).
    - Should receive a valid DataVaultToken.
    """
    payment = DataVaultRequestModel(**datavault_payment_data)
    response = await datavault_service.create(payment)
    assert response.get("IsoCode") == "00"
    print("Token created:", response.get("DataVaultToken"))
    print("Response:", response)
    return response


@pytest.mark.asyncio
async def test_create_sale_datavault(transaction_service, completed_datavault):
    """
    Test sale transaction using a previously created token.

    Verifies that a token can be used for payment processing.

    Expected outcome:
    - Transaction should be successful (IsoCode '00').
    - Should be able to process payment without full card details.
    """
    token = completed_datavault.get("DataVaultToken")

    token_sale_data = {
        "Channel": "EC",
        "PosInputMode": "E-Commerce",
        "Amount": "1000",
        "Itbis": "180",  # Optional for TokenSaleModel, but good to test
        "DataVaultToken": token,
        "CustomOrderId": "token-sale-test-001",
        "Store": "39038540035",  # Added missing Store key
    }

    payment = TokenSaleModel(**token_sale_data)
    response = await transaction_service.sale(
        payment
    )  # transaction_service.sale expects a model instance
    assert response.get("IsoCode") == "00"
    print("Token used:", token)
    print("Response:", response)
    return response


@pytest.fixture
async def completed_datavault(datavault_service, datavault_payment_data):
    """
    Create a token and return the creation response.

    Used by other tests that need a pre-existing token.

    Returns:
        dict: API response containing the created token.
    """
    payment = DataVaultRequestModel(**datavault_payment_data)
    return await datavault_service.create(payment)


@pytest.mark.asyncio
async def test_delete_and_sale_datavault(
    datavault_service, transaction_service, completed_datavault
):
    """
    Test the complete token lifecycle.

    1. Delete an existing token.
    2. Attempt a sale with the deleted token.

    Expected outcomes:
    - Token deletion should be successful.
    - Subsequent sale attempt should fail with 'TokenId does not exist'.
    - Should handle errors appropriately.
    """
    token = completed_datavault.get("DataVaultToken")
    store_id = completed_datavault.get(
        "Store", "39038540035"
    )  # Get store from response or default

    try:
        # Delete token using DataVaultRequestModel
        delete_payment_data = {
            "Channel": "EC",
            "Store": store_id,
            "DataVaultToken": token,
            "TrxType": TRX_TYPE_DELETE,
        }
        delete_payment = DataVaultRequestModel(**delete_payment_data)
        delete_response = await datavault_service.delete(delete_payment)
        print("Delete response:", delete_response)
        assert (
            delete_response.get("IsoCode") == "00"
        ), "Token deletion should be successful"
    except (
        Exception
    ) as e:  # Catching general Exception, consider more specific if possible
        print(f"Error during token deletion: {str(e)}")
        # This assertion might be too broad if other errors can occur
        assert "does not exist" in str(e) or "TokenId no existe" in str(
            e
        ), "Error should indicate token doesn't exist"

    # Attempt sale with deleted token
    token_sale_data = {
        "Channel": "EC",
        "PosInputMode": "E-Commerce",
        "Amount": "1000",
        "Itbis": "180",
        "DataVaultToken": token,
        "CustomOrderId": "token-sale-test-002",
        "Store": store_id,  # Use the same store_id
    }
    payment = TokenSaleModel(**token_sale_data)
    try:
        sale_response = await transaction_service.sale(payment)
        print("Token used:", token)
        print("Sale response:", sale_response)
        # If the sale succeeds, it's an error in the test logic or API behavior
        raise AssertionError(
            f"Sale should not succeed with deleted token. Response: {sale_response}"
        )
    except Exception as e:
        print(f"Expected error with deleted token: {str(e)}")
        # Check for specific error messages indicating token invalidity
        # The exact message might vary based on API response
        assert (
            "TokenId does not exist" in str(e)
            or "TokenId no existe" in str(e)
            or "INVALID_TOKEN" in str(e).upper()
        ), "Error should indicate token is invalid"
