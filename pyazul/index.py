# Python packages
import json
import logging

# Third party packages
import httpx
from . import validate

_logger = logging.getLogger(__name__)


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
        self.ENVIRONMENT = environment

        if environment == 'dev':
            self.url = 'https://pruebas.azul.com.do/webservices/JSON/Default.aspx'
        else:
            self.url = 'https://pagos.azul.com.do/webservices/JSON/Default.aspx'
            self.ALT_URL = 'https://contpagos.azul.com.do/Webservices/JSON/default.aspx'

    def azul_request(self, data, operation=''):
        #  Required parameters for all transactions
        parameters = {
            'Channel': data.get('Channel', ''),
            'Store': data.get('Store', ''),
        }

        # Updating parameters with the extra parameters
        parameters.update(data)

        azul_endpoint = self.url + f'?{operation}'
        cert_path = self.certificate_path

        headers = {
            'Content-Type': 'application/json',
            'Auth1': self.auth1,
            'Auth2': self.auth2,
        }
        r = {}
        _logger.debug('azul_request: called with data:\n%s', data)

        try:
            r = httpx.post(
                azul_endpoint,
                json=parameters,
                headers=headers,
                cert=cert_path,
                timeout=30,
            )
            if r.raise_for_status() and self.ENVIRONMENT == 'prod':
                azul_endpoint = self.ALT_URL + f'?{operation}'
                r = httpx.post(
                    azul_endpoint,
                    json=parameters,
                    headers=headers,
                    cert=cert_path,
                    timeout=30,
                )
        except Exception as err:
            _logger.error(
                'azul_request: Got the following error\n%s', str(err))
            raise Exception(str(err))

        response = json.loads(r.text)
        _logger.debug('azul_request: Values received\n%s', json.loads(r.text))

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
        data.update(validate.verify_transaction(data))
        return self.azul_request(data, operation='VerifyPayment')

    def nulify_transaction(self, data):
        data.update(validate.nullify_transaction(data))
        return self.azul_request(data)

    def datavault_create(self, data):
        data.update(validate.datavault_create(data))
        return self.azul_request(data, operation='ProcessDatavault')

    def datavault_delete(self, data):
        data.update(validate.datavault_delete(data))
        return self.azul_request(data, operation='ProcessDatavault')


class AzulAPIAsync(AzulAPI):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    async def azul_request(self, data, operation=''):
        #  Required parameters for all transactions
        parameters = {
            'Channel': data.get('Channel', ''),
            'Store': data.get('Store', ''),
        }

        # Updating parameters with the extra parameters
        parameters.update(data)

        azul_endpoint = self.url + f'?{operation}'
        cert_path = self.certificate_path

        headers = {
            'Content-Type': 'application/json',
            'Auth1': self.auth1,
            'Auth2': self.auth2,
        }
        r = {}
        _logger.debug('azul_request: called with data:\n%s', data)

        try:
            async with httpx.AsyncClient(cert=cert_path) as client: 
                r = await client.post(
                    azul_endpoint,
                    json=parameters,
                    headers=headers,
                    timeout=30,
                )
                if r.raise_for_status() and self.ENVIRONMENT == 'prod':
                    azul_endpoint = self.ALT_URL + f'?{operation}'
                    r = httpx.post(
                        azul_endpoint,
                        json=parameters,
                        headers=headers,
                        timeout=30,
                    )
        except Exception as err:
            _logger.error(
                'azul_request: Got the following error\n%s', str(err))
            raise Exception(str(err))

        response = json.loads(r.text)
        _logger.debug('azul_request: Values received\n%s', json.loads(r.text))

        return response

    async def sale_transaction(self, data):
        data.update(validate.sale_transaction(data))
        return await self.azul_request(data)

    async def hold_transaction(self, data):
        data.update(validate.hold_transaction(data))
        return await self.azul_request(data)

    async def refund_transaction(self, data):
        data.update(validate.refund_transaction(data))
        return await self.azul_request(data)

    async def void_transaction(self, data):
        data.update(validate.void_transaction(data))
        return await self.azul_request(data, operation='ProcessVoid')

    async def post_sale_transaction(self, data):
        data.update(validate.post_sale_transaction(data))
        return await self.azul_request(data, operation='ProcessPost')

    async def verify_transaction(self, data):
        data.update(validate.verify_transaction(data))
        return await self.azul_request(data, operation='VerifyPayment')

    async def nulify_transaction(self, data):
        data.update(validate.nullify_transaction(data))
        return await self.azul_request(data)

    async def datavault_create(self, data):
        data.update(validate.datavault_create(data))
        return await self.azul_request(data, operation='ProcessDatavault')

    async def datavault_delete(self, data):
        data.update(validate.datavault_delete(data))
        return await self.azul_request(data, operation='ProcessDatavault')