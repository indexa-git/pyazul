
def main(data):
    '''
    This function receives a dictionary with candidate parameters for 
    a transaction of type 'DataVault Delete'.

    Returns a dictionary with valid key, value pairs.
    '''

    parameters = {
        'Channel': data['Channel'],
        'Store': data['Store'],
        'CardNumber': data['CardNumber'],
        'Expiration': data['Expiration'],
        'CVC': data['CVC'],
        'TrxType': data['TrxType'],
    }

    return parameters
