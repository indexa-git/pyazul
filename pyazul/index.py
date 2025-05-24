from typing import Any, Dict, Optional

from .api.client import AzulAPI
from .core.config import AzulSettings, get_azul_settings
from .models import (
    DataVaultCreateModel,
    DataVaultDeleteModel,
    HoldTransactionModel,
    PaymentPageModel,
    PostSaleTransactionModel,
    RefundTransactionModel,
    SaleTransactionModel,
    SecureSaleRequest,
    SecureTokenSale,
    TokenSaleModel,
    VerifyTransactionModel,
    VoidTransactionModel,
)
from .services.datavault import DataVaultService
from .services.payment_page import PaymentPageService
from .services.secure import SecureService
from .services.transaction import TransactionService


class PyAzul:
    """
    Cliente principal para la integración con Azul Payment Gateway.

    Esta clase proporciona acceso centralizado a todos los servicios de Azul:
    - Procesamiento de pagos directos y 3D Secure
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

    def __init__(
        self,
        settings: Optional[AzulSettings] = None,
    ):
        """
        Inicializa el cliente PyAzul.

        Args:
            settings: Configuración personalizada opcional. Si no se proporciona,
                     se utilizarán las variables de entorno.
        """
        if settings is None:
            settings = get_azul_settings()
        self.settings = settings

        # Crear cliente API compartido
        self.api = AzulAPI(settings=self.settings)

        # Inicializar servicios con el cliente API, configuraciones y session_store
        self.transaction = TransactionService(
            settings=self.settings, api_client=self.api
        )
        self.datavault = DataVaultService(settings=self.settings, api_client=self.api)
        self.payment_page = PaymentPageService(settings=self.settings)
        self.secure = SecureService(api_client=self.api)

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

    def create_payment_page(self, data: Dict[str, Any]) -> str:
        """
        Crea el HTML del formulario para la página de pago de Azul.

        Returns:
            str: HTML del formulario listo para ser renderizado y auto-enviado.
        """
        return self.payment_page.create_payment_form(PaymentPageModel(**data))

    # --- Métodos Seguros (3D Secure) ---

    async def secure_sale(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Procesa un pago con tarjeta utilizando autenticación 3D Secure."""
        return await self.secure.process_sale(SecureSaleRequest(**data))

    async def secure_token_sale(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Procesa un pago con token utilizando autenticación 3D Secure."""
        return await self.secure.process_token_sale(SecureTokenSale(**data))

    async def secure_hold(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Realiza una retención en una tarjeta (pre-autorización) con 3D Secure."""
        # SecureService process_hold expects SecureSaleRequest model
        return await self.secure.process_hold(SecureSaleRequest(**data))

    async def secure_3ds_method(
        self, azul_order_id: str, method_notification_status: str
    ) -> Dict[str, Any]:
        """Procesa la notificación del método 3D Secure."""
        return await self.secure.process_3ds_method(
            azul_order_id, method_notification_status
        )

    async def secure_challenge(self, secure_id: str, cres: str) -> Dict[str, Any]:
        """Procesa el resultado del desafío 3D Secure."""
        return await self.secure.process_challenge(secure_id, cres)

    def create_challenge_form(
        self, creq: str, term_url: str, redirect_post_url: str
    ) -> str:
        """
        Crea el HTML del formulario para el desafío 3DS.
        Este es un método de conveniencia que llama al método estático en SecureService.
        """
        return SecureService._create_challenge_form(creq, term_url, redirect_post_url)
