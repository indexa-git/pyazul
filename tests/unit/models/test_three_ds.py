"""Unit tests for 3D Secure models."""

import pytest
from pydantic import ValidationError

from pyazul.models.three_ds import (
    CardHolderInfo,
    ChallengeIndicator,
    SecureTokenHold,
    ThreeDSAuth,
)


class TestSecureTokenHold:
    """Tests for SecureTokenHold model."""

    def test_secure_token_hold_valid_data(self):
        """Test creating SecureTokenHold with valid data."""
        cardholder = CardHolderInfo(
            Name="Test User",
            Email="test@example.com",
        )

        three_ds_auth = ThreeDSAuth(
            TermUrl="https://example.com/term",
            MethodNotificationUrl="https://example.com/method",
            RequestChallengeIndicator=ChallengeIndicator.CHALLENGE,
        )

        token_hold = SecureTokenHold(
            Store="39038540035",
            Amount="1000",
            Itbis="180",
            DataVaultToken="6EF85D01-B07C-4E67-99F74E13A449DCDD",
            OrderNumber="TEST001",
            CardHolderInfo=cardholder,
            ThreeDSAuth=three_ds_auth,
        )

        assert token_hold.Store == "39038540035"
        assert token_hold.Amount == "1000"
        assert token_hold.Itbis == "180"
        assert token_hold.DataVaultToken == "6EF85D01-B07C-4E67-99F74E13A449DCDD"
        assert token_hold.OrderNumber == "TEST001"
        assert token_hold.TrxType == "Hold"
        assert token_hold.Expiration == ""
        assert token_hold.Channel == "EC"
        assert token_hold.PosInputMode == "E-Commerce"

    def test_secure_token_hold_default_values(self):
        """Test SecureTokenHold with default values."""
        cardholder = CardHolderInfo(Name="Test User")
        three_ds_auth = ThreeDSAuth(
            TermUrl="https://example.com/term",
            MethodNotificationUrl="https://example.com/method",
            RequestChallengeIndicator=ChallengeIndicator.CHALLENGE,
        )

        token_hold = SecureTokenHold(
            Store="39038540035",
            Amount="1000",
            DataVaultToken="6EF85D01-B07C-4E67-99F74E13A449DCDD",
            OrderNumber="TEST001",
            CardHolderInfo=cardholder,
            ThreeDSAuth=three_ds_auth,
        )

        # Check default values
        assert token_hold.Channel == "EC"
        assert token_hold.PosInputMode == "E-Commerce"
        assert token_hold.TrxType == "Hold"
        assert token_hold.Expiration == ""
        assert token_hold.ForceNo3DS == "0"
        assert token_hold.AcquirerRefData == "1"

    def test_secure_token_hold_required_fields(self):
        """Test that SecureTokenHold validates required fields."""
        with pytest.raises(ValidationError) as exc_info:
            SecureTokenHold()  # type: ignore

        errors = exc_info.value.errors()
        required_fields = [
            error["loc"][0] for error in errors if error["type"] == "missing"
        ]

        # Check that required fields are validated
        assert "Store" in required_fields
        assert "Amount" in required_fields
        assert "DataVaultToken" in required_fields
        assert "OrderNumber" in required_fields
        assert "CardHolderInfo" in required_fields
        assert "ThreeDSAuth" in required_fields

    def test_secure_token_hold_trx_type_validation(self):
        """Test that TrxType field only accepts 'Hold'."""
        cardholder = CardHolderInfo(Name="Test User")
        three_ds_auth = ThreeDSAuth(
            TermUrl="https://example.com/term",
            MethodNotificationUrl="https://example.com/method",
            RequestChallengeIndicator=ChallengeIndicator.CHALLENGE,
        )

        # Should raise validation error for invalid TrxType
        with pytest.raises(ValidationError) as exc_info:
            SecureTokenHold(
                Store="39038540035",
                Amount="1000",
                DataVaultToken="6EF85D01-B07C-4E67-99F74E13A449DCDD",
                OrderNumber="TEST001",
                TrxType="Sale",  # Invalid for token hold
                CardHolderInfo=cardholder,
                ThreeDSAuth=three_ds_auth,
            )

        errors = exc_info.value.errors()
        pattern_error = next(
            (e for e in errors if e["type"] == "string_pattern_mismatch"), None
        )
        assert pattern_error is not None

    def test_secure_token_hold_token_validation(self):
        """Test DataVaultToken format validation."""
        cardholder = CardHolderInfo(Name="Test User")
        three_ds_auth = ThreeDSAuth(
            TermUrl="https://example.com/term",
            MethodNotificationUrl="https://example.com/method",
            RequestChallengeIndicator=ChallengeIndicator.CHALLENGE,
        )

        # Should raise validation error for invalid token format
        with pytest.raises(ValidationError) as exc_info:
            SecureTokenHold(
                Store="39038540035",
                Amount="1000",
                DataVaultToken="invalid-token",  # Invalid format
                OrderNumber="TEST001",
                CardHolderInfo=cardholder,
                ThreeDSAuth=three_ds_auth,
            )

        errors = exc_info.value.errors()
        pattern_error = next(
            (e for e in errors if e["type"] == "string_pattern_mismatch"), None
        )
        assert pattern_error is not None

    def test_secure_token_hold_force_no_3ds_validation(self):
        """Test ForceNo3DS field validation."""
        cardholder = CardHolderInfo(Name="Test User")
        three_ds_auth = ThreeDSAuth(
            TermUrl="https://example.com/term",
            MethodNotificationUrl="https://example.com/method",
            RequestChallengeIndicator=ChallengeIndicator.CHALLENGE,
        )

        # Should raise validation error for invalid ForceNo3DS value
        with pytest.raises(ValidationError) as exc_info:
            SecureTokenHold(
                Store="39038540035",
                Amount="1000",
                DataVaultToken="6EF85D01-B07C-4E67-99F74E13A449DCDD",
                OrderNumber="TEST001",
                ForceNo3DS="2",  # Invalid value
                CardHolderInfo=cardholder,
                ThreeDSAuth=three_ds_auth,
            )

        errors = exc_info.value.errors()
        pattern_error = next(
            (e for e in errors if e["type"] == "string_pattern_mismatch"), None
        )
        assert pattern_error is not None

    def test_secure_token_hold_optional_fields(self):
        """Test SecureTokenHold with optional fields."""
        cardholder = CardHolderInfo(
            Name="Test User",
            Email="test@example.com",
            BillingAddressCity="Test City",
        )

        three_ds_auth = ThreeDSAuth(
            TermUrl="https://example.com/term",
            MethodNotificationUrl="https://example.com/method",
            RequestChallengeIndicator=ChallengeIndicator.NO_CHALLENGE,
        )

        token_hold = SecureTokenHold(
            Store="39038540035",
            Amount="1000",
            Itbis="180",
            DataVaultToken="6EF85D01-B07C-4E67-99F74E13A449DCDD",
            OrderNumber="TEST001",
            CustomOrderId="CUSTOM001",
            CVC="123",
            CardNumber="4111111111111111",
            CardHolderInfo=cardholder,
            ThreeDSAuth=three_ds_auth,
        )

        assert token_hold.CustomOrderId == "CUSTOM001"
        assert token_hold.CVC == "123"
        assert token_hold.CardNumber == "4111111111111111"

    def test_secure_token_hold_model_dump(self):
        """Test model serialization with exclude_none."""
        cardholder = CardHolderInfo(
            Name="Test User",
            Email="test@example.com",
        )

        three_ds_auth = ThreeDSAuth(
            TermUrl="https://example.com/term",
            MethodNotificationUrl="https://example.com/method",
            RequestChallengeIndicator=ChallengeIndicator.CHALLENGE,
        )

        token_hold = SecureTokenHold(
            Store="39038540035",
            Amount="1000",
            DataVaultToken="6EF85D01-B07C-4E67-99F74E13A449DCDD",
            OrderNumber="TEST001",
            CardHolderInfo=cardholder,
            ThreeDSAuth=three_ds_auth,
        )

        # Serialize with exclude_none=True (as used in the service)
        data = token_hold.model_dump(exclude_none=True)

        # Required fields should be present
        assert "Store" in data
        assert "Amount" in data
        assert "DataVaultToken" in data
        assert "OrderNumber" in data
        assert "TrxType" in data
        assert "CardHolderInfo" in data
        assert "ThreeDSAuth" in data

        # Optional fields with None values should be excluded
        assert "Itbis" not in data or data["Itbis"] is not None
        assert "CVC" not in data or data["CVC"] is not None
        assert "CardNumber" not in data or data["CardNumber"] is not None
