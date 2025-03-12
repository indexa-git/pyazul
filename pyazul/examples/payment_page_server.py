from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from pyazul.models.schemas import PaymentPageModel
from pyazul.services.payment_page import PaymentPageService
from pyazul.core.config import get_azul_settings

"""
Example server for Azul Payment Page integration.

This server demonstrates how to:
1. Create a payment form with specified amounts
2. Handle the payment page redirection
3. View the payment amounts in different formats

Amounts format:
- All amounts are in cents (last two digits are decimals)
- Example: "100000" = $1,000.00
- For zero ITBIS use "000"
"""

# Initialize FastAPI app and payment service
app = FastAPI()
payment_page_service = PaymentPageService(get_azul_settings())


@app.get("/", response_class=HTMLResponse)
async def home():
    """Serve home page with payment options"""
    return """
        <form action="/buy-ticket" method="GET">
            <input type="submit" value="Pay now" />
        </form>
        <br/>
        <form action="/view-amounts" method="GET">
            <input type="submit" value="View amounts" />
        </form>
    """


@app.get("/view-amounts")
async def view_amounts():
    """
    View payment amounts in different formats.
    Shows both the raw amounts (in cents) and formatted amounts (in USD).
    """
    payment_request = PaymentPageModel(
        Amount="100000",     # $1,000.00 (total amount including ITBIS)
        ITBIS="18000",      # $180.00 (18% of base amount)
        ApprovedUrl="https://www.instagram.com/progressa.group/#",
        DeclineUrl="https://www.progressa.group/",
        CancelUrl="https://www.progressa.group/",
        UseCustomField1="0",
        CustomField1Label="",
        CustomField1Value=""
    )

    return JSONResponse({
        # Formatted amounts in USD
        "string_representation": str(payment_request),
        "amount_in_cents": payment_request.Amount,      # Raw amount in cents
        "itbis_in_cents": payment_request.ITBIS        # Raw ITBIS in cents
    })


@app.get("/buy-ticket", response_class=HTMLResponse)
async def buy_ticket(request: Request):
    """
    Create and return a payment form for Azul Payment Page.
    
    The form will automatically submit to Azul's payment page where
    the user can enter their card details securely.
    """
    try:
        # Create payment request with:
        # - Total amount: $1,000.00 = "100000" cents
        # - ITBIS: $180.00 = "18000" cents (18% of base amount)
        payment_request = PaymentPageModel(
            Amount="100000",     # $1,000.00
            ITBIS="18000",      # $180.00
            ApprovedUrl="https://www.instagram.com/progressa.group/#",
            DeclineUrl="https://www.progressa.group/",
            CancelUrl="https://www.progressa.group/",
            UseCustomField1="0",
            CustomField1Label="",
            CustomField1Value=""
        )

        # Generate and return the HTML form
        return payment_page_service.create_payment_form(payment_request)

    except Exception:
        return """
            <h1>Error</h1>
            <p>Failed to create payment form. Please try again later.</p>
        """

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
