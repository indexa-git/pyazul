import pytest
from pydantic import ValidationError
from pyazul.models import (
    clean_amount,
    AzulBaseModel,
    TransactionWithAmountModel,
    SaleTransactionModel,
    VoidTransactionModel,
    DataVaultCreateModel,
    DataVaultDeleteModel,
    HoldTransactionModel,
    PostSaleTransactionModel,
    RefundTransactionModel,
    DataVaultSaleTransactionModel,
    VerifyTransactionModel,
)


def test_clean_amount():
    assert clean_amount("10.50") == 1050
    assert clean_amount("0.01") == 1
    assert clean_amount("100") == 10000


def test_azul_base_model():
    data = {"Channel": "EC", "Store": "123456"}
    validated_data = AzulBaseModel(**data).model_dump()
    assert validated_data == data

    with pytest.raises(ValidationError):
        AzulBaseModel(Channel="EC").model_dump()


def test_transaction_with_amount_model():
    # Test with Itbis
    data = {"Channel": "EC", "Store": "123456", "Amount": "10.50", "Itbis": "1.05"}
    validated_data = TransactionWithAmountModel(**data).model_dump()
    assert validated_data["Amount"] == "1050"
    assert validated_data["Itbis"] == "105"

    # Test without Itbis
    data_without_itbis = {"Channel": "EC", "Store": "123456", "Amount": "10.50"}
    validated_data = TransactionWithAmountModel(**data_without_itbis).model_dump()
    assert validated_data["Amount"] == "1050"
    assert "Itbis" not in validated_data

    # Test with Itbis set to None
    data_with_none_itbis = {
        "Channel": "EC",
        "Store": "123456",
        "Amount": "10.50",
        "Itbis": None,
    }
    validated_data = TransactionWithAmountModel(**data_with_none_itbis).model_dump()
    assert validated_data["Amount"] == "1050"
    assert "Itbis" not in validated_data

    # Test with Itbis set to "0"
    data_with_zero_itbis = {
        "Channel": "EC",
        "Store": "123456",
        "Amount": "10.50",
        "Itbis": "0",
    }
    validated_data = TransactionWithAmountModel(**data_with_zero_itbis).model_dump()
    assert validated_data["Amount"] == "1050"
    assert "Itbis" not in validated_data


def test_sale_transaction_model():
    data = {
        "Channel": "EC",
        "Store": "123456",
        "Amount": "10.50",
        "CurrencyPosCode": "$",
        "CustomerServicePhone": "1234567890",
        "OrderNumber": "ORDER123",
        "EcommerceURL": "https://example.com",
        "CustomOrderID": "CUSTOM123",
    }
    validated_data = SaleTransactionModel(**data).model_dump()
    assert validated_data["Amount"] == "1050"
    assert validated_data["TrxType"] == "Sale"
    assert validated_data["PosInputMode"] == "E-Commerce"


def test_void_transaction_model():
    data = {"Channel": "EC", "Store": "123456", "AzulOrderId": "12345"}
    validated_data = VoidTransactionModel(**data).model_dump()
    assert validated_data["AzulOrderId"] == "12345"


def test_data_vault_create_model():
    data = {
        "Channel": "EC",
        "Store": "123456",
        "CardNumber": "4111111111111111",
        "Expiration": "1225",
        "CVC": "123",
    }
    validated_data = DataVaultCreateModel(**data).model_dump()
    assert validated_data["TrxType"] == "CREATE"


def test_data_vault_delete_model():
    data = {"Channel": "EC", "Store": "123456", "DataVaultToken": "TOKEN123"}
    validated_data = DataVaultDeleteModel(**data).model_dump()
    assert validated_data["TrxType"] == "DELETE"


def test_hold_transaction_model():
    data = {
        "Channel": "EC",
        "Store": "123456",
        "Amount": "10.50",
        "CurrencyPosCode": "$",
        "OrderNumber": "ORDER123",
    }
    validated_data = HoldTransactionModel(**data).model_dump()
    assert validated_data["Amount"] == "1050"
    assert validated_data["TrxType"] == "Hold"


def test_post_sale_transaction_model():
    data = {
        "Channel": "EC",
        "Store": "123456",
        "Amount": "10.50",
        "AzulOrderId": "12345",
    }
    validated_data = PostSaleTransactionModel(**data).model_dump()
    assert validated_data["Amount"] == "1050"
    assert validated_data["AzulOrderId"] == "12345"


def test_refund_transaction_model():
    data = {
        "Channel": "EC",
        "Store": "123456",
        "Amount": "10.50",
        "CurrencyPosCode": "$",
        "CustomerServicePhone": "1234567890",
        "OrderNumber": "ORDER123",
        "EcommerceURL": "https://example.com",
        "CustomOrderID": "CUSTOM123",
        "OriginalDate": "2023-05-01",
        "OriginalTrxTicketNr": "TICKET123",
        "AzulOrderId": "12345",
    }
    validated_data = RefundTransactionModel(**data).model_dump()
    assert validated_data["Amount"] == "1050"
    assert validated_data["TrxType"] == "Refund"


def test_data_vault_sale_transaction_model():
    data = {
        "Channel": "EC",
        "Store": "123456",
        "Amount": "10.50",
        "CurrencyPosCode": "$",
        "OrderNumber": "ORDER123",
        "DataVaultToken": "TOKEN123",
    }
    validated_data = DataVaultSaleTransactionModel(**data).model_dump()
    assert validated_data["Amount"] == "1050"
    assert validated_data["TrxType"] == "Sale"
    assert validated_data["DataVaultToken"] == "TOKEN123"


def test_verify_transaction_model():
    data = {"Channel": "EC", "Store": "123456", "CustomOrderId": "CUSTOM123"}
    validated_data = VerifyTransactionModel(**data).model_dump()
    assert validated_data["CustomOrderId"] == "CUSTOM123"


def test_invalid_data():
    with pytest.raises(ValidationError):
        SaleTransactionModel(Channel="EC", Store="123456").model_dump()

    with pytest.raises(ValidationError):
        TransactionWithAmountModel(
            Channel="EC", Store="123456", Amount="invalid"
        ).model_dump()
