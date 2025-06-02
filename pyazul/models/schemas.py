"""
Core schemas and base models for PyAzul.

This module defines base classes and validation functions used across
all business domain models. Individual transaction models are organized
in their respective business domain modules.

For new code, import directly from business domains:
    from pyazul.models.payment import Sale
    from pyazul.models.datavault import TokenRequest
"""

from typing import Union

from pydantic import BaseModel, Field


# Helper validator functions
def _validate_amount_field(v: Union[str, int, float], info) -> str:
    """
    Validate and normalize amount fields to string representation in cents.

    Accepts int, float, or str input and ensures non-negative integer value.
    Converts float/int inputs to string format required by Azul API.

    Args:
        v: Input value (str, int, or float representing cents)
        info: Pydantic field info

    Returns:
        str: Validated amount as string of digits

    Raises:
        ValueError: If value is negative or not a valid number
    """
    if isinstance(v, float):  # Convert float to int (cents) then to str
        v = str(int(v))
    elif isinstance(v, int):
        v = str(v)

    if not v.isdigit():
        raise ValueError(
            f"{info.field_name} ('{v}') must be a string of digits representing cents."
        )

    numeric_val = int(v)
    if numeric_val < 0:
        raise ValueError(f"{info.field_name} ('{v}') must be non-negative.")

    return str(numeric_val)


def _validate_itbis_field(v: Union[str, int, float, None], info) -> str:
    """
    Validate and normalize ITBIS fields to string representation in cents.

    Accepts int, float, str, or None input. None values are converted to "0".
    Ensures non-negative integer value and converts to string format.

    Args:
        v: Input value (str, int, float, or None representing cents)
        info: Pydantic field info

    Returns:
        str: Validated ITBIS as string of digits

    Raises:
        ValueError: If value is negative or not a valid number
    """
    if v is None:
        return "0"

    if isinstance(v, float):  # Convert float to int (cents) then to str
        v = str(int(v))
    elif isinstance(v, int):
        v = str(v)

    if not v.isdigit():
        raise ValueError(
            f"{info.field_name} ('{v}') must be a string of digits representing cents."
        )

    numeric_val = int(v)
    if numeric_val < 0:
        raise ValueError(f"{info.field_name} ('{v}') must be non-negative.")

    return str(numeric_val)


class AzulBase(BaseModel):
    """Base model for Azul payment operations."""

    Channel: str = Field(
        default="EC", description="Payment channel. Defaults to 'EC'. (X(3))"
    )
    Store: str = Field(
        ..., description="Unique merchant ID (MID). Must be provided. (X(11))"
    )
