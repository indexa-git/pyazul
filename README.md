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
AZUL_CERT=/path/to/certificate.pem
AZUL_KEY=/path/to/key.pem
ENVIRONMENT=dev  # or 'prod'

# Payment Page settings (optional)
AZUL_MERCHANT_ID=your_merchant_id
AZUL_AUTH_KEY=your_auth_key
MERCHANT_NAME=Your_Business_Name
MERCHANT_TYPE=Your_Business_Type

# 3D Secure settings (optional)
AUTH1_3D=your_auth1_3d
AUTH2_3D=your_auth2_3d
```

## Basic Usage

### Process a Payment

```python
from pyazul import PyAzul

azul = PyAzul()  # Uses environment variables

async def process_payment():
    response = await azul.sale({
        "Channel": "EC",
        "PosInputMode": "E-Commerce",
        "Amount": "100000",           # $1,000.00 (in cents)
        "Itbis": "18000",             # $180.00 tax (in cents)
        "CardNumber": "4111********1111",
        "Expiration": "2028**",
        "CVC": "***",
        "CustomOrderId": "order-001",
        "OrderNumber": "INV-12345",
    })
    
    if response.get("ResponseMessage") == "APROBADA":
        print(f"Payment approved: {response.get('AuthorizationCode')}")
    else:
        print(f"Error: {response.get('ResponseMessage')}")
```

### Tokenize a Card

```python
async def tokenize_card():
    # Create token
    token_response = await azul.create_token({
        "CardNumber": "4111********1111",
        "Expiration": "2028**",
        "store": "39038540035"
    })
    
    token_id = token_response.get("DataVaultToken")
    
    # Use token for payment
    await azul.token_sale({
        "Channel": "EC",
        "DataVaultToken": token_id,
        "Amount": "100000",
        "CustomOrderId": "token-payment-001"
    })
```

### Payment Page Integration

This examples use fastapi to exponds the endpoint to render the payment page
```python
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pyazul import PyAzul

app = FastAPI()
azul = PyAzul()

@app.get("/pay/{order_id}", response_class=HTMLResponse)
async def payment_page(order_id: str):
    return azul.create_payment_page({
        "Amount": "100000",           # $1,000.00
        "ITBIS": "18000",             # $180.00
        "CustomOrderId": order_id,
        "ApprovedUrl": "https://your-site.com/success",
        "DeclineUrl": "https://your-site.com/declined",
        "CancelUrl": "https://your-site.com/cancel"
    })
```

## 3D Secure Implementation

PyAzul provides a comprehensive 3D Secure 2.0 integration that enables secure transactions with advanced authentication. The complete flow consists of several steps and requires proper client initialization.

### Proper Initialization

**Important**: To use the 3DS service, you must explicitly pass an `AzulAPI` instance to the PyAzul constructor:

```python
from pyazul import PyAzul
from pyazul.api.client import AzulAPI

# Create the API client first
api_client = AzulAPI()

# Pass the API client to PyAzul
azul = PyAzul(api_client=api_client)
```

### Complete 3D Secure Flow

The 3DS process requires multiple steps:

1. **Transaction Initiation**:
```python
# You can pass a simple dictionary (no need to create a Pydantic model)
response = await azul.secure_sale({
    "CardNumber": "4111111111111111",
    "Expiration": "202812",
    "CVC": "123",
    "Amount": 100000,         # $1,000.00 (in cents)
    "ITBIS": 18000,           # $180.00 (in cents)
    "OrderNumber": "ORDER123",
    "Channel": "EC",
    "PosInputMode": "E-Commerce",
    "forceNo3DS": "0",
    "cardHolderInfo": {
        "Name": "John Doe",
        "Email": "john@example.com",
        "BillingAddressCity": "Santo Domingo",
        "BillingAddressCountry": "DO",
        "BillingAddressLine1": "Main Street #123",
        "BillingAddressState": "National District",
        "BillingAddressZip": "10101",
        "ShippingAddressCity": "Santo Domingo",
        "ShippingAddressCountry": "DO",
        "ShippingAddressLine1": "Main Street #123",
        "ShippingAddressState": "National District",
        "ShippingAddressZip": "10101"
    },
    "threeDSAuth": {
        "TermUrl": "https://your-domain.com/post-3ds",
        "MethodNotificationUrl": "https://your-domain.com/capture-3ds",
        "RequestChallengeIndicator": "03"  # Request challenge
    }
})

