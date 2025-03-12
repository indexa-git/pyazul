from typing import Dict,Any,Optional
from .core.config import get_azul_settings, AzulSettings
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


class PyAzul:
    """
    Cliente principal para la integración con Azul Payment Gateway.
    
    Esta clase proporciona acceso centralizado a todos los servicios de Azul:
    - Procesamiento de pagos directos
    - Tokenización de tarjetas (DataVault)
    - Página de pago
    - Verificación de transacciones
    - Reembolsos y anulaciones
    - Retención/captura de transacciones
    
    Example:
        >>> from pyazul import PyAzul
        >>> azul = PyAzul()  # Usa variables de entorno para la configuración
        >>> 
        >>> # Procesar un pago
        >>> response = await azul.transaction.sale({
        ...     "Channel": "EC",
        ...     "Store": "39038540035",
        ...     "CardNumber": "4111111111111111",
        ...     "Expiration": "202812",
        ...     "CVC": "123",
        ...     "Amount": "100000"  # $1,000.00
        ... })
        >>>
        >>> # Tokenizar una tarjeta
        >>> token_response = await azul.datavault.create({
        ...     "CardNumber": "4111111111111111",
        ...     "Expiration": "202812",
        ...     "store": "39038540035"
        ... })
    """
    
    def __init__(self, settings: Optional[AzulSettings] = None):
        """
        Inicializa el cliente PyAzul.
        
        Args:
            settings: Configuración personalizada opcional. Si no se proporciona,
                     se utilizarán las variables de entorno.
        """
        if settings is None:
            settings = get_azul_settings()
            
        self.settings = settings
        
        # Inicializar servicios
        self.transaction = TransactionService(settings)
        self.datavault = DataVaultService(settings)
        self.payment_page = PaymentPageService(settings)
    
    async def sale(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Procesa un pago directo con tarjeta."""
        return await self.transaction.sale(SaleTransactionModel(**data))
    
    async def hold(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Realiza una retención en una tarjeta (pre-autorización)."""
        return await self.transaction.hold(HoldTransactionModel(**data))
    
    async def refund(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Procesa un reembolso de una transacción anterior."""
        return await self.transaction.refund(RefundTransactionModel(**data))
    
    async def void(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Anula (cancela) una transacción."""
        return await self.transaction.void(VoidTransactionModel(**data))
    
    async def post_sale(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Completa una transacción previamente retenida."""
        return await self.transaction.post_sale(PostSaleTransactionModel(**data))
    
    async def verify(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Verifica el estado de una transacción."""
        return await self.transaction.verify(VerifyTransactionModel(**data))
    
    async def create_token(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Crea un token de tarjeta en DataVault."""
        return await self.datavault.create(DataVaultCreateModel(**data))
    
    async def delete_token(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Elimina un token de DataVault."""
        return await self.datavault.delete(DataVaultDeleteModel(**data))
    
    async def token_sale(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Procesa un pago usando un token de DataVault."""
        return await self.transaction.sale(TokenSaleModel(**data))
    
    def create_payment_page(self, data: Dict[str, Any]) -> PaymentPageModel:
        """
        Crea una página de pago de Azul.
        
        Returns:
            PaymentPageModel: Modelo con todos los datos necesarios para
                            renderizar la página de pago.
        """
        return self.payment_page.create_payment_form(PaymentPageModel(**data))
    
