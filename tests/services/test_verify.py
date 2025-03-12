import pytest
from pyazul.models.schemas import VerifyTransactionModel
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
async def test_verify_transaction(transaction_service):
    """
    Test the verify transaction method.
    """
    transaction = VerifyTransactionModel(CustomOrderId='sale-test-001')
    result = await transaction_service.verify(transaction)  
    assert result is not None
    assert result['IsoCode'] == '00', "Transaction should be verified successfully"
    assert result['Found'], "Transaction should be found"
    return result