# The library automatically stores session details
if response.get("redirect"):
    secure_id = response.get("id")
    
    # Return HTML form to client to continue 3DS process
    html_form = response.get("html")
```

2. **3DS Method Processing**:
```python
# When you receive 3DS method notification:
@app.post("/capture-3ds")
async def capture_3ds(request: Request, secure_id: str = None):
    # The library automatically manages sessions internally
    # Get the session data from the secure service
    session = azul.secure.secure_sessions.get(secure_id)
    
    if not session:
        return {"error": "Invalid session"}
    
    # Process 3DS method notification
    result = await azul.secure_3ds_method(
        session["azul_order_id"],
        "RECEIVED"  # Notification status
    )
    
    # Check if challenge is required
    if result.get("ResponseMessage") == "3D_SECURE_CHALLENGE":
        # Generate HTML form for the challenge
        form_html = azul.create_challenge_form(
            result["ThreeDSChallenge"]["CReq"],
            session["term_url"],
            result["ThreeDSChallenge"]["RedirectPostUrl"]
        )
        return {"redirect": True, "html": form_html}
```

3. **3DS Challenge Processing**:
```python
@app.post("/post-3ds")
async def post_3ds(request: Request, secure_id: str = None, cres: str = None):
    # Complete the process with the challenge response
    result = await azul.secure_challenge(secure_id, cres)
    # Process final response
    return result
```

### Important Notes

- The library automatically manages 3DS sessions internally through the `secure_sessions` attribute.
- For production systems, you may want to implement your own session storage system for better persistence and reliability.
- The `secure_id` is the key to access session data throughout the 3DS flow.

## API Reference

### Main Services

- **Transaction Service**: `azul.transaction` - Payment processing
- **DataVault Service**: `azul.datavault` - Card tokenization
- **Payment Page Service**: `azul.payment_page` - Payment form generation
- **Secure Service**: `azul.secure` - 3D Secure authentication

### Key Methods

```python
# Transaction processing
await azul.sale({...})              # Direct card payment
await azul.hold({...})              # Authorization hold
await azul.post_sale({...})         # Capture authorized payment
await azul.void({...})              # Void transaction
await azul.refund({...})            # Refund transaction
await azul.verify({...})            # Verify transaction status

# Card tokenization
await azul.create_token({...})      # Create card token
await azul.delete_token({...})      # Delete card token
await azul.token_sale({...})        # Payment with token

# Payment Page
azul.create_payment_page({...})     # Generate payment form

# 3D Secure
await azul.secure_sale({...})        # 3DS card payment
await azul.secure_hold({...})        # 3DS card hold transaction
await azul.secure_token_sale({...})  # 3DS token payment
await azul.secure_3ds_method(...)    # Process 3DS method notification
await azul.secure_challenge(...)     # Process 3DS challenge result
```

## Request Data Reference

> **Note**: These examples show the structure of data expected by PyAzul methods. You can pass dictionaries with these fields directly to the methods without manually creating Pydantic instances.


### Basic Transaction Models

```python
# Card Sale Transaction
{
    "CardNumber": "4111111111111111",
    "Expiration": "202812",  # YYYYMM format
    "CVC": "123",
    "Amount": "100000",      # $1,000.00
    "Itbis": "18000",        # $180.00
    "CustomOrderId": "order-123", #Optional
    "OrderNumber": "INV-12345",
    "SaveToDataVault": '1 - Save to token' | '2 - Do not save'
}

