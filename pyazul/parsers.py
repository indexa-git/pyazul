
def dv_create(**kwargs):

    # Mandatory parameters
    parameters = {
        'Channel': kwargs['Channel'],
        'Store': kwargs['Store'],
        'CardNumber': kwargs['CardNumber'],
        'Expiration': kwargs['Expiration'],
        'CVC': kwargs['CVC'],
        'TrxType': kwargs['TrxType'],
    }

    return parameters


def dv_delete(**kwargs):

    # Mandatory parameters
    parameters = {
        'Channel': kwargs['Channel'],
        'Store': kwargs['Store'],
        'CardNumber': kwargs['CardNumber'],
        'Expiration': kwargs['Expiration'],
        'CVC': kwargs['CVC'],
        'TrxType': kwargs['TrxType'],
    }

    return parameters


def sale_transaction(**kwargs):

    # Mandatory parameters
    parameters = {
        'Channel': kwargs['Channel'],
        'Store': kwargs['Store'],
        'CardNumber': kwargs['CardNumber'],
        'Expiration': kwargs['Expiration'],
        'CVC': kwargs['CVC'],
        'PosInputMode': kwargs['PosInputMode'],
        'TrxType': kwargs['TrxType'],
        'Amount': kwargs['Amount'],
        'Itbis': kwargs['Itbis'],
        'CurrencyPosCode': kwargs['CurrencyPosCode'],
        'Payments': kwargs['Payments'],
        'Plan': kwargs['Plan'],
        'AcquirerRefData': kwargs['AcquirerRefData'],
        'CustomerServicePhone': kwargs['CustomerServicePhone'],
        'OrderNumber': kwargs['OrderNumber'],
        'ECommerceUrl': kwargs['ECommerceUrl'],
        'CustomOrderId': kwargs['CustomOrderId'],
        # 'AltMerchantName': kwargs['AltMerchantName']
    }

    # Optional parameters
    for key, value in kwargs.items():
        if key.lower() == 'DataVaultToken':
            parameters['DataVaultToken'] = value
        elif key.lower() == 'SaveToDataVault':
            parameters['SaveToDataVault'] = value
        elif key.lower() == 'ForceNo3DS':
            parameters['ForceNo3DS'] = value
        elif key.lower() == 'AltMerchantName':
            parameters['AltMerchantName'] = value

    return parameters


def dv_sale_transaction(**kwargs):

    # Mandatory parameters
    parameters = {
        'Channel': kwargs['Channel'],
        'Store': kwargs['Store'],
        'CardNumber': '',
        'Expiration': '',
        'CVC': '',
        'PosInputMode': kwargs['PosInputMode'],
        'TrxType': kwargs['TrxType'],
        'Amount': kwargs['Amount'],
        'Itbis': kwargs['Itbis'],
        'CurrencyPosCode': kwargs['CurrencyPosCode'],
        'Payments': kwargs['Payments'],
        'Plan': kwargs['Plan'],
        'AcquirerRefData': kwargs['AcquirerRefData'],
        'OrderNumber': kwargs['OrderNumber'],
        'DataVaultToken': kwargs['DataVaultToken']
        # 'AltMerchantName': kwargs['AltMerchantName']
    }

    # Optional parameters
    for key, value in kwargs.items():
        if key == 'CustomerServicePhone':
            parameters['CustomerServicePhone'] = value
        elif key == 'ECommerceUrl':
            parameters['ECommerceUrl'] = value
        elif key == 'CustomOrderId':
            parameters['CustomOrderId'] = value

    return parameters


def verify_transaction(**kwargs):

    # Mandatory parameters
    parameters = {
        'Channel': kwargs['Channel'],
        'Store': kwargs['Store'],
        'CustomOrderId': kwargs['CustomOrderId'],
    }

    return parameters
