# Python packages
import os
import json

# Third party packages
import requests
from . import validate


class AzulAPI:
    def __init__(self, auth1, auth2, certificate_path, environment='dev'):
        '''
        :param auth1
        :param auth2
        :param certificate_path (path to your .p12 certificate)
        :param environment (string, defaults 'dev' can also be set to 'prod')
        '''
        self.certificate_path = (
            certificate_path  # TODO validate this is an actual certificate
        )
        self.auth1 = auth1
        self.auth2 = auth2
        if environment == 'dev':
            self.url = 'https://pruebas.azul.com.do/webservices/JSON/Default.aspx'
        else:
            self.url = 'https://pagos.azul.com.do/webservices/JSON/Default.aspx'
            self.ALT_PRODUCTION_URL = (
                'https://contpagos.azul.com.do/Webservices/JSON/default.aspx'
            )

    def azul_request(self, data, operation=''):
        # FIXME: do this validation in a separate function
        try:
            #  Required parameters for all transactions
            parameters = {
                'Channel': data['Channel'],
                'Store': data['Store'],
            }

            # Updating parameters with the extra parameters
            parameters.update(data)

        except KeyError as missing_key:
            print(f'You are missing {missing_key} which is a required parameter.')
            return

        azul_endpoint = self.url + f'?{operation}'
        cert_path = self.certificate_path

        headers = {
            'Content-Type': 'application/json',
            'Auth1': self.auth1,
            'Auth2': self.auth2,
        }
        r = {}
        try:
            r = requests.post(
                azul_endpoint,
                json=parameters,
                headers=headers,
                cert=cert_path,
                timeout=30,
            )
        except Exception as err:
            if self.ENVIRONMENT == 'prod':
                try:
                    azul_endpoint = self.ALT_PRODUCTION_URL + f'?{operation}'
                    r = requests.post(
                        azul_endpoint,
                        json=parameters,
                        headers=headers,
                        cert=cert_path,
                        timeout=30,
                    )
                except Exception as err:
                    print(
                        {
                            'status': 'error',
                            'message': 'Could not reach Azul Web Service. Error: %s '
                            % str(err),
                        }
                    )
            print(
                {
                    'status': 'error',
                    'message': 'Could not reach Azul Web Service. Error: %s '
                    % str(err),
                }
            )

        response = json.loads(r.text)
        return response

    def sale_transaction(self, data):
        data.update(validate.sale_transaction(data))
        return self.azul_request(data)

    def hold_transaction(self, data):
        data.update(validate.hold_transaction(data))
        return self.azul_request(data)

    def refund_transaction(self, data):
        data.update(validate.refund_transaction(data))
        return self.azul_request(data)

    def void_transaction(self, data):
        data.update(validate.void_transaction(data))
        return self.azul_request(data, operation='ProcessVoid')

    def post_sale_transaction(self, data):
        data.update(validate.post_sale_transaction(data))
        return self.azul_request(data, operation='ProcessPost')

    def verify_transaction(self, data):
        data.update(validate.verify_transaction(data, operation='VerifyPayment'))
        return self.azul_request(data)

    def nulify_transaction(self, data):
        data.update(validate.nullify_transaction(data))
        return self.azul_request(data)

    def datavault_create(self, data):
        data.update(validate.datavault_create(data))
        return self.azul_request(data, operation='ProcessDatavault')

    def datavault_delete(self, data):
        data.update(validate.datavault_delete(data))
        return self.azul_request(data, operation='ProcessDatavault')
