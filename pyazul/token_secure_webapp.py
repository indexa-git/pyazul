"""
Mini aplicación FastAPI para demostrar el flujo completo de pagos con token y 3DS:
1. Crea un token a partir de una tarjeta de prueba
2. Usa el token para procesar un pago con autenticación 3DS
3. Maneja el flujo completo de 3DS (método y desafío)
"""

import logging
import uvicorn
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from typing import Optional, Dict, Any
from datetime import datetime
import json

from pyazul.api.client import AzulAPI
from pyazul.services.datavault import DataVaultService
from pyazul.services.secure import SecureService
from pyazul.models.schemas import DataVaultCreateModel
from pyazul.models.secure import CardHolderInfo, SecureTokenSale
from pyazul.core.config import get_azul_settings
from pyazul.core.exceptions import AzulError

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Inicializar la aplicación FastAPI
app = FastAPI(title="Azul Token Payment Demo")
templates = Jinja2Templates(directory="templates")

# Inicializar servicios compartidos (singleton)
api_client = AzulAPI()
secure_service = SecureService(api_client)
datavault_service = DataVaultService(get_azul_settings())

# Tarjetas de prueba para 3DS
TEST_CARDS = [
    {
        "number": "4265880000000007",
        "label": "Frictionless con 3DSMethod",
        "expiration": "202812",
        "cvv": "123",
        "force_no_3ds": "0",
        "challenge_indicator": "02"  # NO_CHALLENGE - Frictionless
    },
    {
        "number": "4147463011110117",
        "label": "Frictionless sin 3DSMethod",
        "expiration": "202812",
        "cvv": "123",
        "force_no_3ds": "1",
        "challenge_indicator": "02"  # NO_CHALLENGE - Frictionless
    },
    {
        "number": "4005520000000129",
        "label": "Challenge con 3DSMethod (Límite RD$ 50)",
        "expiration": "202812",
        "cvv": "123",
        "force_no_3ds": "0",
        "challenge_indicator": "03",  # CHALLENGE
        "max_amount": 50
    },
    {
        "number": "4147463011110059",
        "label": "Challenge sin 3DSMethod",
        "expiration": "202812",
        "cvv": "123",
        "force_no_3ds": "0",
        "challenge_indicator": "03"  # CHALLENGE
    }
]

