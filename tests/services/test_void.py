import pytest
from pyazul.models.schemas import VoidTransactionModel, HoldTransactionModel
from pyazul.services.transaction import TransactionService
from pyazul.core.config import get_azul_settings

@pytest.fixture
def transaction_service():
    """
    Fixture that provides a configured TransactionService instance.
    Used for processing hold/authorization transactions.
    """
    settings = get_azul_settings()
    return TransactionService(settings)



@pytest.mark.asyncio
async def test_void_transaction(transaction_service):

    """
    Test the hold transaction method.
    """
    hold_transaction = HoldTransactionModel(
        CardNumber='5413330089600119',
        Expiration='202812',
        CVC='979',
        Amount='1000',
        Itbis='100',
        TrxType='Hold',
        CustomOrderId='hold_test_to_post'
    )
    hold_result = await transaction_service.hold(hold_transaction)
    assert hold_result['IsoCode'] == '00', "Hold transaction should be successful"
    azul_order_id = hold_result['AzulOrderId']
    """
    Test the void transaction method.
    """
    transaction = VoidTransactionModel(AzulOrderId=azul_order_id, store=transaction_service.settings.AZUL_MERCHANT_ID)
    result = await transaction_service.void(transaction)
    assert result is not None
    assert result['IsoCode'] == '00', "Transaction should be voided successfully"