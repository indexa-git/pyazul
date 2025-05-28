"""Tests for 3D Secure functionalities of the PyAzul SDK."""

import uuid
from unittest.mock import AsyncMock, Mock

import pytest

from pyazul.core.exceptions import AzulError
from pyazul.models.secure import (
    CardHolderInfo,
    ChallengeIndicator,
    SecureSaleRequest,
    ThreeDSAuth,
)
from pyazul.services.secure import SecureService
from tests.fixtures.cards import get_card
from tests.fixtures.order import generate_order_number


@pytest.fixture
def mock_api_client():
    """Create a mock API client."""
    client = Mock()
    # Use configure_mock to avoid protected access warnings
    client.configure_mock(**{"_async_request": AsyncMock()})
    client.settings = Mock()
    client.settings.MERCHANT_ID = "39038540035"  # Using the MERCHANT_ID from .env
    return client


@pytest.fixture
def secure_service(mock_api_client):
    """Create a SecureService instance with mock API client."""
    return SecureService(mock_api_client)


@pytest.fixture
def sample_sale_request(mock_api_client):
    """Create a sample sale request."""
    card = get_card("SECURE_3DS_CHALLENGE_WITH_3DS")
    return SecureSaleRequest(
        Store=mock_api_client.settings.MERCHANT_ID,
        Amount="1000",
        Itbis="180",
        CardNumber=card["number"],
        CVC=card["cvv"],
        Expiration=card["expiration"],
        OrderNumber=generate_order_number(),
        Channel="EC",
        PosInputMode="E-Commerce",
        AcquirerRefData="1",
        CustomOrderId=None,
        SaveToDataVault="0",
        forceNo3DS="0",
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
            TermUrl="https://example.com/post-3ds",
            MethodNotificationUrl="https://example.com/capture-3ds",
            RequestChallengeIndicator=ChallengeIndicator.CHALLENGE,
        ),
    )


@pytest.fixture
def sample_hold_request(mock_api_client):
    """Create a sample hold request."""
    card = get_card("SECURE_3DS_CHALLENGE_WITH_3DS")
    return SecureSaleRequest(
        Store=mock_api_client.settings.MERCHANT_ID,
        Amount="1000",
        Itbis="180",
        CardNumber=card["number"],
        CVC=card["cvv"],
        Expiration=card["expiration"],
        OrderNumber=generate_order_number(),
        Channel="EC",
        PosInputMode="E-Commerce",
        AcquirerRefData="1",
        CustomOrderId=None,
        SaveToDataVault="0",
        forceNo3DS="0",
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
            TermUrl="https://example.com/post-3ds-hold",
            MethodNotificationUrl="https://example.com/capture-3ds-hold",
            RequestChallengeIndicator=ChallengeIndicator.CHALLENGE,
        ),
    )


# Fixture aliases to avoid redefined outer name warnings
@pytest.fixture
def service(secure_service):
    """Alias for secure_service fixture."""
    return secure_service


@pytest.fixture
def api_client(mock_api_client):
    """Alias for mock_api_client fixture."""
    return mock_api_client


@pytest.fixture
def sale_request(sample_sale_request):
    """Alias for sample_sale_request fixture."""
    return sample_sale_request


@pytest.fixture
def hold_request(sample_hold_request):
    """Alias for sample_hold_request fixture."""
    return sample_hold_request


@pytest.mark.asyncio
async def test_process_sale_3ds_challenge(service, sale_request, api_client):
    """Test process_sale with 3DS challenge response."""
    # Mock API response for 3DS challenge
    getattr(api_client, "_async_request").return_value = {
        "ResponseMessage": "3D_SECURE_CHALLENGE",
        "AzulOrderId": "12345",
        "ThreeDSChallenge": {
            "CReq": "test_creq",
            "RedirectPostUrl": "https://test.com/3ds",
        },
    }

    result = await service.process_sale(sale_request)

    assert result["redirect"] is True
    assert "html" in result
    assert result["id"] is not None


@pytest.mark.asyncio
async def test_process_sale_direct_approval(service, sale_request, api_client):
    """Test process_sale with direct approval (no 3DS)."""
    # Mock API response for direct approval
    getattr(api_client, "_async_request").return_value = {
        "ResponseMessage": "APROBADA",
        "IsoCode": "00",
        "AzulOrderId": "12345",
    }

    result = await service.process_sale(sale_request)

    assert result["redirect"] is False
    assert result["value"]["ResponseMessage"] == "APROBADA"
    assert result["value"]["IsoCode"] == "00"


@pytest.mark.asyncio
async def test_process_3ds_method(service, api_client):
    """Test process_3ds_method with successful response."""
    # Set up session data for the azul_order_id
    service.secure_sessions["test_session"] = {
        "azul_order_id": "12345",
        "amount": "1000",
        "itbis": "180",
        "order_number": "TEST123",
        "term_url": "https://example.com/post-3ds?secure_id=test_session",
    }

    # Mock API response for 3DS method
    getattr(api_client, "_async_request").return_value = {
        "ResponseMessage": "3D_SECURE_CHALLENGE",
        "AzulOrderId": "12345",
        "ThreeDSChallenge": {
            "CReq": "test_creq",
            "RedirectPostUrl": "https://test.com/3ds",
        },
    }

    result = await service.process_3ds_method("12345", "RECEIVED")

    assert result["ResponseMessage"] == "3D_SECURE_CHALLENGE"
    assert "ThreeDSChallenge" in result


