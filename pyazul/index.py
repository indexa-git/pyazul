# Python packages
import os

# Third party packages
import requests
from . import parsers


class EngineConfiguration():
    def __init__(self, certificate_path, auth1, auth2, connString=None, dbHost=None, dbPswd=None):
        self.auth1 = auth1
        self.auth2 = auth2
        self.db_host = dbHost
        self.db_password = dbPswd
        self.connection_string = connString
        self.certificate_path = certificate_path


class TransactionEngine():

    def __init__(self, environment='dev', dataVault=False, **kwargs):
        self.TEST_URL = 'https://pruebas.azul.com.do/webservices/JSON/Default.aspx'
        self.PRODUCTION_URL = 'https://pagos.azul.com.do/webservices/JSON/Default.aspx'
        self.ALT_PRODUCTION_URL = 'https://contpagos.azul.com.do/Webservices/JSON/default.aspx'
        self.ENVIRONMENT = environment
        self.dataVault = dataVault
        if 'config' in kwargs:
            engineConfig = kwargs.get('config')
            if isinstance(engineConfig, EngineConfiguration):
                self.config = engineConfig

    def run_transaction(self, transaction_type, **kwargs):
        '''
        Available transaction types:
        - sales_transaction
        - verify_transaction
        - dv_sale_transaction
        - dv_create
        - dv_delete
        '''
        if self.ENVIRONMENT == 'prod':
            azul_endpoint = self.PRODUCTION_URL
        else:
            azul_endpoint = self.TEST_URL

        try:
            methods_handler = {
                'sale_transaction': parsers.sale_transaction(**kwargs),
                'verify_transaction': parsers.verify_transaction(**kwargs),
                'dv_sale_transaction': parsers.dv_sale_transaction(**kwargs),
                'dv_create': parsers.dv_create(**kwargs),
                'dv_delete': parsers.dv_delete(**kwargs)
            }
            parameters = methods_handler.get(transaction_type)
        except KeyError as missing_key:
            print(
                f'You are missing {missing_key} which is a required parameter for {transaction_type}.')
            return

        cert_path = self.config.certificate_path
        auth1 = self.config.auth1
        auth2 = self.config.auth2

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
                azul_endpoint = ALT_PRODUCTION_URL
                response = requests.post(azul_endpoint, json=parameters,
                                         headers=headers, cert=cert_path)
            except:
                print(
                    {'status': 'error',
                     'message': 'Could not reach Azul Web Service.'})

        return response


if __name__ == '__main__':
    engineConfig = EngineConfiguration('server.pem', 'testcert2', 'testcert2')
    trxEngine = TransactionEngine(config=engineConfig)
    response = trxEngine.run_transaction(
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
