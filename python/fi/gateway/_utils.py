"""Timeout/header helpers, no-send inspection and explicit-origin health checks."""

from __future__ import annotations

import json
import time
from collections.abc import Callable, Mapping
from typing import Any

import httpx

from fi.gateway._constants import DEFAULT_TIMEOUT, is_credential_name
from fi.gateway._env import KEY_ENV, URL_ENV, from_env, guard_fi_key_pair, normalize_base_url
from fi.gateway._exceptions import AgentCCError


def parse_timeout(timeout: float | Any | None) -> httpx.Timeout:
    """Convert a scalar, Timeout dataclass or httpx.Timeout to an HTTP timeout."""
    if timeout is None:
        return httpx.Timeout(DEFAULT_TIMEOUT)
    if isinstance(timeout, (int, float)):
        return httpx.Timeout(float(timeout))
    if hasattr(timeout, "connect"):
        return httpx.Timeout(
            connect=timeout.connect, read=timeout.read,
            write=timeout.write, pool=timeout.pool,
        )
    return httpx.Timeout(DEFAULT_TIMEOUT)


def redact_headers(headers: Mapping[str, str]) -> dict[str, str]:
    """Copy headers without disclosing authentication material."""
    return {
        key: "[REDACTED]" if is_credential_name(key)
        else value for key, value in headers.items()
    }


def serialize_agentcc_param(key: str, value: Any) -> str:
    if key == "request_metadata" and isinstance(value, dict):
        return json.dumps(value, separators=(",", ":"))
    if key == "cache_force_refresh" and isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


from fi.gateway._deprecation import deprecated


@deprecated
def return_raw_request(
    *, model: str, messages: list[dict[str, Any]],
    base_url: str | None = None, api_key: str | None = None, **kwargs: Any,
) -> dict[str, Any]:
    """Build the wrapper's request without a client or any network traffic.

    ``body`` retains the released decoded mapping; ``body_bytes`` is the exact
    HTTPX-encoded payload. Headers include the resolved key for wire parity:
    treat the result as sensitive, not as a safe logging snapshot. With no key
    supplied or configured, legacy inspection uses the ``[REDACTED]`` placeholder.
    The wrapper applies the same validation to argument, environment and service default origins.
    """
    from fi.gateway._env import resolve_wrapper_settings
    from fi.gateway._transport._request import RequestBuilder
    from fi.gateway.resources.chat._params import _prepare

    key, origin = resolve_wrapper_settings(api_key, base_url)
    builder = RequestBuilder(api_key=key or "[REDACTED]", base_url=origin)
    options, params = _prepare(builder, {"model": model, "messages": messages, **kwargs})
    request = builder._build_request(options, params)
    return {
        "method": request.method, "url": str(request.url),
        "headers": {k.decode("ascii"): v.decode("latin-1") for k, v in request.headers.raw},
        "body": options.body,
        "body_bytes": request.content,
    }


_DIRECT_METHODS = {httpx.get: "GET", httpx.post: "POST"}


def _send_utility(send: Callable[..., httpx.Response], url: str, **kwargs: Any) -> httpx.Response:
    """Send one utility request with ``send`` (``httpx.get`` / ``httpx.post`` or a callable with their signature).

    An ``https`` request to a host that is not loopback goes through the ``send`` that was passed, whatever callable it
    is, so the environment proxy and ``NO_PROXY`` apply as ``send`` applies them (a proxy carries the tunnel). A plain
    ``http`` request, and a loopback host (the one rule, :func:`fi._core.loopback.is_loopback_host`), go through the
    gateway clients' own client class (``LoopbackDirectClient``) when ``send`` is ``httpx.get`` or ``httpx.post``: the
    request goes straight to its host, whatever the proxy variables say, and ``SSL_CERT_FILE`` and ``SSL_CERT_DIR`` stay in effect. That client is built on httpx and
    does not read ``.netrc``; ``.netrc`` applies on the ``requests``-based paths. Any other callable, such as a
    replacement installed for a test, is called for loopback hosts too.
    """
    from fi._core.loopback import is_loopback_host

    method = _DIRECT_METHODS.get(send)
    parsed = httpx.URL(url)
    if method is None or (parsed.scheme != "http" and not is_loopback_host(parsed.host)):
        return send(url, **kwargs)
    from fi.gateway._transport._direct import LoopbackDirectClient

    timeout = kwargs.pop("timeout", httpx.Timeout(5.0))
    follow_redirects = kwargs.pop("follow_redirects", False)
    with LoopbackDirectClient(timeout=timeout, follow_redirects=follow_redirects) as client:
        return client.request(method, url, **kwargs)


