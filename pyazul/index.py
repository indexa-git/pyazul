# Python packages
import logging

# Third party packages
import requests
from . import validate

_logger = logging.getLogger(__name__)


# -----------------------------------------------------------------------------
# Module errors
# -----------------------------------------------------------------------------
class RequiredParameterNotFound(BaseException):
    pass


class NonOkStatusCode(requests.exceptions.HTTPError):
    pass


# -----------------------------------------------------------------------------
# Class for managing azul
# -----------------------------------------------------------------------------
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

    def __issue_http_requests(
        self, url, json, headers, cert, method, timeout=30
    ):

        try:
            r = requests.__getattribute__(method)(
                url,
                json=json,
                headers=headers,
                cert=cert,
                timeout=timeout,
            )

        except requests.exceptions.RequestException as err:
            _logger.error(f'azul_request: Got the following error {err}')
            raise Exception(err)

        else:
            return r

    def azul_request(self, data, operation=''):

        if not ('Channel' in data and 'Store' in data):
            err = (
                'Channel and Store must be present in data, and contain values'
            )
            _logger.error(err)
            raise RequiredParameterNotFound(err)

        cert_path = self.certificate_path

        headers = {
            'Content-Type': 'application/json',
            'Auth1': self.auth1,
            'Auth2': self.auth2,
        }

        _logger.debug(f'azul_request: called with data:\n {data}')

        r = self.__issue_http_requests(
            url=f'{self.url}?{operation}',
            json=data,
            headers=headers,
            cert=cert_path,
            method="post",
            timeout=30
        )

        if (not r.ok) and self.ENVIRONMENT == 'prod':
            r = self.__issue_http_requests(
                url=f'{self.ALT_URL}?{operation}',
                json=data,
                headers=headers,
                cert=cert_path,
                method="post",
                timeout=30,
            )

        if not r.ok:
            _logger.error(
                f'azul_request: Got the following http code {r.status_code}'
            )
            raise NonOkStatusCode(r.status_code)

        response = r.json()
        _logger.debug(f'azul_request: Values received {response}')

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
        data.update(validate.verify_transaction(
            data, operation='VerifyPayment'))
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
