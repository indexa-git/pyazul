
def main(data):
    '''
    This function receives a dictionary with candidate parameters for 
    a transaction of type 'Process Payment'.

    Returns a dictionary with valid key, value pairs.
    '''

    parameters = {
        'Channel': data['Channel'],
        'Store': data['Store'],
        'CustomerOrderId': data['CustomerOrderId'],
    }

    return parameters
