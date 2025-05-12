from typing import Dict,Any,Optional
from .core.config import get_azul_settings, AzulSettings
from .api.client import AzulAPI
from .services.datavault import DataVaultService
from .services.transaction import TransactionService
from .services.payment_page import PaymentPageService
from .models.schemas import (
    SaleTransactionModel,
    HoldTransactionModel,
    DataVaultCreateModel,
    DataVaultDeleteModel,
    TokenSaleModel,
    VerifyTransactionModel,
    VoidTransactionModel,
    PaymentPageModel,
    RefundTransactionModel,
    PostSaleTransactionModel
)
from .services.secure import SecureService
from .models.secure import SecureSaleRequest,SecureTokenSale

class PyAzul:
    """
    Main client for integration with Azul Payment Gateway.
    
    This class provides centralized access to all Azul services:
    - Direct payment processing
    - Card tokenization (DataVault)
    - Payment page
    - Transaction verification
    - Refunds and voids
    - Hold/capture transactions
    - 3D Secure
    - Payment Page
    """
    
    def __init__(self, settings: Optional[AzulSettings] = None, api_client: Optional[AzulAPI] = None):
        """
        Initializes the PyAzul client.
        
        Args:
            settings: Optional custom configuration. If not provided,
                     environment variables will be used.
        """
        if settings is None:
            settings = get_azul_settings()
        if api_client is None:
            api_client = AzulAPI()

        self.api_client = api_client
        self.settings = settings
        
        # Initialize services
        self.transaction = TransactionService(settings)
        self.datavault = DataVaultService(settings)
        self.payment_page = PaymentPageService(settings)
        self.secure = SecureService(api_client)
    
    async def sale(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Processes a direct card payment."""
        return await self.transaction.sale(SaleTransactionModel(**data))
    
    async def hold(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Performs a hold on a card (pre-authorization)."""
        return await self.transaction.hold(HoldTransactionModel(**data))
    
    async def refund(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Processes a refund of a previous transaction."""
        return await self.transaction.refund(RefundTransactionModel(**data))
    
    async def void(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Voids (cancels) a transaction."""
        return await self.transaction.void(VoidTransactionModel(**data))
    
    async def post_sale(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Completes a previously held transaction."""
        return await self.transaction.post_sale(PostSaleTransactionModel(**data))
    
    async def verify(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Verifies the status of a transaction."""
        return await self.transaction.verify(VerifyTransactionModel(**data))
    
    async def create_token(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Creates a card token in DataVault."""
        return await self.datavault.create(DataVaultCreateModel(**data))
    
    async def delete_token(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Deletes a token from DataVault."""
        return await self.datavault.delete(DataVaultDeleteModel(**data))
    
    async def token_sale(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Processes a payment using a DataVault token."""
        return await self.transaction.sale(TokenSaleModel(**data))
    
    def create_payment_page(self, data: Dict[str, Any]) -> PaymentPageModel:
        """
        Creates an Azul payment page.
        
        Returns:
            PaymentPageModel: Model with all the necessary data to
                            render the payment page.
        """
        return self.payment_page.create_payment_form(PaymentPageModel(**data))
    async def secure_sale(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Processes a transaction with 3D Secure."""
        return await self.secure.process_sale(SecureSaleRequest(**data))
    
    async def secure_hold(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Processes a hold with 3D Secure."""
        return await self.secure.process_hold(SecureSaleRequest(**data))
    
    async def secure_3ds_method(self, secure_id: str, method: str) -> Dict[str, Any]:
        """Processes a 3D Secure method."""
        return await self.secure.process_3ds_method(secure_id, method)
    
    async def secure_challenge(self, secure_id: str, cres: str) -> Dict[str, Any]:
        """Processes a 3D Secure challenge."""
        return await self.secure.process_challenge(secure_id, cres)
    
    def create_challenge_form(self, creq: str, term_url: str, redirect_post_url: str) -> str:
        """Creates a 3D Secure challenge form."""
        return self.secure._create_challenge_form(creq, term_url, redirect_post_url)
    
    async def secure_token_sale(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Processes a transaction with 3D Secure using a DataVault token."""
        return await self.secure.process_sale(SecureTokenSale(**data))
