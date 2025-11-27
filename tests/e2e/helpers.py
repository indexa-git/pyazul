"""Helper functions for e2e tests."""

import json
from typing import Any, Dict, Literal, Optional, Tuple

import pytest


def assert_3ds_response(
    result: Dict[str, Any],
    expected_type: Literal["redirect", "wrapped_approval", "direct_approval", "any"] = "any",
) -> Tuple[Optional[str], Optional[Dict[str, Any]]]:
    """
    Validate and extract data from 3DS response.

    Handles three 3DS response types:
    1. `redirect: true` - 3DS Method/Challenge required
    2. `value: {...}` - Wrapped approval response
    3. Top-level `IsoCode: "00"` - Direct frictionless approval

    Args:
        result: Response dict from secure_sale/secure_token_sale
        expected_type: Expected response type. "any" accepts any valid type.

    Returns:
        Tuple of (secure_id, response_data):
        - secure_id: The secure_id if redirect is required, None otherwise
        - response_data: The actual response dict (from value field or top-level)

    Raises:
        pytest.fail: If the response doesn't match expected type or is invalid
    """
    if not isinstance(result, dict):
        pytest.fail(f"Expected dict response, got: {type(result)}")

    # Case 1: Redirect required (3DS Method/Challenge)
    if result.get("redirect") and result.get("html") and result.get("id"):
        secure_id = result["id"]
        if expected_type not in ("redirect", "any"):
            response_dump = json.dumps(result, indent=2) if isinstance(result, dict) else str(result)
            pytest.fail(
                f"Expected {expected_type}, but got redirect response. "
                f"Response: {response_dump}"
            )
        return secure_id, None

    # Case 2: Wrapped approval response (value field)
    if result.get("value") and isinstance(result["value"], dict):
        response = result["value"]
        if response.get("IsoCode") == "00":
            if expected_type not in ("wrapped_approval", "direct_approval", "any"):
                response_dump = json.dumps(result, indent=2)
                pytest.fail(
                    f"Expected {expected_type}, but got wrapped approval. "
                    f"Response: {response_dump}"
                )
            assert response.get("ResponseMessage") == "APROBADA", (
                f"Expected APROBADA, got: {response.get('ResponseMessage')}"
            )
            return None, response
        # If value exists but IsoCode is not "00", it might be an error
        # Let the caller handle it

    # Case 3: Direct approval at top level
    if result.get("IsoCode") == "00":
        if expected_type not in ("direct_approval", "any"):
            response_dump = json.dumps(result, indent=2) if isinstance(result, dict) else str(result)
            pytest.fail(
                f"Expected {expected_type}, but got direct approval (top-level). "
                f"Response: {response_dump}"
            )
        assert result.get("ResponseMessage") == "APROBADA", (
            f"Expected APROBADA, got: {result.get('ResponseMessage')}"
        )
        return None, result

    # If we get here, the response doesn't match any expected pattern
    response_dump = json.dumps(result, indent=2) if isinstance(result, dict) else str(result)
    pytest.fail(
        f"Unexpected 3DS response format. Expected one of: redirect, "
        f"wrapped_approval, or direct_approval. Got: {response_dump}"
    )

