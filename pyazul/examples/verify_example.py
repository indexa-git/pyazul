import asyncio
from pyazul.models.schemas import VerifyTransactionModel
from pyazul.services.transaction import TransactionService
from pyazul.core.config import get_azul_settings

async def main():
    settings = get_azul_settings()
    transaction_service = TransactionService(settings)

    # Create a verify transaction
    verify_transaction = VerifyTransactionModel(
        CustomOrderId='sale-test-001'
    )
    verify_result = await transaction_service.verify(verify_transaction)
    print("Verify Result:", verify_result)
    if verify_result['IsoCode'] == '00':
        print("Transaction verified successfully")
    else:
        print("Transaction verification failed")

if __name__ == "__main__":
    asyncio.run(main()) 