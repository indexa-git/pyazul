
import pytz
from google.cloud import secretmanager
from datetime import date, datetime, timedelta


def recursive_items(dictionary):
    """
    This functions iterates over a nested dictionary and returns a generator
    """
    for key, value in dictionary.items():
        if type(value) is dict:
            yield from recursive_items(value)
        else:
            yield (key, value)


def getDate():
    tzinfo = pytz.timezone('America/Santo_Domingo')
    today = datetime.now(tz=tzinfo)
    return today


def getSecret(secret_name):
    secrets_client = secretmanager.SecretManagerServiceClient()
    resource_id = f'projects/637553027390/secrets/{secret_name}/versions/latest'
    response = secrets_client.access_secret_version(resource_id)
    return response.payload.data.decode('UTF-8')
