## pyazul

Consulta esta [wiki](https://github.com/indexa-git/pyazul/wiki) para saber más sobre AZUL Webservices.

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
        "Channel"="EC",
        "Store"="39038540035",
        "CardNumber"="",
        "Expiration"="",
        "CVC"="",
        "PosInputMode"="E-Commerce",
        "Amount"="12",
        "CurrencyPosCode"="$",
        "RNN"="null",
        "CustomerServicePhone"="809-111-2222",
        "OrderNumber"="SO039-2",
        "ECommerceUrl"="azul.iterativo.do",
        "CustomOrderId"="53",
        "DataVaultToken"="74EAA676-FB9A-49E3-82CD-485DF85ECB61",
        "ForceNo3DS"="1",
        "SaveToDataVault"="0"
    }
    response = pyazul.sale_transaction(params)

```

---

&copy; LGPL License
