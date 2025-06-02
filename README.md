![Build & publish](https://github.com/indexa-git/pyazul/workflows/Build%20&%20publish/badge.svg)
![Docstring Coverage](docs/interrogate_badge.svg)

# PyAzul

Python SDK for the Azul Payment Gateway. PyAzul allows you to process payments, tokenize cards, and implement 3D Secure authentication by interacting with the Azul API.

## Installation

```bash
pip install pyazul
```

## Quick Setup & Configuration

### Environment Variables (.env file)

Create a `.env` file in your project root:

```bash
# Basic API Credentials
AUTH1=your_auth1
AUTH2=your_auth2
MERCHANT_ID=your_merchant_id
ENVIRONMENT=dev  # 'dev' for testing, 'prod' for live

# SSL Certificates (Path, PEM string, or Base64 PEM)
AZUL_CERT=/path/to/certificate.pem
AZUL_KEY=/path/to/key.pem

# Payment Page Settings (Optional)
AZUL_AUTH_KEY=your_auth_key_for_page
MERCHANT_NAME=Your_Business_Name
MERCHANT_TYPE=Your_Business_Type
```

**Note on Certificates**: `AZUL_CERT` and `AZUL_KEY` can be file paths. Alternatively, `AZUL_CERT` can be the full PEM content string, and `AZUL_KEY` can be the PEM content string or Base64 encoded. The library handles temporary files internally if direct content is provided.

### Initializing PyAzul

```python
from pyazul import PyAzul

azul = PyAzul()  # Loads settings from .env and environment variables

# For custom settings (e.g., if not using .env):
# from pyazul.core.config import AzulSettings
# settings = AzulSettings(AUTH1="...", AUTH2="...", ...)
# azul = PyAzul(settings=settings)
```

### Logging

PyAzul uses standard Python logging. To enable detailed debug logs:

```python
import logging

logging.getLogger('pyazul').setLevel(logging.DEBUG)
# For specific services, e.g.: logging.getLogger('pyazul.services.secure').setLevel(logging.DEBUG)
logging.basicConfig(level=logging.DEBUG) # Ensure a handler is configured
```

## Core Functionality Examples

Ensure `azul = PyAzul()` is initialized.

### Process a Payment (Non-3DS)

```python
from pyazul import PyAzul, AzulError

# azul = PyAzul() # Assumed initialized

async def process_payment():
    payment_data = {
        # Channel and PosInputMode default to "EC" and "E-Commerce"
        "Amount": 100000,  # In cents (e.g., 1000.00)
        "Itbis": 18000,    # In cents (e.g., 180.00)
        "CardNumber": "4111********1111", # Use a test card
        "Expiration": "202812", # YYYYMM
        "CVC": "***",
        "OrderNumber": "INV-12345",
    }
    try:
        response = await azul.sale(payment_data)
        if response.get("ResponseMessage") == "APROBADA":
            print(f"Payment approved: {response.get('AuthorizationCode')}, AzulOrderId: {response.get('AzulOrderId')}")
        else:
            print(f"Error: {response.get('ResponseMessage')}, Details: {response.get('ErrorDescription', response)}")
    except AzulError as e:
        print(f"An API error occurred: {e}")
```

### Tokenize a Card

```python
# from pyazul import PyAzul, AzulError # Assumed imported
# azul = PyAzul() # Assumed initialized

async def tokenize_card():
    token_creation_data = {
        "CardNumber": "4111********1111",
        "Expiration": "202812",
        # Store defaults to your Merchant ID from settings
    }
    try:
        token_response = await azul.create_token(token_creation_data)
        if token_response.get("ResponseMessage") == "APROBADA":
            token_id = token_response.get("DataVaultToken")
            print(f"Token created: {token_id}")

            # Example: Use token for a non-3DS payment
            token_payment_data = {
                "DataVaultToken": token_id,
                "Amount": 50000, # 500.00 in cents
                "Itbis": 0,      # 0.00 in cents
                "OrderNumber": "TOKEN-ORD-XYZ"
            }
            payment_response = await azul.token_sale(token_payment_data)
            if payment_response.get("ResponseMessage") == "APROBADA":
                print(f"Token payment approved: {payment_response.get('AuthorizationCode')}")
            else:
                print(f"Token payment error: {payment_response.get('ResponseMessage')}")
        else:
            print(f"Token creation error: {token_response.get('ResponseMessage')}")
    except AzulError as e:
        print(f"An API error occurred: {e}")
```

### Payment Page Integration (FastAPI Example)

```python
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pyazul import PyAzul

# app = FastAPI()
# azul = PyAzul() # Assumed initialized

@app.get("/pay/{order_id}", response_class=HTMLResponse)
async def get_payment_page(order_id: str):
    page_data = {
        "Amount": 100000, # 1000.00 in cents
        "ITBIS": 18000,   # 180.00 in cents
        "OrderNumber": order_id,
        "ApprovedUrl": "https://your-site.com/success",
        "DeclineUrl": "https://your-site.com/declined",
        "CancelUrl": "https://your-site.com/cancel",
        # Other fields like UseStoreLogo, ShowLoyaltyBar are optional
    }
    html_form = azul.payment_page(page_data)
    return HTMLResponse(content=html_form)
```

## 3D Secure Implementation Guide

PyAzul supports 3D Secure 2.0. This involves interactions between the customer's browser, your server, the card issuer's ACS, and Azul. PyAzul simplifies this by initiating the transaction, providing helpers for redirection, processing ACS callbacks, and finalizing the transaction.

A unique `secure_id` (UUID string generated by PyAzul) is created for each 3DS transaction. PyAzul appends this `secure_id` as a query parameter (e.g., `?secure_id=<generated_id>`) to your provided `TermUrl` and `MethodNotificationUrl`. Your application must extract this `secure_id` from callback query parameters to track the 3DS session.

**Application-Side State Management**: For production, your application **MUST** implement its own persistent session management (e.g., Redis, database) to reliably manage state across asynchronous 3DS callbacks. Use the `secure_id` to store/retrieve your order details, the `azul_order_id` (from the initial `secure_sale` response or via `await azul.get_session_info(secure_id)`), and the original `TermUrl`. PyAzul's internal session store (`await azul.get_session_info(secure_id)`) is for its operational needs and is not persistent.

### Complete 3D Secure Flow (FastAPI Example)

```python
from fastapi import FastAPI, Form, Query
from fastapi.responses import HTMLResponse, JSONResponse
from pyazul import PyAzul, AzulError

app = FastAPI()
azul = PyAzul() # Assumed initialized

# --- Application-Level Session Store (Example - REPLACE FOR PRODUCTION) ---
app_level_session_store = {} # Use Redis, database, etc., in production.
# --- End Example Session Store ---

# 1. Transaction Initiation
@app.post("/initiate-3ds-payment")
async def initiate_3ds_payment(request_data: dict): # Your payment request data
    original_term_url = request_data.get("threeDSAuth", {}).get("TermUrl")

    try:
        response = await azul.secure_sale(request_data)
        secure_id = response.get("id") # PyAzul's unique ID for this 3DS session

        azul_order_id_initial = response.get("value", {}).get("AzulOrderId")

        if secure_id:
            # Store in YOUR application's session store
            app_level_session_store[secure_id] = {
                "original_term_url": original_term_url,
                "azul_order_id": azul_order_id_initial,
                "internal_order_ref": request_data.get("OrderNumber"),
            }
            # If azul_order_id wasn't in the immediate response (e.g., redirect occurred),
            # try getting it from PyAzul's internal session for your app's store
            if not azul_order_id_initial:
                pyazul_session = await azul.get_session_info(secure_id)
                if pyazul_session and pyazul_session.get("azul_order_id"):
                    app_level_session_store[secure_id]["azul_order_id"] = pyazul_session.get("azul_order_id")

        if response.get("redirect"): # HTML for redirection to 3DS Method or ACS Challenge
            return HTMLResponse(content=response.get("html"))
        elif response.get("value", {}).get("ResponseMessage") == "APROBADA": # Frictionless approval
            return JSONResponse(content={"status": "approved_frictionless", "data": response.get("value")})
        else: # Other initial responses (e.g., declined)
            return JSONResponse(content={"status": "error_or_declined_early", "data": response.get("value")}, status_code=400)
    except AzulError as e:
        return JSONResponse(content={"status": "sdk_error", "message": str(e)}, status_code=500)

# 2. 3DS Method Notification Callback (Your MethodNotificationUrl)
@app.post("/capture-3ds-method") # Matches MethodNotificationUrl
async def capture_3ds_method_callback(secure_id: str = Query(...)): # secure_id from query
    try:
        app_session = app_level_session_store.get(secure_id)
        if not app_session or not app_session.get("azul_order_id") or not app_session.get("original_term_url"):
            # Attempt to fetch from PyAzul's session as a fallback if critical info missing
            pyazul_session_fallback = await azul.get_session_info(secure_id)
            if not app_session: app_session = {} # Initialize if was None
            if pyazul_session_fallback:
                if not app_session.get("azul_order_id"):
                    app_session["azul_order_id"] = pyazul_session_fallback.get("azul_order_id")
                if not app_session.get("original_term_url"): # PyAzul stores its version with ?secure_id
                    # We need the user's original TermUrl for create_challenge_form if it wasn't stored
                    # This part of the example assumes original_term_url was robustly stored by the app.
                    # For simplicity, we'll proceed assuming it was.
                    # In a real app, handle this more gracefully or ensure it's always in app_session.
                    pass


            if not app_session.get("azul_order_id") or not app_session.get("original_term_url"):
                 return JSONResponse(content={"error": "Critical session data (AzulOrderId or original TermUrl) missing"}, status_code=400)


        result = await azul.process_3ds_method(
            azul_order_id=app_session["azul_order_id"],
            method_notification_status="RECEIVED"
        )

        if result.get("ResponseMessage") == "3D_SECURE_CHALLENGE":
            # Use the TermUrl from your app session. PyAzul's internal one already has secure_id.
            # If you stored the user's original TermUrl, append secure_id yourself.
            term_url_for_challenge = app_session["original_term_url"]
            if "?secure_id=" not in term_url_for_challenge: # Ensure secure_id is present
                 term_url_for_challenge += f"?secure_id={secure_id}"

            form_html = azul.create_challenge_form(
                result["ThreeDSChallenge"]["CReq"],
                term_url_for_challenge,
                result["ThreeDSChallenge"]["RedirectPostUrl"]
            )
            return HTMLResponse(content=form_html)
        elif result.get("ResponseMessage") == "APROBADA":
            return JSONResponse(content={"status": "approved_after_method", "data": result})
        else:
            return JSONResponse(content={"status": "pending_or_error_after_method", "data": result})
    except AzulError as e:
        return JSONResponse(content={"status": "sdk_error", "message": str(e)}, status_code=500)

# 3. 3DS Challenge Completion Callback (Your TermUrl)
@app.post("/post-3ds-callback") # Matches TermUrl
async def post_3ds_challenge_callback(secure_id: str = Query(...), CRes: str = Form(...)):
    try:
        final_result = await azul.process_challenge(session_id=secure_id, challenge_response=CRes)
        if final_result.get("ResponseMessage") == "APROBADA":
            return JSONResponse(content={"status": "approved_after_challenge", "data": final_result})
        else:
            return JSONResponse(content={"status": "declined_or_error_after_challenge", "data": final_result}, status_code=400)
    except AzulError as e:
        return JSONResponse(content={"status": "sdk_error", "message": str(e)}, status_code=500)
```

### Key Considerations for 3DS

- **Callback URLs**: Ensure `TermUrl` and `MethodNotificationUrl` correctly point to your server endpoints.
- **`CardHolderInfo` and `ThreeDSAuth`**: Provide accurate data in these objects during `secure_sale` initiation.
- **Error Handling**: Implement robust error handling for each step.

## Request Data

PyAzul methods accept Python dictionaries for request data. The SDK's internal Pydantic models handle formatting for fields like `Amount` and `ITBIS` (provide as integers representing cents).

**Example: `secure_sale` Request Data**

```python
{
    "CardNumber": "4111...", "Expiration": "202812", "CVC": "123",
    "Amount": 100000,      # Integer cents (e.g., 1000.00)
    "Itbis": 18000,        # Integer cents (e.g., 180.00)
    "OrderNumber": "3DS-ORDER-123",
    # Store defaults to MerchantID from settings
    # forceNo3DS defaults to "0" (enable 3DS)
    "cardHolderInfo": { # Provide as much detail as possible
        "Name": "John Doe", "Email": "john@example.com",
        "BillingAddressCity": "Santo Domingo", "BillingAddressCountry": "DO",
        # ... other cardHolderInfo fields
    },
    "threeDSAuth": { # Required for secure transactions
        "TermUrl": "https://your-domain.com/post-3ds-callback",
        "MethodNotificationUrl": "https://your-domain.com/capture-3ds-method",
        # RequestChallengeIndicator defaults to "03" (Prefer challenge)
        # ... other threeDSAuth fields
    }
}
```

Refer to `pyazul/models/` for Pydantic model definitions if you wish to use them for type hinting or constructing request data, then pass `your_model_instance.model_dump(exclude_none=True)`.

## API Reference

The `PyAzul` object is the main entry point. Key methods:

```python
# azul = PyAzul() # Assumed initialized

# --- Non-3DS Transactions ---
# await azul.sale(data_dict)
# await azul.token_sale(data_dict)
# await azul.hold(data_dict)
# await azul.post_auth(data_dict) # Capture a hold
# await azul.void(data_dict)
# await azul.refund(data_dict)
# await azul.verify_transaction(data_dict)   # Verify transaction status

# --- Card Tokenization (DataVault) ---
# await azul.create_token(data_dict)
# await azul.delete_token(data_dict)

# --- Payment Page ---
# html_form_string = azul.payment_page(data_dict)

# --- 3D Secure ---
# response = await azul.secure_sale(data_dict)
# response = await azul.secure_token_sale(data_dict)
# response = await azul.secure_hold(data_dict)

# --- 3DS Callback Helpers ---
# response = await azul.process_3ds_method(azul_order_id="...", method_notification_status="...")
# response = await azul.process_challenge(session_id="...", challenge_response="...")
# html_form = azul.create_challenge_form(creq="...", term_url="...", redirect_post_url="...")

# --- 3DS Session Inspection (Primarily for PyAzul's internal state) ---
# session_data = await azul.get_session_info(session_id="...")

# Access to underlying components (generally not needed for typical use):
# azul.transaction, azul.datavault, azul.payment_page_service, azul.secure
# azul.api (AzulAPI instance), azul.settings (AzulSettings instance)
```

## Error Handling

PyAzul uses custom exceptions inheriting from `pyazul.AzulError`:

- `pyazul.core.exceptions.SSLError`: SSL configuration issues.
- `pyazul.core.exceptions.APIError`: General HTTP/API communication problems.
- `pyazul.core.exceptions.AzulResponseError`: Azul API returned an error (e.g., transaction declined). Has `response_data` attribute.

```python
from pyazul import AzulError, AzulResponseError
from pyazul.core.exceptions import APIError, SSLError

try:
    # response = await azul.sale({...})
    pass # Your PyAzul call
except AzulResponseError as e:
    print(f"Azul API Error: {e.message}, Response: {e.response_data}")
except APIError as e: # Covers other API communication issues (network, etc.)
    print(f"API Communication Error: {e}")
except SSLError as e:
    print(f"SSL Config Error: {e}")
except AzulError as e: # Catch-all for other PyAzul specific errors
    print(f"PyAzul SDK Error: {e}")
except Exception as e: # Other unexpected errors
    print(f"An unexpected error occurred: {e}")
```

## More Information

For official Azul API documentation, visit the [Azul Developer Portal](https://dev.azul.com.do/Pages/developer/index.aspx) (link subject to change).

---

&copy; MIT License
