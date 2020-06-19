''' Validation module '''
from . import exceptions
from . import utils


def check_maximum_length(max_length):
    '''
    Checks the max value of an int for the specific field
    '''
    def inner(_, value):
        if isinstance(value, int):
            value = str(value)

        if len(value) > max_length:
            raise exceptions.MaximumLengthExceeded(
                f'Maximum length allowed is: {max_length}, {value} has a length of {len(value)}.'
            )
        return True

    return inner


def check_type(_type):
    '''
    Checks value matches a certain data type
    '''
    def inner(_, value):
        if not isinstance(value, _type):
            raise exceptions.UnsupportedType(
                f'Expected type: {_type}, got {type(value)} instead.')
        return True
    return inner


def validate(data, validation_rule_sets):
    '''
    Validates that dictionary contains all the minimum required fields.
    '''
    for rule_set in validation_rule_sets:
        key = rule_set

        try:
            value = data.get(key)
        except KeyError:
            raise exceptions.RequiredParameterNotFound(key)

        current_rule_set = validation_rule_sets[key]

        for rule in current_rule_set:
            rule(key, value)


def sale_transaction(data):

    validation_rule_sets = {
        'CardNumber': (),
        'Expiration': (),
        'CVC': (check_maximum_length(3),),
        'PosInputMode': (),
        'Payments': (check_maximum_length(1),),
        'Plan': (check_maximum_length(1),),
        'Amount': (
            check_maximum_length(6),
            check_type(int),
        ),
        'Itbis': (check_maximum_length(6), check_type(int),),
        'CurrencyPosCode':  (),
        'AcquirerRefData': (
            check_maximum_length(1),
            check_type(int),
        ),
        'CustomerServicePhone': (),
        'OrderNumber': (),
        'ECommerceUrl': (),
        'CustomOrderId': (),
    }

    validate(data, validation_rule_sets)


def hold_transaction(data):

    required = {
        'CardNumber': data.get('CardNumber', ''),
        'Expiration': data.get('Expiration', ''),
        'CVC': data.get('CVC', ''),
        'PosInputMode': data.get('PosInputMode', 'E-Commerce'),
        'TrxType': 'Hold',
        'Payments': data.get('Payments', '1'),
        'Plan': data.get('Plan', '0'),
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
        'PosInputMode': data.get('PosInputMode', 'E-Commerce'),
        'TrxType': 'Sale',
        'Payments': data.get('Payments', '1'),
        'Plan': data.get('Plan', '0'),
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
        'PosInputMode': data.get('PosInputMode', 'E-Commerce'),
        'TrxType': 'Refund',
        'Payments': data.get('Payments', '1'),
        'Plan': data.get('Plan', '0'),
        'Amount': str(utils.clean_amount(data.get('Amount', 0))),
        'Itbis': utils.clean_amount(data.get('Itbis', 0)),
        'CurrencyPosCode': data.get('CurrencyPosCode', ''),
        'OriginalTrxTicketNr': data.get('OriginalTrxTicketNr', ''),
        'AcquirerRefData': data.get('AcquirerRefData', '1'),
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
        'PosInputMode': data.get('PosInputMode', 'E-Commerce'),
        'TrxType': 'Sale',
        'Amount': utils.clean_amount(data.get('Amount', 0)),
        'Itbis': utils.clean_amount(data.get('Itbis', 0)),
        'CurrencyPosCode': data.get('CurrencyPosCode', ''),
        'Payments': data.get('Payments', '1'),
        'Plan': data.get('Plan', '0'),
        'AcquirerRefData': data.get('AcquirerRefData', '1'),
        'OrderNumber': data.get('OrderNumber', ''),
        'DataVaultToken': data.get('DataVaultToken', ''),
    }

    return required


def verify_transaction(data):

    required = {
        'CustomOrderId': data.get('CustomOrderId', ''),
    }

    return required


def datavault_create(data):
    required = {
        'CardNumber': data.get('CardNumber', ''),
        'Expiration': data.get('Expiration', ''),
        'CVC': data.get('CVC', ''),
        'TrxType': r'CREATE',
    }

    return required


def datavault_delete(data):
    required = {
        'DataVaultToken': data.get('DataVaultToken', ''),
        'TrxType': r'DELETE',
    }

    return required
