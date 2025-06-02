"""
Comprehensive 3D Secure Payment Example with PyAzul.

This example demonstrates the complete 3DS workflow using PyAzul's unified callback
approach, combining the best practices from both detailed debugging and simplified
architecture.

Features:
- Unified webhook endpoint for all 3DS phases (method, challenge, completion)
- Support for both sale and hold transactions
- Comprehensive test cards for different 3DS scenarios
- Detailed logging and debugging capabilities
- Automatic 3DS phase detection and routing
- Clean session management
- Production-ready error handling

Key improvements over separate endpoint approach:
- Single webhook endpoint handles all 3DS phases automatically
- Reduced complexity in callback handling
- Better aligned with industry standard payment flows
- Easier to deploy and maintain
"""

import logging
import os
import time
from datetime import datetime
from typing import Any, Dict, List

import uvicorn
from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from pyazul import PyAzul
from pyazul.core.exceptions import AzulError
from pyazul.models import CardHolderInfo, ThreeDSAuth

# Configure comprehensive logging for debugging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("secure_3ds_example.log", mode="a"),
    ],
)

# Set specific logger levels
logging.getLogger("pyazul").setLevel(logging.DEBUG)
logging.getLogger("uvicorn.access").setLevel(logging.INFO)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)

app = FastAPI(title="PyAzul 3D Secure Payment Demo")

# Setup templates
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATES_DIR = os.path.join(SCRIPT_DIR, "templates")
templates = Jinja2Templates(directory=TEMPLATES_DIR)

logger = logging.getLogger(__name__)

# Initialize PyAzul
azul = PyAzul()
settings = azul.settings

