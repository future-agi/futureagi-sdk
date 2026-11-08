"""Pure gateway request construction; no client, pool, socket or send operation."""

from __future__ import annotations

from typing import Any

import httpx

from fi.gateway._agentcc_params import _layer_metadata
from fi.gateway._constants import (
    AGENTCC_PARAM_TO_HEADER, HEADER_API_KEY, HEADER_CONTENT_TYPE,
    HEADER_SDK_VERSION, HEADER_USER_AGENT, NOT_GIVEN, __version__,
)
from fi.gateway._env import guard_fi_key_pair
from fi.gateway._http_security import validate_destination
from fi.gateway._utils import serialize_agentcc_param


class RequestBuilder:
    """The no-I/O half shared by both transports and raw request inspection."""

    def __init__(
        self, *, api_key: str, base_url: str,
        default_headers: dict[str, str] | None = None,
        default_query: dict[str, str] | None = None,
        session_id: str | None = None, metadata: dict[str, Any] | None = None,
        config: Any = None,
    ) -> None:
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        validate_destination(self._base_url, self._base_url)
        self._default_headers = default_headers or {}
        self._default_query = default_query or {}
        self._session_id = session_id
        self._metadata = metadata
        self._config = config

    def _build_headers(
        self, options: Any, agentcc_params: dict[str, Any] | None = None,
    ) -> dict[str, str]:
        """The released seven-level merge, guarded on every construction."""
        guard_fi_key_pair(self._api_key)
        headers: dict[str, str] = {
            HEADER_USER_AGENT: f"agentcc-python/{__version__}",
            HEADER_CONTENT_TYPE: "application/json",
            HEADER_SDK_VERSION: __version__,
            HEADER_API_KEY: f"Bearer {self._api_key}",
        }
        headers.update(self._default_headers)
        if self._session_id is not None:
            headers[AGENTCC_PARAM_TO_HEADER["session_id"]] = self._session_id
        if self._metadata is not None:
            headers[AGENTCC_PARAM_TO_HEADER["request_metadata"]] = serialize_agentcc_param(
                "request_metadata", self._metadata,
            )
        if self._config is not None and hasattr(self._config, "to_headers"):
            headers.update(self._config.to_headers())
        if agentcc_params:
            for key, value in agentcc_params.items():
                if value is NOT_GIVEN or value is None:
                    continue
                name = AGENTCC_PARAM_TO_HEADER.get(key)
                if name:
                    if key == "request_metadata":
                        value = _layer_metadata(self._metadata, value)
                    headers[name] = serialize_agentcc_param(key, value)
        headers.update(options.headers)
        for name, value in headers.items():
            if name.lower() in {"authorization", "x-api-key"}:
                guard_fi_key_pair(value)
        return headers

    def _build_url(self, path: str) -> str:
        """Validate the destination and merge default queries; never resolve DNS."""
        url = path if path.startswith(("http://", "https://")) else (
            self._base_url + "/" + path.lstrip("/")
        )
        validate_destination(self._base_url, url)
        if not self._default_query:
            return url
        parsed = httpx.URL(url)
        query = httpx.QueryParams(self._default_query).merge(parsed.params)
        return str(parsed.copy_with(params=query))

    def _build_request(self, options: Any, params: Any = None) -> httpx.Request:
        """Encode JSON once for inspection and sends, using HTTPX's own encoder.

        Explicit transport defaults keep the inspection independent of client
        creation and of optional compression packages. Caller headers still win.
        Multipart remains on the transport's streaming files/data path.
        """
        if options.files is not None:
            raise TypeError("Raw JSON request construction does not accept file uploads")
        headers = httpx.Headers({
            "Accept": "*/*", "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
        })
        headers.update(self._build_headers(options, params))
        return httpx.Request(
            method=options.method, url=self._build_url(options.url),
            headers=headers, json=options.body,
        )
