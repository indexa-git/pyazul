"""
Mini FastAPI app for demonstrating token payments and 3DS flow with PyAzul.

This application showcases:
1. Creating a token from a test card.
2. Using the token for a 3DS-authenticated payment.
3. Handling the complete 3DS flow (method and challenge).
"""

import json
import logging
from datetime import datetime
from typing import Any, Dict, Optional

import uvicorn
from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates

from pyazul.api.client import AzulAPI
from pyazul.core.config import AzulSettings, get_azul_settings
from pyazul.core.exceptions import AzulError
from pyazul.models import (
    CardHolderInfo,
    DataVaultCreateModel,
    SecureChallengeRequest,
    SecureSessionID,
    SecureTokenSale,
)
from pyazul.services.datavault import DataVaultService
from pyazul.services.secure import SecureService

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Initialize FastAPI application
app = FastAPI(title="Azul Token Payment Demo")
templates = Jinja2Templates(directory="templates")

# Initialize shared services (singleton)
settings: AzulSettings = get_azul_settings()
api_client: AzulAPI = AzulAPI(settings=settings)
secure_service: SecureService = SecureService(api_client=api_client)
datavault_service: DataVaultService = DataVaultService(api_client=api_client)

# Test cards for 3DS
TEST_CARDS = [
    {
        "number": "4265880000000007",
        "label": "Frictionless with 3DSMethod",
        "expiration": "202812",
        "cvv": "123",
        "force_no_3ds": "0",
        "challenge_indicator": "02",  # NO_CHALLENGE - Frictionless
    },
    {
        "number": "4147463011110117",
        "label": "Frictionless without 3DSMethod",
        "expiration": "202812",
        "cvv": "123",
        "force_no_3ds": "1",
        "challenge_indicator": "02",  # NO_CHALLENGE - Frictionless
    },
    {
        "number": "4005520000000129",
        "label": "Challenge with 3DSMethod (Limit RD$ 50)",
        "expiration": "202812",
        "cvv": "123",
        "force_no_3ds": "0",
        "challenge_indicator": "03",  # CHALLENGE
        "max_amount": 50,
    },
    {
        "number": "4147463011110059",
        "label": "Challenge without 3DSMethod",
        "expiration": "202812",
        "cvv": "123",
        "force_no_3ds": "0",
        "challenge_indicator": "03",  # CHALLENGE
    },
]

