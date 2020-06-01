from . import utils

def datavault_create(data):
    required = {
        'CardNumber': data['CardNumber'],
        'Expiration': data['Expiration'],
        'CVC': data['CVC'],
        'TrxType': 'CREATE',
    }

    return required


def datavault_delete(data):
    required = {
        'DataVaultToken': data['DataVaultToken'],
        'TrxType': 'DELETE',
    }

    return required


def sale_transaction(data):
    required = {
        'CardNumber': data['CardNumber'],
        'Expiration': data['Expiration'],
        'CVC': data['CVC'],
        'PosInputMode': data['PosInputMode'],
        'TrxType': 'Sale',
        'Amount': str(utils.clean_amount(data['Amount'])),
        'Itbis': utils.clean_amount(data['Itbis']),
        'CurrencyPosCode': data['CurrencyPosCode'],
        'CustomerServicePhone': data['CustomerServicePhone'],
        'OrderNumber': data['OrderNumber'],
        'ECommerceUrl': data['ECommerceUrl'],
        'CustomOrderId': data['CustomOrderId'],
    }

    return required


def hold_transaction(data):
    
    required = {
        'CardNumber': data['CardNumber'],
        'Expiration': data['Expiration'],
        'CVC': data['CVC'],
        'PosInputMode': data['PosInputMode'],
        'TrxType': 'Hold',
        'Amount': utils.clean_amount(data['Amount']),
        'Itbis': utils.clean_amount(data['Itbis']),
        'CurrencyPosCode': data['CurrencyPosCode'],
        'OrderNumber': data['OrderNumber']
    }

    return required


def post_sale_transaction(data):
    required = {
        'AzulOrderId': data['AzulOrderId'],
        'Amount': utils.clean_amount(data['Amount']),
        'Itbis': utils.clean_amount(data['Itbis'])
    }

    return required


def nullify_transaction(data):
    
    required = {
        'CardNumber': data['CardNumber'],
        'Expiration': data['Expiration'],
        'CVC': data['CVC'],
        'PosInputMode': data['PosInputMode'],
        'TrxType': 'Sale',
        'Amount': utils.clean_amount(data['Amount']),
        'Itbis': utils.clean_amount(data['Itbis']),
        'CurrencyPosCode': data['CurrencyPosCode'],
        'CustomerServicePhone': data['CustomerServicePhone'],
        'OrderNumber': data['OrderNumber']
    }

    return required


def refund_transaction(data):
    required = {
        'PosInputMode': data['PosInputMode'],
        'TrxType': data['TrxType'],
        'Amount': data['Amount'],
        'Itbis': data['Itbis'],
        'CurrencyPosCode': data['CurrencyPosCode'],
        'OriginalDate': data['OriginalDate'],
        'AzulOrderId': data['AzulOrderId']
    }
    
    return required


def void_transaction(data):
    required = {
        'AzulOrderId': data['AzulOrderId'],
    }
    return required  


def datavault_sale_transaction(data):
    
    required = {
        'CardNumber': '',
        'Expiration': '',
        'CVC': '',
        'PosInputMode': data['PosInputMode'],
        'TrxType': 'Sale',
        'Amount': utils.clean_amount(data['Amount']),
        'Itbis': utils.clean_amount(data['Itbis']),
        'CurrencyPosCode': data['CurrencyPosCode'],
        'Payments': data['Payments'],
        'Plan': data['Plan'],
        'AcquirerRefData': data['AcquirerRefData'],
        'OrderNumber': data['OrderNumber'],
        'DataVaultToken': data['DataVaultToken']
    }

    return required


def verify_transaction(data):
   
    required = {
        'CustomOrderId': data['CustomOrderId'],
    }

    return required
