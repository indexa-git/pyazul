"""
3D Secure service for PyAzul.

This module provides services for managing 3D Secure authentication flows,
including cardholder verification, challenge handling, and secure transactions.
"""

import logging
import uuid
from typing import Any, Dict, Optional, Union

from ..api.client import AzulAPI
from ..core.config import AzulSettings
from ..core.exceptions import AzulError
from ..models.three_ds import SecureSale, SecureTokenSale

_logger = logging.getLogger(__name__)


class SecureService:
    """Service for managing 3D Secure authentication and transactions."""

    def __init__(
        self,
        client: AzulAPI,
        settings: AzulSettings,
        session_store: Optional[Dict] = None,
    ):
        """Initialize the 3D Secure service with API client and settings."""
        self.client = client
        self.settings = settings
        self.session_store = session_store or {}
        # Track processed methods to prevent duplicate processing
        self.processed_methods: Dict[str, bool] = {}

    def _generate_secure_id(self) -> str:
        """Generate a unique secure session ID."""
        return str(uuid.uuid4())

    @staticmethod
    def _create_challenge_form(creq: str, term_url: str, redirect_post_url: str) -> str:
        """Create an HTML form for the 3DS challenge redirect."""
        return (
            f'<form id="form3ds" action="{redirect_post_url}" method="POST" '
            f'style="display: none;">'
            f'    <input type="hidden" name="creq" value="{creq}" />'
            f'    <input type="hidden" name="TermUrl" value="{term_url}" />'
            f"</form>"
            f"<script>document.getElementById('form3ds').submit();</script>"
        )

    def create_challenge_form(
        self, redirect_post_url: str, creq: str, term_url: str
    ) -> str:
        """Create an HTML form for the 3DS challenge redirect."""
        return self._create_challenge_form(creq, term_url, redirect_post_url)

    def _check_3ds_method_required(self, response: Dict[str, Any]) -> bool:
        """Check if 3DS Method is required based on response."""
        return (
            response.get("IsoCode") == "3D2METHOD"
            and response.get("ResponseMessage") == "3D_SECURE_2_METHOD"
            and "ThreeDSMethod" in response
            and response.get("ThreeDSMethod", {}).get("MethodForm")
        )

    def _check_3ds_challenge_required(self, response: Dict[str, Any]) -> bool:
        """Check if 3DS Challenge is required based on response."""
        return (
            response.get("IsoCode") == "3D"
            and response.get("ResponseMessage") == "3D_SECURE_CHALLENGE"
            and "ThreeDSChallenge" in response
        )

    def _process_3ds_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """Process 3DS response and add redirect/html fields if needed."""
        # Check for 3DS Method requirement
        if self._check_3ds_method_required(response):
            method_form = response["ThreeDSMethod"]["MethodForm"]
            response.update(
                {
                    "redirect": True,
                    "method_form": method_form,
                    "html": method_form,
                    "message": "3DS Method required",
                }
            )
            return response

        # Check for 3DS Challenge requirement
        if self._check_3ds_challenge_required(response):
            challenge_data = response["ThreeDSChallenge"]
            creq = challenge_data.get("CReq")
            redirect_url = challenge_data.get("RedirectPostUrl")

            if creq and redirect_url:
                challenge_html = self._create_challenge_form(creq, "", redirect_url)
                response.update(
                    {
                        "redirect": True,
                        "html": challenge_html,
                        "challenge_html": challenge_html,
                        "challenge_required": True,
                        "message": "3DS Challenge required",
                    }
                )

        return response

    def _get_transaction_status(
        self, response: Dict[str, Any]
    ) -> tuple[str, Optional[str]]:
        """Extract transaction status and error description from response."""
        response_msg = response.get("ResponseMessage", "")
        iso_code = response.get("IsoCode", "")
        error_description = response.get("ErrorDescription", "")

        # Direct status mapping
        status_map = {
            ("APROBADA", "00"): "approved",
            ("ALREADY_PROCESSED", ""): "processing",
        }

        status = status_map.get((response_msg, iso_code))
        if status:
            return status, error_description or None

        # Handle declined/error cases
        if response_msg in ["DENEGADA", "DECLINED"] or (
            response_msg == "ERROR" and iso_code == "99"
        ):
            return "declined", error_description or None

        # Build composite status for unknown cases
        if error_description and response_msg:
            status = f"{response_msg}: {error_description}"
        elif error_description:
            status = error_description
        elif response_msg:
            status = response_msg
        else:
            status = "unknown"

        return status, error_description or None

    def _store_session_data(self, secure_id: str, data: Dict[str, Any]) -> None:
        """Store session data for a secure transaction."""
        self.session_store[secure_id] = data

    def get_session_info(self, secure_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve information about an active 3DS session.

        Args:
            secure_id: The secure session ID

        Returns:
            Session data dictionary or None if session not found
        """
        return self.session_store.get(secure_id)

    def _prepare_secure_request_data(
        self,
        request: Union[SecureSale, SecureTokenSale],
        secure_id: str,
        transaction_type: str = "Sale",
    ) -> tuple[Dict[str, Any], str]:
        """Prepare request data for secure transactions."""
        # Modify URLs to include secure_id parameter
        term_url = f"{request.ThreeDSAuth.TermUrl}?secure_id={secure_id}"
        method_notification_url = (
            f"{request.ThreeDSAuth.MethodNotificationUrl}?secure_id={secure_id}"
        )

        # Update the request URLs with secure_id
        request.ThreeDSAuth.TermUrl = term_url
        request.ThreeDSAuth.MethodNotificationUrl = method_notification_url

        # Use clean model serialization
        request_data = request.model_dump(exclude_none=True)
        request_data["Currency"] = "DOP"  # Required by Azul API

        # Override transaction type if needed
        if transaction_type != "Sale":
            request_data["TrxType"] = transaction_type

        return request_data, term_url

    def _create_session_data(
        self,
        response: Dict[str, Any],
        request: Union[SecureSale, SecureTokenSale],
        term_url: str,
        transaction_type: str = "sale",
    ) -> Dict[str, Any]:
        """Create session data for storing transaction information."""
        session_data = {
            "azul_order_id": response.get("AzulOrderId"),
            "amount": request.Amount,
            "itbis": request.Itbis,
            "order_number": request.OrderNumber,
            "term_url": term_url,
            "status": "processing",
        }

        # Add card details for hold/token transactions
        if transaction_type in ["hold", "token"]:
            session_data.update(
                {
                    "card_number": request.CardNumber,
                    "expiration": request.Expiration,
                    "cvc": request.CVC,
                }
            )

        # Store 3DS forms if available
        if response.get("method_form"):
            session_data.update(
                {"method_form": response["method_form"], "method_required": True}
            )

        if response.get("challenge_html"):
            session_data.update(
                {
                    "challenge_html": response["challenge_html"],
                    "challenge_required": True,
                }
            )

        return session_data

    def _update_session_with_result(
        self, secure_id: str, result: Dict[str, Any], is_final: bool = False
    ) -> str:
        """Update session data with transaction result and return status."""
        status, error_description = self._get_transaction_status(result)

        session_data = self.get_session_info(secure_id)
        if session_data:
            session_data.update({"status": status, "final_result": result})
            if error_description:
                session_data["error_description"] = error_description
            self._store_session_data(secure_id, session_data)

        # Clean up completed transactions
        if is_final and status in ["approved", "declined"]:
            self._cleanup_session(secure_id)

        return status

    def _cleanup_session(self, secure_id: str) -> None:
        """Clean up session data after transaction completion."""
        try:
            if secure_id in self.session_store:
                del self.session_store[secure_id]
                _logger.debug(f"Cleaned up session data for secure_id: {secure_id}")
        except Exception as e:
            _logger.warning(f"Failed to cleanup session {secure_id}: {e}")

    async def _process_secure_transaction(
        self,
        request: Union[SecureSale, SecureTokenSale],
        transaction_type: str,
        transaction_name: str,
    ) -> Dict[str, Any]:
        """Process any type of secure transaction with common logic."""
        try:
            secure_id = self._generate_secure_id()
            request_data, term_url = self._prepare_secure_request_data(
                request, secure_id, transaction_type
            )

            response = await self.client._async_request(
                data=request_data, is_secure=True
            )

            # Add secure_id to response first
            response["id"] = secure_id

            # Process 3DS response to add redirect/html fields if needed
            response = self._process_3ds_response(response)

            # Create and store session data after 3DS processing
            session_data = self._create_session_data(
                response, request, term_url, transaction_type
            )
            self._store_session_data(secure_id, session_data)

            return response

        except Exception as e:
            _logger.error(f"3D Secure {transaction_name} transaction failed: {e}")
            raise AzulError(
                f"3D Secure {transaction_name} transaction failed: {e}"
            ) from e

    async def process_sale(self, request: SecureSale) -> Dict[str, Any]:
        """Process a 3D Secure sale transaction."""
        return await self._process_secure_transaction(request, "Sale", "sale")

    async def process_token_sale(self, request: SecureTokenSale) -> Dict[str, Any]:
        """Process a 3D Secure token sale transaction."""
        return await self._process_secure_transaction(request, "Sale", "token sale")

    async def process_hold(self, request: SecureSale) -> Dict[str, Any]:
        """Process a 3D Secure hold transaction."""
        return await self._process_secure_transaction(request, "Hold", "hold")

    async def process_3ds_method(
        self, azul_order_id: str, method_notification_status: str
    ) -> Dict[str, Any]:
        """Process 3DS method notification."""
        try:
            # Check if already processed
            if self.processed_methods.get(azul_order_id):
                return {
                    "ResponseMessage": "ALREADY_PROCESSED",
                    "AzulOrderId": azul_order_id,
                }

            # Mark as processed
            self.processed_methods[azul_order_id] = True

            # Find session data for this azul_order_id
            session_data = next(
                (
                    session
                    for session in self.session_store.values()
                    if session.get("azul_order_id") == azul_order_id
                ),
                None,
            )

            if not session_data:
                return {
                    "ResponseMessage": "SESSION_NOT_FOUND",
                    "AzulOrderId": azul_order_id,
                }

            # Build request data
            data = {
                "Channel": "EC",
                "Store": self.settings.MERCHANT_ID,
                "AzulOrderId": azul_order_id,
                "MethodNotificationStatus": method_notification_status,
                "Amount": str(session_data.get("amount", "")),
                "Currency": "DOP",
                "OrderNumber": session_data.get("order_number", ""),
            }

            if "itbis" in session_data:
                data["Itbis"] = str(session_data["itbis"])

            response = await self.client._async_request(
                data, operation="processthreedsmethod", is_secure=True
            )

            return response

        except Exception as e:
            # Remove processed mark on error
            self.processed_methods.pop(azul_order_id, None)
            _logger.error(f"3DS method processing failed: {e}")
            raise AzulError(f"3DS method processing failed: {e}") from e

    async def process_challenge(
        self, session_id: str, challenge_response: str
    ) -> Dict[str, Any]:
        """Process 3DS challenge response."""
        try:
            session_data = self.get_session_info(session_id)
            if not session_data:
                raise AzulError(f"No session data found for session_id: {session_id}")

            azul_order_id = session_data.get("azul_order_id")
            if not azul_order_id:
                raise AzulError("No AzulOrderId found in session data")

            data = {
                "Channel": "EC",
                "Store": self.settings.MERCHANT_ID,
                "AzulOrderId": azul_order_id,
                "CRes": challenge_response,
            }

            response = await self.client._async_request(
                data, operation="processthreedschallenge", is_secure=True
            )

            return response

        except Exception as e:
            _logger.error(f"3DS challenge processing failed: {e}")
            raise AzulError(f"3DS challenge processing failed: {e}") from e

    async def handle_3ds_callback(
        self,
        secure_id: str,
        callback_data: Dict[str, Any],
        form_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Handle 3DS callbacks - automatically detects and routes to handler."""
        try:
            # Auto-detect callback type based on form data
            if "threeDSMethodData" in form_data:
                return await self._handle_method_notification(secure_id)
            elif "CRes" in form_data or "cres" in form_data:
                cres = form_data.get("CRes") or form_data.get("cres")
                if not cres:
                    raise AzulError("No challenge response found in form data")
                return await self._handle_challenge_response(secure_id, cres)
            else:
                return await self._handle_return_redirect(secure_id)

        except Exception as e:
            _logger.error(f"3DS callback processing failed: {e}")
            raise AzulError(f"3DS callback processing failed: {e}") from e

    async def _handle_method_notification(self, secure_id: str) -> Dict[str, Any]:
        """Handle 3DS method notification callback."""
        session_data = self.get_session_info(secure_id)
        if not session_data:
            raise AzulError(f"No session data found for secure_id: {secure_id}")

        # Clear method form flags and update status
        session_data.pop("method_required", None)
        session_data.pop("method_form", None)
        session_data["status"] = "method_processed"
        self._store_session_data(secure_id, session_data)

        azul_order_id = session_data.get("azul_order_id")
        if not azul_order_id:
            raise AzulError("No AzulOrderId found in session data")

        result = await self.process_3ds_method(azul_order_id, "RECEIVED")

        # Check if challenge is required after method processing
        if self._check_3ds_challenge_required(result):
            challenge_data = result.get("ThreeDSChallenge", {})
            creq = challenge_data.get("CReq")
            redirect_url = challenge_data.get("RedirectPostUrl")

            if creq and redirect_url:
                term_url = session_data.get("term_url", "")
                challenge_html = self._create_challenge_form(
                    creq, term_url, redirect_url
                )

                # Update session with challenge info
                session_data.update(
                    {
                        "challenge_html": challenge_html,
                        "challenge_required": True,
                        "status": "challenge_required",
                    }
                )
                self._store_session_data(secure_id, session_data)

                return {
                    "completed": False,
                    "requires_redirect": False,
                    "AzulOrderId": result.get("AzulOrderId"),
                    "status": "challenge_stored",
                    "message": "Challenge data stored for frontend retrieval",
                }

        # Update session with final result
        status = self._update_session_with_result(secure_id, result)

        return {
            "completed": status != "processing",
            "requires_redirect": False,
            "AzulOrderId": result.get("AzulOrderId"),
            "status": status,
            "result": result,
        }

    async def _handle_challenge_response(
        self, secure_id: str, cres: str
    ) -> Dict[str, Any]:
        """Handle 3DS challenge response callback."""
        result = await self.process_challenge(secure_id, cres)

        # Update session with final result
        status = self._update_session_with_result(secure_id, result, is_final=True)

        return {
            "completed": True,
            "requires_redirect": False,
            "AzulOrderId": result.get("AzulOrderId"),
            "status": status,
            "result": result,
        }

    async def _handle_return_redirect(self, secure_id: str) -> Dict[str, Any]:
        """Handle return redirect without specific form data."""
        session_data = self.get_session_info(secure_id)
        if not session_data:
            raise AzulError(f"No session data found for secure_id: {secure_id}")

        azul_order_id = session_data.get("azul_order_id")
        if not azul_order_id:
            raise AzulError("No AzulOrderId found for verification")

        return {
            "completed": False,
            "requires_redirect": False,
            "AzulOrderId": azul_order_id,
            "status": "verification_needed",
            "message": "Manual verification required",
        }
