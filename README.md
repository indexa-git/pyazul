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

### 3D Secure Implementation

```python
from pyazul import PyAzul
from pyazul.models.secure import SecureSaleRequest, CardHolderInfo

azul = PyAzul()

async def secure_payment(card_number, expiry, cvv, amount):
    # Card holder data (required for 3DS)
    cardholder_info = CardHolderInfo(
        BillingFirstName="John",
        BillingLastName="Doe",
        BillingAddressLine1="Main Street",
        BillingAddressCity="Santo Domingo",
        BillingAddressZip="10101",
        BillingAddressCountry="DO",
        Email="customer@example.com"
    )
    
    # Create 3DS request
    secure_request = SecureSaleRequest(
        CardNumber=card_number,
        Expiration=expiry,
        CVC=cvv,
        Amount=amount,
        ITBIS="0",
        OrderNumber="ORDER-3DS-123",
        threeDSAuth={
            "TermUrl": "https://your-site.com/api/post-3ds",
            "MethodNotificationUrl": "https://your-site.com/api/method-3ds",
            "RequestChallengeIndicator": "03"
        },
        cardHolderInfo=cardholder_info,
        forceNo3DS="0"
    )

    # Process 3DS payment
    result = await azul.secure.process_sale(secure_request)
    
    if result.get("redirect"):
        # Return HTML form for 3DS redirection
        return result.get("html")
    else:
        # Transaction completed without 3DS
        return result.get("value")
```

### Token Sale 3DS implementations

``` python

from pyazul import PyAzul
from pyazul.models.secure import SecureSaleRequest, CardHolderInfo,ThreeDSAuth

azul = Pyazul()
async def secure_payment_token(token):

    cardholder_info = CardHolderInfo(
        BillingFirstName="John",
        BillingLastName="Doe",
        BillingAddressLine1="Main Street",
        BillingAddressCity="Santo Domingo",
        BillingAddressZip="10101",
        BillingAddressCountry="DO",
        Email="customer@example.com"
    )

    three_ds_auth = ThreeDSAuth(
        TermUrl="https://your-site.com/api/post-3ds",  # URL to return after 3DS authentication
        MethodNotificationUrl="https://your-site.com/api/method-3ds",  # URL for 3DS method notification
        RequestChallengeIndicator="02"  # Challenge indicator 
        """
        01= No preference for challenge
        02=No challenge requested, 
        03=Challenge requested, 
        04=Challenge mandated"""
    )

    # También se puede usar un token con 3DS
   
    secure_token_request = SecureTokenSale(
        DataVaultToken=token,
        Amount=150000,              # $1,500.00
        ITBIS=27000,               # $270.00
        OrderNumber="TOKEN-3DS-001",
        AcquirerRefData="REF124",
        cardHolderInfo=cardholder,
        threeDSAuth=three_ds_auth,
        forceNo3DS="0"
    )

    token_result = await azul.secure.process_token_sale(secure_token_request)
    return token_result
```

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
await azul.secure.process_sale({...})        # 3DS card payment
await azul.secure.process_token_sale({...})  # 3DS token payment
await azul.secure.process_3ds_method(...)    # Process 3DS method notification
await azul.secure.process_challenge(...)     # Process 3DS challenge result
```

# Pydantic Models by the key methods 

```python
from pyazul.models.schemas import (
    SaleTransactionModel, HoldTransactionModel, RefundTransactionModel,
    DataVaultCreateModel, DataVaultDeleteModel, TokenSaleModel,
    PostSaleTransactionModel, VerifyTransactionModel, VoidTransactionModel,
    PaymentPageModel
)
from pyazul.models.secure import (
    CardHolderInfo, ThreeDSAuth, ChallengeIndicator,
    SecureSaleRequest, SecureTokenSale
)

# Card Sale Transaction
sale_model = SaleTransactionModel(
    CardNumber="4111********1111",
    Expiration="202812",  # YYYYMM format
    CVC="123",
    Amount="100000",      # $1,000.00
    Itbis="18000",        # $180.00
    CustomOrderId="order-123"
)