def _utility_exchange(send: Callable[..., httpx.Response], url: str, **kwargs: Any) -> httpx.Response:
    """Use the same finally boundary for each independent utility exchange. A loopback host's
    request skips an environment proxy (:func:`_send_utility`)."""
    from fi.gateway._transport._scrub import (
        composed_credential_values, scrub_error_text, scrub_sent_request,
    )

    names = frozenset(name.lower() for name in kwargs.get("headers", {}))
    credentials = composed_credential_values(kwargs.get("headers", {}), names)
    response = None
    error = None
    try:
        response = _send_utility(send, url, **kwargs)
        return response
    except BaseException as exc:
        error = exc
        scrub_error_text(exc, credentials)
        raise
    finally:
        scrub_sent_request(None, response, error, names)


def health_check(
    model: str | None = None, api_key: str | None = None,
    base_url: str | None = None, timeout: float = 10.0,
) -> dict[str, Any]:
    """Check /healthz, falling back to /health only on HTTP 404.

    Model probes use the completions endpoint and do not take the health fallback.
    The same key/origin policy applies to clients and to both health endpoints.
    """
    from fi.gateway._http_security import validate_destination

    resolved_key = api_key or from_env(KEY_ENV)
    resolved_url = normalize_base_url(base_url or from_env(URL_ENV))
    if not resolved_url:
        return {"status": "error", "error": "base_url is required"}
    try:
        if resolved_key:
            guard_fi_key_pair(resolved_key)
        validate_destination(resolved_url, resolved_url, warn_plain_http=bool(resolved_key))
    except (AgentCCError, httpx.InvalidURL) as exc:
        return {"status": "error", "error": str(exc)}
    headers = {"Authorization": f"Bearer {resolved_key}"} if resolved_key else {}
    try:
        start = time.monotonic()
        if model is None:
            response = _utility_exchange(httpx.get,
                f"{resolved_url}/healthz", headers=headers, timeout=timeout,
                follow_redirects=False,
            )
            if response.status_code == 404:
                response = _utility_exchange(httpx.get,
                    f"{resolved_url}/health", headers=headers, timeout=timeout,
                    follow_redirects=False,
                )
        else:
            response = _utility_exchange(httpx.post,
                f"{resolved_url}/v1/chat/completions",
                headers={**headers, "Content-Type": "application/json"},
                json={"model": model, "messages": [{"role": "user", "content": "hi"}], "max_tokens": 1},
                timeout=timeout, follow_redirects=False,
            )
        elapsed_ms = (time.monotonic() - start) * 1000
        result = {"status": "ok" if response.status_code < 300 else "error", "latency_ms": round(elapsed_ms, 1)}
        if response.status_code >= 300:
            result["error"] = f"HTTP {response.status_code}"
        return result
    except Exception as exc:
        return {"status": "error", "error": str(exc)}


def check_valid_key(api_key: str, base_url: str) -> bool:
    """Check authentication; refuse platform keys and unsafe origins before sending."""
    from fi.gateway._http_security import validate_destination

    guard_fi_key_pair(api_key)
    base_url = normalize_base_url(base_url)
    try:
        validate_destination(base_url, base_url)
    except (AgentCCError, httpx.InvalidURL):
        return False  # a destination the SDK will not send keys to gives False
    try:
        response = _utility_exchange(httpx.get,
            f"{base_url}/v1/models",
            headers={"Authorization": f"Bearer {api_key}"}, timeout=10.0,
            follow_redirects=False,
        )
        return response.status_code == 200
    except Exception:
        return False
