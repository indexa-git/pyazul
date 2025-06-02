"""Unit tests for pyazul.models schema validation and data structures."""

import pytest
from pydantic import ValidationError

from pyazul.models.three_ds import CardHolderInfo, ChallengeIndicator, ThreeDSAuth


class TestCardHolderInfo:
    """Tests for the CardHolderInfo model."""

    def test_card_holder_info_valid(self):
        """Test successful creation of CardHolderInfo with valid data."""
        data = {
            "Name": "Test User",
            "Email": "test@example.com",
            "BillingAddressLine1": "123 Main St",
            "BillingAddressCity": "Anytown",
            "BillingAddressState": "CA",
            "BillingAddressCountry": "US",
            "BillingAddressZip": "90210",
        }
        info = CardHolderInfo(**data)
        assert info.Name == data["Name"]
        assert info.Email == data["Email"]
        assert info.BillingAddressZip == data["BillingAddressZip"]

    def test_card_holder_info_name_is_required(self):
        """Test CardHolderInfo requires Name field, other fields are optional."""
        # Test that Name is required
        with pytest.raises(ValidationError) as exc_info:
            CardHolderInfo()  # type: ignore
        assert any(err["loc"] == ("Name",) for err in exc_info.value.errors())

        # Test that only Name is required, other fields are optional
        info = CardHolderInfo(Name="Test User")
        assert info.Name == "Test User"
        assert info.Email is None
        assert info.BillingAddressLine1 is None
        # ... can add more checks for other fields if desired

    def test_card_holder_info_optional_fields_provided(self):
        """Test CardHolderInfo with optional fields provided."""
        required_data = {
            "Name": "Test User",
            "Email": "test@example.com",
            "BillingAddressLine1": "123 Main St",
            "BillingAddressCity": "Anytown",
            "BillingAddressState": "CA",
            "BillingAddressCountry": "US",
            "BillingAddressZip": "90210",
        }
        # All optional fields are None by default if not provided
        info_minimal = CardHolderInfo(**required_data)
        assert info_minimal.BillingAddressLine2 is None
        assert info_minimal.PhoneHome is None

        info_with_optionals = CardHolderInfo(
            **required_data, PhoneHome="555-1234", ShippingAddressLine1="456 Ship Ave"
        )
        assert info_with_optionals.PhoneHome == "555-1234"
        assert info_with_optionals.ShippingAddressLine1 == "456 Ship Ave"


class TestThreeDSAuth:
    """Tests for the ThreeDSAuth model."""

    def test_three_ds_auth_valid(self):
        """Test successful creation of ThreeDSAuth with valid data."""
        data = {
            "TermUrl": "https://example.com/term",
            "MethodNotificationUrl": "https://example.com/method",
            "RequestChallengeIndicator": ChallengeIndicator.NO_PREFERENCE,
        }
        auth = ThreeDSAuth(**data)
        assert auth.TermUrl == data["TermUrl"]
        assert auth.MethodNotificationUrl == data["MethodNotificationUrl"]
        assert auth.RequestChallengeIndicator == data["RequestChallengeIndicator"]

    def test_three_ds_auth_missing_one_required_field_raises_error(self):
        """Test ThreeDSAuth raises ValidationError for a missing required field."""
        with pytest.raises(ValidationError) as exc_info:
            ThreeDSAuth(  # type: ignore
                TermUrl="https://example.com/term",
                RequestChallengeIndicator=ChallengeIndicator.CHALLENGE,
            )
        assert any(
            err["loc"] == ("MethodNotificationUrl",) for err in exc_info.value.errors()
        )

    def test_three_ds_auth_invalid_challenge_indicator(self):
        """Test ThreeDSAuth with an invalid RequestChallengeIndicator value."""
        with pytest.raises(ValidationError) as exc_info:
            ThreeDSAuth(
                TermUrl="https://example.com/term",
                MethodNotificationUrl="https://example.com/method",
                RequestChallengeIndicator="INVALID_VALUE",  # type: ignore
            )
        assert any(
            err["loc"] == ("RequestChallengeIndicator",)
            for err in exc_info.value.errors()
        )


# Add more model tests here as needed, e.g., for SecureSaleRequest, etc.