# Authorization Hold
hold_model = HoldTransactionModel(
    CardNumber="4111********1111",
    Expiration="202812",
    CVC="123",
    Amount="100000",
    Itbis="18000",
    CustomOrderId="hold-123"
)

# Refund Transaction
refund_model = RefundTransactionModel(
    AzulOrderId="12345678",
    Amount="100000"
)

# Create Card Token
token_create_model = DataVaultCreateModel(
    CardNumber="4111********1111",
    Expiration="202812",
    store="39038540035",
    CustomOrderId="token-123"
)

# Delete Card Token
token_delete_model = DataVaultDeleteModel(
    DataVaultToken="a1b2c3d4e5f6",
    store="39038540035"
)

# Payment using Token
token_sale_model = TokenSaleModel(
    DataVaultToken="a1b2c3d4e5f6",
    Amount="100000",
    Itbis="18000",
    CustomOrderId="token-sale-123"
)

# Post Sale (Capture pre-authorized payment)
post_sale_model = PostSaleTransactionModel(
    AzulOrderId="12345678",
    Amount="100000",
    Itbis="18000",
    CardNumber="4111********1111",
    Expiration="202812",
    CVC="123",
    ApprovedUrl="https://your-site.com/success",
    DeclinedUrl="https://your-site.com/declined",
    CancelUrl="https://your-site.com/cancel"
)

# Verify Transaction
verify_model = VerifyTransactionModel(
    CustomOrderId="order-123"
)

# Void Transaction
void_model = VoidTransactionModel(
    AzulOrderId="12345678",
    store="39038540035"
)

# Payment Page Integration
payment_page_model = PaymentPageModel(
    Amount="100000",      # $1,000.00
    ITBIS="18000",        # $180.00
    ApprovedUrl="https://your-site.com/success",
    DeclineUrl="https://your-site.com/declined",
    CancelUrl="https://your-site.com/cancel",
    UseCustomField1="1",
    CustomField1Label="Order Reference",
    CustomField1Value="ORD-123456"
)

# 3D Secure Models

# Cardholder Information for 3DS
cardholder_info = CardHolderInfo(
    BillingAddressCity="Santo Domingo",
    BillingAddressCountry="DO",
    BillingAddressLine1="Avenida Principal #123",
    BillingAddressState="Distrito Nacional",
    BillingAddressZip="10101",
    Email="customer@example.com",
    Name="John Doe",
    PhoneMobile="+18094567890",
    ShippingAddressCity="Santo Domingo",
    ShippingAddressCountry="DO",
    ShippingAddressLine1="Avenida Principal #123",
    ShippingAddressState="Distrito Nacional",
    ShippingAddressZip="10101"
)

# 3DS Authentication Parameters
three_ds_auth = ThreeDSAuth(
    TermUrl="https://your-site.com/3ds-complete",
    MethodNotificationUrl="https://your-site.com/3ds-method",
    RequestChallengeIndicator=ChallengeIndicator.CHALLENGE  # "03" - Request challenge
)

# 3DS Direct Card Payment
secure_sale = SecureSaleRequest(
    CardNumber="4111********1111",
    Expiration="202812",
    CVC="123",
    Amount=100000,           # $1,000.00 (in cents)
    ITBIS=18000,             # $180.00 tax (in cents)
    OrderNumber="3DS-ORDER-123",
    forceNo3DS="0",          # Enable 3DS
    cardHolderInfo=cardholder_info,
    threeDSAuth=three_ds_auth
)

# 3DS Token Payment
secure_token_sale = SecureTokenSale(
    DataVaultToken="a1b2c3d4e5f6",
    Amount=100000,           # $1,000.00 (in cents)
    ITBIS=18000,             # $180.00 tax (in cents)
    OrderNumber="3DS-TOKEN-ORDER-456",
    Expiration="202812",     # Required even with token
    forceNo3DS="0",          # Enable 3DS
    cardHolderInfo=cardholder_info,
    threeDSAuth=three_ds_auth
)

```

## More Information about the azul

For complete API documentation, see the [Wiki](https://dev.azul.com.do/Pages/developer/pages/lib/index.aspx).

---

&copy; LGPL License
