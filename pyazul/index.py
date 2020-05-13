# Python packages
import os

# Third party packages
import requests
from . import validate


class APIConfiguration():
    def __init__(self, certificate_path, auth1, auth2, connString=None, dbHost=None, dbPswd=None):
        self.certificate_path = certificate_path
        self.auth1 = auth1
        self.auth2 = auth2

        # only set these if you are using datavault
        self.db_host = dbHost 
        self.db_password = dbPswd
        self.connection_string = connString


class AzulAPI():

    def __init__(self, config, environment='dev', dataVault=False):
        '''
        :param config (type APIConfigutation)
        :param environment (string, defaults 'dev' can also be set to 'prod')
        :param dataVault (boolean, you must configurate database credentials for this)
        '''
        self.config = config
        self.dataVault = dataVault
        self.ENVIRONMENT = environment
        self.TEST_URL = 'https://pruebas.azul.com.do/webservices/JSON/Default.aspx'
        self.PRODUCTION_URL = 'https://pagos.azul.com.do/webservices/JSON/Default.aspx'
        self.ALT_PRODUCTION_URL = 'https://contpagos.azul.com.do/Webservices/JSON/default.aspx'
        

    def azul_request(self, transaction_type, **kwargs):
        '''
        :param transaction_type (string)
        Options:
            * Sale (sale)
            * Hold (hold)
            * Refund (refund)
            * Transaction Post (post)
            * Verify transaction  (verify)
            * Nullify a transaction
            * Datavault Create (datavault_create)
            * Datavault Delete (datavault_delete)
        '''
        
        if self.ENVIRONMENT == 'prod':
            azul_endpoint = self.PRODUCTION_URL
        else:
            azul_endpoint = self.TEST_URL

        try:
            validation_handler = {
                'sale': validate.sale_transaction(kwargs),
                'hold': validate.hold_transaction(kwargs),
                'refund': validate.refund_transaction(kwargs),
                'post': validate.post_sale_transaction(kwargs),
                'verify': validate.verify_transaction(kwargs),
                'nullify': validate.nulify_transaction(kwargs),
                'datavault_create': validate.datavault_create(kwargs),
                'datavault_delete': validate.datavault_delete(kwargs)
            }
            parameters = {
                'Channel': kwargs['Channel'],
                'Store': kwargs['Store'],
            }
            # Validating that kwargs has all required attributes.
            validation_handler.get(transaction_type.lower())

            # Updating parameters with kwargs
            parameters.update(kwargs)
        
        except KeyError as missing_key:
            print(
                f'You are missing {missing_key} which is a required parameter for {transaction_type}.')
            return

        cert_path = self.config.certificate_path

        headers = {
            'Content-Type': 'application/json',
            'Auth1': self.config.auth1,
            'Auth2': self.config.auth2
        }
        try:
            response = requests.post(azul_endpoint, json=parameters,
                                     headers=headers, cert=cert_path)
        except:
            try:
                azul_endpoint = ALT_PRODUCTION_URL
                response = requests.post(azul_endpoint, json=parameters,
                                         headers=headers, cert=cert_path)
            except:
                print(
                    {'status': 'error',
                     'message': 'Could not reach Azul Web Service.'})

        return response


if __name__ == '__main__':
    apiConfig = APIConfiguration('server.pem', 'testcert2', 'testcert2')
    trxEngine = AzulAPI(apiConfig)
    response = trxEngine.azul_request(
        'sale_transaction',
        Channel='EC',
        Store='39038540035',
        CardNumber='4035874000424977',
        Expiration='202012',
        CVC='977',
        PosInputMode='E-Commerce',
        TrxType='Sale',
        Amount='1000',
        Itbis='180',
        CurrencyPosCode='$',
        Payments='1',
        Plan='0',
        AcquirerRefData='1',
        RNN='null',
        CustomerServicePhone='809-111-2222',
        OrderNumber='',
        ECommerceUrl='azul.iterativo.do',
        CustomOrderId='ABC123',
        DataVaultToken='',
        ForceNo3DS='1',
        SaveToDataVault='0'
    )
    print(response.text)