# Authorization Hold
{
    "CardNumber": "4111111111111111",
    "Expiration": "202812",
    "CVC": "123",
    "Amount": "100000",
    "Itbis": "18000",
    "CustomOrderId": "hold-123" 
}

# Refund Transaction
{
    "AzulOrderId": "12345678",
    "Amount": "100000"
}

# Void Transaction
{
    "AzulOrderId": "12345678",
    "store": "39038540035"
}

# Verify Transaction
{
    "CustomOrderId": "order-123"
}

# Post Sale (Capture)
{
    "AzulOrderId": "12345678",
    "Amount": "100000",
    "Itbis": "18000"
}
```

### Token Operations

```python
# Create Card Token
{
    "CardNumber": "4111111111111111",
    "Expiration": "202812",
    "store": "39038540035",
    "CustomOrderId": "token-123"
}

# Delete Card Token
{
    "DataVaultToken": "a1b2c3d4e5f6",
    "store": "39038540035"
}

# Payment using Token
{
    "DataVaultToken": "a1b2c3d4e5f6",
    "Amount": "100000",
    "Itbis": "18000",
    "CustomOrderId": "token-sale-123",
    "Channel": "EC"
}
```

### Payment Page Configuration

```python
# Payment Page Integration
{
    "Amount": "100000",      # $1,000.00
    "ITBIS": "18000",        # $180.00
    "ApprovedUrl": "https://your-site.com/success",
    "DeclineUrl": "https://your-site.com/declined",
    "CancelUrl": "https://your-site.com/cancel",
    "UseCustomField1": "1",
    "CustomField1Label": "Order Reference",
    "CustomField1Value": "ORD-123456"
}
```

### 3D Secure Models

```python
# Cardholder Information
{
    "BillingAddressCity": "Santo Domingo",
    "BillingAddressCountry": "DO",
    "BillingAddressLine1": "Main Street #123",
    "BillingAddressState": "National District",
    "BillingAddressZip": "10101",
    "Email": "customer@example.com",
    "Name": "John Doe",
    "PhoneMobile": "+18094567890",  # Optional
    "ShippingAddressCity": "Santo Domingo",
    "ShippingAddressCountry": "DO",
    "ShippingAddressLine1": "Main Street #123",
    "ShippingAddressState": "National District",
    "ShippingAddressZip": "10101"
}

# 3DS Authentication Parameters
{
    "TermUrl": "https://your-site.com/3ds-complete",
    "MethodNotificationUrl": "https://your-site.com/3ds-method",
    "RequestChallengeIndicator": "03"  # "03" - Request challenge
    # Other values: "01" - No preference, "02" - No challenge requested, "04" - Challenge mandated
}

# 3DS Direct Card Payment
{
    "CardNumber": "4111111111111111",
    "Expiration": "202812",
    "CVC": "123",
    "Amount": 100000,           # $1,000.00 (in cents)
    "ITBIS": 18000,             # $180.00 tax (in cents)
    "OrderNumber": "3DS-ORDER-123",
    "Channel": "EC",
    "PosInputMode": "E-Commerce",
    "forceNo3DS": "0",          # Enable 3DS
    "cardHolderInfo": {
        # Cardholder info as shown above
    },
    "threeDSAuth": {
        # 3DS Authentication Parameters as shown above
    }
}

# 3DS Token Payment
{
    "DataVaultToken": "a1b2c3d4e5f6",
    "Amount": 100000,           # $1,000.00 (in cents)
    "ITBIS": 18000,             # $180.00 tax (in cents)
    "OrderNumber": "3DS-TOKEN-ORDER-456",
    "Channel": "EC",
    "forceNo3DS": "0",          # Enable 3DS
    "cardHolderInfo": {
        # Cardholder info as shown above
    },
    "threeDSAuth": {
        # 3DS Authentication Parameters as shown above
    }
}
```

## More Information about the azul

For complete API documentation, see the [Wiki](https://dev.azul.com.do/Pages/developer/pages/lib/index.aspx).

---

&copy; LGPL License
