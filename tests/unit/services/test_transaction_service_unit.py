"""Unit tests for pyazul.services.transaction."""

from unittest.mock import MagicMock

import pytest

from pyazul.api.client import AzulAPI
from pyazul.models.schemas import (
    HoldTransactionModel,
    PostSaleTransactionModel,
    RefundTransactionModel,
    SaleTransactionModel,
    VoidTransactionModel,
)
from pyazul.services.transaction import TransactionService

SAMPLE_SALE_VALUES = {
    "Store": "12345",
    "Channel": "EC",
    "OrderNumber": "ORDER001",
    "Amount": "1000",
    "Itbis": "180",
    "CardNumber": "4000000000000001",
    "Expiration": "202512",
    "CVC": "123",
    "PosInputMode": "E-Commerce",
    "AcquirerRefData": "RefData123",
    "SaveToDataVault": "0",
}

SAMPLE_HOLD_VALUES = SAMPLE_SALE_VALUES

SAMPLE_REFUND_VALUES = {
    "Store": "12345",
    "Channel": "EC",
    "OrderNumber": "ORDER001",
    "AzulOrderId": "AZULREF001",
    "Amount": "500",
    "Itbis": "90",
    "AcquirerRefData": "RefundRef123",
}

SAMPLE_VOID_VALUES = {"Store": "12345", "Channel": "EC", "AzulOrderId": "AZULVOID002"}

SAMPLE_POST_SALE_VALUES = {
    "Store": "12345",
    "Channel": "EC",
    "OrderNumber": "ORDER001",
    "AzulOrderId": "AZULHOLD001",
    "Amount": "1000",
    "Itbis": "180",
    "AcquirerRefData": "PostRef456",
}


@pytest.fixture
def transaction_service(mock_api_client: AzulAPI) -> TransactionService:
    """Return a TransactionService instance with a mock API client."""
    return TransactionService(api_client=mock_api_client)


class TestTransactionService:
    """Tests for the TransactionService."""

    @pytest.mark.asyncio
    async def test_sale(
        self, transaction_service: TransactionService, mock_api_client: MagicMock
    ):
        """Test the sale method of TransactionService."""
        sale_request_model = SaleTransactionModel(TrxType="Sale", **SAMPLE_SALE_VALUES)
        expected_response = {"ResponseMessage": "APROBADA", "IsoCode": "00"}
        mock_api_client._async_request.return_value = expected_response

        response = await transaction_service.sale(sale_request_model)

        assert response == expected_response
        actual_call_args = mock_api_client._async_request.call_args
        assert actual_call_args is not None
        expected_payload = sale_request_model.model_dump(
            exclude_none=True, exclude_defaults=False, exclude_unset=False
        )
        assert actual_call_args[0][0] == expected_payload
        assert "operation" not in actual_call_args[1]

    @pytest.mark.asyncio
    async def test_refund(
        self, transaction_service: TransactionService, mock_api_client: MagicMock
    ):
        """Test the refund method of TransactionService."""
        refund_request_model = RefundTransactionModel(
            TrxType="Refund", **SAMPLE_REFUND_VALUES
        )
        expected_response = {"ResponseMessage": "APROBADA", "IsoCode": "00"}
        mock_api_client._async_request.return_value = expected_response

        response = await transaction_service.refund(refund_request_model)

        assert response == expected_response
        actual_call_args = mock_api_client._async_request.call_args
        assert actual_call_args is not None
        assert actual_call_args[0][0] == refund_request_model.model_dump(
            exclude_none=True
        )
        assert "operation" not in actual_call_args[1]

    @pytest.mark.asyncio
    async def test_void(
        self, transaction_service: TransactionService, mock_api_client: MagicMock
    ):
        """Test the void method of TransactionService."""
        void_request_model = VoidTransactionModel(**SAMPLE_VOID_VALUES)
        expected_response = {"ResponseMessage": "APROBADA", "IsoCode": "00"}
        mock_api_client._async_request.return_value = expected_response

        response = await transaction_service.void(void_request_model)

        assert response == expected_response
        actual_call_args = mock_api_client._async_request.call_args
        assert actual_call_args is not None
        assert actual_call_args[0][0] == void_request_model.model_dump(
            exclude_none=True
        )
        assert actual_call_args[1]["operation"] == "ProcessVoid"

    @pytest.mark.asyncio
    async def test_hold(
        self, transaction_service: TransactionService, mock_api_client: MagicMock
    ):
        """Test the hold method of TransactionService."""
        hold_request_model = HoldTransactionModel(TrxType="Hold", **SAMPLE_HOLD_VALUES)
        expected_response = {"ResponseMessage": "APROBADA", "IsoCode": "00"}
        mock_api_client._async_request.return_value = expected_response

        response = await transaction_service.hold(hold_request_model)

        assert response == expected_response
        actual_call_args = mock_api_client._async_request.call_args
        assert actual_call_args is not None
        assert actual_call_args[0][0] == hold_request_model.model_dump(
            exclude_none=True
        )
        assert "operation" not in actual_call_args[1]

    @pytest.mark.asyncio
    async def test_post_sale(
        self, transaction_service: TransactionService, mock_api_client: MagicMock
    ):
        """Test the post_sale method of TransactionService."""
        post_request_model = PostSaleTransactionModel(**SAMPLE_POST_SALE_VALUES)
        expected_response = {"ResponseMessage": "APROBADA", "IsoCode": "00"}
        mock_api_client._async_request.return_value = expected_response

        response = await transaction_service.post_sale(post_request_model)

        assert response == expected_response
        actual_call_args = mock_api_client._async_request.call_args
        assert actual_call_args is not None
        assert actual_call_args[0][0] == post_request_model.model_dump(
            exclude_none=True
        )
        assert actual_call_args[1]["operation"] == "ProcessPost"
