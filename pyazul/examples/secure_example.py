"""
feat(example): Implement 3DS payment demo with complete flow

- Created FastAPI application for 3DS payment demonstration
- Added test cards with different configurations
- Implemented endpoints for payment processing
- Added custom error handling and user feedback
- Implemented complete 3DS flow with method and challenge support
- Improved session handling with secure_id
- Added visual feedback system for transaction states
"""

import logging
import uvicorn

from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from typing import Optional
from datetime import datetime

from pyazul.api.client import AzulAPI
from pyazul.services.secure import SecureService
from pyazul.models.secure import SecureSaleRequest, ThreeDSAuth, CardHolderInfo
from pyazul.core.exceptions import AzulError

app = FastAPI()
templates = Jinja2Templates(directory="templates")

logger = logging.getLogger(__name__)

api_client = AzulAPI()
secure_service = SecureService(api_client)

TEST_CARDS = [
    {
        "number": "4265880000000007",
        "label": "Frictionless with 3DSMethod",
        "expiration": "202812",
        "cvv": "123",
        "force_no_3ds": "0",
        "challenge_indicator": "02"  # NO_CHALLENGE - Frictionless
    },
    {
        "number": "4147463011110117",
        "label": "Frictionless without 3DSMethod",
        "expiration": "202812",
        "cvv": "123",
        "force_no_3ds": "1",
        "challenge_indicator": "02"  # NO_CHALLENGE - Frictionless
    },
    {
        "number": "4005520000000129",
        "label": "Challenge with 3DSMethod (Limit RD$ 50)",
        "expiration": "202812",
        "cvv": "123",
        "force_no_3ds": "0",
        "challenge_indicator": "03",  # CHALLENGE
        "max_amount": 50
    },
    {
        "number": "4147463011110059",
        "label": "Challenge without 3DSMethod",
        "expiration": "202812",
        "cvv": "123",
        "force_no_3ds": "0",
        "challenge_indicator": "03"  # CHALLENGE
    }
]

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Render the payment form."""
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "cards": TEST_CARDS,
        }
    )

@app.get("/result", response_class=HTMLResponse)
async def result_page(request: Request, order_id: str):
    """Render the result page."""
    return templates.TemplateResponse(
        "result.html",
        {
            "request": request,
            "result": {"AzulOrderId": order_id}
        }
    )

@app.post("/process-payment")
async def process_payment(
    request: Request,
    card_number: str = Form(...),
    amount: float = Form(...),
    itbis: float = Form(...)
):
    """Process a secure payment with 3D Secure authentication."""
    
    card = next((c for c in TEST_CARDS if c["number"] == card_number), None)
    if not card:
        logger.error(f"Invalid card: {card_number}")
        return templates.TemplateResponse(
            "error.html",
            {
                "request": request,
                "error": "Invalid card. Please select a valid test card."
            }
        )

    try:
        base_url = str(request.base_url).rstrip('/')
        
        sale_request = SecureSaleRequest(
            Amount=int(amount * 100),
            ITBIS=int(itbis * 100),
            CardNumber=card["number"],
            CVC=card["cvv"],
            Expiration=card["expiration"],
            OrderNumber=datetime.now().strftime("%Y%m%d%H%M%S"),
            Channel="EC",
            PosInputMode="E-Commerce",
            forceNo3DS=card["force_no_3ds"],
            cardHolderInfo=CardHolderInfo(
                BillingAddressCity="Santo Domingo",
                BillingAddressCountry="DO",
                BillingAddressLine1="Main Street #123",
                BillingAddressState="National District",
                BillingAddressZip="10101",
                Email="test@example.com",
                Name="Test User",
                ShippingAddressCity="Santo Domingo",
                ShippingAddressCountry="DO",
                ShippingAddressLine1="Main Street #123",
                ShippingAddressState="National District",
                ShippingAddressZip="10101"
            ),
            threeDSAuth=ThreeDSAuth(
                TermUrl=f"{base_url}/post-3ds",
                MethodNotificationUrl=f"{base_url}/capture-3ds",
                RequestChallengeIndicator=card["challenge_indicator"]
            )
        )

        logger.info("Processing sale...")
        result = await secure_service.process_sale(sale_request)
        logger.info("Sale processed")
        return result
        
    except AzulError as e:
        logger.error(f"Error in payment process: {str(e)}")
        error_message = str(e)
        if "BIN NOT FOUND" in error_message:
            error_message = "The card used is not registered in the test environment. Please use one of the provided test cards."
        return templates.TemplateResponse(
            "error.html",
            {
                "request": request,
                "error": error_message
            }
        )
    except Exception as e:
        logger.error(f"Error in payment process: {str(e)}")
        return templates.TemplateResponse(
            "error.html",
            {
                "request": request,
                "error": "Unexpected error processing payment. Please try again."
            }
        )

@app.post('/process-hold')
async def process_hold(
    request: Request,
    card_number: str = Form(...),
    amount: float = Form(...),
    itbis: float = Form(...)
):
    """Process a secure payment with 3D Secure authentication."""
    
    card = next((c for c in TEST_CARDS if c["number"] == card_number), None)
    if not card:
        logger.error(f"Invalid card: {card_number}")
        return templates.TemplateResponse(
            "error.html",
            {
                "request": request,
                "error": "Invalid card. Please select a valid test card."
            }
        )

    try:
        base_url = str(request.base_url).rstrip('/')
        # AcquirerRefData
        
        hold_request = SecureSaleRequest(
            Amount=int(amount * 100),
            ITBIS=int(itbis * 100),
            CardNumber=card["number"],
            CVC=card["cvv"],
            Expiration=card["expiration"],
            OrderNumber=datetime.now().strftime("%Y%m%d%H%M%S"),
            Channel="EC",
            PosInputMode="E-Commerce",
            forceNo3DS=card["force_no_3ds"],
            cardHolderInfo=CardHolderInfo(
                BillingAddressCity="Santo Domingo",
                BillingAddressCountry="DO",
                BillingAddressLine1="Main Street #123",
                BillingAddressState="National District",
                BillingAddressZip="10101",
                Email="test@example.com",
                Name="Test User",
                ShippingAddressCity="Santo Domingo",
                ShippingAddressCountry="DO",
                ShippingAddressLine1="Main Street #123",
                ShippingAddressState="National District",
                ShippingAddressZip="10101"
            ),
            threeDSAuth=ThreeDSAuth(
                TermUrl=f"{base_url}/post-3ds",
                MethodNotificationUrl=f"{base_url}/capture-3ds",
                RequestChallengeIndicator=card["challenge_indicator"]
            )
        )

        logger.info("Processing hold...")
        result = await secure_service.process_hold(hold_request)
        logger.info("HOLD processed")
        return result
        
    except AzulError as e:
        logger.error(f"Error in payment process: {str(e)}")
        error_message = str(e)
        if "BIN NOT FOUND" in error_message:
            error_message = "The card used is not registered in the test environment. Please use one of the provided test cards."
        return templates.TemplateResponse(
            "error.html",
            {
                "request": request,
                "error": error_message
            }
        )
    except Exception as e:
        logger.error(f"Error in payment process: {str(e)}")
        return templates.TemplateResponse(
            "error.html",
            {
                "request": request,
                "error": "Unexpected error processing payment. Please try again."
            }
        )




@app.post("/capture-3ds")
async def capture_3ds(
    request: Request,
    secure_id: Optional[str] = None,
    sid: Optional[str] = None
):
    """
    Handle 3DS method notification.
    
    This endpoint receives the response from the ACS (Access Control Server)
    after the 3DS method has been completed.
    """
    # Use the first available ID
    session_id = secure_id or sid
    
    if not session_id:
        return {"error": "No session identifier provided"}

    logger.info(f"Received 3DS notification for session: {session_id}")

    try:
        # Get the session
        session = secure_service.secure_sessions.get(session_id)
        if not session:
            logger.error(f"Session not found: {session_id}")
            return templates.TemplateResponse(
                "error.html",
                {
                    "request": request,
                    "error": "Invalid session"
                }
            )

        # Process 3DS method
        try:
            result = await secure_service.process_3ds_method(
                session["azul_order_id"],
                "RECEIVED"  # 3DS method completed
            )
        except AzulError as e:
            logger.error(f"Error in 3DS process: {str(e)}")
            error_message = str(e)
            if "BIN NOT FOUND" in error_message:
                error_message = "The card used is not registered in the test environment. Please use one of the provided test cards."
            return templates.TemplateResponse(
                "error.html",
                {
                    "request": request,
                    "error": error_message
                }
            )

        # If transaction was already processed, return OK
        if result.get("ResponseMessage") == "ALREADY_PROCESSED":
            return {"status": "ok"}
        
        # Check if additional challenge is required
        if result.get("ResponseMessage") == "3D_SECURE_CHALLENGE":
            logger.info("Additional 3DS challenge required")
            return {
                "redirect": True,
                "html": secure_service._create_challenge_form(
                    result["ThreeDSChallenge"]["CReq"],
                    session["term_url"],
                    result["ThreeDSChallenge"]["RedirectPostUrl"]
                )
            }
            
        return result

    except Exception as e:
        logger.error(f"Error processing 3DS method: {str(e)}")
        return templates.TemplateResponse(
            "error.html",
            {
                "request": request,
                "error": "Error processing 3DS authentication. Please try again."
            }
        )

@app.post("/post-3ds")
async def post_3ds(
    request: Request,
    secure_id: Optional[str] = None,
    sid: Optional[str] = None,
    cres: Optional[str] = Form(None)
):
    """
    Handle 3DS challenge response.
    
    This endpoint receives the challenge response from the ACS
    after the cardholder completes the authentication.
    """
    session_id = secure_id or sid
    
    if not session_id:
        return templates.TemplateResponse(
            "error.html",
            {
                "request": request,
                "error": "No session identifier provided"
            }
        )
        
    if not cres:
        return templates.TemplateResponse(
            "error.html",
            {
                "request": request,
                "error": "No challenge response provided"
            }
        )

    try:
        result = await secure_service.process_challenge(session_id, cres)
        return templates.TemplateResponse(
            "result.html",
            {
                "request": request,
                "result": result
            }
        )
    except AzulError as e:
        logger.error(f"Error processing challenge: {str(e)}")
        return templates.TemplateResponse(
            "error.html",
            {
                "request": request,
                "error": str(e)
            }
        )
    except Exception as e:
        logger.error(f"Unexpected error processing challenge: {str(e)}")
        return templates.TemplateResponse(
            "error.html",
            {
                "request": request,
                "error": "Unexpected error processing authentication. Please try again."
            }
        )

if __name__ == "__main__":
    uvicorn.run(app, port=8000)