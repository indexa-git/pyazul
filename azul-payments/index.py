# Python packages
import os
import json
import logging

# Third party packages
import requests
from flask import Flask, Response
from method_parsers.verify_transaction import verify_transaction
from method_parsers.create import dv_create
from method_parsers.delete import dv_delete
from method_parsers.process_payment import (
    sale_transaction,
    dv_sale_transaction
)


def executeMethod(data, method, env='test'):
    if env == 'prod':
        azul_endpoint = 'https://pagos.azul.com.do/webservices/JSON/Default.aspx'
    else:
        azul_endpoint = 'https://pruebas.azul.com.do/webservices/JSON/Default.aspx'

    try:
        # method = method.lower()
        methods_handler = {
            'sale_transaction': sale_transaction.main(data),
            'verify_transaction': verify_transaction.main(data),
            'dv_saletransaction': dv_sale_transaction.main(data),
            'dv_create': dv_create.main(data),
            'dv_delete': dv_delete.main(data)
        }
        parameters = methods_handler.get(method)
    except KeyError as missing_key:
        print(f'You are missing {missing_key} which is a required parameter.')
        return

    # Certificate path
    cert_path = 'server.pem'

    # Authentication
    auth1 = 'testcert2'
    auth2 = 'testcert2'

    headers = {
        'Content-Type': 'application/json',
        'Auth1': auth1,
        'Auth2': auth2
    }
    try:
        response = requests.post(azul_endpoint, json=parameters,
                                 headers=headers, cert=cert_path)
    except:
        try:
            azul_endpoint = 'https://contpagos.azul.com.do/Webservices/JSON/default.aspx'
            response = requests.post(azul_endpoint, json=parameters,
                                     headers=headers, cert=cert_path)
        except:
            print(
                {'status': 'error',
                 'message': 'Could not reach Azul Web Service.'})

    print(response.text)


if __name__ == '__main__':
    params = {
        "Channel": "EC",
        "Store": "39038540035",
        "CardNumber": "4035874000424977",
        "Expiration": "202012",
        "CVC": "977",
        "PosInputMode": "E-Commerce",
        "TrxType": "Sale",
        "Amount": "1000",
        "Itbis": "180",
        "CurrencyPosCode": "$",
        "Payments": "1",
        "Plan": "0",
        "AcquirerRefData": "1",
        "RRN": "null",
        "CustomerServicePhone": "809-111-2222",
        "OrderNumber": "",
        "ECommerceUrl": "azul.iterativo.do",
        "CustomOrderId": "ABC123",
        "DataVaultToken": "",
        "ForceNo3DS": "1",
        "SaveToDataVault": "0",
    }
    executeMethod(params, 'sale_transaction')
