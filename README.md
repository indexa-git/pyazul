![Build & publish](https://github.com/indexa-git/pyazul/workflows/Build%20&%20publish/badge.svg)

## pyazul

Consulta esta [wiki](https://github.com/indexa-git/pyazul/wiki/Azul-Webservice-Documentation) para saber más sobre AZUL Webservices.

## Instalación

1. Instala [pypi](https://pypi.org/).
2. `$ pip install pyazul`

## Sale

```python
from pyazul import AzulAPI

def sample_sale():
    auth1 = 'testcert2' # primer auth factor (se obtiene de Azul)
    auth2 = 'testcert2' # segundo auth factor (se obtiene de Azul)
    certificate_path = 'certificate.pem'
    environment = 'prod' # defaults 'dev'
    pyazul = AzulAPI(auth1, auth2, certificate_path)
    params = {
        "Channel": "EC",
        "Store": "37094649930",
        "CardNumber": "",
        "Expiration": "",
        "CVC": "",
        "PosInputMode": "E-Commerce",
        "Amount": "12",
        "CurrencyPosCode": "$",
        "RNN": "null",
        "CustomerServicePhone": "809-111-2222",
        "OrderNumber": "SO039-2",
        "ECommerceUrl": "azul.iterativo.do",
        "CustomOrderId": "53",
        "DataVaultToken": "74EAA676-FB9A-49E3-82CD-485DF85ECB61",
        "ForceNo3DS": "1",
        "SaveToDataVault": "0"
    }
    response = pyazul.sale_transaction(params)

```

## Void

```python
from pyazul import AzulAPI

def sample_void():
    auth1 = 'testcert2' # primer auth factor (se obtiene de Azul)
    auth2 = 'testcert2' # segundo auth factor (se obtiene de Azul)
    certificate_path = 'certificate.pem'
    environment = 'prod' # defaults 'dev'
    pyazul = AzulAPI(auth1, auth2, certificate_path)
    params = {
        "Channel":"EC",
	    "Store":"37094649930",
	    "AzulOrderId": 27917,
    }
    response = pyazul.void_transaction(params)

```

## Refund

```python
from pyazul import AzulAPI

def sample_refund():
    auth1 = 'testcert2' # primer auth factor (se obtiene de Azul)
    auth2 = 'testcert2' # segundo auth factor (se obtiene de Azul)
    certificate_path = 'certificate.pem'
    environment = 'prod' # defaults 'dev'
    pyazul = AzulAPI(auth1, auth2, certificate_path)
    params = {
        "Channel":"EC",
        "Store":"37094649930",
        "PosInputMode":"E-Commerce",
        "Amount":"30000",
        "Itbis":"2800",
        "CurrencyPosCode":"$",
        "OriginalDate":"20191217",
        "OriginalTrxTicketNr":"",
        "AuthorizationCode":"",
        "ResponseCode":"",
        "AcquirerRefData":"",
        "RRN":"null",
        "AzulOrderId":40208,
        "CustomerServicePhone":"",
        "OrderNumber":"",
        "ECommerceUrl":"www.Google.com",
        "CustomOrderId":"",
        "DataVaultToken":"",
        "SaveToDataVault":"0",
        "ForceNo3DS":""
    }
    response = pyazul.refund_transaction(params)

```

## Async support
Pyazul tambien es compatible con operaciones asíncronas de la siguiente manera:

```python
import asyncio
# Import the Async module
from pyazul import AzulAPIAsync

# Make sure your function is async
async def sample_sale():
    auth1 = 'testcert2' # primer auth factor (se obtiene de Azul)
    auth2 = 'testcert2' # segundo auth factor (se obtiene de Azul)
    certificate_path = 'certificate.pem'
    environment = 'prod' # defaults 'dev'
    pyazul = AzulAPIAsync(auth1, auth2, certificate_path)
    params = {
        "Channel": "EC",
        "Store": "37094649930",
        "CardNumber": "",
        "Expiration": "",
        "CVC": "",
        "PosInputMode": "E-Commerce",
        "Amount": "12",
        "CurrencyPosCode": "$",
        "RNN": "null",
        "CustomerServicePhone": "809-111-2222",
        "OrderNumber": "SO039-2",
        "ECommerceUrl": "azul.iterativo.do",
        "CustomOrderId": "53",
        "DataVaultToken": "74EAA676-FB9A-49E3-82CD-485DF85ECB61",
        "ForceNo3DS": "1",
        "SaveToDataVault": "0"
    }
    response = await pyazul.sale_transaction(params)

# Test with asynccio
if __name__ == "__main__":
    asyncio.run(sample_sale())

```
---

&copy; LGPL License
