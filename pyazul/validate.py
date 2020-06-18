''' Validation module '''
from . import exceptions
from . import utils


def check_not_empty(value):
    '''
    Returns True if a value is not empty
    '''
    if not value:
        raise exceptions.UnexpectedEmptyValue
    return True


def check_minimum_length(length):
    '''
    Checks that a string has minimum provided length
    '''
    def inner(_, value):
        value_len = len(value)
        if value_len < length:
            raise exceptions.MinimumLengthNotReached(
                f'{value}: current length {value_len}'
                f'expected {length}'
            )
        return True
    return inner


def check_exists_in(data):
    '''
    Checks if a given key exists in the data dictionary
    '''
    def inner(key, _):
        if key not in data:
            raise exceptions.RequiredParameterNotFound(key)
        return True
    return inner


def check_type(_type):
    '''
    Checks value matches a certain data type
    '''
    def inner(_, value):
        if not isinstance(value, _type):
            raise exceptions.UnsuportedType
        return True
    return inner


def validate(data, validation_rule_sets):
    '''
    Validates that dictionary contains all the minimum required fields and also its values.
    '''
    for rule_set in validation_rule_sets:

        key = rule_set
        value = data[key]
        rule_set = validation_rule_sets[rule_set]

        for rule in rule_set:
            rule(key, value)


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


def sale_transaction(data):
    validation_rule_sets = {
        'CardNumber': (check_exists_in(data), check_not_empty),
        'Expiration': (check_exists_in(data)),
        'CVC': (check_exists_in(data)),
        'PosInputMode': (
            check_exists_in(data),
        ),
        'Payments': (check_exists_in(data), check_minimum_length(1)),
        'Plan': (check_exists_in(data), check_minimum_length(1)),
        'Amount': (
            check_exists_in(data),
            check_minimum_length(1),
            check_type(int),
        ),
        'Itbis': (
            check_exists_in(data),
            check_minimum_length(1),
            check_type(int),
        ),
        'CurrencyPosCode':  (check_exists_in(data)),
        'AcquirerRefData': (
            check_exists_in(data),
            check_minimum_length(1),
            check_type(str)
        ),
        'CustomerServicePhone': (check_exists_in(data)),
        'OrderNumber': (check_exists_in(data)),
        'EcommerceURL': (check_exists_in(data)),
        'CustomOrderID': (check_exists_in(data)),
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