# Almacenamiento de tokens (en memoria para este demo)
token_storage: Dict[str, Dict[str, Any]] = {}

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Página principal con formulario de pago"""
    return templates.TemplateResponse(
        "token_index.html",
        {
            "request": request,
            "cards": TEST_CARDS
        }
    )

@app.post("/create-token")
async def create_token(
    request: Request,
    card_number: str = Form(...),
    amount: float = Form(...),
    itbis: float = Form(...)
):
    """Crear un token a partir de los datos de la tarjeta"""
    try:
        # Buscar la tarjeta seleccionada
        card = next((c for c in TEST_CARDS if c["number"] == card_number), None)
        if not card:
            return JSONResponse(
                status_code=400,
                content={"error": "Tarjeta no válida"}
            )
        
        # Preparar datos para crear el token
        datavault_data = {
            "Channel": "EC",
            "PosInputMode": "E-Commerce",
            "Amount": str(int(amount * 100)),  # Convertir a centavos
            "Itbis": str(int(itbis * 100)),    # Convertir a centavos
            "CardNumber": card["number"],
            "Expiration": card["expiration"],
            "CustomOrderId": f"web-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "store": get_azul_settings().MERCHANT_ID
        }
        
        # Crear el token - usar el servicio global
        payment = DataVaultCreateModel(**datavault_data)
        response = await datavault_service.create(payment)
        
        logger.info(f"Token Creation Response: {json.dumps(response)}")
        
        if response.get('IsoCode') != '00':
            return JSONResponse(
                status_code=400,
                content={"error": f"Error al crear token: {response.get('ResponseMessage')}"}
            )
        
        # Guardar datos del token
        token_id = response.get('DataVaultToken')
        token_data = {
            "token": token_id,
            "expiration": datavault_data["Expiration"],
            "brand": response.get('Brand', ''),
            "masked_card": response.get('CardNumber', ''),
            "has_cvv": response.get('HasCVV', False),
            "card_data": card,
            "created_at": datetime.now().isoformat()
        }
        
        # Guardar en el almacenamiento temporal
        token_storage[token_id] = token_data
        
        # Devolver los datos del token
        return {
            "token_id": token_id,
            "masked_card": response.get('CardNumber', ''),
            "brand": response.get('Brand', ''),
            "message": "Token creado exitosamente"
        }
        
    except AzulError as e:
        logger.error(f"Error en Azul al crear token: {str(e)}")
        return JSONResponse(
            status_code=400,
            content={"error": str(e)}
        )
    except Exception as e:
        logger.error(f"Error inesperado al crear token: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"error": "Error interno del servidor"}
        )


@app.post("/process-token-payment")
async def process_token_payment(
    request: Request,
    token_id: str = Form(...),
    amount: float = Form(...),
    itbis: float = Form(...),
    challenge_indicator: Optional[str] = Form("03")
):
    """Procesar un pago utilizando un token existente con 3DS"""
    try:
        # Verificar que el token exista
        if token_id not in token_storage:
            return JSONResponse(
                status_code=400,
                content={"error": "Token no válido o expirado"}
            )
        
        # Obtener datos del token
        token_data = token_storage[token_id]
        card_data = token_data.get("card_data", {})
        
        # Generar un número de orden único
        order_number = f"TOKEN-{datetime.now().strftime('%Y%m%')}"
        
        # URL base para callbacks 3DS
        base_url = str(request.base_url).rstrip('/')
        
        # Crear datos del titular de la tarjeta
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
            ShippingAddressZip="10148"
        )
        
        # Crear datos para la venta
        sale_data = {
            "DataVaultToken": token_id,
            "Expiration": '',  # No es necesario con token
            "Amount": int(amount * 100),  # Convertir a centavos
            "ITBIS": int(itbis * 100),    # Convertir a centavos
            "OrderNumber": order_number,
            "TrxType": "Sale",
            "AcquirerRefData": "1",
            "forceNo3DS": card_data.get("force_no_3ds", "0"),
            "Channel": "EC",
            "PosInputMode": "E-Commerce",
            "cardHolderInfo": cardholder_info.model_dump(),
            "threeDSAuth": {
                "TermUrl": f"{base_url}/post-3ds",
                "MethodNotificationUrl": f"{base_url}/capture-3ds",
                "RequestChallengeIndicator": challenge_indicator or card_data.get("challenge_indicator", "03")
            }
        }
        
        # Procesar la venta con token usando el servicio global
        logger.info(f"Processing token sale: {token_id}, Order: {order_number}")
        data = SecureTokenSale(**sale_data)
        
        # Registrar las sesiones antes de la llamada
        logger.info(f"Secure sessions before call: {list(secure_service.secure_sessions.keys())}")
        
        response = await secure_service.process_token_sale(data)
        
        # Registrar las sesiones después de la llamada
        logger.info(f"Secure sessions after call: {list(secure_service.secure_sessions.keys())}")
        
        # Si hay un ID de sesión en la respuesta, registrarlo
        if "id" in response:
            logger.info(f"Response includes session ID: {response['id']}")
            
            # Verificar si la sesión existe en secure_service
            session_exists = response["id"] in secure_service.secure_sessions
            logger.info(f"Session exists in secure_sessions: {session_exists}")
            
            if session_exists:
                # Imprimir la información de la sesión
                session_info = secure_service.secure_sessions[response["id"]]
                logger.info(f"Session info: azul_order_id={session_info.get('azul_order_id')}")
        
        # Loguear la respuesta
        logger.info(f"Token Sale Response: {json.dumps(response)}")
        
        # Devolver la respuesta
        return response
        
    except AzulError as e:
        logger.error(f"Error en Azul al procesar pago: {str(e)}")
        return JSONResponse(
            status_code=400,
            content={"error": str(e)}
        )
    except Exception as e:
        logger.error(f"Error inesperado al procesar pago: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"error": "Error interno del servidor"}
        )


@app.post("/capture-3ds")
async def capture_3ds(
    request: Request,
    secure_id: Optional[str] = None,
    sid: Optional[str] = None
):
    """
    Manejar la notificación del método 3DS.
    
    Este endpoint recibe la respuesta del ACS (Access Control Server)
    después de que se ha completado el método 3DS.
    """
    # Usar el primer ID disponible
    session_id = secure_id or sid
    
    if not session_id:
        return JSONResponse(
            status_code=400,
            content={"error": "No se proporcionó un identificador de sesión"}
        )

    logger.info(f"3DS notification received for session: {session_id}")
    
    # Registrar las sesiones activas
    logger.info(f"Active secure sessions: {list(secure_service.secure_sessions.keys())}")

    try:
        # Obtener la sesión usando el servicio global
        session = secure_service.secure_sessions.get(session_id)
        if not session:
            logger.error(f"Session not found: {session_id}")
            return JSONResponse(
                status_code=400,
                content={"error": "Sesión no válida"}
            )

        # Procesar el método 3DS
        azul_order_id = session.get("azul_order_id", "")
        logger.info(f"Processing 3DS method for order: {azul_order_id}")
        
        result = await secure_service.process_3ds_method(
            azul_order_id,
            "RECEIVED"  # Método 3DS completado
        )
        
        logger.info(f"3DS Method result: {json.dumps(result)}")

        # Si la transacción ya fue procesada, devolver OK
        if result.get("ResponseMessage") == "ALREADY_PROCESSED":
            return {"status": "ok"}
        
        # Verificar si se requiere un desafío adicional
        if result.get("ResponseMessage") == "3D_SECURE_CHALLENGE":
            logger.info("Additional 3DS challenge required")
            return {
                "redirect": True,
                "html": secure_service._create_challenge_form(
                    result["ThreeDSChallenge"]["CReq"],
                    session["term_url"],
                    result["ThreeDSChallenge"]["RedirectPostUrl"]
                )
            }
            
        return result

    except AzulError as e:
        logger.error(f"Error en Azul al procesar método 3DS: {str(e)}")
        return JSONResponse(
            status_code=400,
            content={"error": str(e)}
        )
    except Exception as e:
        logger.error(f"Error inesperado al procesar método 3DS: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"error": "Error interno del servidor"}
        )


@app.post("/post-3ds")
async def post_3ds(
    request: Request,
    secure_id: Optional[str] = None,
    sid: Optional[str] = None,
    cres: Optional[str] = Form(None)
):
    """
    Manejar la respuesta del desafío 3DS.
    
    Este endpoint recibe la respuesta del desafío del ACS
    después de que el titular de la tarjeta completa la autenticación.
    """
    session_id = secure_id or sid
    
    if not session_id:
        return JSONResponse(
            status_code=400,
            content={"error": "No se proporcionó un identificador de sesión"}
        )
        
    if not cres:
        return JSONResponse(
            status_code=400,
            content={"error": "No se proporcionó respuesta del desafío"}
        )

    try:
        # Procesar el desafío usando el servicio global
        logger.info(f"Processing 3DS challenge for session: {session_id}")
        result = await secure_service.process_challenge(session_id, cres)
        logger.info(f"Challenge result: {json.dumps(result)}")
        
        return templates.TemplateResponse(
            "result.html",
            {
                "request": request,
                "result": result
            }
        )
    except AzulError as e:
        logger.error(f"Error en Azul al procesar desafío: {str(e)}")
        return templates.TemplateResponse(
            "error.html",
            {
                "request": request,
                "error": str(e)
            }
        )
    except Exception as e:
        logger.error(f"Error inesperado al procesar desafío: {str(e)}")
        return templates.TemplateResponse(
            "error.html",
            {
                "request": request,
                "error": "Error inesperado al procesar la autenticación"
            }
        )


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001) 