"""
Tests for Token Secure Integration

Este módulo contiene pruebas para verificar el flujo completo de pago con token y 3DS:
1. Crear un token de tarjeta (DataVault)
2. Procesar una venta con token utilizando 3DS
3. Probar diferentes escenarios de 3DS: challenge, direct approval, method
"""

import pytest
from unittest.mock import Mock, AsyncMock
from pyazul.services.secure import SecureService
from pyazul.services.datavault import DataVaultService
from pyazul.models.secure import SecureTokenSale, CardHolderInfo, ThreeDSAuth
from pyazul.models.schemas import DataVaultCreateModel
import uuid

@pytest.fixture
def mock_api_client():
    """Create a mock API client."""
    client = Mock()
    client._async_request = AsyncMock()
    client.settings = Mock()
    client.settings.MERCHANT_ID = "39038540035"  # Using the MERCHANT_ID from .env
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
def tokenization_request():
    """Create a sample token creation request."""
    return DataVaultCreateModel(
        CardNumber="4111111111111111",  # Test Visa card
        Expiration="202812",
        store="39038540035"
    )

@pytest.fixture
async def created_token(datavault_service, tokenization_request, mock_api_client):
    """Create a token and return the token value."""
    # Mock API response for token creation
    mock_api_client._async_request.return_value = {
        "ResponseMessage": "APROBADA",
        "IsoCode": "00",
        "DataVaultToken": "TEST_TOKEN_123456789"
    }
    
    response = await datavault_service.create(tokenization_request)
    return response.get("DataVaultToken")

@pytest.fixture
def token_3ds_sale_request(created_token):
    """Create a sample token sale request with 3DS."""
    return SecureTokenSale(
        Amount=1000,  # $10.00
        ITBIS=180,    # $1.80
        DataVaultToken=created_token,
        OrderNumber=f"TOKEN3DS-{uuid.uuid4().hex[:8]}",
        Channel="EC",
        PosInputMode="E-Commerce",
        forceNo3DS="0",
        AcquirerRefData="1",
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
            ShippingAddressZip="10101"
        ),
        threeDSAuth=ThreeDSAuth(
            TermUrl="https://example.com/post-3ds-token",
            MethodNotificationUrl="https://example.com/capture-3ds-token",
            RequestChallengeIndicator="03"
        )
    )

@pytest.mark.asyncio
async def test_token_creation(datavault_service, tokenization_request, mock_api_client):
    """Test token creation."""
    # Mock API response for token creation
    mock_api_client._async_request.return_value = {
        "ResponseMessage": "APROBADA",
        "IsoCode": "00",
        "DataVaultToken": "TEST_TOKEN_123456789"
    }
    
    response = await datavault_service.create(tokenization_request)
    
    assert response.get("IsoCode") == "00"
    assert response.get("ResponseMessage") == "APROBADA"
    assert response.get("DataVaultToken") is not None
    
    # Return token for use in other tests
    return response.get("DataVaultToken")

@pytest.mark.asyncio
async def test_token_sale_with_3ds_challenge(secure_service, token_3ds_sale_request, mock_api_client):
    """Test token sale with 3DS challenge response."""
    # Mock API response for 3DS challenge
    mock_api_client._async_request.return_value = {
        "ResponseMessage": "3D_SECURE_CHALLENGE",
        "AzulOrderId": "12345",
        "ThreeDSChallenge": {
            "CReq": "test_token_creq",
            "RedirectPostUrl": "https://test.com/3ds-token"
        }
    }

    result = await secure_service.process_token_sale(token_3ds_sale_request)

    assert result["redirect"] is True
    assert "html" in result
    assert result["id"] is not None
    
    # Simulate challenge completion
    secure_id = result["id"]
    secure_service.secure_sessions[secure_id] = {
        "azul_order_id": "12345",
        "token": token_3ds_sale_request.DataVaultToken,
        "amount": token_3ds_sale_request.Amount,
        "itbis": token_3ds_sale_request.ITBIS
    }
    
    # Mock API response for challenge completion
    mock_api_client._async_request.return_value = {
        "ResponseMessage": "APROBADA",
        "IsoCode": "00",
        "AzulOrderId": "12345",
        "AuthorizationCode": "123456"
    }
    
    # Process the challenge
    challenge_result = await secure_service.process_challenge(secure_id, "test_cres")
    
    assert challenge_result["ResponseMessage"] == "APROBADA"
    assert challenge_result["IsoCode"] == "00"
    assert challenge_result["AzulOrderId"] == "12345"

