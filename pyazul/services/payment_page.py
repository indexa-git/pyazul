import hmac
import hashlib
from dataclasses import dataclass
from pyazul.models.schemas import PaymentPageModel
from pyazul.core.config import get_azul_settings
from pyazul.api.constants import Environment, AzulEndpoints

"""
Azul Payment Page Service Module

This module provides the service layer for interacting with Azul's Payment Page.
It handles:
- Payment form generation
- Authentication hash calculation
- Environment-specific configurations
- Form field formatting and validation

The payment page allows secure card processing by redirecting users to Azul's hosted payment form.
"""


@dataclass
class AzulPageConfig:
    """
    Configuration for Azul Payment Page.
    
    Attributes:
        merchant_id: Merchant identifier provided by Azul
        merchant_name: Merchant name to display on payment page
        merchant_type: Type of merchant (provided by Azul)
        auth_key: Authentication key for hash generation
        enviroment: Current environment (dev/prod)
    """
    merchant_id: str
    merchant_name: str
    merchant_type: str
    auth_key: str
    enviroment: str


class PaymentPageService:
    """
    Service for handling Azul Payment Page Operations.
    
    This service provides methods to:
    1. Generate secure payment forms
    2. Calculate authentication hashes
    3. Handle environment-specific URLs
    
    Usage example:
        service = PaymentPageService(settings)
        form = service.create_payment_form(payment_request)
    """

    def __init__(self, settings: get_azul_settings):
        """
        Initialize PaymentPage Service.
        
        Args:
            settings: Azul configuration settings
        """
        self.config = AzulPageConfig(
            merchant_id=settings.AZUL_MERCHANT_ID,
            merchant_name=settings.MERCHANT_NAME,
            merchant_type=settings.MERCHANT_TYPE,
            auth_key=settings.AZUL_AUTH_KEY,
            enviroment=settings.ENVIRONMENT
        )

        self.azul_url = self._get_base_url()

    def _get_base_url(self) -> str:
        """
        Get the base URL for Payment Page based on environment.
        
        Returns:
            str: Base URL for the payment page
        """
        if self.config.enviroment == Environment.DEV:
            return AzulEndpoints.DEV_URL_PAYMEMT
        return AzulEndpoints.PROD_URL_PAYMEMT

    def _generate_auth_hash(self, payment_request: PaymentPageModel) -> str:
        """
        Generate authentication hash for the payment request.
        
        The hash is calculated using HMAC-SHA512 with the following components:
        - Merchant ID
        - Merchant Name
        - Merchant Type
        - Currency Code
        - Order Number
        - Amount
        - ITBIS
        - URLs (Approved, Decline, Cancel)
        - Custom Fields
        - Auth Key
        
        Args:
            payment_request: Payment page request model
            
        Returns: 
            str: Generated hash for authentication
        """
        # Create the string to hash following Azul's specification
        has_components = [
            self.config.merchant_id,
            self.config.merchant_name,
            self.config.merchant_type,
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

        # Only include SaveToDataVault if it's not None
        if payment_request.SaveToDataVault is not None:
            has_components.append(payment_request.SaveToDataVault)

        has_components.append(self.config.auth_key)
        hash_string = "".join(has_components)

        # Generate HMAC SHA-512 hash
        hmac_obj = hmac.new(
            self.config.auth_key.encode('utf-8'),
            hash_string.encode('utf-8'),
            hashlib.sha512
        )
        return hmac_obj.hexdigest()

    def create_payment_form(self, payment_request: PaymentPageModel) -> str:
        """
        Create HTML form for Payment Page redirect.
        
        This method:
        1. Generates an authentication hash
        2. Creates a hidden form with all required fields
        3. Adds auto-submit JavaScript
        
        The generated form will automatically redirect the user to Azul's
        payment page when loaded.
        
        Args:
            payment_request: Payment page request model
            
        Returns:
            str: HTML form ready for automatic submission
            
        Example form fields:
            - MerchantId
            - MerchantName
            - MerchantType
            - CurrencyCode
            - OrderNumber
            - Amount
            - ITBIS
            - URLs (Approved, Declined, Cancel)
            - Custom Fields
            - AuthHash
        """
        # Generate authentication hash
        auth_hash = self._generate_auth_hash(payment_request)

        # Create the HTML form with base fields
        form_fields = [
            f'<input type="hidden" id="MerchantId" name="MerchantId" value="{self.config.merchant_id}" />',
            f'<input type="hidden" id="MerchantName" name="MerchantName" value="{self.config.merchant_name}" />',
            f'<input type="hidden" id="MerchantType" name="MerchantType" value="{self.config.merchant_type}" />',
            f'<input type="hidden" id="CurrencyCode" name="CurrencyCode" value="{payment_request.CurrencyCode}" />',
            f'<input type="hidden" id="OrderNumber" name="OrderNumber" value="{payment_request.OrderNumber}" />',
            f'<input type="hidden" id="Amount" name="Amount" value="{payment_request.Amount}" />',
            f'<input type="hidden" id="ITBIS" name="ITBIS" value="{payment_request.ITBIS}" />',
            f'<input type="hidden" id="ApprovedUrl" name="ApprovedUrl" value="{payment_request.ApprovedUrl}" />',
            f'<input type="hidden" id="DeclinedUrl" name="DeclinedUrl" value="{payment_request.DeclineUrl}" />',
            f'<input type="hidden" id="CancelUrl" name="CancelUrl" value="{payment_request.CancelUrl}" />',
            f'<input type="hidden" id="UseCustomField1" name="UseCustomField1" value="{payment_request.UseCustomField1}" />',
            f'<input type="hidden" id="CustomField1Label" name="CustomField1Label" value="{payment_request.CustomField1Label}" />',
            f'<input type="hidden" id="CustomField1Value" name="CustomField1Value" value="{payment_request.CustomField1Value}" />',
            f'<input type="hidden" id="UseCustomField2" name="UseCustomField2" value="{payment_request.UseCustomField2}" />',
            f'<input type="hidden" id="CustomField2Label" name="CustomField2Label" value="{payment_request.CustomField2Label}" />',
            f'<input type="hidden" id="CustomField2Value" name="CustomField2Value" value="{payment_request.CustomField2Value}" />',
            f'<input type="hidden" id="ShowTransactionResult" name="ShowTransactionResult" value="{payment_request.ShowTransactionResult}" />',
            f'<input type="hidden" id="Locale" name="Locale" value="{payment_request.Locale}" />'
        ]

        # Only include SaveToDataVault if present
        if payment_request.SaveToDataVault is not None:
            form_fields.append(
                f'<input type="hidden" id="SaveToDataVault" name="SaveToDataVault" value="{payment_request.SaveToDataVault}" />')

        # Add authentication hash
        form_fields.append(
            f'<input type="hidden" id="AuthHash" name="AuthHash" value="{auth_hash}" />')

        # Create complete HTML form with auto-submit
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
        <form method="POST" action="{self.azul_url}">
            {"".join(form_fields)}
        </form>
        </body>
        </html>
        """
        return form
