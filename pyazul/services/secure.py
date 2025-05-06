"""
feat(secure): Implement 3DS secure payment service with session management

- Added SecureService for handling 3DS authenticated payments
- Implemented process_sale for initiating secure transactions
- Added support for 3DSMethod and challenge handling
- Improved session and form management with UI feedback
- Implemented tracking system for 3DS methods
- Optimized authentication flow and error handling
- Added detailed logging for debugging
"""

from typing import Dict, Any
from uuid import uuid4
import logging
import json
import asyncio


from ..api.client import AzulAPI
from ..models.secure import SecureSaleRequest
from ..core.exceptions import AzulError
from ..models.secure import SecureTokenSale

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

class SecureService:
    def __init__(self, api_client: AzulAPI):
        self.api_client = api_client
        self.secure_sessions: Dict[str, Dict[str, Any]] = {}
        self.processed_methods: Dict[str, bool] = {}  # Track processed 3DS methods
        self.transaction_states: Dict[str, str] = {}  # Track transaction states
        
    async def process_sale(self, request: SecureSaleRequest) -> Dict[str, Any]:
        secure_id = str(uuid4())
        logger.info("="*50)
        logger.info(f"STARTING SECURE SALE PROCESS - ID: {secure_id}")
        logger.info("="*50)
        
        try:
            request_dict = request.model_dump()
            
            # Ensure URLs have secure_id as query parameter
            term_url = f"{request_dict['threeDSAuth']['TermUrl']}?secure_id={secure_id}"
            method_notification_url = f"{request_dict['threeDSAuth']['MethodNotificationUrl']}?secure_id={secure_id}"
            
            sale_data = {
                "Store": self.api_client.settings.MERCHANT_ID,
                "Channel": "EC",
                "CardNumber": request_dict["CardNumber"],
                "Expiration": request_dict["Expiration"],
                "CVC": request_dict["CVC"],
                "PosInputMode": "E-Commerce",
                "TrxType": "Sale",
                "AcquirerRefData":request_dict['AcquirerRefData'],
                "Amount": str(request_dict["Amount"]),
                "Itbis": str(request_dict["ITBIS"]),
                "OrderNumber": request_dict["OrderNumber"],
                "Currency": "DOP",
                "ThreeDSAuth": {
                    "TermUrl": term_url,
                    "MethodNotificationUrl": method_notification_url,
                    "RequestChallengeIndicator": request_dict["threeDSAuth"]["RequestChallengeIndicator"]
                },
                "CardHolderInfo": request_dict["cardHolderInfo"],
                "ForceNo3DS": request_dict["forceNo3DS"]
            }

            # Make the request
            logger.info("SENDING REQUEST TO AZUL...")
            logger.info("-"*50)
            logger.info(json.dumps(sale_data, indent=2))
            logger.info("-"*50)
            result = await self.api_client._async_request(
                data=sale_data,
                is_secure=True  # Indicate this is a 3DS request
            )
            
            # Detailed response logging
            logger.info("AZUL RESPONSE:")
            logger.info("-"*50)
            logger.info(json.dumps(result, indent=2))
            logger.info("-"*50)
            
            # Save session information
            self.secure_sessions[secure_id] = {
                "azul_order_id": result.get("AzulOrderId"),
                "card_number": request_dict["CardNumber"],
                "expiration": request_dict["Expiration"],
                "cvc": request_dict["CVC"],
                "amount": request_dict["Amount"],
                "itbis": request_dict["ITBIS"],
                "order_number": request_dict["OrderNumber"],
                "term_url": term_url  # Store term_url in session
            }

            response_message = result.get("ResponseMessage", "")
            
            if response_message == "3D_SECURE_CHALLENGE":
                logger.info("INITIATING 3D SECURE CHALLENGE!")
                return {
                    "redirect": True,
                    "id": secure_id,
                    "html": self._create_challenge_form(
                        result["ThreeDSChallenge"]["CReq"],
                        term_url,
                        result["ThreeDSChallenge"]["RedirectPostUrl"]
                    ),
                    "message": "Starting 3D Secure verification..."
                }
            elif response_message == "3D_SECURE_2_METHOD":
                logger.info("INITIATING 3D SECURE METHOD!")
                return {
                    "redirect": True,
                    "id": secure_id,
                    "html": result["ThreeDSMethod"]["MethodForm"],
                    "message": "Starting 3D Secure verification..."
                }
            elif response_message == "APROBADA":
                logger.info("TRANSACTION APPROVED WITHOUT 3DS!")
                return {
                    "redirect": False,
                    "id": secure_id,
                    "value": result
                }
            else:
                logger.warning(f"UNEXPECTED RESPONSE! Message: {response_message}")
                logger.warning("Complete response:")
                logger.warning(json.dumps(result, indent=2))
                return {
                    "redirect": False,
                    "id": secure_id,
                    "value": result,
                    "message": f"Unexpected response: {response_message}"
                }
                
        except Exception as e:
            logger.error(f"ERROR IN SALE PROCESS! {str(e)}")
            raise AzulError(f"Error processing secure sale: {str(e)}")

    async def process_token_sale(self, request: SecureTokenSale) -> Dict[str, Any]:
        """
        Process a secure token sale transaction.
        This method is similar to process_sale but specifically for token sales.
        It includes detailed logging and session management.
        """

        secure_id = str(uuid4())
        logger.info("="*50)
        logger.info(f"STARTING SECURE TOKEN SALE PROCESS - ID: {secure_id}")
        logger.info("="*50)
        
        try:
            request_dict = request.model_dump()
            
            # Ensure URLs have secure_id as query parameter
            term_url = f"{request_dict['threeDSAuth']['TermUrl']}?secure_id={secure_id}"
            method_notification_url = f"{request_dict['threeDSAuth']['MethodNotificationUrl']}?secure_id={secure_id}"
            
            sale_data = {
                "Store": self.api_client.settings.MERCHANT_ID,
                "Channel": "EC",
                "DataVaultToken": request_dict["DataVaultToken"],
                "Expiration": '',
                "PosInputMode": "E-Commerce",
                "TrxType": "Sale",
                "AcquirerRefData": request_dict['AcquirerRefData'],
                "Amount": str(request_dict["Amount"]),
                "Itbis": str(request_dict["ITBIS"]),
                "OrderNumber": request_dict["OrderNumber"],
                "Currency": "DOP", 
                "CustomOrderId": request_dict.get("CustomOrderId", ""),
                "ThreeDSAuth": {
                    "TermUrl": term_url,
                    "MethodNotificationUrl": method_notification_url,
                    "RequestChallengeIndicator": request_dict["threeDSAuth"]["RequestChallengeIndicator"]
                },
                "CardHolderInfo": request_dict["cardHolderInfo"],
                "ForceNo3DS": request_dict["forceNo3DS"]
            }
            
            # Make the request
            logger.info("SENDING REQUEST TO AZUL...")
            logger.info("-"*50)
            logger.info(json.dumps(sale_data, indent=2))
            logger.info("-"*50)
            result = await self.api_client._async_request(
                data=sale_data,
                is_secure=True 
            )
            
            # Detailed response logging
            logger.info("AZUL RESPONSE:")
            logger.info("-"*50)
            logger.info(json.dumps(result, indent=2))
            logger.info("-"*50)
            
            # Save session information
            self.secure_sessions[secure_id] = {
                "azul_order_id": result.get("AzulOrderId"),
                "amount": request_dict["Amount"],
                "itbis": request_dict["ITBIS"],
                "order_number": request_dict["OrderNumber"],
                "term_url": term_url 
            }

            response_message = result.get("ResponseMessage", "")
            
            if response_message == "3D_SECURE_CHALLENGE":
                logger.info("INITIATING 3D SECURE CHALLENGE!")
                return {
                    "redirect": True,
                    "id": secure_id,
                    "html": self._create_challenge_form(
                        result["ThreeDSChallenge"]["CReq"],
                        term_url,
                        result["ThreeDSChallenge"]["RedirectPostUrl"]
                    ),
                    "message": "Starting 3D Secure verification..."
                }
            elif response_message == "3D_SECURE_2_METHOD":
                logger.info("INITIATING 3D SECURE METHOD!")
                return {
                    "redirect": True,
                    "id": secure_id,
                    "html": result["ThreeDSMethod"]["MethodForm"],
                    "message": "Starting 3D Secure verification..."
                }
            elif response_message == "APROBADA":
                logger.info("TRANSACTION APPROVED WITHOUT 3DS!")
                return {
                    "redirect": False,
                    "id": secure_id,
                    "value": result
                }
            else:
                logger.warning(f"UNEXPECTED RESPONSE! Message: {response_message}")
                logger.warning("Complete response:")
                logger.warning(json.dumps(result, indent=2))
                return {
                    "redirect": False,
                    "id": secure_id,
                    "value": result,
                    "message": f"Unexpected response: {response_message}"
                }
                
        except Exception as e:
            logger.error(f"ERROR IN SALE PROCESS! {str(e)}")
            raise AzulError(f"Error processing secure sale: {str(e)}")
    async def process_hold(self, request:SecureSaleRequest) -> Dict[str, Any]:
        """
        Process a secure hold transaction con 3DS.
        This method is similar to process_sale but specifically for hold transactions.
        It includes detailed logging and session management.
        """
        secure_id = str(uuid4())
        logger.info("="*50)
        logger.info(f"STARTING SECURE HOLD PROCESS - ID: {secure_id}")
        logger.info("="*50)
        
        try:
            request_dict = request.model_dump()
            
            # Ensure URLs have secure_id as query parameter
            term_url = f"{request_dict['threeDSAuth']['TermUrl']}?secure_id={secure_id}"
            method_notification_url = f"{request_dict['threeDSAuth']['MethodNotificationUrl']}?secure_id={secure_id}"
            
            hold_data = {
                "Store": self.api_client.settings.MERCHANT_ID,
                "Channel": "EC",
                "CardNumber": request_dict["CardNumber"],
                "Expiration": request_dict["Expiration"],
                "CVC": request_dict["CVC"],
                "PosInputMode": "E-Commerce",
                "TrxType": "Hold",
                "AcquirerRefData":request_dict['AcquirerRefData'],
                "Amount": str(request_dict["Amount"]),
                "Itbis": str(request_dict["ITBIS"]),
                "OrderNumber": request_dict["OrderNumber"],
                "Currency": "DOP",
                "ThreeDSAuth": {
                    "TermUrl": term_url,
                    "MethodNotificationUrl": method_notification_url,
                    "RequestChallengeIndicator": request_dict["threeDSAuth"]["RequestChallengeIndicator"]
                },
                "CardHolderInfo": request_dict["cardHolderInfo"],
                "ForceNo3DS": request_dict["forceNo3DS"]
            }

            # Make the request
            logger.info("SENDING REQUEST TO AZUL...")
            logger.info("-"*50)
            logger.info(json.dumps(hold_data, indent=2))
            logger.info("-"*50)
            result = await self.api_client._async_request(
                data=hold_data,
                is_secure=True  # Indicate this is a 3DS request
            )
            
            # Detailed response logging
            logger.info("AZUL RESPONSE:")
            logger.info("-"*50)
            logger.info(json.dumps(result, indent=2))
            logger.info("-"*50)
            
            # Save session information
            self.secure_sessions[secure_id] = {
                "azul_order_id": result.get("AzulOrderId"),
                "card_number": request_dict["CardNumber"],
                "expiration": request_dict["Expiration"],
                "cvc": request_dict["CVC"],
                "amount": request_dict["Amount"],
                "itbis": request_dict["ITBIS"],
                "order_number": request_dict["OrderNumber"],
                "term_url": term_url  # Store term_url in session
            }

            response_message = result.get("ResponseMessage", "")
            
            if response_message == "3D_SECURE_CHALLENGE":
                logger.info("INITIATING 3D SECURE CHALLENGE!")
                return {
                    "redirect": True,
                    "id": secure_id,
                    "html": self._create_challenge_form(
                        result["ThreeDSChallenge"]["CReq"],
                        term_url,
                        result["ThreeDSChallenge"]["RedirectPostUrl"]
                    ),
                    "message": "Starting 3D Secure verification..."
                }
            elif response_message == "3D_SECURE_2_METHOD":
                logger.info("INITIATING 3D SECURE METHOD!")
                return {
                    "redirect": True,
                    "id": secure_id,
                    "html": result["ThreeDSMethod"]["MethodForm"],
                    "message": "Starting 3D Secure verification..."
                }
            elif response_message == "APROBADA":
                logger.info("TRANSACTION APPROVED WITHOUT 3DS!")
                return {
                    "redirect": False,
                    "id": secure_id,
                    "value": result
                }
            else:
                logger.warning(f"UNEXPECTED RESPONSE! Message: {response_message}")
                logger.warning("Complete response:")
                logger.warning(json.dumps(result, indent=2))
                return {
                    "redirect": False,
                    "id": secure_id,
                    "value": result,
                    "message": f"Unexpected response: {response_message}"
                }
                
        except Exception as e:
            logger.error(f"ERROR IN HOLD PROCESS! {str(e)}")
            raise AzulError(f"Error processing secure hold: {str(e)}")

    async def process_3ds_method(
        self,
        azul_order_id: str,
        method_notification_status: str
    ) -> Dict[str, Any]:
        """
        Process 3DS method notification.
        Implements mechanism to avoid duplicate processing.
        """
        # Check if we already processed this order
        if self.processed_methods.get(azul_order_id):
            return {
                "ResponseMessage": "ALREADY_PROCESSED",
                "AzulOrderId": azul_order_id
            }
            
        try:
            # Mark as processed before making request
            self.processed_methods[azul_order_id] = True
            data = {
                "Channel": "EC",
                "Store": self.api_client.settings.MERCHANT_ID,
                "AzulOrderId": azul_order_id,
                "MethodNotificationStatus": method_notification_status
            }

            logger.info("SENDING REQUEST TO AZUL WITH 3DS METHOD NOTIFICATION...")
            logger.info("-"*50)
            logger.info(json.dumps(data, indent=2))
            logger.info("-"*50)
            
            result = await self.api_client._async_request(
                data,
                operation="processthreedsmethod"
            )
            
            # Update transaction state
            if isinstance(result, dict):
                self.transaction_states[azul_order_id] = result.get("ResponseMessage", "UNKNOWN")
                
            logger.info("3DS METHOD NOTIFICATION PROCESS RESULT")
            logger.info("-"*50)
            logger.info(json.dumps(result, indent=2))
            logger.info("-"*50)
            return result
            
        except Exception as e:
            # If error occurs, remove processed mark
            self.processed_methods.pop(azul_order_id, None)
            raise AzulError(f"Error processing 3DS method notification: {str(e)}")

    async def process_challenge(
        self,
        secure_id: str,
        cres: str
    ) -> Dict[str, Any]:
        session = self.secure_sessions.get(secure_id)
        if not session:
            raise AzulError("Invalid secure session ID")
            
        azul_order_id = session["azul_order_id"]
        
        # Check current transaction state
        current_state = self.transaction_states.get(azul_order_id)
        if current_state != "3D_SECURE_CHALLENGE":
            logger.warning(f"Unexpected state for 3DS challenge: {current_state}")
            logger.warning("Waiting 2 seconds before continuing...")
            await asyncio.sleep(2)  # Wait a bit before continuing
            
        data = {
            "Channel": "EC",
            "Store": self.api_client.settings.MERCHANT_ID,
            "AzulOrderId": azul_order_id,
            "CRes": cres
        }
        
        logger.info("INITIATING 3DS CHALLENGE PROCESS...")
        logger.info("="*50)
        logger.info(f"Session ID: {secure_id}")
        logger.info(f"Order ID: {azul_order_id}")
        logger.info(f"Current state: {current_state}")
        logger.info("="*50)
        
        logger.info("SENDING REQUEST TO AZUL WITH 3DS CHALLENGE NOTIFICATION...")
        logger.info("-"*50)
        logger.info(json.dumps(data, indent=2))
        logger.info("-"*50)
        
        try:
            result = await self.api_client._async_request(
                data,
                operation="processthreedschallenge",
                is_secure=True  
            )
            
            # Log the result
            logger.info("3DS CHALLENGE RESPONSE:")
            logger.info("-"*50)
            logger.info(json.dumps(result, indent=2))
            logger.info("-"*50)
            
            # Check for specific state error
            if isinstance(result, dict) and "ErrorDescription" in result:
                if "Wrong transaction state" in result["ErrorDescription"]:
                    logger.error("Transaction state error:")
                    logger.error(f"- Current state: {result.get('TransactionState', 'Unknown')}")
                    logger.error(f"- Error code: {result.get('ErrorCode', 'Unknown')}")
                    logger.error(f"- Description: {result['ErrorDescription']}")
                    
                    # Return a more friendly message
                    result["ErrorDescription"] = (
                        "The transaction could not be completed because it expired or was previously processed. "
                        "Please try the payment again."
                    )
            
            return result
                
        except Exception as e:
            logger.error(f"Error processing 3DS challenge: {str(e)}")
            error_msg = str(e)
            
            # Improve error message for user
            if "Wrong transaction state" in error_msg:
                error_msg = (
                    "The transaction could not be completed because it expired or was previously processed. "
                    "Please try the payment again."
                )
            
            raise AzulError(f"Error processing 3DS challenge: {error_msg}")

    @staticmethod
    def _create_challenge_form(creq: str, term_url: str, redirect_post_url: str) -> str:
        """
        Create HTML form for 3DS challenge with visual feedback of the result.
        """
        return f"""
                <form id="form3ds" action="{redirect_post_url}" method="POST" style="display: none;">
                    <input type="hidden" name="creq" value="{creq}" />
                    <input type="hidden" name="TermUrl" value="{term_url}" />
                </form>
        """