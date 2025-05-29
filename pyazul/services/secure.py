"""
Service for handling 3D Secure (3DS) authenticated payments with Azul.

This service manages the 3DS flow, including initiating secure sales/holds,
processing 3DS method notifications, handling challenges, and managing sessions.
"""

import asyncio
import json
import logging
from typing import Any, Dict
from uuid import uuid4

from ..api.client import AzulAPI
from ..core.exceptions import AzulError
from ..models.secure import SecureSaleRequest, SecureTokenSale

logger = logging.getLogger(__name__)


class SecureService:
    """Manages 3D Secure (3DS) payment flows."""

    def __init__(self, api_client: AzulAPI):
        """Initialize the SecureService with an AzulAPI client."""
        self.api = api_client
        self.secure_sessions: Dict[str, Dict[str, Any]] = {}
        self.processed_methods: Dict[str, bool] = {}  # Track processed 3DS methods
        self.transaction_states: Dict[str, str] = {}  # Track transaction states

    async def process_sale(self, request: SecureSaleRequest) -> Dict[str, Any]:
        """Process a secure sale transaction with 3DS authentication."""
        secure_id = str(uuid4())
        logger.debug("=" * 50)
        logger.debug("STARTING SECURE SALE PROCESS - ID: %s", secure_id)
        logger.debug("=" * 50)

        try:
            request_dict = request.model_dump()

            # Ensure URLs have secure_id as query parameter
            term_url = f"{request_dict['threeDSAuth']['TermUrl']}?secure_id={secure_id}"
            method_notification_url = (
                f"{request_dict['threeDSAuth']['MethodNotificationUrl']}"
                f"?secure_id={secure_id}"
            )

            sale_data = {
                "Store": self.api.settings.MERCHANT_ID,
                "Channel": "EC",
                "CardNumber": request_dict["CardNumber"],
                "Expiration": request_dict["Expiration"],
                "CVC": request_dict["CVC"],
                "PosInputMode": "E-Commerce",
                "TrxType": "Sale",
                "AcquirerRefData": request_dict["AcquirerRefData"],
                "Amount": str(request_dict["Amount"]),
                "Itbis": str(request_dict["Itbis"]),
                "OrderNumber": request_dict["OrderNumber"],
                "Currency": "DOP",
                "CustomOrderId": request_dict.get("CustomOrderId", ""),
                "SaveToDataVault": request_dict.get("SaveToDataVault", "0"),
                "ThreeDSAuth": {
                    "TermUrl": term_url,
                    "MethodNotificationUrl": method_notification_url,
                    "RequestChallengeIndicator": request_dict["threeDSAuth"][
                        "RequestChallengeIndicator"
                    ],
                },
                "CardHolderInfo": request_dict["cardHolderInfo"],
                "ForceNo3DS": request_dict["forceNo3DS"],
            }

            # Make the request
            logger.debug("SENDING REQUEST TO AZUL...")
            logger.debug("-" * 50)
            logger.debug(json.dumps(sale_data, indent=2))
            logger.debug("-" * 50)
            # pylint: disable=protected-access
            result = await self.api._async_request(
                data=sale_data,
                is_secure=True,  # Indicate this is a 3DS request
            )

            # Detailed response logging
            logger.debug("AZUL RESPONSE:")
            logger.debug("-" * 50)
            logger.debug(json.dumps(result, indent=2))
            logger.debug("-" * 50)

            # Save session information
            self.secure_sessions[secure_id] = {
                "azul_order_id": result.get("AzulOrderId"),
                "card_number": request_dict["CardNumber"],
                "expiration": request_dict["Expiration"],
                "cvc": request_dict["CVC"],
                "amount": request_dict["Amount"],
                "itbis": request_dict["Itbis"],
                "order_number": request_dict["OrderNumber"],
                "term_url": term_url,  # Store term_url in session
            }
            azul_order_id_for_state = result.get("AzulOrderId")

            response_message = result.get("ResponseMessage", "")

            if response_message == "3D_SECURE_CHALLENGE":
                logger.debug("INITIATING 3D SECURE CHALLENGE!")
                if azul_order_id_for_state:
                    self.transaction_states[azul_order_id_for_state] = (
                        "3D_SECURE_CHALLENGE"
                    )
                return {
                    "redirect": True,
                    "id": secure_id,
                    "html": self._create_challenge_form(
                        result["ThreeDSChallenge"]["CReq"],
                        term_url,
                        result["ThreeDSChallenge"]["RedirectPostUrl"],
                    ),
                    "message": "Starting 3D Secure verification...",
                }
            elif response_message == "3D_SECURE_2_METHOD":
                logger.debug("INITIATING 3D SECURE METHOD!")
                return {
                    "redirect": True,
                    "id": secure_id,
                    "html": result["ThreeDSMethod"]["MethodForm"],
                    "message": "Starting 3D Secure verification...",
                }
            elif response_message == "APROBADA":
                logger.debug("TRANSACTION APPROVED WITHOUT 3DS!")
                return {"redirect": False, "id": secure_id, "value": result}
            else:
                logger.warning("UNEXPECTED RESPONSE! Message: %s", response_message)
                logger.warning("Complete response:")
                logger.debug(json.dumps(result, indent=2))
                return {
                    "redirect": False,
                    "id": secure_id,
                    "value": result,
                    "message": f"Unexpected response: {response_message}",
                }

        except Exception as e:
            logger.error("ERROR IN SALE PROCESS! %s", str(e))
            raise AzulError(f"Error processing secure sale: {str(e)}") from e

    async def process_token_sale(self, request: SecureTokenSale) -> Dict[str, Any]:
        """
        Process a secure token sale transaction with 3DS.

        This method handles tokenized payments that require 3DS authentication,
        including session management and detailed logging.
        """
        secure_id = str(uuid4())
        logger.debug("=" * 50)
        logger.debug("STARTING SECURE TOKEN SALE PROCESS - ID: %s", secure_id)
        logger.debug("=" * 50)

        try:
            request_dict = request.model_dump()

            # Ensure URLs have secure_id as query parameter
            term_url = f"{request_dict['threeDSAuth']['TermUrl']}?secure_id={secure_id}"
            method_notification_url = (
                f"{request_dict['threeDSAuth']['MethodNotificationUrl']}"
                f"?secure_id={secure_id}"
            )

            sale_data = {
                "Store": self.api.settings.MERCHANT_ID,
                "Channel": "EC",
                "DataVaultToken": request_dict["DataVaultToken"],
                "Expiration": "",
                "PosInputMode": "E-Commerce",
                "TrxType": "Sale",
                "AcquirerRefData": request_dict["AcquirerRefData"],
                "Amount": str(request_dict["Amount"]),
                "Itbis": str(request_dict["Itbis"]),
                "OrderNumber": request_dict["OrderNumber"],
                "Currency": "DOP",
                "CustomOrderId": request_dict.get("CustomOrderId", ""),
                "ThreeDSAuth": {
                    "TermUrl": term_url,
                    "MethodNotificationUrl": method_notification_url,
                    "RequestChallengeIndicator": request_dict["threeDSAuth"][
                        "RequestChallengeIndicator"
                    ],
                },
                "CardHolderInfo": request_dict["cardHolderInfo"],
                "ForceNo3DS": request_dict["forceNo3DS"],
            }

            # Make the request
            logger.debug("SENDING REQUEST TO AZUL...")
            logger.debug("-" * 50)
            logger.debug(json.dumps(sale_data, indent=2))
            logger.debug("-" * 50)
            # pylint: disable=protected-access
            result = await self.api._async_request(data=sale_data, is_secure=True)

            # Detailed response logging
            logger.debug("AZUL RESPONSE:")
            logger.debug("-" * 50)
            logger.debug(json.dumps(result, indent=2))
            logger.debug("-" * 50)

            # Save session information
            self.secure_sessions[secure_id] = {
                "azul_order_id": result.get("AzulOrderId"),
                "amount": request_dict["Amount"],
                "itbis": request_dict["Itbis"],
                "order_number": request_dict["OrderNumber"],
                "term_url": term_url,
            }
            azul_order_id_for_state = result.get("AzulOrderId")

            response_message = result.get("ResponseMessage", "")

            if response_message == "3D_SECURE_CHALLENGE":
                logger.debug("INITIATING 3D SECURE CHALLENGE!")
                if azul_order_id_for_state:
                    self.transaction_states[azul_order_id_for_state] = (
                        "3D_SECURE_CHALLENGE"
                    )
                return {
                    "redirect": True,
                    "id": secure_id,
                    "html": self._create_challenge_form(
                        result["ThreeDSChallenge"]["CReq"],
                        term_url,
                        result["ThreeDSChallenge"]["RedirectPostUrl"],
                    ),
                    "message": "Starting 3D Secure verification...",
                }
            elif response_message == "3D_SECURE_2_METHOD":
                logger.debug("INITIATING 3D SECURE METHOD!")
                return {
                    "redirect": True,
                    "id": secure_id,
                    "html": result["ThreeDSMethod"]["MethodForm"],
                    "message": "Starting 3D Secure verification...",
                }
            elif response_message == "APROBADA":
                logger.debug("TRANSACTION APPROVED WITHOUT 3DS!")
                return {"redirect": False, "id": secure_id, "value": result}
            else:
                logger.warning("UNEXPECTED RESPONSE! Message: %s", response_message)
                logger.warning("Complete response:")
                logger.debug(json.dumps(result, indent=2))
                return {
                    "redirect": False,
                    "id": secure_id,
                    "value": result,
                    "message": f"Unexpected response: {response_message}",
                }

        except Exception as e:
            logger.error("ERROR IN SALE PROCESS! %s", str(e))
            raise AzulError(f"Error processing secure sale: {str(e)}") from e

    async def process_hold(self, request: SecureSaleRequest) -> Dict[str, Any]:
        """
        Process a secure hold transaction with 3DS.

        Similar to a secure sale, but performs a pre-authorization (hold)
        on the card, including 3DS authentication steps.
        """
        secure_id = str(uuid4())
        logger.debug("=" * 50)
        logger.debug("STARTING SECURE HOLD PROCESS - ID: %s", secure_id)
        logger.debug("=" * 50)

        try:
            request_dict = request.model_dump()

            # Ensure URLs have secure_id as query parameter
            term_url = f"{request_dict['threeDSAuth']['TermUrl']}?secure_id={secure_id}"
            method_notification_url = (
                f"{request_dict['threeDSAuth']['MethodNotificationUrl']}"
                f"?secure_id={secure_id}"
            )

            hold_data = {
                "Store": self.api.settings.MERCHANT_ID,
                "Channel": "EC",
                "CardNumber": request_dict["CardNumber"],
                "Expiration": request_dict["Expiration"],
                "CVC": request_dict["CVC"],
                "PosInputMode": "E-Commerce",
                "TrxType": "Hold",
                "AcquirerRefData": request_dict["AcquirerRefData"],
                "Amount": str(request_dict["Amount"]),
                "Itbis": str(request_dict["Itbis"]),
                "OrderNumber": request_dict["OrderNumber"],
                "Currency": "DOP",
                "CustomOrderId": request_dict.get("CustomOrderId", ""),
                "SaveToDataVault": request_dict.get("SaveToDataVault", "0"),
                "ThreeDSAuth": {
                    "TermUrl": term_url,
                    "MethodNotificationUrl": method_notification_url,
                    "RequestChallengeIndicator": request_dict["threeDSAuth"][
                        "RequestChallengeIndicator"
                    ],
                },
                "CardHolderInfo": request_dict["cardHolderInfo"],
                "ForceNo3DS": request_dict["forceNo3DS"],
            }

            # Make the request
            logger.debug("SENDING REQUEST TO AZUL...")
            logger.debug("-" * 50)
            logger.debug(json.dumps(hold_data, indent=2))
            logger.debug("-" * 50)
            # pylint: disable=protected-access
            result = await self.api._async_request(
                data=hold_data,
                is_secure=True,  # Indicate this is a 3DS request
            )

            # Detailed response logging
            logger.debug("AZUL RESPONSE:")
            logger.debug("-" * 50)
            logger.debug(json.dumps(result, indent=2))
            logger.debug("-" * 50)

            # Save session information
            self.secure_sessions[secure_id] = {
                "azul_order_id": result.get("AzulOrderId"),
                "card_number": request_dict["CardNumber"],
                "expiration": request_dict["Expiration"],
                "cvc": request_dict["CVC"],
                "amount": request_dict["Amount"],
                "itbis": request_dict["Itbis"],
                "order_number": request_dict["OrderNumber"],
                "term_url": term_url,  # Store term_url in session
            }
            azul_order_id_for_state = result.get("AzulOrderId")

            response_message = result.get("ResponseMessage", "")

            if response_message == "3D_SECURE_CHALLENGE":
                logger.debug("INITIATING 3D SECURE CHALLENGE!")
                if azul_order_id_for_state:
                    self.transaction_states[azul_order_id_for_state] = (
                        "3D_SECURE_CHALLENGE"
                    )
                return {
                    "redirect": True,
                    "id": secure_id,
                    "html": self._create_challenge_form(
                        result["ThreeDSChallenge"]["CReq"],
                        term_url,
                        result["ThreeDSChallenge"]["RedirectPostUrl"],
                    ),
                    "message": "Starting 3D Secure verification...",
                }
            elif response_message == "3D_SECURE_2_METHOD":
                logger.debug("INITIATING 3D SECURE METHOD!")
                return {
                    "redirect": True,
                    "id": secure_id,
                    "html": result["ThreeDSMethod"]["MethodForm"],
                    "message": "Starting 3D Secure verification...",
                }
            elif response_message == "APROBADA":
                logger.debug("TRANSACTION APPROVED WITHOUT 3DS!")
                return {"redirect": False, "id": secure_id, "value": result}
            else:
                logger.warning("UNEXPECTED RESPONSE! Message: %s", response_message)
                logger.warning("Complete response:")
                logger.debug(json.dumps(result, indent=2))
                return {
                    "redirect": False,
                    "id": secure_id,
                    "value": result,
                    "message": f"Unexpected response: {response_message}",
                }

        except Exception as e:
            logger.error("ERROR IN HOLD PROCESS! %s", str(e))
            raise AzulError(f"Error processing secure hold: {str(e)}") from e

    async def process_3ds_method(
        self, azul_order_id: str, method_notification_status: str
    ) -> Dict[str, Any]:
        """
        Process a 3DS method notification from the ACS.

        Marks the method as processed to prevent duplicates and updates
        the transaction state based on the notification.
        """
        # Check if we already processed this order
        if self.processed_methods.get(azul_order_id):
            return {
                "ResponseMessage": "ALREADY_PROCESSED",
                "AzulOrderId": azul_order_id,
            }

        try:
            # Mark as processed before making request
            self.processed_methods[azul_order_id] = True

            # Find the session data for this azul_order_id
            session_data = None
            for _, session in self.secure_sessions.items():
                if session.get("azul_order_id") == azul_order_id:
                    session_data = session
                    break

            if not session_data:
                logger.error(
                    "No session data found for azul_order_id: %s", azul_order_id
                )
                return {
                    "ResponseMessage": "SESSION_NOT_FOUND",
                    "AzulOrderId": azul_order_id,
                }

            data = {
                "Channel": "EC",
                "Store": self.api.settings.MERCHANT_ID,
                "AzulOrderId": azul_order_id,
                "MethodNotificationStatus": method_notification_status,
                # Add required fields that were missing
                "Amount": str(session_data.get("amount", "")),
                "Currency": "DOP",
                "OrderNumber": session_data.get("order_number", ""),
            }

            # Add Itbis if available in session
            if "itbis" in session_data:
                data["Itbis"] = str(session_data["itbis"])

            logger.debug("SENDING REQUEST TO AZUL WITH 3DS METHOD NOTIFICATION...")
            logger.debug("-" * 50)
            logger.debug(json.dumps(data, indent=2))
            logger.debug("-" * 50)

            # pylint: disable=protected-access
            result = await self.api._async_request(
                data, operation="processthreedsmethod", is_secure=True
            )

            # Update transaction state
            if isinstance(result, dict):
                self.transaction_states[azul_order_id] = result.get(
                    "ResponseMessage", "UNKNOWN"
                )

            logger.debug("3DS METHOD NOTIFICATION PROCESS RESULT")
            logger.debug("-" * 50)
            logger.debug(json.dumps(result, indent=2))
            logger.debug("-" * 50)
            return result

        except Exception as e:
            # If error occurs, remove processed mark
            self.processed_methods.pop(azul_order_id, None)
            raise AzulError(
                f"Error processing 3DS method notification: {str(e)}"
            ) from e

    async def process_challenge(self, secure_id: str, cres: str) -> Dict[str, Any]:
        """Process the 3DS challenge response (CRes) from the ACS."""
        session = self.secure_sessions.get(secure_id)
        if not session:
            raise AzulError("Invalid secure session ID")

        azul_order_id = session["azul_order_id"]

        # Check current transaction state
        current_state = self.transaction_states.get(azul_order_id)
        if current_state != "3D_SECURE_CHALLENGE":
            logger.warning("Unexpected state for 3DS challenge: %s", current_state)
            logger.warning("Waiting 2 seconds before continuing...")
            await asyncio.sleep(2)  # Wait a bit before continuing

        data = {
            "Channel": "EC",
            "Store": self.api.settings.MERCHANT_ID,
            "AzulOrderId": azul_order_id,
            "CRes": cres,
        }

        logger.debug("INITIATING 3DS CHALLENGE PROCESS...")
        logger.debug("Session ID: %s", secure_id)
        logger.debug("Order ID: %s", azul_order_id)
        logger.debug("Current state: %s", current_state)
        logger.debug("=" * 50)

        logger.debug("SENDING REQUEST TO AZUL WITH 3DS CHALLENGE NOTIFICATION...")
        logger.debug("-" * 50)
        logger.debug(json.dumps(data, indent=2))
        logger.debug("-" * 50)

        try:
            # pylint: disable=protected-access
            result = await self.api._async_request(
                data, operation="processthreedschallenge", is_secure=True
            )

            # Log the result
            logger.debug("3DS CHALLENGE RESPONSE:")
            logger.debug("-" * 50)
            logger.debug(json.dumps(result, indent=2))
            logger.debug("-" * 50)

            # Check for specific state error
            if isinstance(result, dict) and "ErrorDescription" in result:
                if "Wrong transaction state" in result["ErrorDescription"]:
                    logger.error("Transaction state error:")
                    logger.error(
                        "- Current state: %s", result.get("TransactionState", "Unknown")
                    )
                    logger.error("- Error code: %s", result.get("ErrorCode", "Unknown"))
                    logger.error("- Description: %s", result["ErrorDescription"])

                    # Return a more friendly message
                    result["ErrorDescription"] = (
                        "The transaction could not be completed because it expired or "
                        "was previously processed. Please try the payment again."
                    )

            return result

        except Exception as e:
            logger.error("Error processing 3DS challenge: %s", str(e))
            error_msg = str(e)

            # Improve error message for user
            if "Wrong transaction state" in error_msg:
                error_msg = (
                    "The transaction could not be completed because it expired or "
                    "was previously processed. Please try the payment again."
                )

            raise AzulError(f"Error processing 3DS challenge: {error_msg}") from e

    @staticmethod
    def _create_challenge_form(creq: str, term_url: str, redirect_post_url: str) -> str:
        """Create an HTML form for the 3DS challenge redirect."""
        return (
            f'<form id="form3ds" action="{redirect_post_url}" method="POST" '
            f'style="display: none;">'
            f'    <input type="hidden" name="creq" value="{creq}" />'
            f'    <input type="hidden" name="TermUrl" value="{term_url}" />'
            f"</form>"
        )
