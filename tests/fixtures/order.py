"""Order number generation utility for PyAzul tests."""

import datetime
import random


def generate_order_number() -> str:
    """
    Generate a unique order number with a maximum length of 15 characters.

    The format is: YYMMDD (6 chars) + random numbers (9 chars) = 15 chars total.
    Example: 240318123456789.
    """
    now = datetime.datetime.now()
    date_str = now.strftime("%y%m%d")  # YYMMDD
    random_num_int = random.randint(0, 999999999)  # Generate a 9-digit number
    random_num_str = str(random_num_int).zfill(9)  # Pad with leading zeros
    return f"{date_str}{random_num_str}"
