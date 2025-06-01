"""Test card definitions and utilities for PyAzul tests."""

import random
from typing import List, Literal, Optional, TypedDict, cast


class CardDetails(TypedDict):
    """Type definition for a test card's details."""

    number: str
    expiration: str
    cvv: str
    max_amount: Optional[int]
    description: Optional[str]  # Added for clarity


# Test card data based on Azul documentation and common test card knowledge
TEST_CARDS = {
    "MASTERCARD_1": CardDetails(
        number="5424180279791732",
        expiration="202812",
        cvv="732",
        max_amount=None,
        description="Standard MasterCard test card",
    ),
    "DISCOVER": CardDetails(
        number="6011000990099818",
        expiration="202812",
        cvv="818",
        max_amount=None,
        description="Standard Discover test card",
    ),
    "VISA_1": CardDetails(
        number="4260550061845872",
        expiration="202812",
        cvv="872",
        max_amount=None,
        description="Standard Visa test card",
    ),
    "VISA_LIMITED": CardDetails(
        number="4005520000000129",
        expiration="202812",
        cvv="977",
        max_amount=75,
        description="Limited amount Visa test card (Max: RD$ 75)",
    ),
    "MASTERCARD_2": CardDetails(
        number="5413330089600119",
        expiration="202812",
        cvv="979",
        max_amount=None,
        description="Standard MasterCard test card",
    ),
    "VISA_2": CardDetails(
        number="4012000033330026",
        expiration="202812",
        cvv="123",
        max_amount=None,
        description="Standard Visa test card",
    ),
    "VISA_TEST_CARD": CardDetails(
        number="4012000033330026",
        expiration="202812",
        cvv="123",
        max_amount=None,
        description="Standard Visa test card (duplicate for naming consistency)",
    ),
    "SECURE_3DS_FRICTIONLESS_WITH_3DS": CardDetails(
        number="4265880000000007",
        expiration="202812",
        cvv="123",
        max_amount=None,
        description="3DS test card - Frictionless with 3DS Method",
    ),
    "SECURE_3DS_FRICTIONLESS_NO_3DS": CardDetails(
        number="4147463011110117",
        expiration="202812",
        cvv="123",
        max_amount=None,
        description="3DS test card - Frictionless without 3DS Method",
    ),
    "SECURE_3DS_CHALLENGE_WITH_3DS": CardDetails(
        number="4005520000000129",  # Same as VISA_LIMITED number
        expiration="202812",
        cvv="123",  # Note: CVV differs from VISA_LIMITED (977)
        max_amount=50,
        description="3DS test card - Challenge with 3DS Method (Max: RD$ 50)",
    ),
    "SECURE_3DS_CHALLENGE_NO_3DS": CardDetails(
        number="4147463011110059",
        expiration="202812",
        cvv="123",
        max_amount=None,
        description="3DS test card - Challenge without 3DS Method",
    ),
}

TestCardKey = Literal[
    "MASTERCARD_1",
    "DISCOVER",
    "VISA_1",
    "VISA_LIMITED",
    "MASTERCARD_2",
    "VISA_2",
    "VISA_TEST_CARD",
    "SECURE_3DS_FRICTIONLESS_WITH_3DS",
    "SECURE_3DS_FRICTIONLESS_NO_3DS",
    "SECURE_3DS_CHALLENGE_WITH_3DS",
    "SECURE_3DS_CHALLENGE_NO_3DS",
]


def get_card(key: TestCardKey) -> CardDetails:
    """
    Get a test card by key.

    Args:
        key: Key of the test card to get.

    Returns:
        The requested test card.
    """
    return TEST_CARDS[key]


def get_random_card(exclude_cards: Optional[List[TestCardKey]] = None) -> CardDetails:
    """
    Get a random test card.

    Args:
        exclude_cards: Card keys to exclude from selection.

    Returns:
        A random test card.
    """
    if exclude_cards is None:
        exclude_cards = []

    available_keys = [key for key in TEST_CARDS.keys() if key not in exclude_cards]
    if not available_keys:
        raise ValueError("No cards available after exclusion.")

    random_key = random.choice(available_keys)
    return TEST_CARDS[cast(TestCardKey, random_key)]
