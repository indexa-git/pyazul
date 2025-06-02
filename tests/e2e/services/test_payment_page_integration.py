"""Integration tests for payment page creation and generation."""

import pytest
from pydantic import HttpUrl, ValidationError

from pyazul.models.payment_page import PaymentPage
from tests.fixtures.order import generate_order_number


@pytest.fixture
def valid_payment_request():
    """Fixture that provides a valid PaymentPageModel instance."""
    return PaymentPage(
        OrderNumber=generate_order_number(),
        Amount="100000",  # $1,000.00
        ITBIS="18000",  # $180.00
        ApprovedUrl=HttpUrl("https://example.com/approved"),
        DeclineUrl=HttpUrl("https://example.com/declined"),
        CancelUrl=HttpUrl("https://example.com/cancel"),
    )


class TestPaymentPageModel:
    """Test cases for PaymentPageModel validation and functionality."""

    def test_valid_amounts(self):
        """Test that valid amounts are accepted."""
        model = PaymentPage(
            OrderNumber=generate_order_number(),
            Amount="100000",  # $1,000.00
            ITBIS="18000",  # $180.00
            ApprovedUrl=HttpUrl("https://example.com/approved"),
            DeclineUrl=HttpUrl("https://example.com/declined"),
            CancelUrl=HttpUrl("https://example.com/cancel"),
            AltMerchantName=None,
        )
        assert model.Amount == "100000"
        assert model.ITBIS == "18000"

    def test_zero_itbis_format(self):
        """Test that zero ITBIS is formatted as '0'."""
        model = PaymentPage(
            OrderNumber=generate_order_number(),
            Amount="100000",
            ITBIS="0",
            ApprovedUrl=HttpUrl("https://example.com/approved"),
            DeclineUrl=HttpUrl("https://example.com/declined"),
            CancelUrl=HttpUrl("https://example.com/cancel"),
            AltMerchantName=None,
        )
        assert model.ITBIS == "0"

    def test_invalid_amount_format(self):
        """Test that invalid amount formats are rejected."""
        with pytest.raises(ValidationError):
            PaymentPage(
                OrderNumber=generate_order_number(),
                Amount="1000.00",  # Invalid: contains decimal point
                ITBIS="180.00",  # Invalid: contains decimal point
                ApprovedUrl=HttpUrl("https://example.com/approved"),
                DeclineUrl=HttpUrl("https://example.com/declined"),
                CancelUrl=HttpUrl("https://example.com/cancel"),
                AltMerchantName=None,
            )

    def test_custom_field_validation(self):
        """Test that custom field validation works correctly."""
        # When UseCustomField1 is "1", label and value are required
        with pytest.raises(ValidationError):
            PaymentPage(
                OrderNumber=generate_order_number(),
                Amount="100000",
                ITBIS="18000",
                ApprovedUrl=HttpUrl("https://example.com/approved"),
                DeclineUrl=HttpUrl("https://example.com/declined"),
                CancelUrl=HttpUrl("https://example.com/cancel"),
                UseCustomField1="1",  # Enabled but no label/value
                CustomField1Label="",  # Empty label should trigger validation error
                CustomField1Value="",  # Empty value should trigger validation error
                AltMerchantName=None,
            )

    def test_string_representation(self):
        """Test the string representation of amounts."""
        order_num = generate_order_number()
        model = PaymentPage(
            OrderNumber=order_num,
            Amount="100000",  # $1,000.00
            ITBIS="18000",  # $180.00
            ApprovedUrl=HttpUrl("https://example.com/approved"),
            DeclineUrl=HttpUrl("https://example.com/declined"),
            CancelUrl=HttpUrl("https://example.com/cancel"),
            AltMerchantName=None,
        )
        expected = "Payment Request - Amount: $1000.00, ITBIS: $180.00"
        assert str(model) == expected


class TestPaymentPageService:
    """Test cases for PaymentPageService functionality."""

    def test_form_generation(
        self, payment_page_service_integration, valid_payment_request
    ):
        """Test that a valid HTML form is generated."""
        form = payment_page_service_integration.generate_payment_form_html(
            valid_payment_request
        )

        # Check that the form contains essential elements
        assert "<form" in form and 'method="post"' in form
        assert "script" in form
        assert "Auto-submit form" in form

        # Check that all required fields are present
        required_fields = [
            "MerchantId",
            "MerchantName",
            "MerchantType",
            "Amount",
            "ITBIS",
            "OrderNumber",
            "AuthHash",
        ]
        for field in required_fields:
            assert f'name="{field}"' in form

    def test_auth_hash_generation(
        self, payment_page_service_integration, valid_payment_request
    ):
        """Test that authentication hash is generated correctly."""
        # Generate form which includes hash calculation
        form = payment_page_service_integration.generate_payment_form_html(
            valid_payment_request
        )

        # Verify hash is present in form
        assert 'name="AuthHash"' in form
        assert 'value="' in form

        # Extract hash value
        import re

        hash_match = re.search(r'name="AuthHash" value="([^"]+)"', form)
        assert hash_match is not None

        # Verify hash is a valid hex string of correct length (SHA512 = 128 chars)
        hash_value = hash_match.group(1)
        assert len(hash_value) == 128
        assert all(c in "0123456789ABCDEFabcdef" for c in hash_value)
