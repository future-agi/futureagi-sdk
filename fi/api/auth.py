import os
import time
from abc import ABC, abstractmethod
from typing import Dict, Optional

from requests import Response

from fi.api.types import RequestType
from fi.integrations.providers.types import ApiKeyName
from fi.utils.constants import API_KEY_ENVVAR_NAME, BASE_URL, SECRET_KEY_ENVVAR_NAME
from fi.utils.errors import AuthError


class BaseClient(ABC):
    @property
    @abstractmethod
    def url(self) -> str:
        pass

    @property
    @abstractmethod
    def headers(self) -> dict:
        pass

    @property
    @abstractmethod
    def params(self) -> dict:
        pass

    @property
    @abstractmethod
    def payload(self) -> dict:
        pass

    @property
    @abstractmethod
    def session(self):
        pass

    def make_request(
        self,
        request_type: RequestType,
        url: Optional[str] = None,
        headers: Optional[dict] = None,
        params: Optional[dict] = None,
        payload: Optional[dict] = None,
    ) -> Response:
        response_future = self.session.request(
            request_type,
            url or self.url,
            headers=headers or self.headers,
            params=params or self.params,
            json=payload or self.payload,
        )
        while response_future.done() is False:
            time.sleep(1)
        return response_future.result()


class APIKeyAuth(BaseClient):
    _fi_api_key: str = None
    _fi_secret_key: str = None
    BASE_URL: str = None

    def __init__(
        self,
        fi_api_key: Optional[str] = None,
        fi_secret_key: Optional[str] = None,
        url: Optional[str] = None,
    ):
        self.__class__._fi_api_key = fi_api_key or os.environ.get(API_KEY_ENVVAR_NAME)
        self.__class__._fi_secret_key = fi_secret_key or os.environ.get(
            SECRET_KEY_ENVVAR_NAME
        )
        self.__class__.BASE_URL = url or BASE_URL
        if self._fi_api_key is None or self._fi_secret_key is None:
            raise AuthError(self._fi_api_key, self._fi_secret_key)


class APIKeyManager(APIKeyAuth):
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize()
        return cls._instance

    @property
    def url(self) -> str:
        return self.BASE_URL + "/model_hub/api-keys"

    @property
    def headers(self) -> dict:
        return {
            "X-Api-Key": self._fi_api_key,
            "X-Secret-Key": self._fi_secret_key,
        }

    def _initialize(self):
        self._api_keys: Dict[ApiKeyName, Optional[str]] = {
            key: os.getenv(key.value) for key in ApiKeyName
        }

    def get_api_key(self, provider: ApiKeyName) -> Optional[str]:
        if provider not in self._api_keys:
            raise ValueError(f"Provider {provider} not found in API keys")  # noqa: E713
        return self._api_keys[provider]

    def set_api_key(self, provider: ApiKeyName, key: str) -> None:
        self._api_keys[provider] = key

    def validate_required_keys(self, required_providers: list[ApiKeyName]) -> bool:
        if not required_providers:
            return True

        missing_keys = [
            provider.value
            for provider in required_providers
            if provider not in self._api_keys
        ]

        if missing_keys:
            raise ValueError(f"Missing required API keys: {', '.join(missing_keys)}")
        return True