# Comprehensive test cards for different 3DS scenarios
TEST_CARDS: List[Dict[str, Any]] = [
    {
        "number": "4265880000000007",
        "label": "Frictionless with 3DS Method",
        "expiration": "202812",
        "cvv": "123",
        "force_no_3ds": "0",
        "challenge_indicator": "02",  # NO_CHALLENGE - Frictionless
        "description": (
            "This card will process frictionlessly after completing the 3DS method"
        ),
    },
    {
        "number": "4147463011110117",
        "label": "Frictionless without 3DS Method",
        "expiration": "202812",
        "cvv": "123",
        "force_no_3ds": "0",
        "challenge_indicator": "02",  # NO_CHALLENGE - Frictionless
        "description": (
            "This card will process frictionlessly without requiring the 3DS method"
        ),
    },
    {
        "number": "4005520000000129",
        "label": "Challenge with 3DS Method (Limit RD$ 50)",
        "expiration": "202812",
        "cvv": "123",
        "force_no_3ds": "0",
        "challenge_indicator": "03",  # CHALLENGE
        "max_amount": 50,
        "description": "This card requires full 3DS challenge authentication",
    },
    {
        "number": "4147463011110059",
        "label": "Challenge without 3DS Method",
        "expiration": "202812",
        "cvv": "123",
        "force_no_3ds": "0",
        "challenge_indicator": "03",  # CHALLENGE
        "description": "This card requires challenge but skips the 3DS method step",
    },
    {
        "number": "5413330089600119",
        "label": "Force No 3DS (Direct Processing)",
        "expiration": "202812",
        "cvv": "979",
        "force_no_3ds": "1",
        "challenge_indicator": "01",  # FORCE_NO_3DS
        "description": "This card bypasses 3DS completely for direct processing",
    },
]


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Render the main payment form with transaction type selection."""
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "cards": TEST_CARDS,
            "title": "Comprehensive 3DS Payment Demo",
        },
    )


@app.post("/process-payment")
async def process_payment(
    request: Request,
    card_number: str = Form(...),
    amount: float = Form(...),
    itbis: float = Form(...),
    transaction_type: str = Form("sale"),  # sale or hold
):
    """Process payment using unified 3DS approach with transaction type selection."""
    logger.info("=" * 80)
    logger.info(f"PROCESSING {transaction_type.upper()} TRANSACTION")
    logger.info("=" * 80)
    masked_card = card_number[-4:].rjust(len(card_number), "*")
    logger.info(f"Card number: {masked_card}")
    logger.info(f"Amount: {amount}")
    logger.info(f"ITBIS: {itbis}")
    logger.info(f"Transaction type: {transaction_type}")

    # Find card configuration
    card = next((c for c in TEST_CARDS if c["number"] == card_number), None)
    if not card:
        logger.error(f"Invalid card: {card_number}")
        return JSONResponse(
            status_code=400,
            content={"error": "Invalid card. Please select a valid test card."},
        )

    logger.info(f"Selected card: {card['label']}")
    logger.info(f"Challenge indicator: {card['challenge_indicator']}")
    logger.info(f"Force No 3DS: {card['force_no_3ds']}")

    try:
        # Get base URL (support ngrok for testing)
        base_url = os.getenv("NGROK_URL", str(request.base_url).rstrip("/"))
        logger.info(f"Base URL: {base_url}")

        # Generate order number that fits within Azul's 15-character limit
        order_number = datetime.now().strftime("%y%m%d%H%M%S")  # 12 chars: YYMMDDHHMMSS
        logger.info(f"Generated order number: {order_number}")

        # Prepare transaction request
        transaction_request = {
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
            "CustomOrderId": f"{transaction_type}-{order_number}",
            "SaveToDataVault": "0",
            "ForceNo3DS": card["force_no_3ds"],
            "CardHolderInfo": CardHolderInfo(
                Name="Test User",
                Email="test@example.com",
            ).model_dump(),
            "ThreeDSAuth": ThreeDSAuth(
                # Unified webhook endpoint for all 3DS phases
                TermUrl=f"{base_url}/payment/azul/webhook",
                MethodNotificationUrl=f"{base_url}/payment/azul/webhook",
                RequestChallengeIndicator=card["challenge_indicator"],
            ).model_dump(),
        }

        logger.info("3DS Auth URLs:")
        term_url = transaction_request["ThreeDSAuth"]["TermUrl"]
        method_url = transaction_request["ThreeDSAuth"]["MethodNotificationUrl"]
        logger.info(f"  TermUrl: {term_url}")
        logger.info(f"  MethodNotificationUrl: {method_url}")

        # Process transaction based on type
        if transaction_type == "sale":
            logger.info(f"Processing secure sale for order: {order_number}")
            result = await azul.secure_sale(transaction_request)
        elif transaction_type == "hold":
            logger.info(f"Processing secure hold for order: {order_number}")
            result = await azul.secure_hold(transaction_request)
        else:
            return JSONResponse(
                status_code=400,
                content={"error": f"Invalid transaction type: {transaction_type}"},
            )

        logger.info("=" * 50)
        logger.info(f"INITIAL SECURE_{transaction_type.upper()} RESPONSE:")
        logger.info("=" * 50)
        result_keys = list(result.keys()) if isinstance(result, dict) else "Not a dict"
        logger.info(f"Result keys: {result_keys}")
        response_msg = (
            result.get("ResponseMessage") if isinstance(result, dict) else "N/A"
        )
        logger.info(f"Response Message: {response_msg}")
        has_redirect = result.get("redirect") if isinstance(result, dict) else False
        logger.info(f"Has redirect: {has_redirect}")
        secure_id = result.get("id") if isinstance(result, dict) else "N/A"
        logger.info(f"Secure ID: {secure_id}")
        logger.info("=" * 50)

        # Check if 3DS redirection is required
        if result.get("redirect") and result.get("html"):
            logger.info("3DS authentication required - returning redirect info")
            return {
                "success": True,
                "requires_3ds": True,
                "redirect": True,  # Frontend expects this property
                "html": result["html"],
                "secure_id": result.get("id"),
                "message": result.get("message", "3DS authentication required"),
                "transaction_type": transaction_type,
            }
        else:
            # Direct approval/decline (frictionless or no 3DS)
            logger.info("Direct transaction result (no 3DS redirection needed)")
            response_data = result.get("value", result)

            # Determine success based on response
            is_success = (
                response_data.get("ResponseMessage") == "APROBADA"
                or response_data.get("IsoCode") == "00"
            )

            return {
                "success": True,
                "requires_3ds": False,
                "result": response_data,
                "azul_order_id": response_data.get("AzulOrderId"),
                "is_approved": is_success,
                "transaction_type": transaction_type,
            }

    except AzulError as e:
        logger.error(f"Error in {transaction_type} process: {str(e)}")
        error_message = str(e)
        if "BIN NOT FOUND" in error_message:
            error_message = (
                "The card used is not registered in the test environment. "
                "Please use one of the provided test cards."
            )
        return JSONResponse(status_code=400, content={"error": error_message})
    except Exception as e:
        error_msg = f"Unexpected error processing {transaction_type}. Please try again."
        logger.error(f"Unexpected error in {transaction_type} process: {str(e)}")
        return JSONResponse(status_code=500, content={"error": error_msg})


@app.api_route("/payment/azul/webhook", methods=["GET", "POST"])
async def unified_3ds_webhook(request: Request):
    """
    Unified 3DS webhook - handles all 3DS callback phases automatically.

    This single endpoint processes:
    1. 3DS Method notifications
    2. Challenge responses (CRes)
    3. Return redirects

    PyAzul's handle_3ds_callback automatically detects the phase and routes accordingly.
    """
    logger.info("=" * 80)
    logger.info("🔔 UNIFIED 3DS WEBHOOK CALLED FROM EXTERNAL SOURCE")
    logger.info("=" * 80)

    # Extract secure_id from query parameters
    secure_id = request.query_params.get("secure_id")

    # Comprehensive debug logging
    logger.info(f"Method: {request.method}")
    logger.info(f"URL: {request.url}")
    logger.info(f"Secure ID: {secure_id}")
    logger.info(f"Query params: {dict(request.query_params)}")

    if not secure_id:
        logger.error("No secure_id provided in webhook")
        return JSONResponse(
            status_code=400,
            content={"status": "error", "message": "No secure_id provided"},
        )

    try:
        # Get callback data
        callback_data = dict(request.query_params)
        form_data = {}

        if request.method == "POST":
            form_data = dict(await request.form())
            logger.info(f"POST form data: {form_data}")

        logger.info("Calling PyAzul unified callback handler...")

        # Process using PyAzul's unified callback handler
        # This automatically detects whether it's a method notification,
        # challenge response, or return redirect
        result = await azul.handle_3ds_callback(
            secure_id=secure_id, callback_data=callback_data, form_data=form_data
        )

        logger.info("=" * 50)
        logger.info("UNIFIED CALLBACK RESULT:")
        logger.info("=" * 50)
        logger.info(f"Completed: {result.get('completed')}")
        logger.info(f"Requires redirect: {result.get('requires_redirect')}")
        logger.info(f"Status: {result.get('status')}")
        logger.info(f"AzulOrderId: {result.get('AzulOrderId')}")
        logger.info("=" * 50)

        # Handle the result based on callback phase
        if result.get("completed"):
            # Transaction is final - redirect to result page
            azul_order_id = result.get("AzulOrderId", "unknown")
            status = result.get("status", "unknown")

            # Map internal status to user-friendly status
            is_approved = status in ["approved", "APROBADA"]
            display_status = "approved" if is_approved else "declined"

            redirect_url = f"/result?order_id={azul_order_id}&status={display_status}"
            logger.info(f"🎯 Transaction completed - redirecting to: {redirect_url}")

            return RedirectResponse(redirect_url, status_code=303)

        elif result.get("requires_redirect"):
            # Challenge required - return HTML for user interaction
            logger.info("🔄 Challenge required - returning challenge HTML")
            return HTMLResponse(result["html"])

        else:
            # Still processing or method notification processed
            logger.info("⏳ Callback processed - returning JSON response")

            # For method notifications from ACS, we need to return appropriate
            # response
            # Check if this was a method notification that requires challenge
            session_info = await azul.get_session_info(secure_id)
            if session_info and session_info.get("challenge_required"):
                # Challenge is now ready, return the challenge HTML
                challenge_html = session_info.get("challenge_html")
                if challenge_html:
                    logger.info(
                        "🔄 Challenge ready after method - returning challenge HTML"
                    )
                    return HTMLResponse(challenge_html)

            # For AJAX requests from frontend polling
            accept_header = request.headers.get("accept", "")
            if accept_header.find("application/json") != -1:
                return JSONResponse(
                    content={
                        "status": "success",
                        "message": result.get("message", "Processing 3DS auth..."),
                        "azul_order_id": result.get("AzulOrderId"),
                        "phase": "processing",
                    }
                )

            # For browser redirects, show processing page
            processing_template = (
                "processing.html"
                if os.path.exists(os.path.join(TEMPLATES_DIR, "processing.html"))
                else "index.html"
            )
            return templates.TemplateResponse(
                processing_template,
                {
                    "request": request,
                    "message": result.get(
                        "message", "Processing 3DS authentication..."
                    ),
                    "secure_id": secure_id,
                },
            )

    except AzulError as e:
        logger.error(f"❌ 3DS callback processing error: {e}")
        return JSONResponse(
            status_code=400, content={"status": "error", "message": str(e)}
        )
    except Exception as e:
        logger.error(f"❌ Unexpected webhook error: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": "Internal server error"},
        )


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all incoming requests to help debug ACS callbacks."""
    start_time = time.time()

    # Log request details
    logger.info(f"🌐 Request: {request.method} {request.url}")
    logger.info(f"🌐 Headers: {dict(request.headers)}")

    response = await call_next(request)

    process_time = time.time() - start_time
    logger.info(f"🌐 Response: {response.status_code} (took {process_time:.3f}s)")

    return response


