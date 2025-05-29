"""Tests for secure token sale functionalities of the PyAzul SDK."""

from unittest.mock import AsyncMock, Mock

import pytest

from pyazul.models import DataVaultRequestModel, TokenSaleModel
from pyazul.models.secure import (
    CardHolderInfo,
    ChallengeIndicator,
    SecureTokenSale,
    ThreeDSAuth,
)
from pyazul.services.datavault import DataVaultService
from pyazul.services.secure import SecureService
from pyazul.services.transaction import TransactionService
from tests.fixtures.cards import get_card
from tests.fixtures.order import generate_order_number


@pytest.fixture
def mock_api_client():
    """Create a mock API client."""
    client = Mock()
    client._async_request = AsyncMock()
    client.settings = Mock()
    client.settings.MERCHANT_ID = "39038540035"
    client.settings.AZUL_CERT = "path/to/cert.pem"
    client.settings.AZUL_KEY = "path/to/key.pem"
    client.settings.ENVIRONMENT = "dev"
    return client


@pytest.fixture
def secure_service(mock_api_client):
    """Create a SecureService instance with mock API client."""
    return SecureService(mock_api_client)


@pytest.fixture
def datavault_service(mock_api_client):
    """Create a DataVaultService instance with mock API client."""
    return DataVaultService(mock_api_client)


@pytest.fixture
def transaction_service(mock_api_client):
    """Create a TransactionService instance with mock API client."""
    return TransactionService(mock_api_client)


@pytest.fixture
def tokenization_request(mock_api_client):
    """Create a sample token creation request."""
    card = get_card("MASTERCARD_1")
    return DataVaultRequestModel(
        CardNumber=card["number"],
        Expiration=card["expiration"],
        Store=mock_api_client.settings.MERCHANT_ID,
        TrxType="CREATE",
        Channel="EC",
        CVC=None,
        DataVaultToken=None,
    )


@pytest.fixture
async def created_token(datavault_service, tokenization_request, mock_api_client):
    """Create a token and return the token value."""
    mock_api_client._async_request.return_value = {
        "ResponseMessage": "APROBADA",
        "IsoCode": "00",
        "DataVaultToken": "TEST_TOKEN_123456789",
    }
    response = await datavault_service.create(tokenization_request)
    return response.get("DataVaultToken")


@pytest.fixture
def token_3ds_sale_request(created_token, mock_api_client):
    """Create a sample token sale request with 3DS."""
    return SecureTokenSale(
        Amount="1000",
        Itbis="180",
        DataVaultToken=created_token,
        OrderNumber=generate_order_number(),
        Store=mock_api_client.settings.MERCHANT_ID,
        Channel="EC",
        PosInputMode="E-Commerce",
        TrxType="Sale",
        forceNo3DS="0",
        CVC="123",
        CustomOrderId=None,
        AcquirerRefData=None,
        cardHolderInfo=CardHolderInfo(
            BillingAddressCity="Santo Domingo",
            BillingAddressCountry="DO",
            BillingAddressLine1="Test Address",
            BillingAddressState="Distrito Nacional",
            BillingAddressZip="10101",
            Email="test@example.com",
            Name="Test User",
            ShippingAddressCity="Santo Domingo",
            ShippingAddressCountry="DO",
            ShippingAddressLine1="Test Address",
            ShippingAddressState="Distrito Nacional",
            ShippingAddressZip="10101",
            BillingAddressLine2=None,
            BillingAddressLine3=None,
            PhoneHome=None,
            PhoneMobile=None,
            PhoneWork=None,
            ShippingAddressLine2=None,
            ShippingAddressLine3=None,
        ),
        threeDSAuth=ThreeDSAuth(
            TermUrl="https://example.com/post-3ds-token",
            MethodNotificationUrl="https://example.com/capture-3ds-token",
            RequestChallengeIndicator=ChallengeIndicator.CHALLENGE,
        ),
    )


@pytest.fixture
def token_non_3ds_sale_request(created_token, mock_api_client):
    """Create a sample token sale request without 3DS."""
    token_sale_data = {
        "Amount": "1000",
        "Itbis": "180",
        "DataVaultToken": created_token,
        "OrderNumber": generate_order_number(),
        "Store": mock_api_client.settings.MERCHANT_ID,
        "Channel": "EC",
        "PosInputMode": "E-Commerce",
        "TrxType": "Sale",
        "ForceNo3DS": "1",
        "CVC": "123",
        "CustomOrderId": None,
        "AcquirerRefData": None,
    }
    return TokenSaleModel(**token_sale_data)


