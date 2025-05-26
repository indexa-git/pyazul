"""
Service for Azul Payment Page interactions.

Handles payment form generation, auth hash calculation, and environment URLs.
"""

import hashlib
import hmac

from pyazul.api.constants import AzulEndpoints, Environment
from pyazul.core.config import AzulSettings
from pyazul.models.schemas import PaymentPageModel


class PaymentPageService:
    """
    Service for handling Azul Payment Page Operations.

    Provides methods to generate secure payment forms, calculate auth hashes,
    and manage environment-specific URLs for primary or alternate production.
    """

    def __init__(self, settings: AzulSettings):
        """Initialize PaymentPage Service with Azul configuration settings."""
        self.settings = settings

    def _get_base_url(self, use_alternate_url: bool = False) -> str:
        """
        Get the base URL for Payment Page.

        Args:
            use_alternate_url (bool): If True and in 'prod' environment,
                                      returns the alternate URL.

        Returns:
            str: Base URL for the payment page.
        """
        if self.settings.ENVIRONMENT == Environment.DEV:
            return AzulEndpoints.DEV_URL_PAYMEMT

        # Production environment
        if use_alternate_url:
            # Prioritize user-set alternate, then constant
            return (
                self.settings.ALT_PROD_URL_PAYMENT or AzulEndpoints.ALT_PROD_URL_PAYMEMT
            )
        return AzulEndpoints.PROD_URL_PAYMEMT

    def _generate_auth_hash(self, payment_request: PaymentPageModel) -> str:
        """Generate authentication hash for the payment request."""
        if self.settings.MERCHANT_ID is None:
            raise ValueError(
                "MERCHANT_ID must be set for payment page hash generation."
            )
        if self.settings.MERCHANT_NAME is None:
            raise ValueError(
                "MERCHANT_NAME must be set for payment page hash generation."
            )
        if self.settings.MERCHANT_TYPE is None:
            raise ValueError(
                "MERCHANT_TYPE must be set for payment page hash generation."
            )
        if self.settings.AZUL_AUTH_KEY is None:
            raise ValueError(
                "AZUL_AUTH_KEY must be set for payment page hash generation."
            )

        # Create the string to hash following Azul's specification
        has_components = [
            self.settings.MERCHANT_ID,
            self.settings.MERCHANT_NAME,
            self.settings.MERCHANT_TYPE,
            payment_request.CurrencyCode,
            payment_request.OrderNumber,
            payment_request.Amount,
            payment_request.ITBIS,
            str(payment_request.ApprovedUrl),
            str(payment_request.DeclineUrl),
            str(payment_request.CancelUrl),
            payment_request.UseCustomField1,
            payment_request.CustomField1Label or "",
            payment_request.CustomField1Value or "",
            payment_request.UseCustomField2,
            payment_request.CustomField2Label or "",
            payment_request.CustomField2Value or "",
        ]

        if payment_request.SaveToDataVault is not None:
            has_components.append(payment_request.SaveToDataVault)

        has_components.append(self.settings.AZUL_AUTH_KEY)
        hash_string = "".join(has_components)

        # Generate HMAC SHA-512 hash
        hmac_obj = hmac.new(
            self.settings.AZUL_AUTH_KEY.encode("utf-8"),
            hash_string.encode("utf-8"),
            hashlib.sha512,
        )
        return hmac_obj.hexdigest()

    def create_payment_form(
        self, payment_request: PaymentPageModel, use_alternate_url: bool = False
    ) -> str:
        """
        Create HTML form for Payment Page redirect.

        Can specify to use the alternate production URL.

        Args:
            payment_request: Payment page request model.
            use_alternate_url (bool): If True and in 'prod' environment,
                                      the form will post to the alternate
                                      payment page URL. Defaults to False.
        Returns:
            str: HTML form ready for automatic submission.
        """
        auth_hash = self._generate_auth_hash(payment_request)

        # Determine the target URL for the form action
        form_action_url = self._get_base_url(use_alternate_url=use_alternate_url)

        form_fields = [
            f'<input type="hidden" id="MerchantId" name="MerchantId" '
            f'value="{self.settings.MERCHANT_ID}" />',
            f'<input type="hidden" id="MerchantName" name="MerchantName" '
            f'value="{self.settings.MERCHANT_NAME}" />',
            f'<input type="hidden" id="MerchantType" name="MerchantType" '
            f'value="{self.settings.MERCHANT_TYPE}" />',
            f'<input type="hidden" id="CurrencyCode" name="CurrencyCode" '
            f'value="{payment_request.CurrencyCode}" />',
            f'<input type="hidden" id="OrderNumber" name="OrderNumber" '
            f'value="{payment_request.OrderNumber}" />',
            f'<input type="hidden" id="Amount" name="Amount" '
            f'value="{payment_request.Amount}" />',
            f'<input type="hidden" id="ITBIS" name="ITBIS" '
            f'value="{payment_request.ITBIS}" />',
            f'<input type="hidden" id="ApprovedUrl" name="ApprovedUrl" '
            f'value="{payment_request.ApprovedUrl}" />',
            f'<input type="hidden" id="DeclinedUrl" name="DeclinedUrl" '
            f'value="{payment_request.DeclineUrl}" />',
            f'<input type="hidden" id="CancelUrl" name="CancelUrl" '
            f'value="{payment_request.CancelUrl}" />',
            f'<input type="hidden" id="UseCustomField1" name="UseCustomField1" '
            f'value="{payment_request.UseCustomField1}" />',
            f'<input type="hidden" id="CustomField1Label" name="CustomField1Label" '
            f'value="{payment_request.CustomField1Label}" />',
            f'<input type="hidden" id="CustomField1Value" name="CustomField1Value" '
            f'value="{payment_request.CustomField1Value}" />',
            f'<input type="hidden" id="UseCustomField2" name="UseCustomField2" '
            f'value="{payment_request.UseCustomField2}" />',
            f'<input type="hidden" id="CustomField2Label" name="CustomField2Label" '
            f'value="{payment_request.CustomField2Label}" />',
            f'<input type="hidden" id="CustomField2Value" name="CustomField2Value" '
            f'value="{payment_request.CustomField2Value}" />',
            f'<input type="hidden" id="ShowTransactionResult" name="ShowTransactionResult" '  # noqa: E501
            f'value="{payment_request.ShowTransactionResult}" />',
            f'<input type="hidden" id="Locale" name="Locale" '
            f'value="{payment_request.Locale}" />',
        ]

        if payment_request.SaveToDataVault is not None:
            form_fields.append(
                f'<input type="hidden" id="SaveToDataVault" name="SaveToDataVault" '
                f'value="{payment_request.SaveToDataVault}"'
                f" />"
            )

        form_fields.append(
            f'<input type="hidden" id="AuthHash" name="AuthHash" value="{auth_hash}" />'
        )

        form = f"""
        <html>
        <head>
        <script>
            window.onload = function() {{
                document.forms[0].submit();
            }}
        </script>
        </head>
        <body>
        <form method="POST" action="{form_action_url}">
            {"".join(form_fields)}
        </form>
        </body>
        </html>
        """
        return form