@app.get("/result")
async def result_page(request: Request, order_id: str, status: str = "unknown"):
    """Display the final transaction result."""
    logger.info(f"📊 Displaying result page - Order: {order_id}, Status: {status}")

    return templates.TemplateResponse(
        "result.html",
        {
            "request": request,
            "order_id": order_id,
            "status": status,
            "success": status == "approved",
        },
    )


@app.get("/payment/status/{secure_id}")
async def get_payment_status(secure_id: str):
    """
    Get the current status of a 3DS transaction.

    This endpoint is useful for:
    - Frontend polling to check transaction status
    - Debugging 3DS flow issues
    - Integration testing
    """
    try:
        logger.info(f"📊 Checking payment status for secure_id: {secure_id}")

        session_info = await azul.get_session_info(secure_id)
        if not session_info:
            logger.warning(f"Session not found for secure_id: {secure_id}")
            return {"status": "not_found", "message": "Session not found"}

        # Check transaction status
        session_status = session_info.get("status", "processing")
        azul_order_id = session_info.get("azul_order_id")

        logger.info(f"Session status: {session_status}, AzulOrderId: {azul_order_id}")

        # Return appropriate response based on status
        if session_status == "approved":
            return {
                "status": "approved",
                "message": "Transaction approved",
                "azul_order_id": azul_order_id,
                "final_result": session_info.get("final_result"),
            }
        elif session_status in ["declined", "denegada"]:
            error_desc = session_info.get("error_description")
            message = (
                f"Transaction declined: {error_desc}"
                if error_desc
                else "Transaction declined"
            )
            return {
                "status": "declined",
                "message": message,
                "azul_order_id": azul_order_id,
                "final_result": session_info.get("final_result"),
                "error_description": error_desc,
            }

        # Check if 3DS method form is needed
        if session_info.get("method_required") and session_info.get("method_form"):
            return {
                "status": "method_required",
                "message": "3DS Method form ready",
                "method_form": session_info.get("method_form"),
                "azul_order_id": azul_order_id,
            }

        # Check if challenge is required
        if session_info.get("challenge_required"):
            return {
                "status": "challenge_required",
                "message": "3DS Challenge required",
                "challenge_html": session_info.get("challenge_html"),
                "azul_order_id": azul_order_id,
            }

        # Default: still processing
        return {
            "status": session_status,
            "message": "Transaction in progress",
            "azul_order_id": azul_order_id,
        }

    except Exception as e:
        logger.error(f"Error getting payment status: {e}")
        return {"status": "error", "message": "Could not retrieve status"}


