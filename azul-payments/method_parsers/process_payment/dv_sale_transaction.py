
def main(data):
    '''
    This function receives a dictionary with candidate parameters for 
    a transaction of type 'DataVault Process Payment'.

    Returns a dictionary with valid key, value pairs.
    '''

    parameters = {
        'Channel': data['Channel'],
        'Store': data['Store'],
        'CardNumber': '',
        'Expiration': '',
        'CVC': '',
        'PosInputMode': data['PosInputMode'],
        'TrxType': data['TrxType'],
        'Amount': data['Amount'],
        'Itbis': data['Itbis'],
        'CurrencyPosCode': data['CurrencyPosCode'],
        'Payments': data['Payments'],
        'Plan': data['Plan'],
        'AcquirerRefData': data['AcquirerRefData'],
        'OrderNumber': data['OrderNumber'],
        'DataVaultToken': data['DataVaultToken']
        # 'AltMerchantName': data['AltMerchantName']
    }

    for key, value in data.items():
        if key == 'CustomerServicePhone':
            parameters['CustomerServicePhone'] = value
        elif key == 'ECommerceUrl':
            parameters['ECommerceUrl'] = value
        elif key == 'CustomOrderId':
            data['CustomOrderId'] = value

    return parameters
