"""
Example demonstrating the 3D Secure payment flow with PyAzul using FastAPI.

This example includes:
- A FastAPI application to simulate a merchant's backend.
- Test card data for different 3DS scenarios (frictionless, challenge).
- Endpoints to initiate payments (/process-payment, /process-hold).
- Callbacks for 3DS method notification (/capture-3ds) and challenge completion
(/post-3ds).
- Basic HTML templates for user interaction and displaying results/errors.
- Session handling using the `secure_id` provided by the library.
"""

import logging
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

import uvicorn
from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from pyazul import PyAzul
from pyazul.core.exceptions import AzulError
from pyazul.models.secure import CardHolderInfo, ThreeDSAuth

app = FastAPI()

# Construct an absolute path to the templates directory
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATES_DIR = os.path.join(SCRIPT_DIR, "templates")
templates = Jinja2Templates(directory=TEMPLATES_DIR)

logger = logging.getLogger(__name__)

# Initialize PyAzul Facade
azul = PyAzul()
settings = azul.settings

# Application-level session store (replace with a persistent store in production)
# This store will link secure_id to necessary application data for callbacks.
app_session_store: Dict[str, Dict[str, Any]] = {}

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


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Render the payment form."""
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "cards": TEST_CARDS,
        },
    )


@app.get("/result", response_class=HTMLResponse)
async def result_page(request: Request, order_id: str):
    """Render the result page."""
    return templates.TemplateResponse(
        "result.html", {"request": request, "result": {"AzulOrderId": order_id}}
    )


@app.post("/process-payment")
async def process_payment(
    request: Request,
    card_number: str = Form(...),
    amount: float = Form(...),
    itbis: float = Form(...),
):
    """Process a secure payment with 3D Secure authentication."""
    card = next((c for c in TEST_CARDS if c["number"] == card_number), None)
    if not card:
        logger.error(f"Invalid card: {card_number}")
        return templates.TemplateResponse(
            "error.html",
            {
                "request": request,
                "error": "Invalid card. Please select a valid test card.",
            },
        )

    try:
        base_url = str(request.base_url).rstrip("/")
        order_number = datetime.now().strftime("%Y%m%d%H%M%S%f")

        sale_request_data = {
            "Store": settings.MERCHANT_ID,
            "OrderNumber": order_number,
            "Amount": int(amount * 100),
            "Itbis": int(itbis * 100),
            "CardNumber": card["number"],
            "CVC": card["cvv"],
            "Expiration": card["expiration"],
            "Channel": "EC",
            "PosInputMode": "E-Commerce",
            "AcquirerRefData": "1",
            "CustomOrderId": f"custom-{order_number}",
            "SaveToDataVault": "0",
            "forceNo3DS": card["force_no_3ds"],
            "cardHolderInfo": CardHolderInfo(
                BillingAddressCity="Santo Domingo",
                BillingAddressCountry="DO",
                BillingAddressLine1="Main Street #123",
                BillingAddressLine2=None,
                BillingAddressLine3=None,
                BillingAddressState="National District",
                BillingAddressZip="10101",
                Email="test@example.com",
                Name="Test User",
                PhoneHome=None,
                PhoneMobile=None,
                PhoneWork=None,
                ShippingAddressCity="Santo Domingo",
                ShippingAddressCountry="DO",
                ShippingAddressLine1="Main Street #123",
                ShippingAddressLine2=None,
                ShippingAddressLine3=None,
                ShippingAddressState="National District",
                ShippingAddressZip="10101",
            ).model_dump(),
            "threeDSAuth": ThreeDSAuth(
                TermUrl=f"{base_url}/post-3ds",
                MethodNotificationUrl=f"{base_url}/capture-3ds-method",
                RequestChallengeIndicator=card["challenge_indicator"],
            ).model_dump(),
        }

        logger.info(f"Processing secure sale for order: {order_number}")
        result = await azul.secure_sale(sale_request_data)
        logger.info(f"Initial secure_sale response: {result}")

        secure_id = result.get("id") if isinstance(result, dict) else None
        if secure_id:
            app_session_store[secure_id] = {
                "original_term_url": sale_request_data["threeDSAuth"]["TermUrl"],
                "azul_order_id": None,
                "app_order_number": order_number,
            }
            value_dict = result.get("value") if isinstance(result, dict) else None
            if isinstance(value_dict, dict):
                app_session_store[secure_id]["azul_order_id"] = value_dict.get(
                    "AzulOrderId"
                )

            if not app_session_store[secure_id]["azul_order_id"]:
                pyazul_session = await azul.get_secure_session_info(secure_id)
                if isinstance(pyazul_session, dict):
                    retrieved_azul_order_id = pyazul_session.get("azul_order_id")
                    if isinstance(retrieved_azul_order_id, str):
                        app_session_store[secure_id][
                            "azul_order_id"
                        ] = retrieved_azul_order_id
                        logger.info(f"Retrieved AzulId for {secure_id}")
                    elif retrieved_azul_order_id is not None:
                        logger.warning(
                            f"AzulId for {secure_id} not str: {type(retrieved_azul_order_id)}"  # noqa: E501
                        )
                elif pyazul_session is not None:
                    logger.warning(f"pyazul_session for {secure_id} not dict")

        return result

    except AzulError as e:
        logger.error(f"Error in payment process: {str(e)}")
        error_message = str(e)
        if "BIN NOT FOUND" in error_message:
            error_message = (
                "The card used is not registered in the test environment. "
                "Please use one of the provided test cards."
            )
        return templates.TemplateResponse(
            "error.html", {"request": request, "error": error_message}
        )
    except Exception as e:
        logger.error(f"Error in payment process: {str(e)}")
        return templates.TemplateResponse(
            "error.html",
            {
                "request": request,
                "error": "Unexpected error processing payment. Please try again.",
            },
        )


@app.post("/process-hold")
async def process_hold(
    request: Request,
    card_number: str = Form(...),
    amount: float = Form(...),
    itbis: float = Form(...),
):
    """Process a secure payment with 3D Secure authentication."""
    card = next((c for c in TEST_CARDS if c["number"] == card_number), None)
    if not card:
        logger.error(f"Invalid card: {card_number}")
        return templates.TemplateResponse(
            "error.html",
            {
                "request": request,
                "error": "Invalid card. Please select a valid test card.",
            },
        )

    try:
        base_url = str(request.base_url).rstrip("/")
        order_number = datetime.now().strftime("%Y%m%d%H%M%S%f")

        hold_request_data = {
            "Store": settings.MERCHANT_ID,
            "OrderNumber": order_number,
            "Amount": int(amount * 100),
            "Itbis": int(itbis * 100),
            "CardNumber": card["number"],
            "CVC": card["cvv"],
            "Expiration": card["expiration"],
            "Channel": "EC",
            "PosInputMode": "E-Commerce",
            "AcquirerRefData": "1",
            "CustomOrderId": f"custom-{order_number}",
            "SaveToDataVault": "0",
            "forceNo3DS": card["force_no_3ds"],
            "cardHolderInfo": CardHolderInfo(
                BillingAddressCity="Santo Domingo",
                BillingAddressCountry="DO",
                BillingAddressLine1="Main Street #123",
                BillingAddressLine2=None,
                BillingAddressLine3=None,
                BillingAddressState="National District",
                BillingAddressZip="10101",
                Email="test@example.com",
                Name="Test User",
                PhoneHome=None,
                PhoneMobile=None,
                PhoneWork=None,
                ShippingAddressCity="Santo Domingo",
                ShippingAddressCountry="DO",
                ShippingAddressLine1="Main Street #123",
                ShippingAddressLine2=None,
                ShippingAddressLine3=None,
                ShippingAddressState="National District",
                ShippingAddressZip="10101",
            ).model_dump(),
            "threeDSAuth": ThreeDSAuth(
                TermUrl=f"{base_url}/post-3ds",
                MethodNotificationUrl=f"{base_url}/capture-3ds-method",
                RequestChallengeIndicator=card["challenge_indicator"],
            ).model_dump(),
        }

        logger.info(f"Processing secure hold for order: {order_number}")
        result = await azul.secure_hold(hold_request_data)
        logger.info(f"Initial secure_hold response: {result}")

        secure_id = result.get("id") if isinstance(result, dict) else None
        if secure_id:
            app_session_store[secure_id] = {
                "original_term_url": hold_request_data["threeDSAuth"]["TermUrl"],
                "azul_order_id": None,
                "app_order_number": order_number,
            }
            value_dict = result.get("value") if isinstance(result, dict) else None
            if isinstance(value_dict, dict):
                app_session_store[secure_id]["azul_order_id"] = value_dict.get(
                    "AzulOrderId"
                )

            if not app_session_store[secure_id]["azul_order_id"]:
                pyazul_session = await azul.get_secure_session_info(secure_id)
                if isinstance(pyazul_session, dict):
                    retrieved_azul_order_id = pyazul_session.get("azul_order_id")
                    if isinstance(retrieved_azul_order_id, str):
                        app_session_store[secure_id][
                            "azul_order_id"
                        ] = retrieved_azul_order_id
                        logger.info(f"Retrieved AzulOrderId for {secure_id}")
                    elif retrieved_azul_order_id is not None:
                        logger.warning(
                            f"AzulOrderId for {secure_id} not str: {type(retrieved_azul_order_id)}"  # noqa: E501
                        )
                elif pyazul_session is not None:
                    logger.warning(
                        f"pyazul_session for {secure_id} not dict: {type(pyazul_session)}"  # noqa: E501
                    )

        return result

    except AzulError as e:
        logger.error(f"Error in hold process: {str(e)}")
        error_message = str(e)
        if "BIN NOT FOUND" in error_message:
            error_message = (
                "The card used is not registered in the test environment. "
                "Please use one of the provided test cards."
            )
        return templates.TemplateResponse(
            "error.html", {"request": request, "error": error_message}
        )
    except Exception as e:
        logger.error(f"Error in hold process: {str(e)}")
        return templates.TemplateResponse(
            "error.html",
            {
                "request": request,
                "error": "Unexpected error processing hold. Please try again.",
            },
        )


@app.post("/capture-3ds-method")
async def capture_3ds_method_route(
    request: Request, secure_id: Optional[str] = None, sid: Optional[str] = None
):
    """
    Handle 3DS method notification.

    This endpoint receives the response from the ACS (Access Control Server)
    after the 3DS method has been completed.
    """
    session_id = secure_id or sid

    if not session_id:
        return templates.TemplateResponse(
            "error.html",
            {
                "request": request,
                "error": "No session identifier (secure_id or sid) provided in query.",
            },
        )

    logger.info(f"Received 3DS method notification for session: {session_id}")

    try:
        app_data = app_session_store.get(session_id)
        if not isinstance(app_data, dict):
            logger.error(
                f"App session data not found or invalid for secure_id: {session_id}"
            )
            return templates.TemplateResponse(
                "error.html",
                {
                    "request": request,
                    "error": "Invalid or expired session (app_data invalid).",
                },
            )

        azul_order_id = app_data.get("azul_order_id")
        original_term_url = app_data.get("original_term_url")

        if azul_order_id is None:
            pyazul_session_data = await azul.get_secure_session_info(session_id)
            if isinstance(pyazul_session_data, dict):
                retrieved_id = pyazul_session_data.get("azul_order_id")
                if isinstance(retrieved_id, str):
                    azul_order_id = retrieved_id
                    app_data["azul_order_id"] = azul_order_id
                    logger.info(
                        f"Retrieved AzulOrderId for {session_id} in 3DS method."
                    )
                elif retrieved_id is not None:
                    logger.warning(
                        f"Retrieved AzulOrderId for {session_id} not str: {type(retrieved_id)}"  # noqa: E501
                    )
            elif pyazul_session_data is not None:
                logger.warning(
                    f"pyazul_session for {session_id} not dict: {type(pyazul_session_data)}"  # noqa: E501
                )

        assert isinstance(
            azul_order_id, str
        ), f"Azul Order ID ({azul_order_id}) non-string for sess {session_id}."

        if not original_term_url or not isinstance(original_term_url, str):
            logger.error(
                f"Original TermUrl not found or invalid for session {session_id} in app_session."  # noqa: E501
            )
            return templates.TemplateResponse(
                "error.html",
                {
                    "request": request,
                    "error": "Critical error: Original TermUrl missing or invalid.",
                },
            )

        result = await azul.process_3ds_method(
            azul_order_id=azul_order_id,
            method_notification_status="RECEIVED",
        )
        logger.info(f"process_3ds_method response: {result}")

        if (
            isinstance(result, dict)
            and result.get("ResponseMessage") == "ALREADY_PROCESSED"
        ):
            return {"status": "ok", "message": "Already processed"}

        if (
            isinstance(result, dict)
            and result.get("ResponseMessage") == "3D_SECURE_CHALLENGE"
        ):
            logger.info("Additional 3DS challenge required after method notification.")
            three_ds_challenge = result.get("ThreeDSChallenge")
            if not isinstance(three_ds_challenge, dict):
                logger.error("ThreeDSChallenge data missing or not a dict in response.")
                return templates.TemplateResponse(
                    "error.html",
                    {"request": request, "error": "Invalid 3DS challenge data."},
                )

            creq = three_ds_challenge.get("CReq")
            redirect_post_url = three_ds_challenge.get("RedirectPostUrl")

            if not isinstance(creq, str) or not isinstance(redirect_post_url, str):
                logger.error(
                    "CReq or RedirectPostUrl missing/malformed in challenge data."
                )
                return templates.TemplateResponse(
                    "error.html",
                    {"request": request, "error": "Invalid 3DS challenge parameters."},
                )

            challenge_html = azul.create_challenge_form(
                creq=creq,
                term_url=original_term_url,
                redirect_post_url=redirect_post_url,
            )
            return {
                "redirect": True,
                "html": challenge_html,
            }

        return result

    except AzulError as e:
        logger.error(f"AzulError in /capture-3ds-method: {str(e)}")
        return templates.TemplateResponse(
            "error.html", {"request": request, "error": str(e)}
        )
    except Exception as e:
        logger.error(f"Unexpected error in /capture-3ds-method: {str(e)}")
        return templates.TemplateResponse(
            "error.html",
            {
                "request": request,
                "error": "Unexpected error processing 3DS method. Please try again.",
            },
        )


@app.post("/post-3ds")
async def post_3ds_challenge_completion(
    request: Request,
    secure_id: Optional[str] = None,
    sid: Optional[str] = None,
    CRes: Optional[str] = Form(None),
):
    """
    Handle 3DS challenge response.

    This endpoint receives the CRes (Challenge Response) from the ACS
    after the cardholder completes the authentication.
    """
    session_id = secure_id or sid

    if not session_id:
        return templates.TemplateResponse(
            "error.html",
            {
                "request": request,
                "error": "No session identifier (secure_id or sid) provided in query.",
            },
        )

    if not CRes:
        return templates.TemplateResponse(
            "error.html",
            {
                "request": request,
                "error": "No challenge response (CRes) provided in form body.",
            },
        )

    try:
        result = await azul.process_challenge(
            session_id=session_id, challenge_response=CRes
        )
        logger.info(f"process_challenge response: {result}")

        if session_id in app_session_store:
            del app_session_store[session_id]

        return templates.TemplateResponse(
            "result.html", {"request": request, "result": result}
        )
    except AzulError as e:
        logger.error(f"Error processing challenge: {str(e)}")
        return templates.TemplateResponse(
            "error.html", {"request": request, "error": str(e)}
        )
    except Exception as e:
        logger.error(f"Unexpected error processing challenge: {str(e)}")
        return templates.TemplateResponse(
            "error.html",
            {
                "request": request,
                "error": "Unexpected error processing authentication. Please try again.",  # noqa: E501
            },
        )


if __name__ == "__main__":
    uvicorn.run(app, port=8000)
