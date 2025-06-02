"""Unit tests for transaction service."""

from unittest.mock import MagicMock

import pytest

from pyazul.api.client import AzulAPI
from pyazul.core.config import AzulSettings
from pyazul.models.payment import Hold, Post, Refund, Sale, Void
from pyazul.services.transaction import TransactionService

SAMPLE_SALE_VALUES = {
    "Store": "12345",
    "OrderNumber": "ORDER001",
    "Amount": "1000",
    "Itbis": "180",
    "CardNumber": "4000000000000001",
    "Expiration": "202512",
    "CVC": "123",
}

SAMPLE_HOLD_VALUES = {
    "Store": "12345",
    "OrderNumber": "ORDER001",
    "Amount": "1000",
    "Itbis": "180",
    "CardNumber": "4000000000000001",
    "Expiration": "202512",
    "CVC": "123",
}

SAMPLE_REFUND_VALUES = {
    "Store": "12345",
    "OrderNumber": "ORDER001",
    "AzulOrderId": "AZULREF001",
    "Amount": "500",
    "Itbis": "90",
}

SAMPLE_VOID_VALUES = {"Store": "12345", "AzulOrderId": "AZULVOID002"}

SAMPLE_POST_SALE_VALUES = {
    "Store": "12345",
    "AzulOrderId": "AZULHOLD001",
    "Amount": "1000",
    "Itbis": "180",
}


@pytest.fixture
def mock_settings() -> AzulSettings:
    """Return a mock AzulSettings instance."""
    settings = MagicMock(spec=AzulSettings)
    settings.MERCHANT_ID = "123456789"
    settings.AUTH1 = "test_auth1"
    settings.AUTH2 = "test_auth2"
    settings.CHANNEL = "EC"
    return settings


@pytest.fixture
def transaction_service(
    mock_api_client: AzulAPI, mock_settings: AzulSettings
) -> TransactionService:
    """Return a TransactionService instance with a mock API client."""
    return TransactionService(client=mock_api_client, settings=mock_settings)


class TestTransactionService:
    """Tests for the TransactionService."""

    @pytest.mark.asyncio
    async def test_sale(
        self, transaction_service: TransactionService, mock_api_client: MagicMock
    ):
        """Test the process_sale method of TransactionService."""
        sale_request_model = Sale(**SAMPLE_SALE_VALUES)
        expected_response = {"ResponseMessage": "APROBADA", "IsoCode": "00"}
        mock_api_client.post.return_value = expected_response

        response = await transaction_service.process_sale(sale_request_model)

        assert response == expected_response
        actual_call_args = mock_api_client.post.call_args
        assert actual_call_args is not None
        expected_payload = sale_request_model.model_dump(
            exclude_none=True, exclude_defaults=False, exclude_unset=False
        )
        assert actual_call_args[0][1] == expected_payload

    @pytest.mark.asyncio
    async def test_refund(
        self, transaction_service: TransactionService, mock_api_client: MagicMock
    ):
        """Test the process_refund method of TransactionService."""
        refund_request_model = Refund(**SAMPLE_REFUND_VALUES)
        expected_response = {"ResponseMessage": "APROBADA", "IsoCode": "00"}
        mock_api_client.post.return_value = expected_response

        response = await transaction_service.process_refund(refund_request_model)

        assert response == expected_response
        actual_call_args = mock_api_client.post.call_args
        assert actual_call_args is not None
        assert actual_call_args[0][1] == refund_request_model.model_dump(
            exclude_none=True
        )

    @pytest.mark.asyncio
    async def test_void(
        self, transaction_service: TransactionService, mock_api_client: MagicMock
    ):
        """Test the process_void method of TransactionService."""
        void_request_model = Void(**SAMPLE_VOID_VALUES)
        expected_response = {"ResponseMessage": "APROBADA", "IsoCode": "00"}
        mock_api_client.post.return_value = expected_response

        response = await transaction_service.process_void(void_request_model)

        assert response == expected_response
        actual_call_args = mock_api_client.post.call_args
        assert actual_call_args is not None
        assert actual_call_args[0][1] == void_request_model.model_dump(
            exclude_none=True
        )
        assert actual_call_args[0][0] == "/webservices/JSON/default.aspx?ProcessVoid"

    @pytest.mark.asyncio
    async def test_hold(
        self, transaction_service: TransactionService, mock_api_client: MagicMock
    ):
        """Test the process_hold method of TransactionService."""
        hold_request_model = Hold(**SAMPLE_HOLD_VALUES)
        expected_response = {"ResponseMessage": "APROBADA", "IsoCode": "00"}
        mock_api_client.post.return_value = expected_response

        response = await transaction_service.process_hold(hold_request_model)

        assert response == expected_response
        actual_call_args = mock_api_client.post.call_args
        assert actual_call_args is not None
        assert actual_call_args[0][1] == hold_request_model.model_dump(
            exclude_none=True
        )

    @pytest.mark.asyncio
    async def test_post_sale(
        self, transaction_service: TransactionService, mock_api_client: MagicMock
    ):
        """Test the process_post method of TransactionService."""
        post_request_model = Post(**SAMPLE_POST_SALE_VALUES)
        expected_response = {"ResponseMessage": "APROBADA", "IsoCode": "00"}
        mock_api_client.post.return_value = expected_response

        response = await transaction_service.process_post(post_request_model)

        assert response == expected_response
        actual_call_args = mock_api_client.post.call_args
        assert actual_call_args is not None
        assert actual_call_args[0][1] == post_request_model.model_dump(
            exclude_none=True
        )
        assert actual_call_args[0][0] == "/webservices/JSON/default.aspx?ProcessPost"
