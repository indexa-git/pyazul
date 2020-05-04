# Python packages
import os
import json
import time
import logging

# Third party packages
import util
import requests
from flask import Flask, Response


def azul_transaction(request):
    # Azul Endpoint (test environment)
    azul_endpoint = 'https://pruebas.azul.com.do/webservices/JSON/Default.aspx'

    # Certificate path
    cert_path = 'tmp/server.pem'

    # Obtain request body as JSON.
    request_json = request.get_json(silent=True)

    # Getting credentials and certificates
    # from secrets, for security purposes.
    start_time1 = time.time()
    auth1 = util.getSecret('Auth1')
    auth2 = util.getSecret('Auth2')
    start_time2 = time.time()
    cert_txt = util.getSecret('AzulCert')
    print("Getting one secret took", time.time() - start_time2, " seconds")
    print("Getting all secrets took", time.time() - start_time1, " seconds")

    # Let's write the certificate temporarily
    start_time1 = time.time()
    with open(cert_path, 'w') as cert_file:  # check more efficient ways to do this
        cert_file.write(cert_txt)
        cert_file.close()
    print("Writing took", time.time() - start_time1, " seconds")

    # Preparing the request
    cert = cert_path
    headers = {
        'Content-Type': 'application/json',
        'Auth1': auth1,
        'Auth2': auth2
    }
    try:
        response = requests.post(azul_endpoint, json=request_json,
                                 headers=headers, cert=cert)
    except:
        return Response(
            {'status': 'error',
             'message': 'Could not reach Azul Web Service.'},
            headers={'Content-Type':
                     'application/json'})

    # Removing certificate after using it, safety purposes.
    start_time1 = time.time()
    os.remove(cert_path)
    print("Printing took", time.time() - start_time1, " seconds")

    return Response(response.text, headers={'Content-Type': 'application/json'})


if __name__ == '__main__':
    azul_transaction()
