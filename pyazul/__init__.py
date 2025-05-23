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
from .models.schemas import (
    DataVaultCreateModel,
    DataVaultDeleteModel,
    HoldTransactionModel,
    PaymentPageModel,
    PostSaleTransactionModel,
    RefundTransactionModel,
    SaleTransactionModel,
    TokenSaleModel,
    VerifyTransactionModel,
    VoidTransactionModel,
)
from .services.datavault import DataVaultService
from .services.payment_page import PaymentPageService
from .services.transaction import TransactionService

__all__ = [
    # Clase principal
    "PyAzul",
    # Configuración
    "get_azul_settings",
    "AzulSettings",
    "AzulError",
    # Servicios
    "DataVaultService",
    "TransactionService",
    "PaymentPageService",
    # Modelos
    "SaleTransactionModel",
    "HoldTransactionModel",
    "DataVaultCreateModel",
    "DataVaultDeleteModel",
    "TokenSaleModel",
    "VerifyTransactionModel",
    "VoidTransactionModel",
    "PaymentPageModel",
    "RefundTransactionModel",
    "PostSaleTransactionModel",
]

# Versión del paquete
__version__ = "0.4.4alpha"
