import asyncio
from pyazul.models.schemas import PostSaleTransactionModel, HoldTransactionModel
from pyazul.services.transaction import TransactionService
from pyazul.core.config import get_azul_settings

async def main():
    settings = get_azul_settings()
    transaction_service = TransactionService(settings)

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
    print("Hold Result:", hold_result)
    if hold_result['IsoCode'] != '00':
        print("Hold transaction failed")
        return
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
    print("Post Result:", post_result)
    if post_result['IsoCode'] == '00':
        print("Post transaction processed successfully")
    else:
        print("Post transaction failed")

if __name__ == "__main__":
    asyncio.run(main()) 