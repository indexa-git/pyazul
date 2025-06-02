"""
Transaction processing services for PyAzul.

This module provides services for processing various types of payment transactions
including sales, holds, refunds, voids, and post-authorization captures.
"""

import logging
from typing import Any, Dict

from ..api.client import AzulAPI
from ..core.config import AzulSettings
from ..core.exceptions import AzulError
from ..models.datavault import TokenSale
from ..models.payment import Hold, Post, Refund, Sale, Void
from ..models.verification import VerifyTransaction

_logger = logging.getLogger(__name__)


class TransactionService:
    """Service for processing payment transactions with Azul."""

    def __init__(self, client: AzulAPI, settings: AzulSettings):
        """Initialize the transaction service with API client and settings."""
        self.client = client
        self.settings = settings

    async def process_sale(self, transaction: Sale) -> Dict[str, Any]:
        """
        Process a sale transaction.

        Args:
            transaction: Sale transaction model

        Returns:
            API response dict

        Raises:
            AzulError: If transaction processing fails
        """
        try:
            _logger.info("Processing sale transaction")
            response = await self.client.post(
                "/webservices/JSON/default.aspx",
                transaction.model_dump(exclude_none=True),
            )
            _logger.info("Sale transaction processed successfully")
            return response
        except Exception as e:
            _logger.error(f"Sale transaction failed: {e}")
            raise AzulError(f"Sale transaction failed: {e}") from e

    async def process_hold(self, transaction: Hold) -> Dict[str, Any]:
        """
        Process a hold (pre-authorization) transaction.

        Args:
            transaction: Hold transaction model

        Returns:
            API response dict

        Raises:
            AzulError: If transaction processing fails
        """
        try:
            _logger.info("Processing hold transaction")
            response = await self.client.post(
                "/webservices/JSON/default.aspx",
                transaction.model_dump(exclude_none=True),
            )
            _logger.info("Hold transaction processed successfully")
            return response
        except Exception as e:
            _logger.error(f"Hold transaction failed: {e}")
            raise AzulError(f"Hold transaction failed: {e}") from e

    async def process_refund(self, transaction: Refund) -> Dict[str, Any]:
        """
        Process a refund transaction.

        Args:
            transaction: Refund transaction model

        Returns:
            API response dict

        Raises:
            AzulError: If transaction processing fails
        """
        try:
            _logger.info("Processing refund transaction")
            response = await self.client.post(
                "/webservices/JSON/default.aspx",
                transaction.model_dump(exclude_none=True),
            )
            _logger.info("Refund transaction processed successfully")
            return response
        except Exception as e:
            _logger.error(f"Refund transaction failed: {e}")
            raise AzulError(f"Refund transaction failed: {e}") from e

    async def process_void(self, transaction: Void) -> Dict[str, Any]:
        """
        Process a void transaction.

        Args:
            transaction: Void transaction model

        Returns:
            API response dict

        Raises:
            AzulError: If transaction processing fails
        """
        try:
            _logger.info("Processing void transaction")
            response = await self.client.post(
                "/webservices/JSON/default.aspx?ProcessVoid",
                transaction.model_dump(exclude_none=True),
            )
            _logger.info("Void transaction processed successfully")
            return response
        except Exception as e:
            _logger.error(f"Void transaction failed: {e}")
            raise AzulError(f"Void transaction failed: {e}") from e

    async def process_post(self, transaction: Post) -> Dict[str, Any]:
        """
        Process a post-authorization (capture) transaction.

        Args:
            transaction: Post transaction model

        Returns:
            API response dict

        Raises:
            AzulError: If transaction processing fails
        """
        try:
            _logger.info("Processing post transaction")
            response = await self.client.post(
                "/webservices/JSON/default.aspx?ProcessPost",
                transaction.model_dump(exclude_none=True),
            )
            _logger.info("Post transaction processed successfully")
            return response
        except Exception as e:
            _logger.error(f"Post transaction failed: {e}")
            raise AzulError(f"Post transaction failed: {e}") from e

    async def process_token_sale(self, transaction: TokenSale) -> Dict[str, Any]:
        """
        Process a sale transaction using a DataVault token.

        Args:
            transaction: Token sale transaction model

        Returns:
            API response dict

        Raises:
            AzulError: If transaction processing fails
        """
        try:
            _logger.info("Processing token sale transaction")
            response = await self.client.post(
                "/webservices/JSON/default.aspx",
                transaction.model_dump(exclude_none=True),
            )
            _logger.info("Token sale transaction processed successfully")
            return response
        except Exception as e:
            _logger.error(f"Token sale transaction failed: {e}")
            raise AzulError(f"Token sale transaction failed: {e}") from e

    async def verify_payment(self, verification: VerifyTransaction) -> Dict[str, Any]:
        """
        Verify an existing payment transaction.

        Args:
            verification: Transaction verification model

        Returns:
            API response dict

        Raises:
            AzulError: If verification fails
        """
        try:
            _logger.info("Verifying payment transaction")
            response = await self.client.post(
                "/webservices/JSON/default.aspx?VerifyPayment",
                verification.model_dump(exclude_none=True),
            )
            _logger.info("Payment verification completed successfully")
            return response
        except Exception as e:
            _logger.error(f"Payment verification failed: {e}")
            raise AzulError(f"Payment verification failed: {e}") from e