@pytest.mark.asyncio
async def test_token_sale_with_3ds_method(secure_service, token_3ds_sale_request, mock_api_client):
    """Test token sale with 3DS method response and subsequent approval."""
    # Mock API response for 3DS method
    mock_api_client._async_request.return_value = {
        "ResponseMessage": "3D_SECURE_2_METHOD",
        "AzulOrderId": "67890",
        "ThreeDSMethod": {
            "MethodForm": "<form id='tdsMethodForm'>...</form>",
            "ServerTransId": "67890-method-1234"
        }
    }

    result = await secure_service.process_token_sale(token_3ds_sale_request)

    assert result["redirect"] is True
    assert "html" in result
    assert result["id"] is not None
  
    
    # Mock API response for method notification
    mock_api_client._async_request.return_value = {
        "ResponseMessage": "APROBADA",
        "IsoCode": "00",
        "AzulOrderId": "67890",
        "AuthorizationCode": "987654"
    }
    
    # Process method notification
    method_result = await secure_service.process_3ds_method("67890", "RECEIVED")
    
    assert method_result["ResponseMessage"] == "APROBADA"
    assert method_result["IsoCode"] == "00"
    assert method_result["AzulOrderId"] == "67890"

@pytest.mark.asyncio
async def test_complete_token_3ds_workflow(secure_service, datavault_service, tokenization_request, mock_api_client):
    """Test the complete token and 3DS workflow."""
    # 1. Create token
    mock_api_client._async_request.return_value = {
        "ResponseMessage": "APROBADA",
        "IsoCode": "00",
        "DataVaultToken": "TEST_TOKEN_123456789"
    }
    
    token_response = await datavault_service.create(tokenization_request)
    token = token_response.get("DataVaultToken")
    assert token is not None
    
    # 2. Create token sale request
    order_number = f"FULL-FLOW-{uuid.uuid4().hex[:8]}"
    token_sale_request = SecureTokenSale(
        Amount=1000,
        ITBIS=180,
        DataVaultToken=token,
        OrderNumber=order_number,
        Channel="EC",
        PosInputMode="E-Commerce",
        forceNo3DS="0",
        AcquirerRefData="1",
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
            ShippingAddressZip="10101"
        ),
        threeDSAuth=ThreeDSAuth(
            TermUrl="https://example.com/post-3ds-token",
            MethodNotificationUrl="https://example.com/capture-3ds-token",
            RequestChallengeIndicator="03"
        )
    )
    
    # 3. Process token sale with 3DS challenge
    mock_api_client._async_request.return_value = {
        "ResponseMessage": "3D_SECURE_CHALLENGE",
        "AzulOrderId": "12345",
        "ThreeDSChallenge": {
            "CReq": "test_token_creq",
            "RedirectPostUrl": "https://test.com/3ds-token"
        }
    }
    
    sale_result = await secure_service.process_token_sale(token_sale_request)
    assert sale_result["redirect"] is True
    secure_id = sale_result["id"]
    
    # 4. Set up session for challenge
    secure_service.secure_sessions[secure_id] = {
        "azul_order_id": "12345",
        "token": token,
        "amount": token_sale_request.Amount,
        "itbis": token_sale_request.ITBIS
    }
    
    # 5. Process challenge
    mock_api_client._async_request.return_value = {
        "ResponseMessage": "APROBADA",
        "IsoCode": "00",
        "AzulOrderId": "12345",
        "AuthorizationCode": "123456",
        "ThreeDSInfo": {
            "AuthenticationStatus": "Y",
            "AuthenticationValue": "3q2+78r+ur7erb7",
            "ECI": "05"
        }
    }
    
    challenge_result = await secure_service.process_challenge(secure_id, "test_cres")
    
    assert challenge_result["ResponseMessage"] == "APROBADA"
    assert challenge_result["IsoCode"] == "00"
    assert "ThreeDSInfo" in challenge_result
    assert challenge_result["ThreeDSInfo"]["AuthenticationStatus"] == "Y" 