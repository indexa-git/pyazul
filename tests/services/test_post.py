import pytest
from pyazul.models.schemas import PostSaleTransactionModel, HoldTransactionModel
from pyazul.services.transaction import TransactionService
from pyazul.core.config import get_azul_settings

@pytest.fixture
def transaction_service():
    """
    Fixture that provides a configured TransactionService instance.
    """
    settings = get_azul_settings()
    return TransactionService(settings)

@pytest.mark.asyncio
async def test_post_sale_transaction(transaction_service):
    """
    Test the post sale transaction method.
    """
    # Step 1: Create a hold transaction
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

    # Step 2: Use the AzulOrderId from hold for the post transaction
    post_transaction = PostSaleTransactionModel(
        AzulOrderId=azul_order_id,
        ApprovedUrl='https://example.com/approved',
        DeclinedUrl='https://example.com/declined',
        CancelUrl='https://example.com/cancelled',
        UseCustomField1='0',
        CardNumber='5413330089600119',
        Expiration='202812',
        CVC='979',
        Amount='1000',
        Itbis='100',
    )
    post_result = await transaction_service.post_sale(post_transaction)
    print(post_result)
    assert post_result['IsoCode'] == '00', "Post transaction should be processed successfully"