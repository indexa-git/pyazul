import pytest # type: ignore
from unittest.mock import patch, AsyncMock
from httpx import HTTPStatusError, Response

from pyazul import AzulAPI, AzulAPIConfig
from pyazul import clean_amount

@pytest.fixture
def azul_api():
    config = AzulAPIConfig(
        auth1="test_auth1",
        auth2="test_auth2",
        # Cert path is omitted for unit tests
        environment="dev"
    )
    return AzulAPI(config)

@pytest.mark.asyncio
async def test_sale_transaction(azul_api):
    sale_data = {
        "Channel": "Web",
        "Store": "TestStore",
        "CardNumber": "1234567890123456",
        "Expiration": "12/25",
        "CVC": "123",
        "Amount": 10000,
        "CurrencyPosCode": "USD",
        "CustomerServicePhone": "1234567890",
        "OrderNumber": "TEST001",
        "EcommerceURL": "https://example.com",
        "CustomOrderID": "CUSTOM001"
    }
    
    mock_response = AsyncMock(spec=Response)
    mock_response.json.return_value = {"ResponseMessage": "Approved"}
    mock_response.raise_for_status = AsyncMock()

    with patch('httpx.AsyncClient.post', return_value=mock_response):
        response = await azul_api.sale_transaction(sale_data)
        
        assert response == {"ResponseMessage": "Approved"}

@pytest.mark.asyncio
async def test_void_transaction(azul_api):
    void_data = {
        "Channel": "Web",
        "Store": "TestStore",
        "AzulOrderId": "ORDER123"
    }
    
    mock_response = AsyncMock(spec=Response)
    mock_response.json.return_value = {"ResponseMessage": "Voided"}
    mock_response.raise_for_status = AsyncMock()

    with patch('httpx.AsyncClient.post', return_value=mock_response):
        response = await azul_api.void_transaction(void_data)
        
        assert response == {"ResponseMessage": "Voided"}

@pytest.mark.asyncio
async def test_azul_request_prod_fallback(azul_api):
    azul_api.config.environment = "prod"
    sale_data = {
        "Channel": "Web",
        "Store": "TestStore",
        "CardNumber": "1234567890123456",
        "Expiration": "12/25",
        "CVC": "123",
        "Amount": 10000,
        "CurrencyPosCode": "USD",
        "CustomerServicePhone": "1234567890",
        "OrderNumber": "TEST001",
        "EcommerceURL": "https://example.com",
        "CustomOrderID": "CUSTOM001"
    }
    
    error_response = AsyncMock(spec=Response)
    error_response.raise_for_status.side_effect = HTTPStatusError("Error", request=AsyncMock(), response=AsyncMock())

    success_response = AsyncMock(spec=Response)
    success_response.json.return_value = {"ResponseMessage": "Approved"}
    success_response.raise_for_status = AsyncMock()

    with patch('httpx.AsyncClient.post', side_effect=[error_response, success_response]):
        response = await azul_api.sale_transaction(sale_data)
        
        assert response == {"ResponseMessage": "Approved"}

@pytest.mark.asyncio
async def test_datavault_create(azul_api):
    datavault_data = {
        "Channel": "Web",
        "Store": "TestStore",
        "CardNumber": "1234567890123456",
        "Expiration": "12/25",
        "CVC": "123"
    }
    
    mock_response = AsyncMock(spec=Response)
    mock_response.json.return_value = {"DataVaultToken": "TOKEN123"}
    mock_response.raise_for_status = AsyncMock()

    with patch('httpx.AsyncClient.post', return_value=mock_response):
        response = await azul_api.datavault_create(datavault_data)
        
        assert response == {"DataVaultToken": "TOKEN123"}

@pytest.mark.asyncio
async def test_verify_transaction(azul_api):
    verify_data = {
        "Channel": "Web",
        "Store": "TestStore",
        "CustomOrderId": "CUSTOM001"
    }
    
    mock_response = AsyncMock(spec=Response)
    mock_response.json.return_value = {"VerificationResult": "Success"}
    mock_response.raise_for_status = AsyncMock()

    with patch('httpx.AsyncClient.post', return_value=mock_response):
        response = await azul_api.verify_transaction(verify_data)
        
        assert response == {"VerificationResult": "Success"}

def test_clean_amount():
    assert clean_amount(100.50) == 10050
    assert clean_amount(99.99) == 9999
    assert clean_amount(0.01) == 1