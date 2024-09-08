import pytest
from unittest.mock import patch, Mock
from httpx import Response
from pydantic import ValidationError

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


def test_api_error_handling(azul_api):
    with patch("httpx.Client.post", side_effect=Exception("API Error")):
        with pytest.raises(ValidationError):
            azul_api.sale_transaction({"Channel": "Web", "Store": "TestStore"})


def test_production_alternate_url(azul_api):
    azul_api.ENVIRONMENT = "prod"
    azul_api.ALT_URL = "https://alt-url.com"

    mock_response1 = Mock(spec=Response)
    mock_response1.raise_for_status.side_effect = Exception("Primary URL failed")

    mock_response2 = Mock(spec=Response)
    mock_response2.json.return_value = {"ResponseMessage": "Success"}
    mock_response2.raise_for_status = Mock()
    mock_response2.text = '{"ResponseMessage": "Success"}'

    sale_data = {
        "Channel": "Web",
        "Store": "TestStore",
        "Amount": "100.00",
        "CurrencyPosCode": "USD",
        "CustomerServicePhone": "1234567890",
        "OrderNumber": "TEST001",
        "EcommerceURL": "https://example.com",
        "CustomOrderID": "CUSTOM001",
        "CardNumber": "1234567890123456",
        "Expiration": "12/25",
        "CVC": "123",
    }

    with patch(
        "httpx.Client.post", side_effect=[mock_response1, mock_response2]
    ) as mock_post:
        response = azul_api.sale_transaction(sale_data)
        assert response == {"ResponseMessage": "Success"}

    # Verify that both URLs were called
    assert mock_post.call_count == 2
    assert mock_post.call_args_list[0][0][0] == azul_api.url
    assert mock_post.call_args_list[1][0][0] == azul_api.ALT_URL


def test_refund_transaction(azul_api):
    refund_data = {
        "Channel": "Web",
        "Store": "TestStore",
        "Amount": "50.00",
        "AzulOrderId": "ORDER123",
        "CurrencyPosCode": "USD",
        "CustomerServicePhone": "1234567890",
        "OrderNumber": "TEST001",
        "EcommerceURL": "https://example.com",
        "CustomOrderID": "CUSTOM001",
        "OriginalDate": "2023-05-01",
        "OriginalTrxTicketNr": "TICKET123",
    }

    mock_response = Mock(spec=Response)
    mock_response.json.return_value = {"ResponseMessage": "Refunded"}
    mock_response.raise_for_status = Mock()
    mock_response.text = '{"ResponseMessage": "Refunded"}'

    with patch("httpx.Client.post", return_value=mock_response):
        response = azul_api.refund_transaction(refund_data)
        assert response == {"ResponseMessage": "Refunded"}


def test_hold_transaction(azul_api):
    hold_data = {
        "Channel": "Web",
        "Store": "TestStore",
        "Amount": "75.00",
        "CardNumber": "1234567890123456",
        "Expiration": "12/25",
        "CVC": "123",
        "CurrencyPosCode": "USD",
        "OrderNumber": "TEST001",
    }

    mock_response = Mock(spec=Response)
    mock_response.json.return_value = {"ResponseMessage": "Hold Placed"}
    mock_response.raise_for_status = Mock()
    mock_response.text = '{"ResponseMessage": "Hold Placed"}'

    with patch("httpx.Client.post", return_value=mock_response):
        response = azul_api.hold_transaction(hold_data)
        assert response == {"ResponseMessage": "Hold Placed"}


def test_custom_url():
    custom_url = "https://custom-azul-api.com"
    api = AzulAPI(auth1="auth1", auth2="auth2", custom_url=custom_url)
    assert api.url == custom_url
