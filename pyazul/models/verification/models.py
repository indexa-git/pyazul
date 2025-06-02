"""
Transaction verification models for PyAzul.

This module defines Pydantic models for verifying existing transactions,
typically used to check payment status or retrieve transaction details.
"""

from pydantic import Field

from ..schemas import AzulBase


class VerifyTransaction(AzulBase):
    """Model for verifying existing transactions using CustomOrderId (VerifyPayment)."""

    CustomOrderId: str = Field(
        ..., description="CustomOrderId of the original transaction to verify. (X(75))"
    )
