"""Integration tests for hold operations."""

import json
from typing import Literal

import pytest

from pyazul import PyAzul
from pyazul.core.config import AzulSettings
from pyazul.models.datavault import TokenRequest, TokenSuccess
from pyazul.models.payment import Hold
from pyazul.models.three_ds import (
    CardHolderInfo,
    ChallengeIndicator,
    SecureTokenHold,
    ThreeDSAuth,
)
from tests.fixtures.cards import get_card
from tests.fixtures.order import generate_order_number


@pytest.fixture
def hold_transaction_data(settings):
    """
    Provide test data for a hold transaction.

    Includes card details, amount, and other necessary fields for creating
    a hold (pre-authorization) on a card.
    """
    card = get_card("MASTERCARD_2")  # Using a standard card
    return {
        "Store": settings.MERCHANT_ID,
        "OrderNumber": generate_order_number(),
        "CustomOrderId": f"hold-test-{generate_order_number()}",
        "ForceNo3DS": "1",  # Test specific
        "Amount": "1000",
        "Itbis": "180",
        "CardNumber": card["number"],
        "Expiration": card["expiration"],
        "CVC": card["cvv"],
    }


@pytest.mark.asyncio
async def test_hold_transaction(transaction_service_integration, hold_transaction_data):
    """
    Test creating a hold transaction.

    Verifies that a hold can be successfully placed on a card,
    resulting in an IsoCode of '00' (success).
    """
    payment = Hold(**hold_transaction_data)
    response = await transaction_service_integration.process_hold(payment)

    print("Hold Response:", response)

    # Verify the hold was successful
    assert response.get("IsoCode") == "00", "Hold transaction should be approved"

    # Verify we got required reference numbers
    assert response.get("AuthorizationCode"), "Should receive authorization code"
    assert response.get("RRN"), "Should receive reference number"


# Helper function for secure token hold tests
def _prepare_secure_token_hold_request_data(
    settings: AzulSettings,
    data_vault_token: str,
    order_num: str,
    card_holder_info: CardHolderInfo,
    challenge_indicator: ChallengeIndicator,
    custom_order_id_prefix: str,
    base_method_url: str,
    base_term_url: str,
    amount_value: int = 1000,
    itbis_value: int = 180,
    force_no_3ds_flag: Literal["0", "1"] = "0",
) -> SecureTokenHold:
    """Create and populate SecureTokenHold."""
    merchant_id = settings.MERCHANT_ID
    if merchant_id is None:
        raise ValueError(
            "MERCHANT_ID in settings cannot be None for secure token hold tests."
        )

    return SecureTokenHold(
        Store=merchant_id,
        OrderNumber=order_num,
        CustomOrderId=f"{custom_order_id_prefix}-{order_num}",
        Amount=str(amount_value),
        Itbis=str(itbis_value),
        DataVaultToken=data_vault_token,
        CardHolderInfo=card_holder_info,
        ThreeDSAuth=ThreeDSAuth(
            MethodNotificationUrl=base_method_url,
            TermUrl=base_term_url,
            RequestChallengeIndicator=challenge_indicator,
        ),
        ForceNo3DS=force_no_3ds_flag,
    )


@pytest.fixture
def card_holder_info_fixture() -> CardHolderInfo:
    """Provide a standard CardHolderInfo object for 3DS tests."""
    return CardHolderInfo(
        Email="test@example.com",
        Name="Test Cardholder",
    )


@pytest.fixture
def azul_fixture(settings) -> PyAzul:
    """Provide a PyAzul instance for testing."""
    azul_client = PyAzul(settings=settings)
    return azul_client


@pytest.fixture
async def created_token_fixture(azul_fixture: PyAzul, settings) -> str:
    """Create a DataVault token for testing token holds."""
    card = get_card("MASTERCARD_1")
    token_request = TokenRequest(
        CardNumber=card["number"],
        Expiration=card["expiration"],
        Store=settings.MERCHANT_ID,
        TrxType="CREATE",
    )

    token_response = await azul_fixture.create_token(token_request.model_dump())

    if isinstance(token_response, TokenSuccess):
        return token_response.DataVaultToken
    else:
        pytest.fail(f"Failed to create token: {token_response}")


