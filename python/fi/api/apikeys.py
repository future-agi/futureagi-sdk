from typing import List, Optional, Union

from requests import Response

from fi.api.auth import APIKeyAuth, ResponseHandler
from fi.api.types import ApiKey, HttpMethod, ModelProvider, RequestConfig
from fi.utils.routes import Routes


class ProviderAPIKeyResponseHandler(ResponseHandler[ApiKey, None]):
    """Handles responses for API key operations"""

    @classmethod
    def _parse_success(cls, response: Response) -> Union[ApiKey, List[ApiKey]]:
        data = response.json()
        method = response.request.method
        if method == HttpMethod.POST.value:
            return {
                "success": True,
            }
        elif method == HttpMethod.GET.value:
            data = data["results"]
            result = []
            for api_key in data:
                result.append(ApiKey(**api_key))
            return result
        else:
            return data

    @classmethod
    def _handle_error(cls, response: Response) -> None:
        if response.status_code >= 400:
            response.raise_for_status()


class ProviderAPIKeyClient(APIKeyAuth):
    """Client for API key operations

    This client can be used in two ways:
    1. As class methods for simple one-off operations:
        ProviderAPIKeyClient.set_api_key(api_key)

    2. As an instance for chained operations:
        client = ProviderAPIKeyClient()
        client.set(api_key).get(provider)
    """

    def __init__(
        self,
        api_key: ApiKey,
        fi_api_key: Optional[str] = None,
        fi_secret_key: Optional[str] = None,
        fi_base_url: Optional[str] = None,
    ):
        """
        Initialize the ProviderAPIKeyClient

        Args:
            fi_api_key (str): The API key for the organization
            fi_secret_key (str): The secret key for the organization
            fi_base_url (str): The base URL for the organization
            api_key (ApiKey): The API key to set

        Returns:
            ProviderAPIKeyClient: The initialized client
        """
        super().__init__(fi_api_key, fi_secret_key, fi_base_url)
        self.api_key = api_key

    # Instance methods for chaining
    def set(self) -> "ProviderAPIKeyClient":
        """Create a new API key and return self for chaining"""
        if self.api_key.key is None:
            raise ValueError("API key is required")
        response = self._set_api_key(self.api_key)  # noqa: F841
        return self

    def get(self) -> Optional[ApiKey]:
        """Get a specific API key by provider"""
        response = self._get_api_key(self.api_key.provider)
        self.api_key = response
        return response

    # Protected internal methods
    def _set_api_key(self, api_key: ApiKey) -> ApiKey:
        """Internal method for setting API key"""
        response = self.request(
            config=RequestConfig(
                method=HttpMethod.POST,
                url=self._base_url + "/" + Routes.model_hub_api_keys.value,
                json={
                    "provider": api_key.provider.value,
                    "key": api_key.key,
                },
            ),
            response_handler=ProviderAPIKeyResponseHandler,
        )
        return response

    def _get_api_key(self, provider: ModelProvider) -> Optional[ApiKey]:
        """Internal method to get API key by provider"""
        response = self.request(
            config=RequestConfig(
                method=HttpMethod.GET,
                url=self._base_url + "/" + Routes.model_hub_api_keys.value,
            ),
            response_handler=ProviderAPIKeyResponseHandler,
        )
        if response:
            for api_key in response:
                if api_key.provider == provider:
                    return api_key
        return None

    # Class methods for simple operations
    @classmethod
    def _get_instance(cls, api_key: ApiKey, **kwargs) -> "ProviderAPIKeyClient":
        """Create a new ProviderAPIKeyClient instance"""
        instance = cls(api_key, **kwargs) if isinstance(cls, type) else cls
        instance.api_key = api_key
        return instance

    @classmethod
    def set_api_key(cls, api_key: ApiKey, **kwargs) -> ApiKey:
        """Class method for simple API key creation"""
        instance = cls._get_instance(api_key, **kwargs)
        return instance.set()

    @classmethod
    def get_api_key(cls, provider: ModelProvider, **kwargs) -> Optional[ApiKey]:
        """Class method for simple API key retrieval"""
        api_key = ApiKey(provider=provider)
        instance = cls._get_instance(api_key, **kwargs)
        return instance.get()

    @classmethod
    def list_api_keys(cls, **kwargs) -> List[ApiKey]:
        """List all API keys for the organization"""
        instance = cls._get_instance(ApiKey(), **kwargs)
        response = instance.request(
            config=RequestConfig(
                method=HttpMethod.GET,
                url=instance._base_url + "/" + Routes.model_hub_api_keys.value,
            ),
            response_handler=ProviderAPIKeyResponseHandler,
        )
        return response