@pytest.mark.asyncio
async def test_token_creation(datavault_service, tokenization_request, mock_api_client):
    """Test token creation."""
    mock_api_client._async_request.return_value = {
        "ResponseMessage": "APROBADA",
        "IsoCode": "00",
        "DataVaultToken": "TEST_TOKEN_123456789",
    }
    response = await datavault_service.create(tokenization_request)
    assert response.get("IsoCode") == "00"
    assert response.get("ResponseMessage") == "APROBADA"
    assert response.get("DataVaultToken") is not None
    return response.get("DataVaultToken")


@pytest.mark.asyncio
async def test_token_sale_non_3ds(
    transaction_service, token_non_3ds_sale_request, mock_api_client
):
    """Test token sale without 3DS (ForceNo3DS=1)."""
    mock_api_client._async_request.return_value = {
        "ResponseMessage": "APROBADA",
        "IsoCode": "00",
        "AuthorizationCode": "123456",
        "RRN": "789012345678",
    }
    response = await transaction_service.sale(token_non_3ds_sale_request)
    assert response.get("IsoCode") == "00"
    assert response.get("ResponseMessage") == "APROBADA"
    assert response.get("AuthorizationCode") is not None


@pytest.mark.asyncio
async def test_token_sale_with_3ds_challenge(
    secure_service, token_3ds_sale_request, mock_api_client
):
    """Test token sale with 3DS challenge response."""
    mock_api_client._async_request.return_value = {
        "ResponseMessage": "3D_SECURE_CHALLENGE",
        "AzulOrderId": "12345",
        "ThreeDSChallenge": {
            "CReq": "test_token_creq",
            "RedirectPostUrl": "https://test.com/3ds-token",
        },
    }
    result = await secure_service.process_token_sale(token_3ds_sale_request)
    assert result["redirect"] is True
    assert "html" in result
    assert result["id"] is not None

    secure_id = result["id"]

    mock_api_client._async_request.return_value = {
        "ResponseMessage": "APROBADA",
        "IsoCode": "00",
        "AzulOrderId": "12345",
        "AuthorizationCode": "123456",
    }
    challenge_result = await secure_service.process_challenge(secure_id, "test_cres")
    assert challenge_result["ResponseMessage"] == "APROBADA"
    assert challenge_result["IsoCode"] == "00"
    assert challenge_result["AzulOrderId"] == "12345"


@pytest.mark.asyncio
async def test_token_sale_with_3ds_method(
    secure_service, token_3ds_sale_request, mock_api_client
):
    """Test token sale with 3DS method response and subsequent approval."""
    mock_api_client._async_request.return_value = {
        "ResponseMessage": "3D_SECURE_2_METHOD",
        "AzulOrderId": "67890",
        "ThreeDSMethod": {
            "MethodForm": "<form id='tdsMethodForm'>...</form>",
            "ServerTransId": "67890-method-1234",
        },
    }
    result = await secure_service.process_token_sale(token_3ds_sale_request)
    assert result["redirect"] is True
    assert "html" in result
    assert result["id"] is not None

    mock_api_client._async_request.return_value = {
        "ResponseMessage": "APROBADA",
        "IsoCode": "00",
        "AzulOrderId": "67890",
        "AuthorizationCode": "987654",
    }
    method_result = await secure_service.process_3ds_method(
        azul_order_id="67890", method_notification_status="RECEIVED"
    )
    assert method_result["ResponseMessage"] == "APROBADA"
    assert method_result["IsoCode"] == "00"
    assert method_result["AzulOrderId"] == "67890"