@pytest.mark.asyncio
async def test_secure_token_hold_frictionless_with_3ds_method(
    azul_fixture: PyAzul,
    card_holder_info_fixture: CardHolderInfo,
    created_token_fixture: str,
    settings,
):
    """Test a frictionless 3DS token hold that involves a 3DS Method."""
    azul = azul_fixture
    order_num = generate_order_number()
    base_dummy_url = "http://localhost:8000/dummy"

    initial_request_data = _prepare_secure_token_hold_request_data(
        settings=settings,
        data_vault_token=created_token_fixture,
        order_num=order_num,
        card_holder_info=card_holder_info_fixture,
        challenge_indicator=ChallengeIndicator.NO_CHALLENGE,
        custom_order_id_prefix="3ds-token-hold-frictionless-method",
        base_method_url=f"{base_dummy_url}/method",
        base_term_url=f"{base_dummy_url}/term",
        force_no_3ds_flag="0",
    )

    initial_response_dict = await azul.secure_token_hold(
        initial_request_data.model_dump(exclude_none=True)
    )
    assert initial_response_dict is not None

    if (
        initial_response_dict.get("redirect")
        and initial_response_dict.get("html")
        and initial_response_dict.get("id")
    ):
        secure_id = initial_response_dict["id"]
        print(f"Initial 3DS Token Hold requires redirect. ID: {secure_id}")

        session_data = await azul.get_session_info(secure_id)
        assert session_data is not None
        azul_order_id_from_session = session_data.get("azul_order_id")
        assert azul_order_id_from_session is not None

        stored_term_url = session_data.get("term_url")
        assert stored_term_url is not None
        assert f"secure_id={secure_id}" in stored_term_url

        method_response = await azul.process_3ds_method(
            azul_order_id=azul_order_id_from_session,
            method_notification_status="RECEIVED",
        )
        assert method_response is not None

        if isinstance(method_response, dict) and method_response.get("IsoCode") == "00":
            print("Token hold approved after 3DS Method (frictionless).")
            assert method_response.get("ResponseMessage") == "APROBADA"
            print(f"Hold successful: {method_response}")
        else:
            if isinstance(method_response, dict):
                response_dump = json.dumps(method_response, indent=2)
            else:
                response_dump = str(method_response)
            pytest.fail(
                f"Expected direct approval for token hold, but got: {response_dump}"
            )
    elif (
        initial_response_dict.get("value")
        and isinstance(initial_response_dict["value"], dict)
        and initial_response_dict["value"].get("IsoCode") == "00"
    ):
        print("Token hold approved directly (frictionless, no method redirect).")
        assert initial_response_dict["value"].get("ResponseMessage") == "APROBADA"
    elif initial_response_dict.get("IsoCode") == "00":
        print("Token hold approved directly (frictionless, no redirect).")
        assert initial_response_dict.get("ResponseMessage") == "APROBADA"
    else:
        response_dump = str(initial_response_dict)
        pytest.fail(
            f"Expected 3DS Method redirect or direct approval. Got: {response_dump}"
        )


@pytest.mark.asyncio
async def test_secure_token_hold_complete_workflow(
    azul_fixture: PyAzul,
    card_holder_info_fixture: CardHolderInfo,
    created_token_fixture: str,
    settings,
):
    """Test complete secure token hold workflow."""
    azul = azul_fixture
    order_num = generate_order_number()
    base_dummy_url = "http://localhost:8000/dummy"

    initial_request_data = _prepare_secure_token_hold_request_data(
        settings=settings,
        data_vault_token=created_token_fixture,
        order_num=order_num,
        card_holder_info=card_holder_info_fixture,
        challenge_indicator=ChallengeIndicator.CHALLENGE,
        custom_order_id_prefix="3ds-token-hold-complete",
        base_method_url=f"{base_dummy_url}/method",
        base_term_url=f"{base_dummy_url}/term",
        force_no_3ds_flag="0",
    )

    # Step 1: Initial secure token hold
    initial_response_dict = await azul.secure_token_hold(
        initial_request_data.model_dump(exclude_none=True)
    )

    assert initial_response_dict is not None

    # Validate the complete workflow structure
    if initial_response_dict.get("redirect"):
        secure_id = initial_response_dict["id"]
        print(f"Token hold initiated with 3DS flow. Secure ID: {secure_id}")

        # Validate session data
        session_data = await azul.get_session_info(secure_id)
        assert session_data is not None
        assert session_data.get("azul_order_id")
        print(
            f"Session data stored for token hold: {session_data.get('azul_order_id')}"
        )

    elif initial_response_dict.get("IsoCode") == "00":
        print("Token hold completed with direct approval (frictionless)")
        assert initial_response_dict.get("ResponseMessage") == "APROBADA"

    else:
        # For any other response, log it for debugging
        print(f"Token hold response: {initial_response_dict}")

    print("Secure token hold workflow completed successfully")
