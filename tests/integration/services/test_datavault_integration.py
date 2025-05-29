"""Tests for DataVault (tokenization) functionalities of the PyAzul SDK."""

from typing import Literal

import pytest

from pyazul import PyAzul
from pyazul.models import DataVaultRequestModel, TokenSaleModel
from pyazul.models.secure import (
    CardHolderInfo,
    ChallengeIndicator,
    SecureTokenSale,
    ThreeDSAuth,
)
from tests.fixtures.cards import get_card
from tests.fixtures.order import generate_order_number

# Define Literal constants for TrxType to satisfy strict type checking
TRX_TYPE_CREATE: Literal["CREATE"] = "CREATE"
TRX_TYPE_DELETE: Literal["DELETE"] = "DELETE"


@pytest.fixture
def datavault_create_data(settings):
    """
    Provide test card data for DataVault token CREATION.

    Returns:
        dict: Test data including card details and merchant information.
    """
    card = get_card("MASTERCARD_2")  # Using a standard card suitable for tokenization
    return {
        "Store": settings.MERCHANT_ID,
        "Channel": settings.CHANNEL,
        "TrxType": TRX_TYPE_CREATE,
        "CardNumber": card["number"],
        "Expiration": card["expiration"],
        "CVC": None,  # Optional for CREATE, some card fixtures might have it
    }


@pytest.fixture
def card_holder_info_fixture() -> CardHolderInfo:
    """Provide a standard CardHolderInfo object for 3DS tests."""
    return CardHolderInfo(
        BillingAddressCity="Santo Domingo",
        BillingAddressCountry="DO",
        BillingAddressLine1="Test Address 123",
        BillingAddressLine2=None,
        BillingAddressLine3=None,
        BillingAddressState="Distrito Nacional",
        BillingAddressZip="10101",
        Email="test@example.com",
        Name="Test Cardholder",
        PhoneHome=None,
        PhoneMobile=None,
        PhoneWork=None,
        ShippingAddressCity="Santo Domingo",
        ShippingAddressCountry="DO",
        ShippingAddressLine1="Test Shipping Address 456",
        ShippingAddressLine2=None,
        ShippingAddressLine3=None,
        ShippingAddressState="Distrito Nacional",
        ShippingAddressZip="10102",
    )


