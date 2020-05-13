
def datavault_create(**kwargs):
    required = {
        'CardNumber': kwargs['CardNumber'],
        'Expiration': kwargs['Expiration'],
        'CVC': kwargs['CVC'],
        'TrxType': 'CREATE',
    }

    return required


def datavault_delete(**kwargs):
    required = {
        'CardNumber': kwargs['CardNumber'],
        'Expiration': kwargs['Expiration'],
        'CVC': kwargs['CVC'],
        'TrxType': 'DELETE',
    }

    return required


def sale_transaction(**kwargs):
    
    required = {
        'CardNumber': kwargs['CardNumber'],
        'Expiration': kwargs['Expiration'],
        'CVC': kwargs['CVC'],
        'PosInputMode': kwargs['PosInputMode'],
        'TrxType': 'Sales',
        'Amount': kwargs['Amount'],
        'Itbis': kwargs['Itbis'],
        'CurrencyPosCode': kwargs['CurrencyPosCode'],
        'Payments': '1',
        'Plan': '0',
        'AcquirerRefData': '1',
        'CustomerServicePhone': kwargs['CustomerServicePhone'],
        'OrderNumber': kwargs['OrderNumber'],
        'ECommerceUrl': kwargs['ECommerceUrl'],
        'CustomOrderId': kwargs['CustomOrderId']
    }

    return required


def hold_transaction(**kwargs):
    
    required = {
        'CardNumber': kwargs['CardNumber'],
        'Expiration': kwargs['Expiration'],
        'CVC': kwargs['CVC'],
        'PosInputMode': kwargs['PosInputMode'],
        'TrxType': 'Hold',
        'Amount': kwargs['Amount'],
        'Itbis': kwargs['Itbis'],
        'CurrencyPosCode': kwargs['CurrencyPosCode'],
        'Payments': '1',
        'Plan': '0',
        'AcquirerRefData': '1',
        'OrderNumber': kwargs['OrderNumber']
    }

    return required


def post_sale_transaction(**kwargs):
    
    required = {
        'AzulOrderId': kwargs['AzulOrderId'],
        'Amount': kwargs['Amount'],
        'ITBIS': kwargs['ITBIS']
    }

    return required


def nullify_transaction(**kwargs):
    
    required = {
        'CardNumber': kwargs['CardNumber'],
        'Expiration': kwargs['Expiration'],
        'CVC': kwargs['CVC'],
        'PosInputMode': kwargs['PosInputMode'],
        'TrxType': 'Sales',
        'Amount': kwargs['Amount'],
        'ITBIS': kwargs['Itbis'],
        'CurrencyPosCode': kwargs['CurrencyPosCode'],
        'Payments': '1',
        'Plan': '0',
        'AcquirerRefData': '1',
        'CustomerServicePhone': kwargs['CustomerServicePhone'],
        'OrderNumber': kwargs['OrderNumber']
    }

    return required


def refund_transaction(**kwargs):
    
    required = {
        'AzulOrderId': kwargs['AzulOrderId'],
        'CVC': None,
        'PosInputMode': kwargs['PosInputMode'],
        'TrxType': 'Refund',
        'Amount': kwargs['Amount'],
        'Itbis': kwargs['Itbis'],
        'CurrencyPosCode': kwargs['CurrencyPosCode'],
        'Payments': kwargs['Payments'],
        'Plan': kwargs['Plan'],
        'AcquirerRefData': None,
        'OriginalDate': kwargs['OriginalDate'],
        'OrderNumber': kwargs['OrderNumber'],
        'ECommerceUrl': kwargs['ECommerceUrl'],
        'CustomOrderId': kwargs['CustomOrderId']
    }

    return required


def datavault_sale_transaction(**kwargs):
    
    required = {
        'CardNumber': '',
        'Expiration': '',
        'CVC': '',
        'PosInputMode': kwargs['PosInputMode'],
        'TrxType': 'Sales',
        'Amount': kwargs['Amount'],
        'Itbis': kwargs['Itbis'],
        'CurrencyPosCode': kwargs['CurrencyPosCode'],
        'Payments': kwargs['Payments'],
        'Plan': kwargs['Plan'],
        'AcquirerRefData': kwargs['AcquirerRefData'],
        'OrderNumber': kwargs['OrderNumber'],
        'DataVaultToken': kwargs['DataVaultToken']
    }

    return required


def verify_transaction(**kwargs):
   
    required = {
        'CustomOrderId': kwargs['CustomOrderId'],
    }

    return required
