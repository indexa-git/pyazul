![Build & publish](https://github.com/indexa-git/pyazul/workflows/Build%20&%20publish/badge.svg)

# PyAzul

Python client for Azul Payment Gateway. Process payments, tokenize cards, and implement 3D Secure authentication with minimal setup.

## Installation

```bash
pip install pyazul
```

## Quick Setup

Create a `.env` file with your credentials:

```bash
# Basic API credentials
AUTH1=your_auth1
AUTH2=your_auth2
MERCHANT_ID=your_merchant_id
AZUL_CERT=/path/to/certificate.pem  # Can be path or PEM content
AZUL_KEY=/path/to/key.pem    # Can be path, PEM content, or Base64 PEM content
ENVIRONMENT=dev  # or 'prod'

# Payment Page settings (optional)
AZUL_MERCHANT_ID=your_merchant_id_for_page # Typically same as MERCHANT_ID
AZUL_AUTH_KEY=your_auth_key_for_page
MERCHANT_NAME=Your_Business_Name
MERCHANT_TYPE=Your_Business_Type

# 3D Secure settings (REQUIRED for 3DS)
AUTH1_3D=your_auth1_3d
AUTH2_3D=your_auth2_3d
```

Certificates (`AZUL_CERT`, `AZUL_KEY`) can be provided as file paths or as the direct PEM string content within the `.env` file. The key can also be base64 encoded PEM content.

## Basic Usage

Initialize PyAzul:

```python
from pyazul import PyAzul

azul = PyAzul()  # Uses environment variables by default
# For custom settings:
# from pyazul.core.config import AzulSettings
# settings = AzulSettings(AUTH1="...", AZUL_CERT="...", ...)
# azul = PyAzul(settings=settings)
```

### Process a Payment (Non-3DS)

```python
from pyazul import PyAzul, AzulError
# from pyazul.models import SaleTransactionModel # Optional: use Pydantic model

azul = PyAzul()

async def process_payment():
    payment_data = {
        "Channel": "EC", # Usually "EC"
        "PosInputMode": "E-Commerce", # Usually "E-Commerce"
        "Amount": "100000",           # $1,000.00 (in cents)
        "Itbis": "18000",             # $180.00 tax (in cents)
        "CardNumber": "4111********1111", # Use a test card
        "Expiration": "202812", # YYYYMM
        "CVC": "***",
        "CustomOrderId": "order-001", # Optional
        "OrderNumber": "INV-12345", # Your internal order number
        # "SaveToDataVault": "1" # Optional: "1" to save card to DataVault, "2" not to save
    }
    try:
        # response = await azul.sale(SaleTransactionModel(**payment_data)) # With Pydantic model
        response = await azul.sale(payment_data) # With dictionary

        if response.get("ResponseMessage") == "APROBADA":
            print(f"Payment approved: {response.get('AuthorizationCode')}, AzulOrderId: {response.get('AzulOrderId')}")
        else:
            print(f"Error: {response.get('ResponseMessage')}, Details: {response.get('ErrorDescription', response)}")
    except AzulError as e:
        print(f"An API error occurred: {e}")

```

### Tokenize a Card

```python
async def tokenize_card():
    # Create token
    token_creation_data = {
        "CardNumber": "4111********1111",
        "Expiration": "202812",
        "store": "your_merchant_id" # Your Merchant ID for DataVault
        # "CustomOrderId": "optional-token-order-id"
    }
    try:
        token_response = await azul.create_token(token_creation_data)

        if token_response.get("ResponseMessage") == "APROBADA":
            token_id = token_response.get("DataVaultToken")
            print(f"Token created: {token_id}")

            # Use token for payment (Example, can be non-3DS or 3DS)
            token_payment_data = {
                "Channel": "EC",
                "DataVaultToken": token_id,
                "Amount": "100000",
                "Itbis": "000", # Example: no ITBIS
                "CustomOrderId": "token-payment-001"
            }
            payment_response = await azul.token_sale(token_payment_data) # Non-3DS token sale
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

This example uses FastAPI to expose an endpoint that returns the HTML for Azul's payment page.

```python
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pyazul import PyAzul

app = FastAPI()
azul = PyAzul() # Ensure Payment Page settings are in .env

@app.get("/pay/{order_id}", response_class=HTMLResponse)
async def get_payment_page(order_id: str):
    page_data = {
        "Amount": "100000",           # $1,000.00
        "ITBIS": "18000",             # $180.00
        "OrderNumber": order_id,      # Your internal order number
        "ApprovedUrl": "https://your-site.com/success",
        "DeclineUrl": "https://your-site.com/declined",
        "CancelUrl": "https://your-site.com/cancel",
        # Optional custom fields:
        # "UseCustomField1": "1",
        # "CustomField1Label": "Order Reference",
        # "CustomField1Value": f"REF-{order_id}"
    }
    # create_payment_page returns the HTML form string
    html_form = azul.create_payment_page(page_data)
    return HTMLResponse(content=html_form)
```

## 3D Secure Implementation

PyAzul provides a comprehensive 3D Secure 2.0 integration.

### Proper Initialization for 3D Secure

To use the 3D Secure service, ensure your `.env` file (or `AzulSettings` if configuring programmatically) includes your 3DS-specific credentials:

```bash
# .env file
# ... other settings ...
AUTH1_3D=your_auth1_3d
AUTH2_3D=your_auth2_3d
```

PyAzul automatically uses these credentials when you call 3DS-related methods.

```python
from pyazul import PyAzul

# Initialize PyAzul - it will pick up 3DS credentials from environment/settings
azul = PyAzul()
```

### Complete 3D Secure Flow

The 3DS process requires multiple steps, all accessible via the `PyAzul` instance. This example uses FastAPI.

It's common for applications to manage some state across the 3DS callback steps (e.g., linking `secure_id` to an internal order or `azul_order_id`). The example below includes a simple dictionary (`app_level_session_store`) to illustrate this concept; replace this with your application's actual session management.

1. **Transaction Initiation**:
   Initiate a 3DS sale (or hold, or token sale). PyAzul automatically appends a unique `secure_id` to your callback URLs (`TermUrl`, `MethodNotificationUrl`) for session tracking.

   ```python
   from fastapi import FastAPI, Request, Form, Query
   from fastapi.responses import HTMLResponse, JSONResponse
   from pyazul import PyAzul, AzulError
   # from pyazul.models import SecureSaleRequest # Optional: use Pydantic model

   app = FastAPI()
   azul = PyAzul() # Ensure AUTH1_3D, AUTH2_3D are in your .env or settings

   # Example: In-memory store for application-level linking of 3DS IDs and data.
   # Replace with your application's session/state management solution.
   app_level_session_store = {}

   @app.post("/initiate-3ds-payment")
   async def initiate_3ds_payment(request_data: dict): # Assuming data comes in request body
       original_term_url = request_data.get("threeDSAuth", {}).get("TermUrl", "")

       try:
           response = await azul.secure_sale(request_data)

           secure_id = response.get("id")
           # `azul_order_id` may be in the initial response if directly approved,
           # otherwise it's primarily managed internally by pyazul linked to `secure_id`.
           azul_order_id_from_response = response.get("value", {}).get("AzulOrderId")

           if secure_id: # Store for your application's reference across callbacks
               app_level_session_store[secure_id] = {
                   "original_term_url": original_term_url,
                   "azul_order_id": azul_order_id_from_response # May be None if redirect flow starts
               }

           if response.get("redirect"):
               # This HTML contains the form for 3DS Method URL or Challenge ACS Redirection
               return HTMLResponse(content=response.get("html"))
           elif response.get("value", {}).get("ResponseMessage") == "APROBADA":
               return JSONResponse(content={"status": "approved_without_3ds_flow", "data": response.get("value")})
           else:
               return JSONResponse(content={"status": "error_or_declined", "data": response.get("value")}, status_code=400)
       except AzulError as e:
           return JSONResponse(content={"status": "api_error", "message": str(e)}, status_code=500)
   ```

2. **3DS Method Processing (Callback)**:
   This endpoint (`MethodNotificationUrl`) is called by the ACS/PSP. PyAzul handles session state internally using `secure_id`.

   ```python
   @app.post("/capture-3ds-method") # Ensure this matches your MethodNotificationUrl path
   async def capture_3ds_method_callback(request: Request, secure_id: str = Query(...)): # secure_id from query param
       try:
           # Retrieve necessary data linked to secure_id from your application's state.
           app_session_data = app_level_session_store.get(secure_id)
           if not app_session_data:
               return JSONResponse(content={"error": "Application session data not found for secure_id"}, status_code=400)

           azul_order_id = app_session_data.get("azul_order_id")
           original_term_url = app_session_data.get("original_term_url")

           # If azul_order_id wasn't in the initial `secure_sale` response (e.g. because it went straight to redirect),
           # pyazul has stored it internally. `secure_3ds_method` requires it. The current library version
           # expects the user to provide it. Future versions might offer helpers.
           if not azul_order_id:
                # This indicates a need to fetch the AzulOrderId linked to secure_id from pyazul's internal session,
                # or ensure it was captured and stored by the application earlier.
                # For this example, we assume it must have been captured if this flow is to work as PyAzul expects.
                # As a fallback, you might re-query the initial transaction if your app stored OrderNumber/CustomOrderId.
                # However, pyazul's SecureService *does* store azul_order_id against secure_id internally.
                # This example proceeds assuming `azul_order_id` was obtained and stored by the app.
                return JSONResponse(content={"error": "Azul Order ID not available from initial app session for secure_id"}, status_code=400)

           if not original_term_url:
                return JSONResponse(content={"error": "Original TermUrl not available from initial app session for secure_id"}, status_code=400)

           result = await azul.secure_3ds_method(
               azul_order_id=azul_order_id,
               method_notification_status="RECEIVED"
           )

           if result.get("ResponseMessage") == "3D_SECURE_CHALLENGE":
               form_html = azul.create_challenge_form(
                   result["ThreeDSChallenge"]["CReq"],
                   original_term_url, # Use the TermUrl you originally sent to Azul
                   result["ThreeDSChallenge"]["RedirectPostUrl"]
               )
               return HTMLResponse(content=form_html)
           elif result.get("ResponseMessage") == "APROBADA":
               return JSONResponse(content={"status": "approved_after_method", "data": result})
           else:
               # Other responses (e.g. RECHAZADA, ERROR, or waiting for challenge via TermUrl)
               return JSONResponse(content={"status": "pending_or_error", "data": result})
       except AzulError as e:
           return JSONResponse(content={"status": "api_error", "message": str(e)}, status_code=500)
   ```

3. **3DS Challenge Processing (Callback)**:
   This is your `TermUrl` endpoint. It receives the `CRes` (Challenge Response) from the ACS, typically via a POST request.

   ```python

   @app.post("/post-3ds-callback") # Ensure this matches your TermUrl path
   async def post_3ds_challenge_callback(
       secure_id: str = Query(...), # secure_id from TermUrl query parameter
       CRes: str = Form(...)
   ):
       try:
           final_result = await azul.secure_challenge(secure_id=secure_id, cres=CRes)

           if final_result.get("ResponseMessage") == "APROBADA":
               return JSONResponse(content={"status": "approved_after_challenge", "data": final_result})
           else:
               return JSONResponse(content={"status": "declined_or_error_after_challenge", "data": final_result}, status_code=400)
       except AzulError as e:
           return JSONResponse(content={"status": "api_error", "message": str(e)}, status_code=500)
   ```

### Important Notes on 3DS

- The `secure_id` generated during transaction initiation is key. PyAzul automatically appends it to your `TermUrl` and `MethodNotificationUrl`. Ensure your callback handlers can receive it (e.g., as a query parameter).
- 3DS Session management is currently handled internally by `pyazul` using in-memory storage. For environments requiring persistent or shared session state across multiple instances, you would need to manage the linkage between `secure_id` and necessary transaction data (like `azul_order_id` and original `TermUrl`) within your application's own session management system.
- `CardHolderInfo` and `ThreeDSAuth` details are critical for successful 3DS 2.0 authentication.
- Error handling: Catch `AzulError` and its derivatives (`AzulResponseError`, `APIError`, `SSLError`) for issues during API calls.

## API Reference

### Main `PyAzul` Object

The `PyAzul` object is your main entry point.

```python
from pyazul import PyAzul
azul = PyAzul()

# Access to underlying services if needed (though direct methods on `azul` are preferred)
# azul.transaction  (TransactionService)
# azul.datavault    (DataVaultService)
# azul.payment_page (PaymentPageService)
# azul.secure       (SecureService)
# azul.api          (AzulAPI - the shared HTTP client)
# azul.settings     (AzulSettings - current configuration)
```

### Key Methods on `PyAzul`

```python
# --- Non-3DS Transaction processing ---
await azul.sale({...})              # Direct card payment
await azul.token_sale({...})        # Payment with token
await azul.hold({...})              # Authorization hold
await azul.post_sale({...})         # Capture authorized payment
await azul.void({...})              # Void transaction
await azul.refund({...})            # Refund transaction
await azul.verify({...})            # Verify transaction status

# --- Card tokenization (DataVault) ---
await azul.create_token({...})      # Create card token
await azul.delete_token({...})      # Delete card token

# --- Payment Page ---
azul.create_payment_page({...})     # Returns HTML string for payment form

# --- 3D Secure ---
await azul.secure_sale({...})        # 3DS card payment
await azul.secure_token_sale({...})  # 3DS token payment
await azul.secure_hold({...})        # 3DS card hold transaction
# Callbacks for 3DS flow:
await azul.secure_3ds_method(azul_order_id="...", method_notification_status="...") # Process 3DS method notification
await azul.secure_challenge(secure_id="...", cres="...")     # Process 3DS challenge result
azul.create_challenge_form(creq="...", term_url="...", redirect_post_url="...") # Helper to get HTML for challenge form
```

## Request Data and Pydantic Models

PyAzul methods primarily accept Python dictionaries as input for request data. For enhanced type safety and auto-completion, you can use the Pydantic models provided by the library. All models are available under `pyazul.models`.

```python
from pyazul.models import SaleTransactionModel, SecureSaleRequest # etc.

# Example using a Pydantic model:
data_model = SaleTransactionModel(
    CardNumber="4111...",
    Expiration="202812",
    CVC="123",
    Amount="5000", # 50.00
    Itbis="000",
    OrderNumber="MYORDER001"
)
response = await azul.sale(data_model.model_dump()) # Pass as dict
# or some methods might accept the model instance directly if type hints allow:
# response = await azul.sale(data_model) # Check method signature
```

Refer to the `pyazul/models/schemas.py` and `pyazul/models/secure.py` files for detailed field definitions within each model. Below are common examples as dictionaries.

(The rest of the "Request Data Reference" sections for Basic Transactions, Token Ops, Payment Page, 3DS Models can largely remain the same, as they show dictionary structures, which are still supported. Ensure amounts in 3DS examples are integers if that's what SecureSaleRequest expects, or strings if they are converted.)

### Basic Transaction Models (Example Dictionaries)

```python
# Card Sale Transaction
{
    "CardNumber": "4111111111111111",
    "Expiration": "202812",  # YYYYMM format
    "CVC": "123",
    "Amount": "100000",      # $1,000.00 (as string of cents)
    "Itbis": "18000",        # $180.00 (as string of cents)
    "CustomOrderId": "order-123", # Optional
    "OrderNumber": "INV-12345",   # Your internal order ID
    "SaveToDataVault": "2"  # Optional: '1' to save, '2' (default) not to save
}

# ... other non-3DS models remain similar ...
```

### 3D Secure Models (Example Dictionaries)

Note: For 3DS `Amount` and `ITBIS` in `SecureSaleRequest`, `SecureTokenSale`, these are often expected as integers (cents) by the Pydantic models, but the service layer converts to string for the API. Pass as integers if using Pydantic models directly, or strings if passing dicts and the model handles conversion. The examples below use integers for `Amount`/`ITBIS` as often preferred for clarity before model conversion.

```python
# Cardholder Information (part of 3DS requests)
{
    "BillingAddressCity": "Santo Domingo",
    "BillingAddressCountry": "DO",
    "BillingAddressLine1": "Main Street #123",
    # ... other cardHolderInfo fields
    "Email": "customer@example.com",
    "Name": "John Doe",
}

# 3DS Authentication Parameters (part of 3DS requests)
{
    "TermUrl": "https://your-site.com/3ds-complete-callback", # PyAzul appends ?secure_id=...
    "MethodNotificationUrl": "https://your-site.com/3ds-method-callback", # PyAzul appends ?secure_id=...
    "RequestChallengeIndicator": "03"  # "01": No preference, "02": No challenge, "03": Prefer challenge, "04": Mandate challenge
}

# 3DS Direct Card Payment (Example Dictionary for azul.secure_sale)
{
    "CardNumber": "4111111111111111",
    "Expiration": "202812",
    "CVC": "123",
    "Amount": 100000,           # $1,000.00 (in cents, as integer)
    "ITBIS": 18000,             # $180.00 tax (in cents, as integer)
    "OrderNumber": "3DS-ORDER-123",
    # "Channel": "EC", # Usually set by library
    # "PosInputMode": "E-Commerce", # Usually set by library
    "forceNo3DS": "0",          # "0" to enable 3DS
    "cardHolderInfo": {
        # Cardholder info dictionary as shown above
        "Name": "John Doe",
        "Email": "john@example.com",
        "BillingAddressCity": "Santo Domingo",
        "BillingAddressCountry": "DO",
        "BillingAddressLine1": "Main St #123",
        "BillingAddressState": "Distrito Nacional",
        "BillingAddressZip": "10101"
    },
    "threeDSAuth": {
        # 3DS Authentication Parameters dictionary as shown above
        "TermUrl": "https://your-domain.com/post-3ds-callback",
        "MethodNotificationUrl": "https://your-domain.com/capture-3ds-method",
        "RequestChallengeIndicator": "03"
    }
}

# ... other 3DS models like SecureTokenSale follow a similar pattern ...
```

## Error Handling

PyAzul uses custom exceptions to indicate issues:

- `pyazul.AzulError`: Base exception for the library.
- `pyazul.SSLError`: For SSL certificate related problems.
- `pyazul.APIError`: For general HTTP client or API communication issues.
- `pyazul.AzulResponseError`: When the Azul API returns a known error (e.g., transaction declined, invalid data). The `response_data` attribute of this exception contains the raw dictionary from Azul.

Always wrap calls to PyAzul methods in `try...except AzulError:` blocks.

```python
try:
    response = await azul.sale({...})
except AzulResponseError as e:
    print(f"Azul returned an error: {e.message}")
    print(f"Full response data: {e.response_data}")
except AzulError as e:
    print(f"An error occurred: {e}")
```

## More Information about Azul

For complete official API documentation, see the [Azul Developer Portal](https://dev.azul.com.do/docs/desarrolladores). (Link might vary, ensure it's current).

---

&copy; LGPL License
