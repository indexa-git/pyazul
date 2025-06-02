"""
Payment Page service for PyAzul.

This module provides services for generating Azul's hosted Payment Page,
including HTML form creation, hash generation, and data formatting.
"""

import hashlib
import logging
from typing import Dict

from ..core.config import AzulSettings
from ..core.exceptions import AzulError
from ..models.payment_page import PaymentPage

_logger = logging.getLogger(__name__)


class PaymentPageService:
    """Service for generating Azul Payment Page forms."""

    def __init__(self, settings: AzulSettings):
        """Initialize the Payment Page service with settings."""
        self.settings = settings

    def generate_payment_form_html(self, payment_data: PaymentPage) -> str:
        """
        Generate HTML form for Azul Payment Page.

        Args:
            payment_data: Payment page model with transaction details

        Returns:
            HTML form string ready for rendering

        Raises:
            AzulError: If form generation fails
        """
        try:
            _logger.info("Generating Payment Page HTML form")

            # Convert model to dictionary for form generation
            form_data = payment_data.model_dump()

            # Add merchant configuration
            form_data.update(
                {
                    "MerchantId": self.settings.MERCHANT_ID,
                    "MerchantName": self.settings.MERCHANT_NAME,
                    "MerchantType": self.settings.MERCHANT_TYPE,
                }
            )

            # Generate hash for form authentication
            auth_hash = self._generate_auth_hash(form_data)
            form_data["AuthHash"] = auth_hash

            # Generate HTML form
            html = self._create_form_html(form_data)

            _logger.info("Payment Page HTML form generated successfully")
            return html

        except Exception as e:
            _logger.error(f"Payment Page form generation failed: {e}")
            raise AzulError(f"Payment Page form generation failed: {e}") from e

    def _generate_auth_hash(self, form_data: Dict[str, str]) -> str:
        """
        Generate authentication hash for Payment Page.

        Args:
            form_data: Dictionary containing form fields

        Returns:
            SHA512 hash string for authentication
        """
        # Create hash string according to Azul's specification
        hash_string = (
            f"{self.settings.AZUL_AUTH_KEY}"
            f"{form_data['MerchantId']}"
            f"{form_data['OrderNumber']}"
            f"{form_data['Amount']}"
            f"{form_data['ITBIS']}"
            f"{self.settings.AZUL_AUTH_KEY}"
        )

        # Generate SHA512 hash
        return hashlib.sha512(hash_string.encode("utf-8")).hexdigest().upper()

    def _create_form_html(self, form_data: Dict[str, str]) -> str:
        """
        Create HTML form with all payment data.

        Args:
            form_data: Dictionary containing all form fields

        Returns:
            Complete HTML form string
        """
        payment_page_url = self._get_payment_page_url()

        # Generate form fields
        form_fields = ""
        for field_name, field_value in form_data.items():
            if field_value is not None:
                form_fields += (
                    f'    <input type="hidden" name="{field_name}" '
                    f'value="{field_value}" />\n'
                )

        # Create complete HTML form
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8" />
    <title>Azul Payment Page</title>
</head>
<body>
    <form id="azul-payment-form" method="post" action="{payment_page_url}">
{form_fields}
        <input type="submit" value="Pay with Azul" />
    </form>

    <script>
        // Auto-submit form (optional)
        // document.getElementById('azul-payment-form').submit();
    </script>
</body>
</html>
"""
        return html

    def _get_payment_page_url(self) -> str:
        """
        Get the appropriate Payment Page URL based on environment.

        Returns:
            Payment Page URL string
        """
        if self.settings.ENVIRONMENT == "prod":
            return "https://pagos.azul.com.do/paymentpage/default.aspx"
        else:
            return "https://pruebas.azul.com.do/paymentpage/default.aspx"

    def create_payment_request(
        self,
        amount: int,
        itbis: int,
        order_number: str,
        approved_url: str,
        decline_url: str,
        cancel_url: str,
        **kwargs,
    ) -> PaymentPage:
        """
        Create a payment request model with the provided parameters.

        Args:
            amount: Total amount in cents
            itbis: Tax amount in cents
            order_number: Unique order identifier
            approved_url: URL for successful payments
            decline_url: URL for declined payments
            cancel_url: URL for cancelled payments
            **kwargs: Additional optional parameters

        Returns:
            PaymentPage model ready for form generation

        Raises:
            AzulError: If payment request creation fails
        """
        try:
            _logger.info("Creating payment request")

            payment_data = {
                "Amount": str(amount),
                "ITBIS": str(itbis),
                "OrderNumber": order_number,
                "ApprovedUrl": approved_url,
                "DeclineUrl": decline_url,
                "CancelUrl": cancel_url,
                **kwargs,
            }

            payment_request = PaymentPage(**payment_data)

            _logger.info("Payment request created successfully")
            return payment_request

        except Exception as e:
            _logger.error(f"Payment request creation failed: {e}")
            raise AzulError(f"Payment request creation failed: {e}") from e
