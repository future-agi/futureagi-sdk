"""Pure gateway request construction; no client, pool, socket or send operation."""

from __future__ import annotations

import threading
from typing import Any

import httpx

from fi.gateway._agentcc_params import _layer_metadata
from fi.gateway._constants import (
    AGENTCC_PARAM_TO_HEADER, HEADER_API_KEY, HEADER_CONTENT_TYPE,
    HEADER_SDK_VERSION, HEADER_USER_AGENT, NOT_GIVEN, __version__,
)
from fi.gateway._env import guard_fi_key_pair
from fi.gateway._http_security import reject_credential_query, validate_destination, validate_header_values
from fi.gateway._utils import serialize_agentcc_param


def _uses_form(options: Any) -> bool:
    """Published uploads use file truthiness; explicit normalized forms opt in."""
    return bool(options.files) or (options.files is not None and options.form is not None)


class RequestBuilder:
    """The no-I/O half shared by both transports and raw request inspection."""

    def __init__(
        self, *, api_key: str, base_url: str,
        default_headers: dict[str, str] | None = None,
        default_query: dict[str, str] | None = None,
        session_id: str | None = None, metadata: dict[str, Any] | None = None,
        config: Any = None, metadata_mode: str = "replace",
    ) -> None:
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._warned_http_origins: set[tuple[str, str, int]] = set()
        self._http_warning_lock = threading.Lock()
        validate_destination(self._base_url, self._base_url, warn_cleartext=False)
        reject_credential_query(default_query)
        self._default_headers = default_headers or {}
        self._default_query = default_query or {}
        self._session_id = session_id
        self._metadata = metadata
        if metadata_mode not in {"replace", "merge"}:
            raise ValueError("metadata_mode must be 'replace' or 'merge'")
        self._metadata_mode = metadata_mode
        self._config = config

    def _build_headers(
        self, options: Any, agentcc_params: dict[str, Any] | None = None,
    ) -> tuple[dict[str, str], frozenset[str]]:
        """Return the released merge and its exchange-local client header names."""
        guard_fi_key_pair(self._api_key)
        headers: dict[str, str] = {
            HEADER_USER_AGENT: f"agentcc-python/{__version__}",
            HEADER_CONTENT_TYPE: "application/json",
            HEADER_SDK_VERSION: __version__,
            HEADER_API_KEY: f"Bearer {self._api_key}",
        }
        composed_names = {HEADER_API_KEY.lower(), *(name.lower() for name in self._default_headers)}
        headers.update(self._default_headers)
        if self._session_id is not None:
            composed_names.add(AGENTCC_PARAM_TO_HEADER["session_id"].lower())
            headers[AGENTCC_PARAM_TO_HEADER["session_id"]] = self._session_id
        if self._metadata is not None:
            composed_names.add(AGENTCC_PARAM_TO_HEADER["request_metadata"].lower())
            headers[AGENTCC_PARAM_TO_HEADER["request_metadata"]] = serialize_agentcc_param(
                "request_metadata", self._metadata,
            )
        if self._config is not None and hasattr(self._config, "to_headers"):
            config_headers = self._config.to_headers()
            composed_names.update(name.lower() for name in config_headers)
            headers.update(config_headers)
        if agentcc_params:
            for key, value in agentcc_params.items():
                if value is NOT_GIVEN or value is None:
                    continue
                name = AGENTCC_PARAM_TO_HEADER.get(key)
                if name:
                    if key == "request_metadata" and self._metadata_mode == "merge":
                        value = _layer_metadata(self._metadata, value)
                    headers[name] = serialize_agentcc_param(key, value)
            # These internal entries originate in the client's active session,
            # not the caller's per-call agentcc parameters.
            session_headers = agentcc_params.get("_session_headers", {})
            composed_names.update(name.lower() for name in session_headers)
            composed_names.update(name.lower() for name in agentcc_params.get("_client_header_names", ()))
            headers.update(session_headers)
        headers.update(options.headers)
        validate_header_values(headers, composed_names)
        for name, value in headers.items():
            if name.lower() in {"authorization", "x-api-key"}:
                guard_fi_key_pair(value)
        return headers, frozenset(composed_names)

    def _build_url(self, path: str) -> str:
        """Validate the destination and merge default queries; never resolve DNS."""
        url = path if path.startswith(("http://", "https://")) else (
            self._base_url + "/" + path.lstrip("/")
        )
        with self._http_warning_lock:
            validate_destination(self._base_url, url, warned_origins=self._warned_http_origins)
        if not self._default_query:
            return url
        parsed = httpx.URL(url)
        query = httpx.QueryParams(self._default_query).merge(parsed.params)
        url = str(parsed.copy_with(params=query))
        validate_destination(self._base_url, url, warn_cleartext=False)
        return url

    def _build_request(
        self, options: Any, params: Any = None, *, headers: dict[str, str] | None = None,
    ) -> httpx.Request:
        """Encode JSON once for inspection and sends, using HTTPX's own encoder.

        Explicit transport defaults keep the inspection independent of client
        creation and of optional compression packages. Caller headers still win.
        Multipart remains on the transport's streaming files/data path.
        """
        if _uses_form(options):
            raise TypeError("Raw JSON request construction does not accept file uploads")
        if headers is None:
            headers, _ = self._build_headers(options, params)
        wire_headers = httpx.Headers({
            "Accept": "*/*", "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
        })
        wire_headers.update(headers)
        return httpx.Request(
            method=options.method, url=self._build_url(options.url),
            headers=wire_headers, json=options.body,
        )
