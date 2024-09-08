import pytest  # type: ignore
from unittest.mock import patch, AsyncMock
from httpx import Response

from pyazul import AzulAPIAsync


@pytest.fixture
def azul_api_async():
    return AzulAPIAsync(
        auth1="auth1",
        auth2="auth2",
        # Cert path is omitted for unit tests
        environment="dev",
    )


@pytest.mark.asyncio
async def test_sale_transaction(azul_api_async):
    sale_data = {
        "Channel": "Web",
        "Store": "TestStore",
        "CardNumber": "1234567890123456",
        "Expiration": "12/25",
        "CVC": "123",
        "Amount": "100.00",
        "CurrencyPosCode": "USD",
        "CustomerServicePhone": "1234567890",
        "OrderNumber": "TEST001",
        "EcommerceURL": "https://example.com",
        "CustomOrderID": "CUSTOM001",
    }

    mock_response = AsyncMock(spec=Response)
    mock_response.json.return_value = {"ResponseMessage": "Approved"}
    mock_response.raise_for_status = AsyncMock()
    mock_response.text = '{"ResponseMessage": "Approved"}'

    with patch("httpx.AsyncClient.post", return_value=mock_response):
        response = await azul_api_async.sale_transaction(sale_data)

        assert response == {"ResponseMessage": "Approved"}


@pytest.mark.asyncio
async def test_void_transaction(azul_api_async):
    void_data = {"Channel": "Web", "Store": "TestStore", "AzulOrderId": "ORDER123"}

    mock_response = AsyncMock(spec=Response)
    mock_response.json.return_value = {"ResponseMessage": "Voided"}
    mock_response.raise_for_status = AsyncMock()
    mock_response.text = '{"ResponseMessage": "Voided"}'

    with patch("httpx.AsyncClient.post", return_value=mock_response):
        response = await azul_api_async.void_transaction(void_data)

        assert response == {"ResponseMessage": "Voided"}


@pytest.mark.asyncio
async def test_datavault_create(azul_api_async):
    datavault_data = {
        "Channel": "Web",
        "Store": "TestStore",
        "CardNumber": "1234567890123456",
        "Expiration": "12/25",
        "CVC": "123",
    }

    mock_response = AsyncMock(spec=Response)
    mock_response.json.return_value = {"DataVaultToken": "TOKEN123"}
    mock_response.raise_for_status = AsyncMock()
    mock_response.text = '{"DataVaultToken": "TOKEN123"}'

    with patch("httpx.AsyncClient.post", return_value=mock_response):
        response = await azul_api_async.datavault_create(datavault_data)

        assert response == {"DataVaultToken": "TOKEN123"}


@pytest.mark.asyncio
async def test_verify_transaction(azul_api_async):
    verify_data = {"Channel": "Web", "Store": "TestStore", "CustomOrderId": "CUSTOM001"}

    mock_response = AsyncMock(spec=Response)
    mock_response.json.return_value = {"VerificationResult": "Success"}
    mock_response.raise_for_status = AsyncMock()
    mock_response.text = '{"VerificationResult": "Success"}'

    with patch("httpx.AsyncClient.post", return_value=mock_response):
        response = await azul_api_async.verify_transaction(verify_data)

        assert response == {"VerificationResult": "Success"}