@pytest.mark.asyncio
async def test_process_challenge(service, api_client):
    """Test process_challenge with successful response."""
    # Setup test data
    secure_id = "test_session"
    card_details = get_card("SECURE_3DS_CHALLENGE_WITH_3DS")
    service.secure_sessions[secure_id] = {
        "azul_order_id": "12345",
        "card_number": card_details["number"],
        "expiration": card_details["expiration"],
        "amount": 1000,
        "itbis": 180,
    }

    # Mock API response for challenge
    getattr(api_client, "_async_request").return_value = {
        "ResponseMessage": "APROBADA",
        "IsoCode": "00",
        "AzulOrderId": "12345",
    }

    result = await service.process_challenge(secure_id, "test_cres")

    assert result["ResponseMessage"] == "APROBADA"
    assert result["IsoCode"] == "00"
    assert result["AzulOrderId"] == "12345"


@pytest.mark.asyncio
async def test_process_challenge_invalid_session(service):
    """Test process_challenge with invalid session."""
    with pytest.raises(AzulError, match="Invalid secure session ID"):
        await service.process_challenge("invalid_session", "test_cres")


@pytest.mark.asyncio
async def test_process_3ds_method_already_processed(service, api_client):
    """Test process_3ds_method with already processed transaction."""
    # Add order to processed methods
    service.processed_methods["12345"] = True

    result = await service.process_3ds_method("12345", "RECEIVED")

    assert result["ResponseMessage"] == "ALREADY_PROCESSED"
    assert result["AzulOrderId"] == "12345"


@pytest.mark.asyncio
async def test_process_sale_with_3ds_authentication(service, sale_request, api_client):
    """Test process_sale with successful 3DS authentication."""
    # Mock API response for 3DS authentication
    getattr(api_client, "_async_request").return_value = {
        "ResponseMessage": "APROBADA",
        "IsoCode": "00",
        "AzulOrderId": "12345",
        "ThreeDSInfo": {
            "AuthenticationStatus": "Y",  # Y = Autenticación exitosa
            "AuthenticationValue": "3q2+78r+ur7erb7",
            "ECI": "05",  # ECI para Visa con autenticación exitosa
        },
    }

    result = await service.process_sale(sale_request)

    assert result["redirect"] is False
    assert result["value"]["ResponseMessage"] == "APROBADA"
    assert result["value"]["IsoCode"] == "00"
    assert "ThreeDSInfo" in result["value"]
    assert result["value"]["ThreeDSInfo"]["AuthenticationStatus"] == "Y"
    assert "AuthenticationValue" in result["value"]["ThreeDSInfo"]
    assert "ECI" in result["value"]["ThreeDSInfo"]


@pytest.mark.asyncio
async def test_process_sale_with_3ds_redirection(service, sale_request, api_client):
    """Test process_sale with 3DS redirection for authentication."""
    # Mock API response for 3DS redirection
    getattr(api_client, "_async_request").return_value = {
        "ResponseMessage": "3D_SECURE_2_METHOD",
        "AzulOrderId": "12345",
        "ThreeDSMethod": {
            "MethodForm": "<form id='tdsMmethodForm'>...</form>",
            "ServerTransId": "12345-method-1234",
        },
    }

    result = await service.process_sale(sale_request)

    assert result["redirect"] is True
    assert isinstance(result["id"], str)
    try:
        uuid.UUID(result["id"])
    except ValueError:
        pytest.fail("result['id'] is not a valid UUID")
    assert result["html"] == "<form id='tdsMmethodForm'>...</form>"
    assert result["message"] == "Starting 3D Secure verification..."


@pytest.mark.asyncio
async def test_process_hold_3ds_challenge(service, hold_request, api_client):
    """Test process_hold with 3DS challenge response."""
    # Mock API response for 3DS challenge
    getattr(api_client, "_async_request").return_value = {
        "ResponseMessage": "3D_SECURE_CHALLENGE",
        "AzulOrderId": "67890",
        "ThreeDSChallenge": {
            "CReq": "test_hold_creq",
            "RedirectPostUrl": "https://test.com/3ds-hold",
        },
    }

    result = await service.process_hold(hold_request)

    assert result["redirect"] is True
    assert "html" in result
    assert result["id"] is not None


@pytest.mark.asyncio
async def test_process_hold_direct_approval(service, hold_request, api_client):
    """Test process_hold with direct approval (no 3DS)."""
    # Mock API response for direct approval
    getattr(api_client, "_async_request").return_value = {
        "ResponseMessage": "APROBADA",
        "IsoCode": "00",
        "AzulOrderId": "67890",
    }

    result = await service.process_hold(hold_request)

    assert result["redirect"] is False
    assert result["value"]["ResponseMessage"] == "APROBADA"
    assert result["value"]["IsoCode"] == "00"


@pytest.mark.asyncio
async def test_process_hold_with_3ds_method(service, hold_request, api_client):
    """Test process_hold with 3DS method response."""
    # Mock API response for 3DS method
    getattr(api_client, "_async_request").return_value = {
        "ResponseMessage": "3D_SECURE_2_METHOD",
        "AzulOrderId": "67890",
        "ThreeDSMethod": {
            "MethodForm": "<form id='tdsMethodForm'>...</form>",
            "ServerTransId": "67890-method-1234",
        },
    }

    result = await service.process_hold(hold_request)

    assert result["redirect"] is True
    assert isinstance(result["id"], str)
    assert "html" in result
    assert result["message"] == "Starting 3D Secure verification..."
