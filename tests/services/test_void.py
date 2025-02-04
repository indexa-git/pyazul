import pytest
from pyazul.models.schemas import VoidTransactionModel
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
    Test the void transaction method.
    """
    transaction = VoidTransactionModel(AzulOrderId='44474225', store=transaction_service.settings.AZUL_MERCHANT_ID)
    result = await transaction_service.void(transaction)
    assert result is not None
    assert result['IsoCode'] == '00', "Transaction should be voided successfully"