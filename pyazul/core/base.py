"""Base classes and utilities for the PyAzul library."""

from ..api.client import AzulAPI


class BaseService:
    """Base class for all Azul API services."""

    def __init__(self, api_client: AzulAPI):
        """
        Initialize the service with a shared AzulAPI client.

        Args:
            api_client (AzulAPI): The shared API client instance.
        """
        self.api = api_client
