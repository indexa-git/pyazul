"""
PyAzul - Cliente Python para Azul Payment Gateway

Este paquete proporciona una interfaz completa para interactuar con los servicios de Azul:
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
    >>> response = await azul.sale({
    ...     "Channel": "EC",
    ...     "Store": "39038540035",
    ...     "CardNumber": "4111111111111111",
    ...     "Expiration": "202812",
    ...     "CVC": "123",
    ...     "Amount": "100000"  # $1,000.00
    ... })
"""

from .core.config import AzulSettings, get_azul_settings
from .core.exceptions import AzulError
from .index import PyAzul

# Import models from the centralized pyazul.models package
from .models import (
    AzulBaseModel,
    CardHolderInfo,
    ChallengeIndicator,
    DataVaultCreateModel,
    DataVaultDeleteModel,
    HoldTransactionModel,
    PaymentPageModel,
    PostSaleTransactionModel,
    RefundTransactionModel,
    SaleTransactionModel,
    SecureSaleRequest,  # Added Secure Models
    SecureTokenSale,  # Added Secure Models
    ThreeDSAuth,  # Added Secure Models
    TokenSaleModel,
    VerifyTransactionModel,
    VoidTransactionModel,
)

# Services - SecureService will be added when PyAzul is updated
from .services.datavault import DataVaultService
from .services.payment_page import PaymentPageService
from .services.transaction import TransactionService

# from .services.secure import SecureService # Will be exposed if needed, or via PyAzul

__all__ = [
    # Clase principal
    "PyAzul",
    # Configuración
    "get_azul_settings",
    "AzulSettings",
    "AzulError",
    # Servicios (Consider if all services need to be public if PyAzul is the main entry)
    "DataVaultService",
    "TransactionService",
    "PaymentPageService",
    # Modelos
    "AzulBaseModel",
    "SaleTransactionModel",
    "HoldTransactionModel",
    "RefundTransactionModel",
    "DataVaultCreateModel",
    "DataVaultDeleteModel",
    "TokenSaleModel",
    "PostSaleTransactionModel",
    "VerifyTransactionModel",
    "VoidTransactionModel",
    "PaymentPageModel",
    "SecureSaleRequest",
    "SecureTokenSale",
    "CardHolderInfo",
    "ThreeDSAuth",
    "ChallengeIndicator",
]
