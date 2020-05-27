# Python packages
import os
import json

# Third party packages
import requests
from . import validate

class AzulAPI():

    def __init__(self, certificate_path, auth1, auth2, environment='dev'):
        '''
        :param auth1
        :param auth2
        :param certificate_path (path to your .p12 certificate)
        :param environment (string, defaults 'dev' can also be set to 'prod')
        '''
        self.certificate_path = certificate_path
        self.auth1 = auth1
        self.auth2 = auth2
        self.ENVIRONMENT = environment
        self.TEST_URL = 'https://pruebas.azul.com.do/webservices/JSON/Default.aspx'
        self.PRODUCTION_URL = 'https://pagos.azul.com.do/webservices/JSON/Default.aspx'
        self.ALT_PRODUCTION_URL = 'https://contpagos.azul.com.do/Webservices/JSON/default.aspx'
        

    def azul_request(self, transaction_type, data):
        try:
            
            # Required parameters for all transactions
            parameters = {
                'Channel': data['Channel'],
                'Store': data['Store'],
                
            }

            # Updating parameters with the extra parameters
            parameters.update(data)    
        
        except KeyError as missing_key:
            print(
                f'You are missing {missing_key} which is a required parameter.')
            return

        if transaction_type == 'void':
                self.TEST_URL += '?processvoid'
                self.PRODUCTION_URL += '?processvoid'
                self.ALT_PRODUCTION_URL += '?processvoid'
            
        elif transaction_type == 'post':
            self.TEST_URL += '?processpost'
            self.PRODUCTION_URL += '?processpost'
            self.ALT_PRODUCTION_URL += '?processpost'

        elif transaction_type == 'datavault_create' or 'datavault_delete':
            self.TEST_URL += '?ProcessDatavault'
            self.PRODUCTION_URL += '?ProcessDatavault'
            self.ALT_PRODUCTION_URL += '?ProcessDatavault'

        if self.ENVIRONMENT == 'prod':
            azul_endpoint = self.PRODUCTION_URL
        else:
            azul_endpoint = self.TEST_URL

        cert_path = self.config.certificate_path

        headers = {
            'Content-Type': 'application/json',
            'Auth1': self.config.auth1,
            'Auth2': self.config.auth2
        }
        response = {}
        try:
            response = requests.post(azul_endpoint, json=parameters,
                                     headers=headers, cert=cert_path)
        except Exception as err:
            try:
                azul_endpoint = self.ALT_PRODUCTION_URL
                response = requests.post(azul_endpoint, json=parameters,
                                         headers=headers, cert=cert_path)
                print(str(err))
            except Exception as err:
                print(
                    {'status': 'error',
                     'message': 'Could not reach Azul Web Service. Error: ' + str(err)})
                
        return response

    def sale_transaction(self, **kwargs):
        kwargs.update(validate.sale_transaction(kwargs))
        return self.azul_request('sale', kwargs)

    def hold_transaction(self, **kwargs):
        kwargs.update(validate.hold_transaction(kwargs))
        return self.azul_request('hold', kwargs)

    def refund_transaction(self, **kwargs):
        kwargs.update(validate.refund_transaction(kwargs))
        return self.azul_request('refund', kwargs)

    def void_transaction(self, **kwargs):
        kwargs.update(validate.void_transaction(kwargs))
        return self.azul_request('void', kwargs)

    def post_sale_transaction(self, **kwargs):
        kwargs.update(validate.post_sale_transaction(kwargs))
        return self.azul_request('post', kwargs)

    def verify_transaction(self, **kwargs):
        kwargs.update(validate.verify_transaction(kwargs))
        return self.azul_request('verify', kwargs)
    
    def nulify_transaction(self, **kwargs):
        kwargs.update(validate.nullify_transaction(kwargs))
        return self.azul_request('nullify', kwargs)
    
    def datavault_create(self, **kwargs):
        kwargs.update(validate.datavault_create(kwargs))
        return self.azul_request('datavault_create', kwargs)
    
    def datavault_delete(self, **kwargs):
        kwargs.update(validate.datavault_delete(kwargs))
        return self.azul_request('datavault_delete', kwargs)