# Token storage (in-memory for this demo)
token_storage: Dict[str, Dict[str, Any]] = {}


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Serve the main page with a payment form."""
    return templates.TemplateResponse(
        "token_index.html", {"request": request, "cards": TEST_CARDS}
    )


@app.post("/create-token")
async def create_token(
    request: Request,
    card_number: str = Form(...),
    amount: float = Form(...),
    itbis: float = Form(...),
):
    """Create a token from card details."""
    try:
        # Find the selected card
        card = next((c for c in TEST_CARDS if c["number"] == card_number), None)
        if not card:
            return JSONResponse(status_code=400, content={"error": "Invalid card"})

        # Prepare data to create the token
        datavault_data = {
            "Channel": "EC",
            "PosInputMode": "E-Commerce",
            "Amount": str(int(amount * 100)),  # Convert to cents
            "Itbis": str(int(itbis * 100)),  # Convert to cents
            "CardNumber": card["number"],
            "Expiration": card["expiration"],
            "CustomOrderId": f"web-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "store": settings.MERCHANT_ID,
        }

        # Create the token - use the global service
        payment = DataVaultCreateModel(**datavault_data)
        response: Dict[str, Any] = await datavault_service.create(payment)

        logger.info(f"Token Creation Response: {json.dumps(response)}")

        if (
            not isinstance(response, dict)
            or response.get("ResponseMessage") != "Approved"
        ):
            error_message = (
                response.get("ResponseMessage", "Unknown error")
                if isinstance(response, dict)
                else "Invalid response format"
            )
            return JSONResponse(
                status_code=400,
                content={"error": f"Error creating token: {error_message}"},
            )

        # Save token data
        token_id: Optional[Any] = response.get("DataVaultToken")
        if not token_id or not isinstance(token_id, str):
            logger.error("Invalid token_id received from DataVault")
            return JSONResponse(
                status_code=500,
                content={"error": "Failed to retrieve a valid token ID"},
            )

        token_data: Dict[str, Any] = {
            "token": token_id,
            "expiration": datavault_data["Expiration"],
            "brand": response.get("Brand", ""),
            "masked_card": response.get("CardNumber", ""),
            "has_cvv": response.get("HasCVV", False),
            "card_data": card,
            "created_at": datetime.now().isoformat(),
        }

        # Save in temporary storage
        token_storage[token_id] = token_data

        # Return token data
        return {
            "token_id": token_id,
            "masked_card": response.get("CardNumber", ""),
            "brand": response.get("Brand", ""),
            "message": "Token created successfully",
        }

    except AzulError as e:
        logger.error(f"Azul error creating token: {str(e)}")
        return JSONResponse(status_code=400, content={"error": str(e)})
    except Exception as e:
        logger.error(f"Unexpected error creating token: {str(e)}")
        return JSONResponse(status_code=500, content={"error": "Internal server error"})


@app.post("/process-token-payment")
async def process_token_payment(
    request: Request,
    token_id: str = Form(...),
    amount: float = Form(...),
    itbis: float = Form(...),
    challenge_indicator: Optional[str] = Form("03"),
):
    """Process a payment using an existing token with 3DS."""
    try:
        # Verify that the token exists
        if token_id not in token_storage:
            return JSONResponse(
                status_code=400, content={"error": "Invalid or expired token"}
            )

        # Get token data
        token_data = token_storage[token_id]
        card_data = token_data.get("card_data", {})
        if not isinstance(card_data, dict):
            card_data = {}

        # Generate a unique order number
        order_number = f"TOKEN-{datetime.now().strftime('%Y%m%d%H%M%S%f')}"

        # Base URL for 3DS callbacks
        base_url = str(request.base_url).rstrip("/")

        # Create cardholder data
        cardholder_info = CardHolderInfo(
            BillingAddressCity="Santo Domingo",
            BillingAddressCountry="DO",
            BillingAddressLine1="Av. Winston Churchill",
            BillingAddressState="Distrito Nacional",
            BillingAddressZip="10148",
            Email="test@example.com",
            Name="TEST USER",
            ShippingAddressCity="Santo Domingo",
            ShippingAddressCountry="DO",
            ShippingAddressLine1="Av. Winston Churchill",
            ShippingAddressState="Distrito Nacional",
            ShippingAddressZip="10148",
        )

        # Create data for the sale
        sale_data_dict: Dict[str, Any] = {
            "DataVaultToken": token_id,
            "Expiration": "",
            "Amount": int(amount * 100),
            "ITBIS": int(itbis * 100),
            "OrderNumber": order_number,
            "TrxType": "Sale",
            "AcquirerRefData": "1",
            "forceNo3DS": card_data.get("force_no_3ds", "0"),
            "Channel": "EC",
            "PosInputMode": "E-Commerce",
            "cardHolderInfo": cardholder_info.model_dump(),
            "threeDSAuth": {
                "TermUrl": f"{base_url}/post-3ds",
                "MethodNotificationUrl": f"{base_url}/capture-3ds-method",
                "RequestChallengeIndicator": challenge_indicator
                or card_data.get("challenge_indicator", "03"),
            },
        }

        logger.info(f"Processing token sale: {token_id}, Order: {order_number}")
        data = SecureTokenSale(**sale_data_dict)

        logger.info(
            f"Secure sessions before call: {list(secure_service.secure_sessions.keys())}"  # noqa: E501
        )
        response = await secure_service.process_token_sale(data)
        logger.info(
            f"Secure sessions after call: {list(secure_service.secure_sessions.keys())}"
        )

        if isinstance(response, dict) and "id" in response and response.get("id"):
            session_id_from_response = response["id"]
            logger.info(f"Response includes session ID: {session_id_from_response}")
            session_exists = session_id_from_response in secure_service.secure_sessions
            logger.info(f"Session exists in secure_sessions: {session_exists}")
            if session_exists:
                session_info = secure_service.secure_sessions[session_id_from_response]
                logger.info(
                    f"Session info: azul_order_id={session_info.get('azul_order_id')}"
                )

        logger.info(f"Token Sale Response: {json.dumps(response)}")
        return response

    except AzulError as e:
        logger.error(f"Azul error processing payment: {str(e)}")
        return JSONResponse(status_code=400, content={"error": str(e)})
    except Exception as e:
        logger.error(f"Unexpected error processing payment: {str(e)}")
        return JSONResponse(status_code=500, content={"error": "Internal server error"})


@app.post("/capture-3ds-method")
async def capture_3ds_method_route(request: Request, data: SecureSessionID):
    """
    Handle 3DS method notification.

    This endpoint receives the response from the ACS after the 3DS method completes.
    """
    session_id = data.session_id

    if not session_id:
        return JSONResponse(
            status_code=400,
            content={"error": "No session identifier provided"},
        )

    logger.info(f"3DS method notification received for session: {session_id}")
    logger.info(
        f"Active secure sessions: {list(secure_service.secure_sessions.keys())}"
    )

    try:
        session = secure_service.secure_sessions.get(session_id)
        if not session or not isinstance(session, dict):
            logger.error(f"Session not found or invalid: {session_id}")
            return JSONResponse(status_code=400, content={"error": "Invalid session"})

        azul_order_id = session.get("azul_order_id", "")
        if not azul_order_id or not isinstance(azul_order_id, str):
            logger.error(f"Azul Order ID not found/invalid in session: {session_id}")
            return JSONResponse(
                status_code=500,
                content={
                    "error": "Internal error: Missing/invalid order ID in session"
                },
            )

        logger.info(f"Processing 3DS method for order: {azul_order_id}")
        result = await secure_service.process_3ds_method(azul_order_id, "RECEIVED")
        logger.info(f"3DS Method result: {json.dumps(result)}")

        if (
            isinstance(result, dict)
            and result.get("ResponseMessage") == "ALREADY_PROCESSED"
        ):
            return {"status": "ok"}

        if (
            isinstance(result, dict)
            and result.get("ResponseMessage") == "3D_SECURE_CHALLENGE"
        ):
            logger.info("Additional 3DS challenge required")
            challenge_data = result.get("ThreeDSChallenge")
            term_url = session.get("term_url")

            if (
                not isinstance(challenge_data, dict)
                or not term_url
                or not isinstance(term_url, str)
            ):
                logger.error(
                    "3DS Challenge data or TermUrl missing/malformed in response/session."  # noqa: E501
                )
                return JSONResponse(
                    status_code=500,
                    content={"error": "Error processing 3DS challenge data"},
                )

            creq = challenge_data.get("CReq", "")
            redirect_post_url = challenge_data.get("RedirectPostUrl", "")

            if not isinstance(creq, str) or not isinstance(redirect_post_url, str):
                logger.error(
                    "CReq or RedirectPostUrl missing/malformed in challenge data."
                )
                return JSONResponse(
                    status_code=500,
                    content={"error": "Error processing 3DS challenge parameters"},
                )

            return {
                "redirect": True,
                "html": secure_service._create_challenge_form(
                    creq, term_url, redirect_post_url
                ),
            }

        return result

    except AzulError as e:
        logger.error(f"Azul error processing 3DS method: {str(e)}")
        return JSONResponse(status_code=400, content={"error": str(e)})
    except Exception as e:
        logger.error(f"Unexpected error processing 3DS method: {str(e)}")
        return JSONResponse(status_code=500, content={"error": "Internal server error"})


@app.post("/post-3ds")
async def post_3ds(request: Request, data: SecureChallengeRequest):
    """
    Handle the 3DS challenge response.

    This endpoint receives the CRes from the ACS after cardholder authentication.
    """
    session_id = data.session_id
    cres = data.cres

    if not session_id or not cres:
        missing_fields = []
        if not session_id:
            missing_fields.append("session_id")
        if not cres:
            missing_fields.append("cres")
        return JSONResponse(
            status_code=400,
            content={"error": f"Missing required fields: {', '.join(missing_fields)}"},
        )

    try:
        logger.info(f"Processing 3DS challenge for session: {session_id}")
        result = await secure_service.process_challenge(session_id, cres)
        logger.info(f"Challenge result: {json.dumps(result)}")

        return templates.TemplateResponse(
            "result.html", {"request": request, "result": result}
        )
    except AzulError as e:
        logger.error(f"Azul error processing challenge: {str(e)}")
        return templates.TemplateResponse(
            "error.html", {"request": request, "error": str(e)}
        )
    except Exception as e:
        logger.error(f"Unexpected error processing challenge: {str(e)}")
        return templates.TemplateResponse(
            "error.html",
            {
                "request": request,
                "error": "Unexpected error processing authentication",
            },
        )


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
