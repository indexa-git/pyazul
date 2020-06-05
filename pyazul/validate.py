from . import utils


def datavault_create(data):
    required = {
        'CardNumber': data.get('CardNumber', ''),
        'Expiration': data.get('Expiration', ''),
        'CVC': data.get('CVC', ''),
        'TrxType': 'CREATE',
    }

    return required


def datavault_delete(data):
    required = {
        'DataVaultToken': data.get('DataVaultToken', ''),
        'TrxType': 'DELETE',
    }

    return required


def sale_transaction(data):
    required = {
        'CardNumber': data.get('CardNumber', ''),
        'Expiration': data.get('Expiration', ''),
        'CVC': data.get('CVC', ''),
        'PosInputMode': data.get('PosInputMode', ''),
        'TrxType': 'Sale',
        'Amount': str(utils.clean_amount(data.get('Amount', 0))),
        'Itbis': utils.clean_amount(data.get('Itbis', 0)),
        'CurrencyPosCode': data.get('CurrencyPosCode', ''),
        'AcquirerRefData': data.get('AcquirerRefData', ''),
        'CustomerServicePhone': data.get('CustomerServicePhone', ''),
        'OrderNumber': data.get('OrderNumber', ''),
        'EcommerceURL': data.get('EcommerceURL', ''),
        'CustomOrderID': data.get('CustomOrderID', ''),
    }

    return required


def hold_transaction(data):

    required = {
        'CardNumber': data.get('CardNumber', ''),
        'Expiration': data.get('Expiration', ''),
        'CVC': data.get('CVC', ''),
        'PosInputMode': data.get('PosInputMode', ''),
        'TrxType': 'Hold',
        'Amount': utils.clean_amount(data.get('Amount', 0)),
        'Itbis': utils.clean_amount(data.get('Itbis', 0)),
        'CurrencyPosCode': data.get('CurrencyPosCode', ''),
        'OrderNumber': data.get('OrderNumber', ''),
    }

    return required


def post_sale_transaction(data):
    required = {
        'AzulOrderId': data.get('AzulOrderId', ''),
        'Amount': utils.clean_amount(data.get('Amount', 0)),
        'Itbis': utils.clean_amount(data.get('Itbis', 0)),
    }

    return required


def nullify_transaction(data):

    required = {
        'CardNumber': data.get('CardNumber', ''),
        'Expiration': data.get('Expiration', ''),
        'CVC': data.get('CVC', ''),
        'PosInputMode': data.get('PosInputMode', ''),
        'TrxType': 'Sale',
        'Amount': utils.clean_amount(data.get('Amount', 0)),
        'Itbis': utils.clean_amount(data.get('Itbis', 0)),
        'CurrencyPosCode': data.get('CurrencyPosCode', ''),
        'CustomerServicePhone': data.get('CustomerServicePhone', ''),
        'OrderNumber': data.get('OrderNumber', ''),
    }

    return required


def refund_transaction(data):
    required = {
        'CardNumber': data.get('CardNumber', ''),
        'Expiration': data.get('Expiration', ''),
        'CVC': data.get('CVC', ''),
        'PosInputMode': data.get('PosInputMode', ''),
        'TrxType': 'Refund',
        'Amount': str(utils.clean_amount(data.get('Amount', 0))),
        'Itbis': utils.clean_amount(data.get('Itbis', 0)),
        'CurrencyPosCode': data.get('CurrencyPosCode', ''),
        'OriginalDate': data.get('OriginalDate', ''),
        'OriginalTrxTicketNr': data.get('OriginalTrxTicketNr', ''),
        'AcquirerRefData': data.get('AcquirerRefData', ''),
        'CustomerServicePhone': data.get('CustomerServicePhone', ''),
        'OrderNumber': data.get('OrderNumber', ''),
        'EcommerceURL': data.get('EcommerceURL', ''),
        'CustomOrderID': data.get('CustomOrderID', ''),
        'OriginalDate': data.get('OriginalDate', ''),
        'AzulOrderId': data.get('AzulOrderId', ''),
    }

    return required


def void_transaction(data):
    required = {
        'AzulOrderId': data.get('AzulOrderId', ''),
    }
    return required


def datavault_sale_transaction(data):

    required = {
        'CardNumber': '',
        'Expiration': '',
        'CVC': '',
        'PosInputMode': data.get('PosInputMode', ''),
        'TrxType': 'Sale',
        'Amount': utils.clean_amount(data.get('Amount', 0)),
        'Itbis': utils.clean_amount(data.get('Itbis', 0)),
        'CurrencyPosCode': data.get('CurrencyPosCode', ''),
        'Payments': data.get('Payments', ''),
        'Plan': data.get('Plan', ''),
        'AcquirerRefData': data.get('AcquirerRefData', ''),
        'OrderNumber': data.get('OrderNumber', ''),
        'DataVaultToken': data.get('DataVaultToken', ''),
    }

    return required


def verify_transaction(data):

    required = {
        'CustomOrderId': data.get('CustomOrderId', ''),
    }

    return required