@pytest.mark.asyncio
async def test_token_sale_comparison_unit(
    transaction_service, secure_service, created_token, mock_api_client
):
    """Test both 3DS and non-3DS token sales with mocks for logic validation."""
    # Test non-3DS token sale
    non_3ds_data = {
        "Amount": "1000",
        "Itbis": "180",
        "DataVaultToken": created_token,
        "OrderNumber": generate_order_number(),
        "Store": mock_api_client.settings.MERCHANT_ID,
        "Channel": "EC",
        "PosInputMode": "E-Commerce",
        "TrxType": "Sale",
        "ForceNo3DS": "1",
        "CVC": "123",
        "CustomOrderId": None,
        "AcquirerRefData": None,
    }

    mock_api_client._async_request.return_value = {
        "ResponseMessage": "APROBADA",
        "IsoCode": "00",
        "AuthorizationCode": "NON3DS123",
    }
    non_3ds_request = TokenSaleModel(**non_3ds_data)
    non_3ds_response = await transaction_service.sale(non_3ds_request)
    assert non_3ds_response.get("IsoCode") == "00"
    assert non_3ds_response.get("AuthorizationCode") == "NON3DS123"

    # Test 3DS token sale
    three_ds_request = SecureTokenSale(
        Amount="1000",
        Itbis="180",
        DataVaultToken=created_token,
        OrderNumber=generate_order_number(),
        Store=mock_api_client.settings.MERCHANT_ID,
        Channel="EC",
        PosInputMode="E-Commerce",
        TrxType="Sale",
        forceNo3DS="0",
        CVC="123",
        CustomOrderId=None,
        AcquirerRefData=None,
        cardHolderInfo=CardHolderInfo(
            BillingAddressCity="Santo Domingo",
            BillingAddressCountry="DO",
            BillingAddressLine1="Test Address",
            BillingAddressState="Distrito Nacional",
            BillingAddressZip="10101",
            Email="test@example.com",
            Name="Test User",
            ShippingAddressCity="Santo Domingo",
            ShippingAddressCountry="DO",
            ShippingAddressLine1="Test Address",
            ShippingAddressState="Distrito Nacional",
            ShippingAddressZip="10101",
            BillingAddressLine2=None,
            BillingAddressLine3=None,
            PhoneHome=None,
            PhoneMobile=None,
            PhoneWork=None,
            ShippingAddressLine2=None,
            ShippingAddressLine3=None,
        ),
        threeDSAuth=ThreeDSAuth(
            TermUrl="https://example.com/post-3ds-token",
            MethodNotificationUrl="https://example.com/capture-3ds-token",
            RequestChallengeIndicator=ChallengeIndicator.NO_CHALLENGE,
        ),
    )

    mock_api_client._async_request.return_value = {
        "ResponseMessage": "APROBADA",
        "IsoCode": "00",
        "AuthorizationCode": "3DS123",
    }
    three_ds_response = await secure_service.process_token_sale(three_ds_request)
    assert three_ds_response.get("value", {}).get("IsoCode") == "00"
    assert three_ds_response.get("value", {}).get("AuthorizationCode") == "3DS123"


@pytest.mark.asyncio
async def test_complete_token_3ds_workflow(
    secure_service, datavault_service, tokenization_request, mock_api_client
):
    """Test the complete token and 3DS workflow."""
    mock_api_client._async_request.return_value = {
        "ResponseMessage": "APROBADA",
        "IsoCode": "00",
        "DataVaultToken": "TEST_TOKEN_123456789",
    }
    token_response = await datavault_service.create(tokenization_request)
    token = token_response.get("DataVaultToken")
    assert token is not None

    order_number = generate_order_number()
    token_sale_request = SecureTokenSale(
        Amount="1000",
        Itbis="180",
        DataVaultToken=token,
        OrderNumber=order_number,
        Store=mock_api_client.settings.MERCHANT_ID,
        Channel="EC",
        PosInputMode="E-Commerce",
        TrxType="Sale",
        forceNo3DS="0",
        CVC="123",
        CustomOrderId=None,
        AcquirerRefData=None,
        cardHolderInfo=CardHolderInfo(
            BillingAddressCity="Santo Domingo",
            BillingAddressCountry="DO",
            BillingAddressLine1="Test Address",
            BillingAddressState="Distrito Nacional",
            BillingAddressZip="10101",
            Email="test@example.com",
            Name="Test User",
            ShippingAddressCity="Santo Domingo",
            ShippingAddressCountry="DO",
            ShippingAddressLine1="Test Address",
            ShippingAddressState="Distrito Nacional",
            ShippingAddressZip="10101",
            BillingAddressLine2=None,
            BillingAddressLine3=None,
            PhoneHome=None,
            PhoneMobile=None,
            PhoneWork=None,
            ShippingAddressLine2=None,
            ShippingAddressLine3=None,
        ),
        threeDSAuth=ThreeDSAuth(
            TermUrl="https://example.com/post-3ds-token",
            MethodNotificationUrl="https://example.com/capture-3ds-token",
            RequestChallengeIndicator=ChallengeIndicator.CHALLENGE,
        ),
    )

    mock_api_client._async_request.return_value = {
        "ResponseMessage": "3D_SECURE_CHALLENGE",
        "AzulOrderId": "12345",
        "ThreeDSChallenge": {
            "CReq": "test_token_creq",
            "RedirectPostUrl": "https://test.com/3ds-token",
        },
    }
    sale_result = await secure_service.process_token_sale(token_sale_request)
    assert sale_result["redirect"] is True
    secure_id = sale_result["id"]

    mock_api_client._async_request.return_value = {
        "ResponseMessage": "APROBADA",
        "IsoCode": "00",
        "AzulOrderId": "12345",
        "AuthorizationCode": "123456",
        "ThreeDSInfo": {
            "AuthenticationStatus": "Y",
            "AuthenticationValue": "3q2+78r+ur7erb7",
            "ECI": "05",
        },
    }
    challenge_result = await secure_service.process_challenge(secure_id, "test_cres")
    assert challenge_result["ResponseMessage"] == "APROBADA"
    assert challenge_result["IsoCode"] == "00"
    assert "ThreeDSInfo" in challenge_result
    assert challenge_result["ThreeDSInfo"]["AuthenticationStatus"] == "Y"
