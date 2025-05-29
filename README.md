![Build & publish](https://github.com/indexa-git/pyazul/workflows/Build%20&%20publish/badge.svg)
![Docstring Coverage](docs/interrogate_badge.svg)

# PyAzul

Python SDK (Software Development Kit) for the Azul Payment Gateway. This library, referred to as PyAzul, allows you to process payments, tokenize cards, and implement 3D Secure authentication with minimal setup by interacting with the external Azul API.

## Installation

```bash
pip install pyazul
```

## Quick Setup & Configuration

This section outlines the necessary setup to get PyAzul running, including environment configuration for API credentials and certificates.

### Environment Variables (.env file)

Create a `.env` file in your project root with your Azul credentials and settings:

```bash
# Basic API Credentials (Required for all operations)
AUTH1=your_auth1
AUTH2=your_auth2
MERCHANT_ID=your_merchant_id
ENVIRONMENT=dev  # 'dev' for testing, 'prod' for live transactions

# SSL Certificates (Required for all operations)
AZUL_CERT=/path/to/certificate.pem  # Can be a file path or the direct PEM string content
AZUL_KEY=/path/to/key.pem    # Can be a file path, direct PEM string content, or Base64 encoded PEM content

# Payment Page Settings (Optional - only if using Payment Page feature)
AZUL_AUTH_KEY=your_auth_key_for_page
MERCHANT_NAME=Your_Business_Name
MERCHANT_TYPE=Your_Business_Type
```

**Note on Certificates**: `AZUL_CERT` and `AZUL_KEY` can be provided as file paths. Alternatively, `AZUL_CERT` can be the full PEM content as a string, and `AZUL_KEY` can be the full PEM content as a string or a Base64 encoded PEM string. The library handles creating temporary files for PEM content internally.

### Initializing PyAzul

Once your `.env` file is configured, initialize the `PyAzul` facade:

```python
from pyazul import PyAzul

# The PyAzul class acts as a facade, providing a simplified interface to the SDK's features.
azul = PyAzul()  # Automatically loads settings from .env and environment variables

# For custom settings (e.g., if not using a .env file or want to override):
# from pyazul.core.config import AzulSettings
# settings = AzulSettings(
#     AUTH1="your_auth1",
#     AUTH2="your_auth2",
#     MERCHANT_ID="your_merchant_id",
#     AZUL_CERT="-----BEGIN CERTIFICATE-----...", # Direct PEM content example
#     AZUL_KEY="/path/to/your/private.key",    # File path example
#     ENVIRONMENT="dev"
# )
# azul = PyAzul(settings=settings)
```

### Logging Configuration

By default, PyAzul minimizes log output in production. Most informational logs are set to `DEBUG` level. To enable detailed logging:

```python
import logging

# To see debug messages from all of pyazul
logging.getLogger('pyazul').setLevel(logging.DEBUG)

# Or for a specific service, e.g., SecureService
logging.getLogger('pyazul.services.secure').setLevel(logging.DEBUG)

# Ensure you have a handler configured (e.g., for console output):
logging.basicConfig(level=logging.DEBUG) # Basic configuration
# If you have an existing logging setup, adjust your handlers as needed.
```

## Core Functionality Examples

The following examples demonstrate common operations using the `PyAzul` facade. Ensure `azul = PyAzul()` has been initialized as shown above.

### Process a Payment (Non-3DS)

```python
from pyazul import PyAzul, AzulError
# from pyazul.models import SaleTransactionModel # Optional: use Pydantic model for request

# azul = PyAzul() # Initialization shown in "Quick Setup & Configuration"

async def process_payment():
    payment_data = {
        "Channel": "EC",
        "PosInputMode": "E-Commerce",
        "Amount": "100000",
        "Itbis": "18000",
        "CardNumber": "4111********1111", # Use a test card number
        "Expiration": "202812", # YYYYMM
        "CVC": "***",
        "CustomOrderId": "order-001",
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
# from pyazul import PyAzul, AzulError # Assuming PyAzul and AzulError are already imported
# azul = PyAzul() # Initialization shown in "Quick Setup & Configuration"

async def tokenize_card():
    token_creation_data = {
        "CardNumber": "4111********1111",
        "Expiration": "202812",
        "Store": "your_merchant_id", # Ensure this matches your Merchant ID
    }
    try:
        token_response = await azul.create_token(token_creation_data)
        if token_response.get("ResponseMessage") == "APROBADA":
            token_id = token_response.get("DataVaultToken")
            print(f"Token created: {token_id}")

            # Example: Use token for a non-3DS payment
            token_payment_data = {
                "Channel": "EC",
                "DataVaultToken": token_id,
                "Amount": "100000",
                "Itbis": "000",
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

### Payment Page Integration

This example uses FastAPI to return the HTML for Azul's hosted payment page.

```python
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pyazul import PyAzul # Assuming PyAzul is imported

# app = FastAPI() # Standard FastAPI app initialization
# azul = PyAzul() # Initialization shown in "Quick Setup & Configuration"

@app.get("/pay/{order_id}", response_class=HTMLResponse)
async def get_payment_page(order_id: str):
    page_data = {
        "Amount": "100000",
        "ITBIS": "18000",
        "OrderNumber": order_id,
        "ApprovedUrl": "https://your-site.com/success",
        "DeclineUrl": "https://your-site.com/declined",
        "CancelUrl": "https://your-site.com/cancel",
    }
    html_form = azul.payment_page(page_data)
    return HTMLResponse(content=html_form)
```

## 3D Secure Implementation Guide

PyAzul provides comprehensive support for 3D Secure 2.0. This section guides you through the multi-step 3DS flow. Ensure you have configured your credentials (`AUTH1`, `AUTH2`) in your `.env` file as outlined in the "Quick Setup & Configuration" section.

### Overview of the 3DS Flow with PyAzul

The 3DS process involves interactions between the customer's browser, your server, the card issuer's Access Control Server (ACS), and the Azul gateway. PyAzul simplifies this by:

1. Initiating the 3DS transaction and obtaining parameters from Azul.
2. Providing helpers for redirecting the user if a challenge is required.
3. Processing callbacks from the ACS (Method Notification and Challenge Completion).
4. Finalizing the transaction with Azul.

A unique `secure_id` (an ID, typically a UUID string, generated by PyAzul) is created during the initiation of a 3DS transaction (e.g., via `secure_sale`). PyAzul automatically appends this `secure_id` as a query parameter (e.g., `?secure_id=<generated_id>`) to the `TermUrl` and `MethodNotificationUrl` you provide. Your application must be prepared to extract this `secure_id` from the query string in your callback handlers to track the 3DS session.

### Application-Side State Management (Crucial for 3DS)

PyAzul's `SecureService` uses an internal, in-memory dictionary (`self.secure_sessions`) to temporarily store some transaction data (like `azul_order_id` received from Azul and the modified `term_url`) associated with the `secure_id`. This internal store is primarily for the library's own operational needs during the 3DS flow and is **not persistent across application restarts or multiple server instances.**

**For production environments, your application MUST implement its own robust session management solution** (e.g., using Redis, a database, or your web framework's session handling). This application-level session store is critical for reliably managing state across the asynchronous callbacks of the 3DS flow. You should use the `secure_id` (obtained from the initial 3DS call's response, e.g., `response.get("id")`, and from callback query parameters) as the key to store and retrieve:

-   Your internal order details or references.
-   The `azul_order_id` if it was returned in the initial response from `secure_sale` (it might be nested under `response.get("value", {}).get("AzulOrderId")`).
-   The original `TermUrl` you provided (needed for `create_challenge_form` if a challenge occurs after a method notification).
-   Any other application-specific data required to complete the order after the 3DS flow concludes.

PyAzul provides `await azul.get_secure_session_info(secure_id)` which allows you to inspect the limited data PyAzul stored internally for that `secure_id` (like `azul_order_id` and `term_url`). This can be useful as a fallback or for debugging but should not replace your application's primary session store.

The FastAPI example below uses a simple Python dictionary (`app_level_session_store`) for illustrative purposes of an application-level session. **Do not use this in-memory dictionary for production.**

### Complete 3D Secure Flow (FastAPI Example)

This example demonstrates the 3DS flow using FastAPI.

```python
from fastapi import FastAPI, Request, Form, Query
from fastapi.responses import HTMLResponse, JSONResponse
from pyazul import PyAzul, AzulError
# from pyazul.models import SecureSaleRequest # Optional: use Pydantic for request

app = FastAPI() # Initialize your FastAPI app
azul = PyAzul() # Initialize PyAzul (ensure 3DS settings are in .env)

# --- Application-Level Session Store (Example - REPLACE FOR PRODUCTION) ---
# This simple dictionary is for demonstration ONLY.
# Use a robust session management solution (Redis, database, etc.) in production.
app_level_session_store = {}
# --- End Example Session Store ---

# 1. Transaction Initiation Endpoint (Your Application)
@app.post("/initiate-3ds-payment")
async def initiate_3ds_payment(request_data: dict): # Process incoming payment data
    # Store the original TermUrl from the request for potential use in create_challenge_form
    # if a challenge arises after a 3DS method notification.
    original_term_url = request_data.get("threeDSAuth", {}).get("TermUrl", "")

    try:
        # Initiate the 3DS process via PyAzul SDK
        response = await azul.secure_sale(request_data)

        secure_id = response.get("id") # PyAzul's unique ID for this 3DS session

        # Attempt to get AzulOrderId if returned in the initial synchronous part of the response
        # This might be nested under a 'value' key for direct approvals/declines.
        azul_order_id_from_initial_response = None
        if response.get("value") and isinstance(response.get("value"), dict):
            azul_order_id_from_initial_response = response.get("value", {}).get("AzulOrderId")

        if secure_id:
            # Store essential data in YOUR application's session store for cross-callback access
            app_session_data = {
                "original_term_url": original_term_url, # Needed if challenge occurs after method step
                "azul_order_id": azul_order_id_from_initial_response, # May be None initially
                "internal_order_ref": request_data.get("OrderNumber"),
                # Add other application-specific data as needed
            }
            app_level_session_store[secure_id] = app_session_data

            # If AzulOrderId wasn't in the immediate response, try getting it from PyAzul's internal session
            # This is particularly relevant if the first step is a redirect (method/challenge)
            if not azul_order_id_from_initial_response:
                pyazul_internal_session = await azul.get_secure_session_info(secure_id)
                if pyazul_internal_session and pyazul_internal_session.get("azul_order_id"):
                    app_level_session_store[secure_id]["azul_order_id"] = pyazul_internal_session.get("azul_order_id")
                    print(f"Updated azul_order_id for {secure_id} from PyAzul session.")

        if response.get("redirect"):
            # HTML for immediate redirection (to 3DS Method URL or ACS Challenge)
            return HTMLResponse(content=response.get("html"))
        elif response.get("value", {}).get("ResponseMessage") == "APROBADA":
            # Approved directly by Azul (e.g., frictionless flow without redirects)
            return JSONResponse(content={"status": "approved_without_3ds_flow", "data": response.get("value")})
        else:
            # Other initial responses from Azul (e.g., declined before 3DS flow)
            return JSONResponse(content={"status": "error_or_declined_early", "data": response.get("value")}, status_code=400)
    except AzulError as e:
        return JSONResponse(content={"status": "sdk_error", "message": str(e)}, status_code=500)

# 2. 3DS Method Notification Callback Endpoint (Your MethodNotificationUrl)
@app.post("/capture-3ds-method") # Path must match your MethodNotificationUrl in the initial request
async def capture_3ds_method_callback(secure_id: str = Query(...)): # secure_id is appended by PyAzul
    try:
        # Retrieve your application's session data using secure_id
        app_session_data = app_level_session_store.get(secure_id)
        if not app_session_data:
            return JSONResponse(content={"error": "Application session not found for secure_id"}, status_code=404)

        azul_order_id = app_session_data.get("azul_order_id")
        original_term_url = app_session_data.get("original_term_url")

        # azul_order_id is required by PyAzul's process_3ds_method.
        # It should have been populated in the app_session_store by the /initiate-3ds-payment endpoint.
        if not azul_order_id:
            # As a fallback, try to get it from PyAzul's internal session again
            pyazul_session = await azul.get_secure_session_info(secure_id)
            if pyazul_session and pyazul_session.get("azul_order_id"):
                azul_order_id = pyazul_session.get("azul_order_id")
                app_level_session_store[secure_id]["azul_order_id"] = azul_order_id # Update your app session
            else:
                return JSONResponse(content={"error": "Azul Order ID not found or retrievable for secure_id"}, status_code=400)

        if not original_term_url:
            return JSONResponse(content={"error": "Original TermUrl not found in app session. This is needed for potential challenge forms."}, status_code=400)

        # Notify PyAzul that the 3DS Method information was processed by the cardholder's bank
        result = await azul.process_3ds_method( # Corrected method name
            azul_order_id=azul_order_id,
            method_notification_status="RECEIVED" # Standard status for successful method notification
        )

        if result.get("ResponseMessage") == "3D_SECURE_CHALLENGE":
            # Challenge is required; generate HTML form to redirect user to the ACS
            form_html = azul.create_challenge_form(
                result["ThreeDSChallenge"]["CReq"], # Challenge Request from Azul
                # Use the TermUrl from your app session, which PyAzul would have already appended secure_id to.
                # If PyAzul's internal term_url is preferred, get it from azul.get_secure_session_info(secure_id)
                app_level_session_store[secure_id].get("original_term_url") + f"?secure_id={secure_id}",
                result["ThreeDSChallenge"]["RedirectPostUrl"] # ACS URL from Azul
            )
            return HTMLResponse(content=form_html)
        elif result.get("ResponseMessage") == "APROBADA":
            # Approved after 3DS Method (e.g., frictionless flow, no challenge was needed)
            return JSONResponse(content={"status": "approved_after_method", "data": result})
        else:
            # Other outcomes (e.g., RECHAZADA, or still pending challenge if ACS flow differs)
            return JSONResponse(content={"status": "pending_or_error_after_method", "data": result})
    except AzulError as e:
        return JSONResponse(content={"status": "sdk_error", "message": str(e)}, status_code=500)

# 3. 3DS Challenge Completion Callback Endpoint (Your TermUrl)
@app.post("/post-3ds-callback") # Path must match your TermUrl in the initial request
async def post_3ds_challenge_callback(
    secure_id: str = Query(...), # secure_id is appended by PyAzul to TermUrl
    CRes: str = Form(...)        # CRes (Challenge Response) POSTed by ACS
):
    try:
        # Process the challenge response via PyAzul SDK
        final_result = await azul.process_challenge(session_id=secure_id, challenge_response=CRes) # Corrected parameter name

        if final_result.get("ResponseMessage") == "APROBADA":
            return JSONResponse(content={"status": "approved_after_challenge", "data": final_result})
        else:
            # Declined or error after challenge completion
            return JSONResponse(content={"status": "declined_or_error_after_challenge", "data": final_result}, status_code=400)
    except AzulError as e:
        return JSONResponse(content={"status": "sdk_error", "message": str(e)}, status_code=500)
```

### Key Considerations for 3DS

- **Callback URLs**: Ensure your `TermUrl` and `MethodNotificationUrl` (provided in the initial `secure_sale` call) correctly point to your server endpoints that can handle these callbacks and extract the `secure_id` query parameter.
- **`CardHolderInfo` and `ThreeDSAuth`**: Provide as much accurate data as possible in these objects during the `secure_sale` initiation to improve the chances of a frictionless flow and successful authentication.
- **Error Handling**: Implement robust error handling for each step, including checking responses from PyAzul and handling potential `AzulError` exceptions.

## Request Data and Pydantic Models

PyAzul methods, accessed via the `PyAzul` facade, primarily accept Python dictionaries for request data. For enhanced type safety and autocompletion in your development environment, you can use PyAzul's Pydantic models (found in `pyazul.models`).

When using Pydantic models, you construct the model instance and then pass `model_instance.model_dump(exclude_none=True)` to the PyAzul method.

### Data Formatting (e.g., Amount, ITBIS)

The SDK's internal Pydantic models automatically handle the formatting of fields like `Amount` and `ITBIS`. You can provide these as:

- Integers (representing cents, e.g., `100000` for $1,000.00)
- Floats (representing cents, e.g., `100000.00`)
- Pre-formatted strings of cents (e.g., `"100000"`)
  The SDK ensures they are converted to the string format required by the external Azul API.

```python
from pyazul.models import SaleTransactionModel # Import specific model

# Example: Using a dictionary (common approach)
payment_dict = {
    "CardNumber": "4111...", "Expiration": "202812", "CVC": "123",
    "Amount": 50000,  # 500.00 (as integer cents)
    "Itbis": 0,       # 0.00 (as integer cents)
    "OrderNumber": "MYORDER001", "Store": "your_merchant_id"
}
# response = await azul.sale(payment_dict)

# Example: Using a Pydantic model
data_model = SaleTransactionModel(
    CardNumber="4111...", Expiration="202812", CVC="123",
    Amount=50000, # 500.00
    Itbis=0,
    OrderNumber="MYORDER001", Store="your_merchant_id"
)
# response = await azul.sale(data_model.model_dump(exclude_none=True))
```

Refer to `pyazul/models/schemas.py` and `pyazul/models/secure.py` for detailed field definitions.

## Example Data Structures (Dictionaries)

Below are common request structures as Python dictionaries.

### Basic Transaction Models

```python
# Card Sale Transaction
{
    "CardNumber": "4111111111111111", "Expiration": "202812", "CVC": "123",
    "Amount": "100000",   # Or integer 100000
    "Itbis": "18000",    # Or integer 18000
    "OrderNumber": "INV-12345",
    "CustomOrderId": "order-123", # Optional
    "SaveToDataVault": "2"  # Optional: "1" to save, "2" (default) not to save
    # "Store": "your_merchant_id" # Required if not matching default in settings
}

# Other non-3DS models (TokenSale, Hold, PostSale, Void, Refund, Verify)
# generally involve similar fields or specific identifiers like AzulOrderId or DataVaultToken.
# Consult model files for specifics.
```

### 3D Secure Models

Essential components for a `secure_sale` request:

```python
# Cardholder Information (part of cardHolderInfo object)
{
    "BillingAddressCity": "Santo Domingo", "BillingAddressCountry": "DO",
    "BillingAddressLine1": "Main Street #123", "BillingAddressState": "Distrito Nacional",
    "BillingAddressZip": "10101", "Email": "customer@example.com", "Name": "John Doe",
    # Other fields like Phone1, ShippingAddress, etc., are available.
}

# 3DS Authentication Parameters (part of threeDSAuth object)
{
    "TermUrl": "https://your-site.com/3ds-complete-callback", # PyAzul appends ?secure_id=...
    "MethodNotificationUrl": "https://your-site.com/3ds-method-callback", # PyAzul appends ?secure_id=...
    "RequestChallengeIndicator": "03" # e.g., "01": No preference, "03": Prefer challenge
}

# Full 3DS Secure Sale Request (Example for azul.secure_sale)
{
    "CardNumber": "4111111111111111", "Expiration": "202812", "CVC": "123",
    "Amount": 100000,      # Integer cents
    "Itbis": 18000,        # Integer cents
    "OrderNumber": "3DS-ORDER-123",
    "Store": "your_merchant_id", # Required
    "forceNo3DS": "0",     # "0" to enable 3DS, "1" to attempt non-3DS
    "cardHolderInfo": {
        "Name": "John Doe", "Email": "john@example.com",
        "BillingAddressCity": "Santo Domingo", "BillingAddressCountry": "DO",
        "BillingAddressLine1": "Main St #123", "BillingAddressState": "Distrito Nacional",
        "BillingAddressZip": "10101"
        # ... other cardHolderInfo fields
    },
    "threeDSAuth": {
        "TermUrl": "https://your-domain.com/post-3ds-callback",
        "MethodNotificationUrl": "https://your-domain.com/capture-3ds-method",
        "RequestChallengeIndicator": "03"
        # ... other threeDSAuth fields
    }
}
# SecureTokenSale and SecureHold follow similar patterns, using DataVaultToken instead of full card details for SecureTokenSale.
```

## API Reference

The `PyAzul` object is your main entry point and acts as a facade to the SDK's capabilities. Key methods include:

```python
# azul = PyAzul() # Assumed initialized

# --- Non-3DS Transaction processing ---
# await azul.sale(data_dict_or_model_dump)
# await azul.token_sale(data_dict_or_model_dump)
# await azul.hold(data_dict_or_model_dump)
# await azul.post_sale(data_dict_or_model_dump) # Capture an existing hold
# await azul.void(data_dict_or_model_dump)
# await azul.refund(data_dict_or_model_dump)
# await azul.verify(data_dict_or_model_dump)   # Verify transaction status

# --- Card Tokenization (DataVault) ---
# await azul.create_token(data_dict_or_model_dump)
# await azul.delete_token(data_dict_or_model_dump)

# --- Payment Page ---
# html_form_string = azul.payment_page(data_dict_or_model_dump)

# --- 3D Secure ---
# response_dict = await azul.secure_sale(data_dict_or_model_dump)
# response_dict = await azul.secure_token_sale(data_dict_or_model_dump)
# response_dict = await azul.secure_hold(data_dict_or_model_dump)

# --- 3DS Callback Helpers ---
# response_dict = await azul.process_3ds_method(azul_order_id="...", method_notification_status="...")
# response_dict = await azul.process_challenge(session_id="...", challenge_response="...")
# html_form_string = azul.create_challenge_form(creq="...", term_url="...", redirect_post_url="...")

# --- 3DS Session Inspection (for debugging) ---
# session_data_dict = await azul.get_secure_session_info(session_id="...")

# Access to underlying components (generally not needed for typical use):
# azul.transaction  # Instance of TransactionService
# azul.datavault    # Instance of DataVaultService
# azul.payment_page # Instance of PaymentPageService
# azul.secure       # Instance of SecureService
# azul.api          # Instance of AzulAPI (the HTTP client for external Azul API)
# azul.settings     # The active AzulSettings instance
```

## Error Handling

The PyAzul SDK uses a hierarchy of custom exceptions (all inheriting from `pyazul.AzulError`) to report issues:

- `pyazul.core.exceptions.AzulError`: Base exception for the library.
- `pyazul.core.exceptions.SSLError`: For SSL certificate loading or configuration problems.
- `pyazul.core.exceptions.APIError`: For general HTTP client issues or problems communicating with the external Azul API (e.g., network errors, unexpected responses not covered by `AzulResponseError`).
- `pyazul.core.exceptions.AzulResponseError`: Raised when the external Azul API explicitly returns an error in its response payload (e.g., transaction declined, invalid field).
  - This exception has a `response_data` attribute containing the raw dictionary response from Azul for inspection.
  - The error message usually includes `ErrorMessage` or `ErrorDescription` from the Azul response.

Always wrap calls to PyAzul SDK methods in `try...except` blocks:

```python
from pyazul import AzulError # Or from pyazul.core.exceptions import AzulError, AzulResponseError, etc.

try:
    # response = await azul.sale({...})
    pass # Replace with your PyAzul SDK call
except AzulResponseError as e:
    print(f"The external Azul API returned an error: {e.message}")
    print(f"Azul Response Data: {e.response_data}")
except APIError as e:
    print(f"API communication error: {e}")
except SSLError as e:
    print(f"SSL configuration error: {e}")
except AzulError as e: # Catch-all for other PyAzul SDK specific errors
    print(f"An error occurred within the PyAzul SDK: {e}")
except Exception as e: # Catch any other unexpected errors
    print(f"An unexpected error occurred: {e}")
```

## More Information about Azul

For complete official documentation on the external Azul API, services, and field specifications, refer to the [Azul Developer Portal](https://dev.azul.com.do/docs/desarrolladores). (This link is subject to change; please verify on Azul's official website if it becomes outdated).

---

&copy; MIT License
