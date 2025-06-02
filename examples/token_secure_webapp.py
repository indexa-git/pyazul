"""
Mini FastAPI app for demonstrating token payments and 3DS flow with PyAzul.

This application showcases:
1. Creating a token from a test card.
2. Using the token for a 3DS-authenticated payment.
3. Handling the complete 3DS flow (method and challenge).
"""

import json
import logging
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

import uvicorn
from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates

from pyazul import PyAzul
from pyazul.core.exceptions import AzulError

# Import models using new clean names
from pyazul.models import CardHolderInfo, ChallengeRequest, SessionID

# Configure logging
# logging.basicConfig(
#     level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
# )
logger = logging.getLogger(__name__)

# Initialize FastAPI application
app = FastAPI(title="Azul Token Secure WebApp Demo")

# Construct an absolute path to the templates directory
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATES_DIR = os.path.join(SCRIPT_DIR, "templates")
templates = Jinja2Templates(directory=TEMPLATES_DIR)

# Initialize PyAzul Facade
azul = PyAzul()
settings = azul.settings

# Test cards for 3DS
TEST_CARDS: List[Dict[str, Any]] = [
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
# Application-level session store for 3DS flow
app_3ds_session_store: Dict[str, Dict[str, Any]] = {}


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

        # Create the token using PyAzul facade
        create_token_payload = {
            "Channel": "EC",
            "Store": settings.MERCHANT_ID,  # Use settings for Store ID
            "TrxType": "CREATE",
            "CardNumber": card["number"],
            "Expiration": card["expiration"],
            # CVC is optional for token creation via DataVaultRequestModel
        }
        response = await azul.create_token(create_token_payload)

        logger.info(f"Token Creation Response: {json.dumps(response)}")

        if (
            not isinstance(response, dict)
            or response.get("ResponseMessage") != "Approved"
        ):
            error_message = (
                response.get(
                    "ErrorDescription", response.get("ResponseMessage", "Unknown error")
                )
                if isinstance(response, dict)
                else "Invalid response format"
            )
            return JSONResponse(
                status_code=400,
                content={"error": f"Error creating token: {error_message}"},
            )

        token_id: Optional[Any] = response.get("DataVaultToken")
        if not token_id or not isinstance(token_id, str):
            logger.error("Invalid token_id received from DataVault")
            return JSONResponse(
                status_code=500,
                content={"error": "Failed to retrieve a valid token ID"},
            )

        token_data: Dict[str, Any] = {
            "token": token_id,
            "expiration": card["expiration"],
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
        order_number = f"TOKSEC-{datetime.now().strftime('%Y%m%d%H%M%S%f')}"
        base_url = str(request.base_url).rstrip("/")

        cardholder_info_dict = CardHolderInfo(
            Email="test@example.com",
            Name="TEST USER TOKEN",
        ).model_dump()

        three_ds_auth_dict = {
            "TermUrl": f"{base_url}/post-3ds",
            "MethodNotificationUrl": f"{base_url}/capture-3ds-method",
            "RequestChallengeIndicator": challenge_indicator
            or card_data.get("challenge_indicator", "03"),
        }

        sale_data_dict: Dict[str, Any] = {
            "Store": settings.MERCHANT_ID,  # Added Store
            "OrderNumber": order_number,  # Added OrderNumber
            "DataVaultToken": token_id,
            "Amount": int(amount * 100),
            "Itbis": int(itbis * 100),
            "TrxType": "Sale",  # SecureTokenSale model requires this
            "AcquirerRefData": "1",  # Required by SecureTokenSale or its base
            "ForceNo3DS": card_data.get("force_no_3ds", "0"),  # PascalCase update
            "Channel": "EC",
            "PosInputMode": "E-Commerce",
            "CardHolderInfo": cardholder_info_dict,  # PascalCase update
            "ThreeDSAuth": three_ds_auth_dict,  # PascalCase update
        }

        logger.info(f"Processing secure token sale: {token_id}, Order: {order_number}")
        # SecureTokenSale model is handled by azul.secure_token_sale
        response = await azul.secure_token_sale(sale_data_dict)

        logger.info(f"Secure Token Sale Initial Response: {json.dumps(response)}")

        secure_id = response.get("id") if isinstance(response, dict) else None
        if secure_id:
            app_3ds_session_store[secure_id] = {
                "original_term_url": three_ds_auth_dict["TermUrl"],
                "azul_order_id": None,  # Initialize as None
                "app_order_number": order_number,
            }
            value_dict = response.get("value") if isinstance(response, dict) else None
            if isinstance(value_dict, dict):
                app_3ds_session_store[secure_id]["azul_order_id"] = value_dict.get(
                    "AzulOrderId"
                )

            if not app_3ds_session_store[secure_id]["azul_order_id"]:
                pyazul_session = await azul.get_session_info(secure_id)
                if isinstance(pyazul_session, dict):
                    retrieved_azul_order_id = pyazul_session.get("azul_order_id")
                    if isinstance(retrieved_azul_order_id, str):
                        app_3ds_session_store[secure_id][
                            "azul_order_id"
                        ] = retrieved_azul_order_id
                        logger.info(f"Retrieved AzulOrderId for {secure_id}")
                    elif retrieved_azul_order_id is not None:
                        logger.warning(
                            f"AzulOrderId for {secure_id} not str: "
                            f"{type(retrieved_azul_order_id)}"
                        )
                elif pyazul_session is not None:
                    logger.warning(
                        f"pyazul_session for {secure_id} not dict: "
                        f"{type(pyazul_session)}"
                    )

        return response

    except AzulError as e:
        logger.error(f"Azul error processing payment: {str(e)}")
        return JSONResponse(status_code=400, content={"error": str(e)})
    except Exception as e:
        logger.error(f"Unexpected error processing payment: {str(e)}")
        return JSONResponse(status_code=500, content={"error": "Internal server error"})


@app.post("/capture-3ds-method")
async def capture_3ds_method_route(request: Request, data: SessionID):
    """
    Handle 3DS method notification.

    This endpoint receives the response from the ACS after the 3DS method completes.
    """
    # Extract data from request body
    azul_order_id = data.AzulOrderId
    method_status = data.MethodNotificationStatus

    if not azul_order_id or not method_status:
        return JSONResponse(
            status_code=400,
            content={"error": "No AzulOrderId or MethodNotificationStatus provided."},
        )

    logger.info(f"3DS method notification received for order: {azul_order_id}")

    try:
        app_data = app_3ds_session_store.get(azul_order_id)
        if not isinstance(app_data, dict):
            logger.error(
                f"App 3DS session data not found or invalid for "
                f"AzulOrderId: {azul_order_id}"
            )
            return JSONResponse(
                status_code=400, content={"error": "Invalid or expired 3DS session."}
            )

        original_term_url = app_data.get("original_term_url")

        if not original_term_url:
            pyazul_session_data = await azul.get_session_info(azul_order_id)
            if isinstance(pyazul_session_data, dict):
                retrieved_original_term_url = pyazul_session_data.get(
                    "original_term_url"
                )
                if isinstance(retrieved_original_term_url, str):
                    original_term_url = retrieved_original_term_url
                    app_data["original_term_url"] = original_term_url
                    logger.info(
                        f"Retrieved original_term_url {original_term_url} for {azul_order_id} (3DS method)."  # noqa: E501
                    )
                elif retrieved_original_term_url is not None:
                    logger.warning(
                        f"original_term_url for {azul_order_id} not str: "
                        f"{type(retrieved_original_term_url)}"
                    )
            elif pyazul_session_data is not None:
                logger.warning(f"pyazul_session for {azul_order_id} not dict")

        assert isinstance(
            azul_order_id, str
        ), f"AzulOrderId ({azul_order_id}) non-str for {azul_order_id}."
        assert isinstance(
            original_term_url, str
        ), f"original_term_url non-str for {azul_order_id}."

        logger.info(f"Processing 3DS method for order: {azul_order_id}")
        result = await azul.process_3ds_method(azul_order_id, method_status)
        logger.info(f"3DS Method result: {json.dumps(result)}")

        if (
            isinstance(result, dict)
            and result.get("ResponseMessage") == "ALREADY_PROCESSED"
        ):
            return {"status": "ok", "message": "Already processed"}

        if (
            isinstance(result, dict)
            and result.get("ResponseMessage") == "3D_SECURE_CHALLENGE"
        ):
            logger.info("Additional 3DS challenge required")
            challenge_data = result.get("ThreeDSChallenge")
            if not isinstance(challenge_data, dict):
                logger.error("ThreeDSChallenge missing in response")
                return JSONResponse(
                    status_code=500,
                    content={"error": "Invalid 3DS challenge data from API"},
                )

            creq = challenge_data.get("CReq")
            redirect_post_url = challenge_data.get("RedirectPostUrl")
            if not isinstance(creq, str) or not isinstance(redirect_post_url, str):
                logger.error(
                    "CReq or RedirectPostUrl missing/malformed in challenge data."
                )
                return JSONResponse(
                    status_code=500,
                    content={"error": "Invalid 3DS challenge parameters from API"},
                )

            return {
                "redirect": True,
                "html": azul.create_challenge_form(
                    creq, original_term_url, redirect_post_url
                ),
            }

        return result  # For other cases like APROBADA directly after method

    except AzulError as e:
        logger.error(f"Azul error processing 3DS method: {str(e)}")
        return JSONResponse(status_code=400, content={"error": str(e)})
    except Exception as e:
        logger.error(f"Unexpected error processing 3DS method: {str(e)}")
        return JSONResponse(status_code=500, content={"error": "Internal server error"})


@app.post("/post-3ds")
async def post_3ds(request: Request, data: ChallengeRequest):
    """
    Handle the 3DS challenge response.

    This endpoint receives the CRes from the ACS after cardholder authentication.
    """
    azul_order_id = data.AzulOrderId
    cres = data.CRes

    if not azul_order_id or not cres:
        return JSONResponse(
            status_code=400,
            content={"error": "Missing AzulOrderId or CRes in challenge response."},
        )

    logger.info(f"3DS challenge response received for order: {azul_order_id}")

    try:
        result = await azul.process_challenge(
            session_id=azul_order_id, challenge_response=cres
        )
        logger.info(f"Challenge result: {json.dumps(result)}")

        # Clean up app 3DS session store
        if azul_order_id in app_3ds_session_store:
            del app_3ds_session_store[azul_order_id]

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
