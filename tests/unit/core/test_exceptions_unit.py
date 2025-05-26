"""Unit tests for pyazul.core.exceptions."""

import pytest

from pyazul.core.exceptions import APIError, AzulError, AzulResponseError, SSLError


def test_azul_error_raising():
    """Test that AzulError can be raised."""
    with pytest.raises(AzulError, match="This is a base Azul error."):
        raise AzulError("This is a base Azul error.")


def test_ssl_error_raising():
    """Test that SSLError can be raised."""
    with pytest.raises(SSLError, match="SSL specific error."):
        raise SSLError("SSL specific error.")


def test_api_error_raising():
    """Test that APIError can be raised."""
    with pytest.raises(APIError, match="Generic API communication error."):
        raise APIError("Generic API communication error.")


def test_azul_response_error_raising_and_stores_data():
    """Test AzulResponseError can be raised and stores response_data."""
    response_data = {"ErrorCode": "01", "ErrorMessage": "Declined"}
    custom_message = "Azul API error: Declined - Code 01"
    with pytest.raises(AzulResponseError, match=custom_message) as exc_info:
        raise AzulResponseError(custom_message, response_data=response_data)

    assert exc_info.value.response_data == response_data
    assert exc_info.value.message == custom_message


def test_exception_chaining():
    """Test that exceptions can be chained using 'from'."""
    original_exception = ValueError("Original issue")
    with pytest.raises(APIError) as exc_info:
        try:
            raise original_exception
        except ValueError as e:
            raise APIError("API failed due to value error") from e

    assert exc_info.value.__cause__ is original_exception