@app.get("/3ds-iframe")
async def threeds_iframe(request: Request, secure_id: str):
    """
    Serve the 3DS iframe handler page.

    This endpoint provides an iframe-friendly interface for 3DS processing,
    useful for embedded payment flows.
    """
    try:
        logger.info(f"🖼️ Serving 3DS iframe for secure_id: {secure_id}")

        # Verify session exists
        session_info = await azul.get_session_info(secure_id)
        if not session_info:
            return HTMLResponse(
                """
                <html><body>
                    <script>
                        parent.postMessage({
                            type: 'threeDS_error',
                            message: 'Session not found'
                        }, '*');
                    </script>
                </body></html>
            """
            )

        return templates.TemplateResponse(
            "iframe_3ds.html",
            {
                "request": request,
                "secure_id": secure_id,
                "base_url": str(request.base_url).rstrip("/"),
            },
        )

    except Exception as e:
        logger.error(f"Error serving 3DS iframe: {e}")
        return HTMLResponse(
            f"""
            <html><body>
                <script>
                    parent.postMessage({{
                        type: 'threeDS_error',
                        message: 'Error loading authentication: {str(e)}'
                    }}, '*');
                </script>
            </body></html>
        """
        )


@app.post("/manual-3ds-method/{secure_id}")
async def manual_3ds_method_processing(secure_id: str):
    """
    Manual trigger for 3DS method processing.

    Useful when the ACS doesn't call back automatically in test environments.
    This endpoint checks if method processing is needed and triggers it if so.
    """
    try:
        logger.info(f"🔧 Manual 3DS method processing triggered for: {secure_id}")

        session_info = await azul.get_session_info(secure_id)
        if not session_info:
            logger.warning(f"Session not found for secure_id: {secure_id}")
            return JSONResponse(
                status_code=404, content={"error": "Session not found or expired"}
            )

        azul_order_id = session_info.get("azul_order_id")
        if not azul_order_id:
            logger.error(f"No AzulOrderId found in session for: {secure_id}")
            return JSONResponse(
                status_code=400, content={"error": "No AzulOrderId found in session"}
            )

        # Check current status first
        current_status = session_info.get("status", "processing")
        logger.info(f"Current session status: {current_status}")

        # If already completed, return the final result
        if current_status in ["approved", "declined", "error"]:
            logger.info(f"Transaction already completed with status: {current_status}")
            final_result = session_info.get(
                "final_result", {"ResponseMessage": current_status.upper()}
            )
            return {
                "success": True,
                "result": final_result,
                "azul_order_id": azul_order_id,
                "message": f"Transaction already completed: {current_status}",
                "already_completed": True,
            }

        # Check if method was already processed
        method_processed = session_info.get("method_processed", False)
        if method_processed:
            logger.info("3DS method already processed, checking for next step")

            # If challenge is required, return that info
            if session_info.get("challenge_required"):
                return {
                    "success": True,
                    "result": {"ResponseMessage": "3D_SECURE_CHALLENGE"},
                    "azul_order_id": azul_order_id,
                    "message": "Method processed, challenge required",
                    "challenge_ready": True,
                }

            # Otherwise return current status
            return {
                "success": True,
                "result": session_info.get(
                    "final_result", {"ResponseMessage": "PROCESSING"}
                ),
                "azul_order_id": azul_order_id,
                "message": "Method processed, checking status",
            }

        # Process the 3DS method manually
        logger.info(f"Processing 3DS method for AzulOrderId: {azul_order_id}")
        result = await azul.process_3ds_method(
            azul_order_id=azul_order_id, method_notification_status="RECEIVED"
        )

        response_msg = result.get("ResponseMessage", "Unknown")
        logger.info(f"Manual 3DS method result: {response_msg}")

        # Detailed result logging
        if response_msg == "3D_SECURE_CHALLENGE":
            logger.info("✅ Method processing triggered challenge requirement")
        elif response_msg == "APROBADA":
            logger.info("✅ Transaction approved after method processing")
        elif result.get("IsoCode") == "00":
            logger.info("✅ Transaction approved (ISO 00) after method processing")
        else:
            logger.warning(f"⚠️ Unexpected method processing result: {response_msg}")

        return {
            "success": True,
            "result": result,
            "azul_order_id": azul_order_id,
            "message": "3DS method processed manually",
            "response_message": response_msg,
        }

    except Exception as e:
        logger.error(
            f"Error in manual 3DS method processing for {secure_id}: {e}", exc_info=True
        )
        return JSONResponse(
            status_code=500,
            content={
                "error": str(e),
                "message": "Failed to process 3DS method manually",
            },
        )


