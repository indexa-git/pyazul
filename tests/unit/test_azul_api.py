import pytest
from unittest.mock import patch, Mock
from httpx import Response

from pyazul import AzulAPI


@pytest.fixture
def azul_api():
    return AzulAPI(
        auth1="auth1",
        auth2="auth2",
        # Cert path is omitted for unit tests
        environment="dev",
    )


def test_sale_transaction(azul_api):
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

    mock_response = Mock(spec=Response)
    mock_response.json.return_value = {"ResponseMessage": "Approved"}
    mock_response.raise_for_status = Mock()
    mock_response.text = '{"ResponseMessage": "Approved"}'

    with patch("httpx.Client.post", return_value=mock_response):
        response = azul_api.sale_transaction(sale_data)

        assert response == {"ResponseMessage": "Approved"}


def test_void_transaction(azul_api):
    void_data = {"Channel": "Web", "Store": "TestStore", "AzulOrderId": "ORDER123"}

    mock_response = Mock(spec=Response)
    mock_response.json.return_value = {"ResponseMessage": "Voided"}
    mock_response.raise_for_status = Mock()
    mock_response.text = '{"ResponseMessage": "Voided"}'

    with patch("httpx.Client.post", return_value=mock_response):
        response = azul_api.void_transaction(void_data)

        assert response == {"ResponseMessage": "Voided"}


def test_datavault_create(azul_api):
    datavault_data = {
        "Channel": "Web",
        "Store": "TestStore",
        "CardNumber": "1234567890123456",
        "Expiration": "12/25",
        "CVC": "123",
    }

    mock_response = Mock(spec=Response)
    mock_response.json.return_value = {"DataVaultToken": "TOKEN123"}
    mock_response.raise_for_status = Mock()
    mock_response.text = '{"DataVaultToken": "TOKEN123"}'

    with patch("httpx.Client.post", return_value=mock_response):
        response = azul_api.datavault_create(datavault_data)

        assert response == {"DataVaultToken": "TOKEN123"}


def test_verify_transaction(azul_api):
    verify_data = {"Channel": "Web", "Store": "TestStore", "CustomOrderId": "CUSTOM001"}

    mock_response = Mock(spec=Response)
    mock_response.json.return_value = {"VerificationResult": "Success"}
    mock_response.raise_for_status = Mock()
    mock_response.text = '{"VerificationResult": "Success"}'

    with patch("httpx.Client.post", return_value=mock_response):
        response = azul_api.verify_transaction(verify_data)

        assert response == {"VerificationResult": "Success"}
