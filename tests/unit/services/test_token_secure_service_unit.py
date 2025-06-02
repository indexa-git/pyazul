"""Unit tests for pyazul secure token & datavault-related functionalities."""

from unittest.mock import AsyncMock, Mock

import pytest

from pyazul.models.datavault import TokenError, TokenRequest, TokenSale, TokenSuccess
from pyazul.models.three_ds import (
    CardHolderInfo,
    ChallengeIndicator,
    SecureSale,
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
    # Use configure_mock to avoid protected access warnings
    client.configure_mock(**{"post": AsyncMock(), "_async_request": AsyncMock()})
    return client


@pytest.fixture
def mock_settings():
    """Create a mock AzulSettings object."""
    settings = Mock()
    settings.MERCHANT_ID = "39038540035"
    settings.CHANNEL = "EC"
    return settings


@pytest.fixture
def secure_service(mock_api_client, mock_settings):
    """Create a SecureService instance with mock API client."""
    return SecureService(mock_api_client, mock_settings)


@pytest.fixture
def datavault_service(mock_api_client, mock_settings):
    """Create a DataVaultService instance with mock API client."""
    return DataVaultService(mock_api_client, mock_settings)


@pytest.fixture
def transaction_service(mock_api_client, mock_settings):
    """Create a TransactionService instance with mock API client."""
    return TransactionService(mock_api_client, mock_settings)


@pytest.fixture
def tokenization_request(mock_settings):
    """Create a sample token creation request."""
    card = get_card("MASTERCARD_1")
    return TokenRequest(
        CardNumber=card["number"],
        Expiration=card["expiration"],
        Store=mock_settings.MERCHANT_ID,
        TrxType="CREATE",
    )


@pytest.fixture
async def created_token(datavault_service, tokenization_request, mock_api_client):
    """Create a token and return the token value."""
    mock_api_client.post.return_value = {
        "ResponseMessage": "APROBADA",
        "IsoCode": "00",
        "DataVaultToken": "6EF85D01-B07C-4E67-99F74E13A449DCDD",
        "CardNumber": "XXXXXX...XXXX8888",  # Masked card number
        "Brand": "MASTERCARD",
        "Expiration": "202812",
    }
    response = await datavault_service.create_token(tokenization_request)
    return response.DataVaultToken


@pytest.fixture
def token_3ds_sale_request(created_token, mock_settings):
    """Create a sample token sale request with 3DS."""
    card = get_card("MASTERCARD_1")
    return SecureSale(
        Amount="1000",
        Itbis="180",
        CardNumber=card["number"],
        Expiration=card["expiration"],
        OrderNumber=generate_order_number(),
        Store=mock_settings.MERCHANT_ID,
        CVC="123",
        CardHolderInfo=CardHolderInfo(
            Email="test@example.com",
            Name="Test User",
        ),
        ThreeDSAuth=ThreeDSAuth(
            TermUrl="https://example.com/post-3ds-token",
            MethodNotificationUrl="https://example.com/capture-3ds-token",
            RequestChallengeIndicator=ChallengeIndicator.CHALLENGE,
        ),
    )


@pytest.fixture
def token_non_3ds_sale_request(created_token, mock_settings):
    """Create a sample token sale request without 3DS."""
    token_sale_data = {
        "Amount": "1000",
        "DataVaultToken": created_token,
        "OrderNumber": generate_order_number(),
        "Store": mock_settings.MERCHANT_ID,
        "ForceNo3DS": "1",
        "CVC": "123",
    }
    return TokenSale(**token_sale_data)


@pytest.mark.asyncio
async def test_token_creation(datavault_service, tokenization_request, mock_api_client):
    """Test token creation with response validation."""
    mock_api_client.post.return_value = {
        "ResponseMessage": "APROBADA",
        "IsoCode": "00",
        "DataVaultToken": "6EF85D01-B07C-4E67-99F74E13A449DCDD",
        "CardNumber": "XXXXXX...XXXX8888",  # Masked card number
        "Brand": "MASTERCARD",
        "Expiration": "202812",
        "HasCVV": True,
    }
    response = await datavault_service.create_token(tokenization_request)

    # Assert we got a success response with CardNumber field
    assert isinstance(response, TokenSuccess)
    assert response.IsoCode == "00"
    assert response.ResponseMessage == "APROBADA"
    assert response.DataVaultToken is not None
    assert response.CardNumber == "XXXXXX...XXXX8888"
    assert response.DataVaultBrand == "MASTERCARD"
    assert response.DataVaultExpiration == "202812"

    return response.DataVaultToken


@pytest.mark.asyncio
async def test_token_creation_cardnumber_field(
    datavault_service, tokenization_request, mock_api_client
):
    """
    Test that CardNumber field is properly included in DataVault response.

    This test validates that the CardNumber field is correctly returned
    and accessible in DataVault responses as documented by Azul.
    """
    # Mock response that includes CardNumber as documented by Azul
    mock_api_client.post.return_value = {
        "ResponseMessage": "APROBADA",
        "IsoCode": "00",
        "DataVaultToken": "6EF85D01-B07C-4E67-99F74E13A449DCDD",
        "CardNumber": "XXXXXX...XXXX8888",  # Masked card number
        "Brand": "MASTERCARD",
        "Expiration": "202812",
        "HasCVV": True,
        "ErrorDescription": "",
    }

    response = await datavault_service.create_token(tokenization_request)

    # Verify typed response structure
    assert isinstance(response, TokenSuccess)

    # Specifically test the CardNumber field
    assert hasattr(response, "CardNumber"), "Response should have CardNumber field"
    assert (
        response.CardNumber == "XXXXXX...XXXX8888"
    ), "CardNumber should match expected masked value"
    assert response.CardNumber is not None, "CardNumber should not be None"
    assert response.CardNumber != "", "CardNumber should not be empty"

    # Verify other expected fields
    assert response.DataVaultToken == "6EF85D01-B07C-4E67-99F74E13A449DCDD"
    assert response.DataVaultBrand == "MASTERCARD"
    assert response.DataVaultExpiration == "202812"
    assert response.IsoCode == "00"
    assert response.ResponseMessage == "APROBADA"

    print(f"✅ CardNumber field validated: {response.CardNumber}")


@pytest.mark.asyncio
async def test_token_creation_error_response(
    datavault_service, tokenization_request, mock_api_client
):
    """
    Test DataVault error response handling with typed responses.

    This ensures error responses are properly typed and contain expected fields.
    """
    # Mock an error response
    mock_api_client.post.return_value = {
        "ResponseMessage": "DECLINED",
        "IsoCode": "99",
        "ErrorDescription": "VALIDATION_ERROR:CardNumber",
        "DataVaultToken": "",
        "CardNumber": "",
        "DataVaultBrand": "",
        "DataVaultExpiration": "",
        "HasCVV": False,
    }

    response = await datavault_service.create_token(tokenization_request)

    # Verify we get an error response type
    assert isinstance(response, TokenError)
    assert response.IsoCode == "99"
    assert response.ResponseMessage == "DECLINED"
    assert response.ErrorDescription == "VALIDATION_ERROR:CardNumber"

    # Error responses should have empty data fields
    assert response.DataVaultToken == ""
    assert response.CardNumber == ""
    assert response.DataVaultBrand == ""
    assert response.DataVaultExpiration == ""
    assert response.HasCVV is False

    print(f"✅ Error response validated: {response.ErrorDescription}")


@pytest.mark.asyncio
async def test_token_sale_non_3ds(
    transaction_service, token_non_3ds_sale_request, mock_api_client
):
    """Test token sale without 3DS (ForceNo3DS=1)."""
    mock_api_client.post.return_value = {
        "ResponseMessage": "APROBADA",
        "IsoCode": "00",
        "AuthorizationCode": "123456",
        "RRN": "789012345678",
    }
    response = await transaction_service.process_token_sale(token_non_3ds_sale_request)
    assert response["ResponseMessage"] == "APROBADA"
    assert response["IsoCode"] == "00"
    assert response["AuthorizationCode"] == "123456"


@pytest.mark.asyncio
async def test_token_sale_with_3ds_challenge(
    secure_service, token_3ds_sale_request, mock_api_client
):
    """Test token sale with 3DS challenge response."""
    mock_api_client._async_request.return_value = {
        "ResponseMessage": "3D_SECURE_CHALLENGE",
        "IsoCode": "3D",
        "AzulOrderId": "12345",
        "ThreeDSChallenge": {
            "CReq": "test_token_creq",
            "RedirectPostUrl": "https://test.com/3ds-token",
        },
    }
    result = await secure_service.process_token_sale(token_3ds_sale_request)
    assert result["redirect"] is True
    assert "html" in result
    assert result["id"] is not None  # secure_id should be present


@pytest.mark.asyncio
async def test_token_sale_with_3ds_method(
    secure_service, token_3ds_sale_request, mock_api_client
):
    """Test token sale with 3DS method response and subsequent approval."""
    mock_api_client._async_request.return_value = {
        "ResponseMessage": "3D_SECURE_2_METHOD",
        "IsoCode": "3D2METHOD",
        "AzulOrderId": "67890",
        "ThreeDSMethod": {
            "MethodForm": "<form id='tdsMmethodForm'>...</form>",
            "ServerTransId": "67890-method-1234",
        },
    }
    result = await secure_service.process_token_sale(token_3ds_sale_request)
    assert result["redirect"] is True
    assert "html" in result
    assert result["id"] is not None  # secure_id should be present

    # Test method notification processing
    secure_id = result["id"]
    session_data = secure_service.get_session_info(secure_id)
    azul_order_id = session_data["azul_order_id"]

    mock_api_client._async_request.return_value = {
        "ResponseMessage": "3D_SECURE_CHALLENGE",
        "IsoCode": "3D",
        "ThreeDSChallenge": {
            "CReq": "test_creq_after_method",
            "RedirectPostUrl": "https://test.com/3ds-challenge",
        },
    }
    method_result = await secure_service.process_3ds_method(azul_order_id, "RECEIVED")
    assert method_result["ResponseMessage"] == "3D_SECURE_CHALLENGE"


@pytest.mark.asyncio
async def test_token_sale_comparison_unit(
    transaction_service, secure_service, created_token, mock_settings, mock_api_client
):
    """Test both 3DS and non-3DS token sales with mocks for logic validation."""
    # Test non-3DS token sale
    non_3ds_data = {
        "Amount": "1000",
        "DataVaultToken": created_token,
        "OrderNumber": generate_order_number(),
        "Store": mock_settings.MERCHANT_ID,
        "ForceNo3DS": "1",
        "CVC": "123",
    }

    mock_api_client.post.return_value = {
        "ResponseMessage": "APROBADA",
        "IsoCode": "00",
        "AuthorizationCode": "NON3DS123",
    }
    non_3ds_request = TokenSale(**non_3ds_data)
    non_3ds_response = await transaction_service.process_token_sale(non_3ds_request)
    assert non_3ds_response.get("IsoCode") == "00"
    assert non_3ds_response.get("AuthorizationCode") == "NON3DS123"

    # Test 3DS token sale
    card = get_card("MASTERCARD_1")
    three_ds_request = SecureSale(
        Amount="1000",
        Itbis="180",
        CardNumber=card["number"],
        Expiration=card["expiration"],
        OrderNumber=generate_order_number(),
        Store=mock_settings.MERCHANT_ID,
        CVC="123",
        CardHolderInfo=CardHolderInfo(
            Name="Test User",
        ),
        ThreeDSAuth=ThreeDSAuth(
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
    assert three_ds_response.get("IsoCode") == "00"
    assert three_ds_response.get("AuthorizationCode") == "3DS123"


@pytest.mark.asyncio
async def test_complete_token_3ds_workflow(
    secure_service,
    datavault_service,
    tokenization_request,
    mock_api_client,
    mock_settings,
):
    """Test the complete token and 3DS workflow."""
    mock_api_client.post.return_value = {
        "ResponseMessage": "APROBADA",
        "IsoCode": "00",
        "DataVaultToken": "6EF85D01-B07C-4E67-99F74E13A449DCDD",
        "CardNumber": "XXXXXX...XXXX8888",  # Masked card number
        "Brand": "MASTERCARD",
        "Expiration": "202812",
    }
    token_response = await datavault_service.create_token(tokenization_request)
    assert isinstance(token_response, TokenSuccess)
    token = token_response.DataVaultToken
    assert token is not None

    order_number = generate_order_number()
    card = get_card("MASTERCARD_1")
    token_sale_request = SecureSale(
        Amount="1000",
        Itbis="180",
        CardNumber=card["number"],
        Expiration=card["expiration"],
        OrderNumber=order_number,
        Store=mock_settings.MERCHANT_ID,
        CVC="123",
        CardHolderInfo=CardHolderInfo(
            Email="test@example.com",
            Name="Test User",
        ),
        ThreeDSAuth=ThreeDSAuth(
            TermUrl="https://example.com/post-3ds-token",
            MethodNotificationUrl="https://example.com/capture-3ds-token",
            RequestChallengeIndicator=ChallengeIndicator.CHALLENGE,
        ),
    )

    mock_api_client._async_request.return_value = {
        "ResponseMessage": "3D_SECURE_CHALLENGE",
        "IsoCode": "3D",
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
