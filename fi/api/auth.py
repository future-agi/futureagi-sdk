import os
import time
from abc import ABC, abstractmethod
from typing import Dict, Generic, Optional, TypeVar, Union

from requests import Response
from requests_futures.sessions import FuturesSession

from fi.api.types import RequestConfig
from fi.integrations.providers.types import ApiKeyName
from fi.utils.constants import (
    API_KEY_ENVVAR_NAME,
    BASE_URL,
    DEFAULT_MAX_QUEUE,
    DEFAULT_MAX_WORKERS,
    DEFAULT_TIMEOUT,
    SECRET_KEY_ENVVAR_NAME,
)
from fi.utils.errors import AuthError
from fi.utils.executor import BoundedExecutor

T = TypeVar("T")


class ResponseHandler(Generic[T], ABC):
    """Handles response parsing and validation"""

    @classmethod
    def parse(cls, response: Response) -> T:
        """Parse the response into the expected type"""
        if not response.ok:
            cls._handle_error(response)
        return cls._parse_success(response)

    @classmethod
    @abstractmethod
    def _parse_success(cls, response: Response) -> T:
        """Parse successful response"""
        pass

    @classmethod
    @abstractmethod
    def _handle_error(cls, response: Response) -> None:
        """Handle error responses"""
        pass


class HttpClient:
    """Base HTTP client with improved request handling"""

    def __init__(
        self,
        base_url: Optional[str] = None,
        session: Optional[FuturesSession] = None,
        default_headers: Optional[Dict[str, str]] = None,
        **kwargs,
    ):
        self._base_url = base_url.rstrip("/") if base_url else BASE_URL.rstrip("/")
        self._session = session or FuturesSession(
            executor=BoundedExecutor(
                bound=kwargs.get("max_queue", DEFAULT_MAX_QUEUE),
                max_workers=kwargs.get("max_workers", DEFAULT_MAX_WORKERS),
            ),
        )
        self._default_headers = default_headers or {}
        self._default_timeout = kwargs.get("timeout", DEFAULT_TIMEOUT)

    def request(
        self,
        config: RequestConfig,
        response_handler: Optional[ResponseHandler[T]] = None,
    ) -> Union[Response, T]:
        """Make an HTTP request with retries and response handling"""

        url = config.url
        headers = {**self._default_headers, **(config.headers or {})}
        params = config.params or {}
        json = config.json or {}
        timeout = config.timeout or self._default_timeout
        for attempt in range(config.retry_attempts):
            try:
                response = self._session.request(
                    method=config.method.value,
                    url=url,
                    headers=headers,
                    params=params,
                    json=json,
                    timeout=timeout,
                ).result()

                if response_handler:
                    return response_handler.parse(response=response)
                return response

            except Exception as e:
                if attempt == config.retry_attempts - 1:
                    raise e
                time.sleep(config.retry_delay)

    def close(self):
        """Close the client session"""
        self._session.close()


class APIKeyAuth(HttpClient):
    _fi_api_key: str = None
    _fi_secret_key: str = None

    def __init__(
        self,
        fi_api_key: Optional[str] = None,
        fi_secret_key: Optional[str] = None,
        fi_base_url: Optional[str] = None,
        **kwargs,
    ):
        self.__class__._fi_api_key = fi_api_key or os.environ.get(API_KEY_ENVVAR_NAME)
        self.__class__._fi_secret_key = fi_secret_key or os.environ.get(
            SECRET_KEY_ENVVAR_NAME
        )
        if self._fi_api_key is None or self._fi_secret_key is None:
            raise AuthError(self._fi_api_key, self._fi_secret_key)

        super().__init__(
            base_url=fi_base_url,
            default_headers={
                "X-Api-Key": self._fi_api_key,
                "X-Secret-Key": self._fi_secret_key,
            },
            **kwargs,
        )


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