@pytest.fixture
def azul_client(settings) -> PyAzul:
    """Provide a PyAzul instance for 3DS token tests."""
    return PyAzul(settings=settings)


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
    Test sale transaction using a previously created token (NON-3DS).

    Verifies that a token can be used for payment processing.
    """
    print(f"Completed Datavault for Sale: {completed_datavault_creation}")
    token = completed_datavault_creation.get("DataVaultToken")

    token_sale_data = {
        # AzulBaseModel fields
        "Store": settings.MERCHANT_ID,
        "Channel": settings.CHANNEL,
        # BaseTransactionAttributes (PosInputMode, AcquirerRefData use defaults)
        "OrderNumber": generate_order_number(),
        "CustomOrderId": f"token-sale-{generate_order_number()}",
        "ForceNo3DS": "1",  # Test specific - NON-3DS
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
async def test_create_sale_datavault_3ds(
    azul_client, completed_datavault_creation, card_holder_info_fixture, settings
):
    """
    Test sale transaction using a previously created token (WITH 3DS).

    This test validates that 3DS token sales work correctly and would catch
    bugs like missing SaveToDataVault field in 3DS flows.
    """
    print(f"Completed Datavault for 3DS Sale: {completed_datavault_creation}")
    token = completed_datavault_creation.get("DataVaultToken")

    base_dummy_url = "http://localhost:8000/dummy"

    # Create 3DS token sale request
    token_sale_request = SecureTokenSale(
        Store=settings.MERCHANT_ID,
        Channel=settings.CHANNEL,
        OrderNumber=generate_order_number(),
        CustomOrderId=f"token-3ds-sale-{generate_order_number()}",
        Amount="1000",
        Itbis="180",
        DataVaultToken=token,
        CVC="123",  # Some providers require CVC even with tokens
        forceNo3DS="0",  # Enable 3DS
        cardHolderInfo=card_holder_info_fixture,
        threeDSAuth=ThreeDSAuth(
            TermUrl=f"{base_dummy_url}/term",
            MethodNotificationUrl=f"{base_dummy_url}/method",
            RequestChallengeIndicator=ChallengeIndicator.NO_CHALLENGE,
        ),
        PosInputMode="E-Commerce",
        TrxType="Sale",
        AcquirerRefData="1",
    )

    # Process the 3DS token sale
    result = await azul_client.secure_token_sale(
        token_sale_request.model_dump(exclude_none=True)
    )

    assert result is not None, "3DS token sale result should not be None"

    # Handle different possible outcomes
    if result.get("redirect"):
        # 3DS method or challenge required
        secure_id = result["id"]
        print(f"3DS token sale initiated with redirect. ID: {secure_id}")

        # This validates that the initial request was successful
        # (if SaveToDataVault was missing, we'd get an error here)
        assert "html" in result, "HTML form should be provided for redirect"

    elif result.get("value") and isinstance(result["value"], dict):
        # Direct approval (frictionless)
        response = result["value"]
        assert response.get("IsoCode") == "00", f"3DS token sale failed: {response}"
        assert response.get("ResponseMessage") == "APROBADA"
        print(f"3DS token sale approved directly: {response.get('AuthorizationCode')}")

    else:
        pytest.fail(f"Unexpected 3DS token sale result: {result}")

    print("3DS token sale completed successfully")
    return result


@pytest.mark.asyncio
async def test_token_sale_comparison_3ds_vs_non_3ds(
    transaction_service_integration,
    azul_client,
    completed_datavault_creation,
    card_holder_info_fixture,
    settings,
):
    """
    Compare token sales with and without 3DS to ensure both work correctly.

    This test validates that both flows work and would catch integration bugs
    that affect only one of the flows.
    """
    token = completed_datavault_creation.get("DataVaultToken")

    # Test 1: Non-3DS token sale
    print("Testing Non-3DS token sale...")
    non_3ds_data = {
        "Store": settings.MERCHANT_ID,
        "Channel": settings.CHANNEL,
        "OrderNumber": generate_order_number(),
        "CustomOrderId": f"compare-no3ds-{generate_order_number()}",
        "ForceNo3DS": "1",  # Disable 3DS
        "Amount": "1000",
        "Itbis": "180",
        "DataVaultToken": token,
        "CVC": None,
    }

    non_3ds_payment = TokenSaleModel(**non_3ds_data)
    non_3ds_response = await transaction_service_integration.sale(non_3ds_payment)

    assert (
        non_3ds_response.get("IsoCode") == "00"
    ), f"Non-3DS failed: {non_3ds_response}"
    print(f"Non-3DS token sale: {non_3ds_response.get('AuthorizationCode')}")

    # Test 2: 3DS token sale
    print("Testing 3DS token sale...")
    base_dummy_url = "http://localhost:8000/dummy"

    three_ds_request = SecureTokenSale(
        Store=settings.MERCHANT_ID,
        Channel=settings.CHANNEL,
        OrderNumber=generate_order_number(),
        CustomOrderId=f"compare-3ds-{generate_order_number()}",
        Amount="1000",
        Itbis="180",
        DataVaultToken=token,
        CVC="123",
        forceNo3DS="0",  # Enable 3DS
        cardHolderInfo=card_holder_info_fixture,
        threeDSAuth=ThreeDSAuth(
            TermUrl=f"{base_dummy_url}/term",
            MethodNotificationUrl=f"{base_dummy_url}/method",
            RequestChallengeIndicator=ChallengeIndicator.NO_CHALLENGE,
        ),
        PosInputMode="E-Commerce",
        TrxType="Sale",
        AcquirerRefData="1",
    )

    three_ds_result = await azul_client.secure_token_sale(
        three_ds_request.model_dump(exclude_none=True)
    )

    assert three_ds_result is not None, "3DS token sale should not be None"

    if three_ds_result.get("redirect"):
        print(f"3DS token sale initiated: {three_ds_result['id']}")
    elif three_ds_result.get("value") and isinstance(three_ds_result["value"], dict):
        response = three_ds_result["value"]
        assert response.get("IsoCode") == "00", f"3DS failed: {response}"
        print(f"3DS token sale approved: {response.get('AuthorizationCode')}")
    else:
        pytest.fail(f"Unexpected 3DS result: {three_ds_result}")

    print("Both 3DS and non-3DS token sales work correctly")


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
        "OrderNumber": generate_order_number(),
        "CustomOrderId": f"token-sale-deleted-{generate_order_number()}",
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
