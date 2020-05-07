
def main(data):
    '''
    This function receives a dictionary with candidate parameters for 
    a transaction of type 'Process Payment'.

    Returns a dictionary with valid key, value pairs.
    '''

    parameters = {
        'Channel': data['Channel'],
        'Store': data['Store'],
        'CardNumber': data['CardNumber'],
        'Expiration': data['Expiration'],
        'CVC': data['CVC'],
        'PosInputMode': data['PosInputMode'],
        'TrxType': data['TrxType'],
        'Amount': data['Amount'],
        'Itbis': data['Itbis'],
        'CurrencyPosCode': data['CurrencyPosCode'],
        'Payments': data['Payments'],
        'Plan': data['Plan'],
        'AcquirerRefData': data['AcquirerRefData'],
        'CustomerServicePhone': data['CustomerServicePhone'],
        'OrderNumber': data['OrderNumber'],
        'ECommerceUrl': data['ECommerceUrl'],
        'CustomOrderId': data['CustomOrderId'],
        # 'AltMerchantName': data['AltMerchantName']
    }

    for key, value in data.items():
        if key.lower() == 'datavaulttoken':
            parameters['DataVaultToken'] = value
        elif key.lower() == 'savetodatavault':
            parameters['SaveToDataVault'] = value
        elif key.lower() == 'forceno3ds':
            parameters['ForceNo3DS'] = value
        elif key.lower() == 'altmerchantname':
            data['AltMerchantName'] = value

    return parameters
