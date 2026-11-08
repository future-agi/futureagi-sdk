"""Adapt the root client's HTTP transport to the legacy evaluation response API.

Only standalone Evaluator instances own a requests session. The platform delegate borrows its
client's httpx connection pool, authentication, headers, timeout and retry policy. Its close()
invalidates the adapter without closing that borrowed pool.
"""
from copy import copy
from typing import Any, Callable

import httpx
import requests

from fi.evals.core import cloud_registry
from fi.evals.evaluator import Evaluator


def _legacy_response(response: httpx.Response) -> requests.Response:
    result = requests.Response()
    result.status_code = response.status_code
    result._content = response.content
    result.headers.update(response.headers)
    result.encoding = response.encoding
    result.url = str(response.url)
    result.reason = response.reason_phrase
    return result


class _BorrowedSession:
    def __init__(self, client: Callable[[], httpx.Client]) -> None:
        self.client = client
        self.registry_cache: dict = cloud_registry._RegistryCache()
        self.closed = False

    def get(self, url: str, **kwargs: Any) -> requests.Response:
        if self.closed:
            raise RuntimeError("the evaluation client is closed")
        return _legacy_response(self.client().get(url, **kwargs))

    def close(self) -> None:
        with cloud_registry._CACHE_LOCK:
            self.closed = True
            cloud_registry._invalidate_cache(self.registry_cache)


class ClientEvaluator(Evaluator):
    """The source-compatible evaluator using the parent client's transport."""

    def __init__(self, *, http_client: Callable[[], httpx.Client], **kwargs: Any) -> None:
        session = _BorrowedSession(http_client)
        super().__init__(session=session, timeout=http_client().timeout.read, **kwargs)
        self._registry_session = session

    def evaluate(self, eval_templates: Any, inputs: Any, timeout: Any = None, **kwargs: Any) -> Any:
        # A per-call view avoids changing shared timeout state while another evaluation is running.
        view = copy(self)
        view._timeout_override = timeout
        return Evaluator.evaluate(view, eval_templates, inputs, timeout=timeout, **kwargs)

    def request(self, config: Any, response_handler: Any = None) -> Any:
        if self._session.closed:
            raise RuntimeError("the evaluation client is closed")
        client = self._session.client()
        options = dict(headers={**self._default_headers, **(config.headers or {})},
                       params=config.params, json=config.json)
        if config.data:
            options["data"] = config.data
        if config.files:
            options["files"] = config.files
        # Retain structured connect/read/write/pool timeouts unless the caller overrides it.
        override = getattr(self, "_timeout_override", None)
        if override is not None:
            options["timeout"] = override
        elif config.timeout is not None and config.timeout != self._default_timeout:
            options["timeout"] = config.timeout
        # The root transport owns retries; do not stack HttpClient's legacy retry loop on it.
        response = _legacy_response(client.request(config.method.value, config.url, **options))
        return response_handler.parse(response=response) if response_handler else response
