"""
Utility functions for the PyAzul library.

This module provides helper functions for common tasks such as amount formatting.
"""


def clean_amount(amount):
    """Convert an amount to cents as an integer."""
    amount = int(round(float(amount) * 100, 0))
    return amount


# This function makes sure to not add 'Itbis' in the dict, unless there's a value.
# Azul documentation doesn't specificy that it will fail if sent empty.
def update_itbis(data):
    """Update the 'Itbis' field in data if present, converting it to cents."""
    if itbis := data.get("Itbis"):
        temp = {
            "Itbis": clean_amount(itbis),
        }
        data.update(temp)
    return data


def format_amount_for_azul(amount: float) -> str:
    """Format a float amount to Azul's required string format (cents)."""
    # Multiply by 100 to convert to cents and remove decimals
    return str(int(amount * 100))


def parse_azul_amount(azul_amount: str) -> float:
    """Parse an amount string from Azul (cents) to a float."""
    # Convert string to integer, then divide by 100
    return float(azul_amount) / 100
