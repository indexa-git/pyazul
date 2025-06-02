"""Integration tests for secure (3DS) operations."""

import json
from typing import Literal

import pytest

from pyazul import PyAzul
from pyazul.core.config import AzulSettings
from pyazul.models.three_ds import (
    CardHolderInfo,
    ChallengeIndicator,
    SecureSale,
    ThreeDSAuth,
)
from tests.fixtures.cards import CardDetails, get_card
from tests.fixtures.order import generate_order_number


# Helper function to prepare SecureSale data
def _prepare_secure_sale_request_data(
    settings: AzulSettings,
    card: CardDetails,
    order_num: str,
    card_holder_info: CardHolderInfo,
    challenge_indicator: ChallengeIndicator,
    custom_order_id_prefix: str,
    base_method_url: str,
    base_term_url: str,
    amount_value: int = 1000,
    itbis_value: int = 180,
    force_no_3ds_flag: Literal["0", "1"] = "0",
) -> SecureSale:
    """Create and populate SecureSale."""
    merchant_id = settings.MERCHANT_ID
    if merchant_id is None:
        raise ValueError(
            "MERCHANT_ID in settings cannot be None for secure sale tests."
        )

    return SecureSale(
        Store=merchant_id,
        OrderNumber=order_num,
        CustomOrderId=f"{custom_order_id_prefix}-{order_num}",
        Amount=str(amount_value),
        Itbis=str(itbis_value),
        CardNumber=card["number"],
        Expiration=card["expiration"],
        CVC=card["cvv"],
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
    """
    Provide a PyAzul instance.

    The PyAzul instance is initialized using the provided `settings`.
    It is assumed to use its default session management internally.
    """
    azul_client = PyAzul(settings=settings)
    return azul_client


@pytest.mark.asyncio
async def test_secure_sale_frictionless_with_3ds_method(
    azul_fixture: PyAzul,
    card_holder_info_fixture: CardHolderInfo,
    settings,
):
    """Test a frictionless 3DS sale that involves a 3DS Method Notification."""
    azul = azul_fixture
    card = get_card("SECURE_3DS_FRICTIONLESS_WITH_3DS")
    order_num = generate_order_number()
    base_dummy_url = "http://localhost:8000/dummy"

    initial_request_data = _prepare_secure_sale_request_data(
        settings=settings,
        card=card,
        order_num=order_num,
        card_holder_info=card_holder_info_fixture,
        challenge_indicator=ChallengeIndicator.NO_CHALLENGE,
        custom_order_id_prefix="3ds-frictionless-method",
        base_method_url=f"{base_dummy_url}/method",
        base_term_url=f"{base_dummy_url}/term",
        force_no_3ds_flag="0",
    )

    initial_response_dict = await azul.secure_sale(
        initial_request_data.model_dump(exclude_none=True)
    )
    assert initial_response_dict is not None

    if (
        initial_response_dict.get("redirect")
        and initial_response_dict.get("html")
        and initial_response_dict.get("id")
    ):
        secure_id = initial_response_dict["id"]
        print(f"Initial 3DS Sale requires redirect (3DS Method). ID: {secure_id}")

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
            print("Approved after 3DS Method (frictionless).")
            assert method_response.get("ResponseMessage") == "APROBADA"
        else:
            if isinstance(method_response, dict):
                response_dump = json.dumps(method_response, indent=2)
            else:
                response_dump = str(method_response)
            pytest.fail(
                f"After 3DS Method, expected direct approval, but got: {response_dump}"
            )
    elif (
        initial_response_dict.get("value")
        and isinstance(initial_response_dict["value"], dict)
        and initial_response_dict["value"].get("IsoCode") == "00"
    ):
        print("Approved directly from secure_sale (frictionless, no method redirect).")
        assert initial_response_dict["value"].get("ResponseMessage") == "APROBADA"
    elif initial_response_dict.get("IsoCode") == "00":
        print("Approved directly (frictionless, no method redirect - top level dict).")
        assert initial_response_dict.get("ResponseMessage") == "APROBADA"
    else:
        response_dump = str(initial_response_dict)
        pytest.fail(
            "Unexpected initial response. Expected 3DS Method redirect or "
            f"direct frictionless approval. Got: {response_dump}"
        )


@pytest.mark.asyncio
async def test_secure_sale_frictionless_direct_approval(
    azul_fixture: PyAzul,
    card_holder_info_fixture: CardHolderInfo,
    settings,
):
    """Test a frictionless 3DS sale, approved directly without a 3DS Method step."""
    azul = azul_fixture
    card = get_card("SECURE_3DS_FRICTIONLESS_NO_3DS")
    order_num = generate_order_number()
    base_dummy_url = "http://localhost:8000/dummy"

    initial_request_data = _prepare_secure_sale_request_data(
        settings=settings,
        card=card,
        order_num=order_num,
        card_holder_info=card_holder_info_fixture,
        challenge_indicator=ChallengeIndicator.NO_CHALLENGE,
        custom_order_id_prefix="3ds-frictionless-direct",
        base_method_url=f"{base_dummy_url}/method_nodirect",
        base_term_url=f"{base_dummy_url}/term_nodirect",
        force_no_3ds_flag="0",
    )

    initial_response_dict = await azul.secure_sale(
        initial_request_data.model_dump(exclude_none=True)
    )
    assert initial_response_dict is not None

    # Debug: Print the actual response structure
    print(f"DEBUG: Actual response: {initial_response_dict}")

    assert not initial_response_dict.get(
        "redirect"
    ), "Expected no redirect for direct frictionless approval."

    value_data = initial_response_dict.get("value")
    if value_data is None:
        # Check if the response is directly at the top level
        if initial_response_dict.get("IsoCode") == "00":
            print("Response is at top level, not in 'value' field")
            assert initial_response_dict.get("ResponseMessage") == "APROBADA"
            return

    assert isinstance(
        value_data, dict
    ), f"Expected 'value' dict in direct approval, got: {type(value_data)}"

    assert (
        value_data.get("IsoCode") == "00"
    ), f"Expected IsoCode 00, got: {value_data.get('IsoCode')}"
    assert (
        value_data.get("ResponseMessage") == "APROBADA"
    ), f"Expected APROBADA, got: {value_data.get('ResponseMessage')}"
    print("Approved directly (frictionless, no method/challenge redirect).")


@pytest.mark.asyncio
async def test_secure_sale_direct_to_challenge(
    azul_fixture: PyAzul,
    card_holder_info_fixture: CardHolderInfo,
    settings,
):
    """Test a 3DS sale that goes directly to challenge without a 3DS Method step."""
    azul = azul_fixture
    card = get_card("SECURE_3DS_CHALLENGE_NO_3DS")
    order_num = generate_order_number()
    base_dummy_url = "http://localhost:8000/dummy"

    initial_request_data = _prepare_secure_sale_request_data(
        settings=settings,
        card=card,
        order_num=order_num,
        card_holder_info=card_holder_info_fixture,
        challenge_indicator=ChallengeIndicator.CHALLENGE,
        custom_order_id_prefix="3ds-direct-challenge",
        base_method_url=f"{base_dummy_url}/method_direct_challenge",
        base_term_url=f"{base_dummy_url}/term_direct_challenge",
        force_no_3ds_flag="0",
    )

    initial_response_dict = await azul.secure_sale(
        initial_request_data.model_dump(exclude_none=True)
    )
    assert initial_response_dict is not None

    if (
        initial_response_dict.get("redirect")
        and initial_response_dict.get("html")
        and initial_response_dict.get("id")
    ):
        secure_id = initial_response_dict["id"]
        message = initial_response_dict.get("message", "")
        print(f"Initial redirect. Message: {message}. ID: {secure_id}")

        session_data = await azul.get_session_info(secure_id)
        assert session_data is not None, "Session data not found."
        stored_term_url = session_data.get("term_url")
        assert stored_term_url is not None, "TermUrl not found."
        assert (
            f"secure_id={secure_id}" in stored_term_url
        ), "secure_id not in stored TermUrl."

        print("Direct challenge by secure_sale as expected.")

    elif (
        initial_response_dict.get("value")
        and isinstance(initial_response_dict["value"], dict)
        and initial_response_dict["value"].get("IsoCode") == "00"
    ):
        print("Unexpected direct approval for a challenge card.")
        assert initial_response_dict["value"].get("ResponseMessage") == "APROBADA"
        pytest.fail("Expected direct challenge, got direct approval.")
    elif initial_response_dict.get("IsoCode") == "00":
        print("Unexpected direct approval (top-level) for a challenge card.")
        assert initial_response_dict.get("ResponseMessage") == "APROBADA"
        pytest.fail("Expected direct challenge, got direct approval (top-level).")
    else:
        response_dump = str(initial_response_dict)
        pytest.fail(
            "Unexpected initial response. Expected 3DS redirect or approval. "
            f"Got: {response_dump}"
        )


@pytest.mark.asyncio
async def test_secure_sale_challenge_after_method(
    azul_fixture: PyAzul,
    card_holder_info_fixture: CardHolderInfo,
    settings,
):
    """Test a 3DS sale that proceeds to challenge after a 3DS Method step."""
    azul = azul_fixture
    card = get_card("SECURE_3DS_CHALLENGE_WITH_3DS")
    order_num = generate_order_number()
    base_dummy_url = "http://localhost:8000/dummy"

    initial_request_data = _prepare_secure_sale_request_data(
        settings=settings,
        card=card,
        order_num=order_num,
        card_holder_info=card_holder_info_fixture,
        challenge_indicator=ChallengeIndicator.CHALLENGE,
        custom_order_id_prefix="3ds-method-challenge",
        base_method_url=f"{base_dummy_url}/method_challenge_after",
        base_term_url=f"{base_dummy_url}/term_challenge_after",
        force_no_3ds_flag="0",
    )

    initial_response_dict = await azul.secure_sale(
        initial_request_data.model_dump(exclude_none=True)
    )
    assert initial_response_dict is not None
    assert initial_response_dict.get("redirect"), "Expected redirect for 3DS Method."
    assert (
        initial_response_dict.get("html") is not None
    ), "HTML expected for 3DS Method."
    assert initial_response_dict.get("id") is not None, "'id' (secure_id) expected."

    secure_id = initial_response_dict["id"]
    print(f"Initial 3DS Sale requires redirect (3DS Method). ID: {secure_id}")

    session_data = await azul.get_session_info(secure_id)
    assert session_data is not None, "Session data not found."
    azul_order_id_from_session = session_data.get("azul_order_id")
    assert azul_order_id_from_session is not None, "AzulOrderId not found in session."
    stored_term_url_after_method = session_data.get("term_url")
    assert stored_term_url_after_method is not None, "TermUrl not in session."

    method_response = await azul.process_3ds_method(
        azul_order_id=azul_order_id_from_session,
        method_notification_status="RECEIVED",
    )
    assert method_response is not None
    assert isinstance(method_response, dict), "method_response should be dict."

    response_msg = method_response.get("ResponseMessage")
    assert (
        response_msg == "3D_SECURE_CHALLENGE"
    ), f"Expected 3D_SECURE_CHALLENGE, got {response_msg}"

    three_ds_challenge_data = method_response.get("ThreeDSChallenge")
    assert isinstance(
        three_ds_challenge_data, dict
    ), "ThreeDSChallenge data missing/not dict"

    creq = three_ds_challenge_data.get("CReq")
    redirect_post_url_from_acs = three_ds_challenge_data.get("RedirectPostUrl")
    assert creq is not None, "CReq missing."
    assert redirect_post_url_from_acs is not None, "RedirectPostUrl missing."

    print(
        f"3DS Method led to challenge. CReq: {creq[:15]}... "
        f"ACS URL: {redirect_post_url_from_acs[:30]}..."
    )

    challenge_form_html = azul.create_challenge_form(
        creq=creq,
        term_url=stored_term_url_after_method,
        redirect_post_url=redirect_post_url_from_acs,
    )
    assert "<form" in challenge_form_html and 'name="creq"' in challenge_form_html

    print("Challenge after 3DS Method initiated as expected.")


@pytest.mark.asyncio
async def test_secure_sale_3ds_method_with_session_validation(
    azul_fixture: PyAzul,
    card_holder_info_fixture: CardHolderInfo,
    settings,
):
    """Test that 3DS method processing includes all required fields and maintains session state."""  # noqa: E501
    azul = azul_fixture
    card = get_card("SECURE_3DS_FRICTIONLESS_WITH_3DS")
    order_num = generate_order_number()
    base_dummy_url = "http://localhost:8000/dummy"

    initial_request_data = _prepare_secure_sale_request_data(
        settings=settings,
        card=card,
        order_num=order_num,
        card_holder_info=card_holder_info_fixture,
        challenge_indicator=ChallengeIndicator.NO_CHALLENGE,
        custom_order_id_prefix="3ds-session-validation",
        base_method_url=f"{base_dummy_url}/method",
        base_term_url=f"{base_dummy_url}/term",
        force_no_3ds_flag="0",
        amount_value=1500,  # Use specific amount to validate
        itbis_value=270,  # Use specific ITBIS to validate
    )

    # Step 1: Initial secure sale
    initial_response_dict = await azul.secure_sale(
        initial_request_data.model_dump(exclude_none=True)
    )

    assert initial_response_dict.get("redirect"), "Expected 3DS method redirect"
    secure_id = initial_response_dict["id"]

    # Step 2: Validate session data is properly stored
    session_data = await azul.get_session_info(secure_id)
    assert session_data is not None, "Session data should be stored"
    assert session_data.get("azul_order_id"), "AzulOrderId should be in session"
    assert session_data.get("amount") == "1500", "Amount should be stored in session"
    assert session_data.get("itbis") == "270", "ITBIS should be stored in session"
    assert session_data.get("order_number") == order_num, "OrderNumber should be stored"

    # Step 3: Validate that process_3ds_method can access session data
    azul_order_id = session_data["azul_order_id"]

    # Step 4: Process 3DS method and validate it includes required fields
    method_response = await azul.process_3ds_method(
        azul_order_id=azul_order_id,
        method_notification_status="RECEIVED",
    )

    # The method should succeed (this validates that all required fields were sent)
    assert method_response is not None, "Method response should not be None"

    # If it's a successful response, validate the structure
    if isinstance(method_response, dict):
        # Should not have errors about missing fields
        error_msg = method_response.get("ErrorDescription", "")
        assert (
            "Amount or currency missing" not in error_msg
        ), f"Should not have missing field errors: {error_msg}"
        assert (
            "No autenticada" not in error_msg
        ), f"Should not have auth errors: {error_msg}"


@pytest.mark.asyncio
async def test_secure_sale_duplicate_method_notification_handling(
    azul_fixture: PyAzul,
    card_holder_info_fixture: CardHolderInfo,
    settings,
):
    """Test that duplicate 3DS method notifications are handled properly."""
    azul = azul_fixture
    card = get_card("SECURE_3DS_FRICTIONLESS_WITH_3DS")
    order_num = generate_order_number()
    base_dummy_url = "http://localhost:8000/dummy"

    initial_request_data = _prepare_secure_sale_request_data(
        settings=settings,
        card=card,
        order_num=order_num,
        card_holder_info=card_holder_info_fixture,
        challenge_indicator=ChallengeIndicator.NO_CHALLENGE,
        custom_order_id_prefix="3ds-duplicate-test",
        base_method_url=f"{base_dummy_url}/method",
        base_term_url=f"{base_dummy_url}/term",
        force_no_3ds_flag="0",
    )

    # Step 1: Initial secure sale
    initial_response_dict = await azul.secure_sale(
        initial_request_data.model_dump(exclude_none=True)
    )

    if not initial_response_dict.get("redirect"):
        pytest.skip("Test requires 3DS method redirect")

    secure_id = initial_response_dict["id"]
    session_data = await azul.get_session_info(secure_id)
    assert session_data is not None, "Session data should not be None"
    azul_order_id = session_data["azul_order_id"]

    # Step 2: First method notification
    first_response = await azul.process_3ds_method(
        azul_order_id=azul_order_id,
        method_notification_status="RECEIVED",
    )

    # Validate first response is successful
    assert first_response is not None, "First method response should not be None"

    # Step 3: Duplicate method notification (should be handled gracefully)
    second_response = await azul.process_3ds_method(
        azul_order_id=azul_order_id,
        method_notification_status="RECEIVED",
    )

    # Should indicate it was already processed
    assert (
        second_response.get("ResponseMessage") == "ALREADY_PROCESSED"
    ), "Duplicate method notification should be detected"