@app.get("/debug/{secure_id}")
async def debug_session(secure_id: str):
    """
    Debug endpoint to inspect 3DS session data.

    Useful for troubleshooting 3DS flows in development.
    """
    try:
        session_info = await azul.get_session_info(secure_id)
        if not session_info:
            return {"error": "Session not found"}

        # Remove sensitive data for debugging
        debug_info = {
            k: v
            for k, v in session_info.items()
            if k not in ["method_form", "challenge_html"]
        }
        debug_info["has_method_form"] = bool(session_info.get("method_form"))
        debug_info["has_challenge_html"] = bool(session_info.get("challenge_html"))

        return {
            "secure_id": secure_id,
            "session_info": debug_info,
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        return {"error": str(e)}


# Error handling
@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    """Handle 404 errors gracefully."""
    return templates.TemplateResponse(
        "error.html", {"request": request, "error": "Page not found"}, status_code=404
    )


@app.exception_handler(500)
async def server_error_handler(request: Request, exc):
    """Handle 500 errors gracefully."""
    logger.error(f"Internal server error: {exc}")
    return templates.TemplateResponse(
        "error.html",
        {"request": request, "error": "Internal server error"},
        status_code=500,
    )


if __name__ == "__main__":
    logger.info("🚀 Starting Comprehensive 3DS Payment Example")
    logger.info("=" * 60)
    logger.info("Features:")
    logger.info("  ✅ Unified 3DS webhook (single endpoint for all phases)")
    logger.info("  ✅ Support for sale and hold transactions")
    logger.info("  ✅ Comprehensive test cards")
    logger.info("  ✅ Detailed logging and debugging")
    logger.info("  ✅ Production-ready error handling")
    logger.info("=" * 60)
    logger.info("Visit http://127.0.0.1:8000 to test the workflow")
    logger.info("For ngrok testing, set NGROK_URL environment variable")

    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="info")
