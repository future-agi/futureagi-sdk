"""Destination validation shared by gateway clients and direct HTTP helpers."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any
from urllib.parse import parse_qsl, urlsplit

import httpx

from fi._core.loopback import is_loopback_host
from fi.gateway._constants import is_credential_name
from fi.gateway._exceptions import AgentCCError

_IN_PROCESS = (httpx.MockTransport, httpx.WSGITransport, httpx.ASGITransport)


def answers_in_process(client: Any, url: str) -> bool:
    """Whether the transport an ``http_client`` the caller supplied uses for ``url`` is exactly httpx's
    ``MockTransport``, ``WSGITransport`` or ``ASGITransport``: the request is answered in the process and makes no
    connection, so it is not judged (0.8.1). A subclass of one can connect, and is judged."""
    try:
        return type(client._transport_for_url(httpx.URL(url))) in _IN_PROCESS
    except Exception:  # noqa: BLE001 - a client that cannot answer is judged
        return False


def caller_base_url(base_url: str, client: Any) -> str:
    """The configured origin for a network-path reference is the caller's HTTPX base."""
    if base_url.startswith("//") and isinstance(client, (httpx.Client, httpx.AsyncClient)):
        caller_base = client.base_url
        if caller_base.is_absolute_url:
            # Check the written reference's structure (e.g. userinfo and fragments),
            # without treating its authority as a destination for the key.
            _origin("https:" + base_url)
            return str(caller_base)
    return base_url


def refuse_proxied_caller_client(client: Any, url: str, owned: bool) -> None:
    """Refuse a plain-http send through an ``http_client`` the caller supplied when it may route the request through a
    proxy (``KeyedProxyRefusedError``): the key would reach the proxy. A client the SDK built sends direct, and a
    caller's client that answers in the process (:func:`answers_in_process`) makes no connection."""
    if owned or url[:5].lower() != "http:" or answers_in_process(client, url):
        return
    from fi._core.http_security import KeyedProxyRefusedError, httpx_client_proxied

    if httpx_client_proxied(client, url):
        raise KeyedProxyRefusedError()


def validate_header_values(headers: dict[str, Any], owned_names: set[str]) -> None:
    """Reject invalid client-owned values without creating a value-bearing codec error.

    HTTPX encodes string values as ASCII; byte values may also contain HTTP
    obs-text. Field values cannot contain control bytes other than an internal
    tab, or start/end with optional whitespace. Do not normalize valid values.
    """
    for name, value in headers.items():
        if name.lower() not in owned_names:
            continue
        if isinstance(value, str):
            valid = (value.isascii() and value == value.strip(" \t")
                     and all(char == "\t" or 32 <= ord(char) < 127 for char in value))
        elif isinstance(value, bytes):
            valid = (value == value.strip(b" \t")
                     and all(char == 9 or 32 <= char != 127 for char in value))
        else:
            valid = False
        if not valid:
            raise AgentCCError(f"Invalid HTTP header value for {name.lower()}.")


def reject_credential_query(query: Any, *, where: str = "default_query") -> None:
    """Refuse a query-parameter mapping that names a credential.

    Uses the one shared credential-name set (lowercase, "-" equals "_"). The error
    names the offending key and not its value.
    """
    if not query:
        return
    if isinstance(query, Mapping):
        names = [str(name) for name in query]
    else:
        try:
            names = list(httpx.QueryParams(query).keys())
        except Exception:
            return
    for name in names:
        if is_credential_name(name):
            raise AgentCCError(f"Gateway {where} must not contain the credential parameter {name!r}.")


def _origin(url: str, in_process: bool = False) -> tuple[str, str, int]:
    try:
        parsed = urlsplit(url)
        if (
            parsed.scheme not in {"http", "https"} or not parsed.hostname
            or parsed.username is not None or parsed.password is not None
            or parsed.fragment or "\\" in url or any(ord(c) < 32 for c in url)
        ):
            raise ValueError
        if any(
            is_credential_name(name)
            for name, _ in parse_qsl(parsed.query, keep_blank_values=True)
        ):
            raise AgentCCError("Gateway URL must not contain credential query parameters.")
        host = parsed.hostname.lower()
        if parsed.scheme == "http" and not host.isascii() and not in_process:
            raise _origin_refusal("The gateway base URL writes its host with non-ASCII characters. Write the host with ASCII characters.")
        if in_process and not host.isascii():
            host = httpx.URL(f"http://{host}/").raw_host.decode("ascii")  # the A-label httpx sends: both spellings, one origin
        port = parsed.port
        if port is None:
            port = 443 if parsed.scheme == "https" else 80
        return parsed.scheme, host, port
    except ValueError:
        _let_the_library_refuse(url)
        _refuse_written_url(url)
        raise AgentCCError("Gateway URL must be an absolute HTTP(S) URL without userinfo or fragment.") from None


def _let_the_library_refuse(url: str) -> None:
    """A plain-http URL the HTTP library cannot read is refused by the library, with its own error."""
    if url.strip()[:5].lower() != "http:":
        return
    try:
        httpx.URL(url.strip())
    except httpx.InvalidURL:
        raise _origin_refusal("The gateway base URL cannot be read as an HTTP URL. Check it for a backslash, a control character or a malformed port.") from None
    except ValueError:
        pass


def _origin_refusal(message: str) -> Exception:
    """An ``AgentCCError`` with the code ``insecure_http_origin`` that is also an ``httpx.InvalidURL``, so a caller that
    catches the library's error also catches it."""
    from fi._keyed_errors import plain_origin_refusal

    class _Unreadable(AgentCCError, httpx.InvalidURL):  # type: ignore[misc]
        pass

    error = plain_origin_refusal(_Unreadable, message)
    error.args = (message,)
    return error


def _refuse_written_url(url: str, *, allow_insecure_http: bool | None = None) -> None:
    """Refuse a URL, judged as written, that the shared rule does not send keys to, with the code of its situation
    (``insecure_http_origin``): user info, a backslash, brackets in the user info, no host, an ``@`` after the host of a
    plain-http URL, whitespace or a control character around a plain-http URL, a plain-http host written with a non-ASCII dot
    (the library reads it as a dot and connects to an address the text does not name), and a plain-http host that is not
    loopback without the opt-in. A Future AGI host keeps its own code (:func:`_refuse_plain_future_agi`), and a URL that
    needs no refusal returns."""
    from fi._core.http_security import future_agi_connect_host, insecure_http_refusal, plaintext_decision
    from fi._keyed_errors import plain_origin_refusal

    _let_the_library_refuse(url)  # a URL the HTTP library cannot read keeps the library's own error
    if url.strip()[:5].lower() == "http:" and future_agi_connect_host(url.strip()) is not None:
        return
    if plaintext_decision(url, allow_insecure_http=allow_insecure_http, proxies_disabled=True).allowed:
        return
    message = insecure_http_refusal(url, allow_insecure_http=allow_insecure_http, proxies_disabled=True)
    if message is not None:
        raise plain_origin_refusal(AgentCCError, message)


def _refuse_plain_future_agi(url: str) -> None:
    """A plain-http URL whose host, as the HTTP library reads it, is a Future AGI host is refused as one even when another
    rule (user info, a fragment) also refuses the URL as written."""
    from fi._core.http_security import future_agi_connect_host, future_agi_host_refusal, insecure_http_refusal

    text = url.strip()
    host = future_agi_connect_host(text) if text[:5].lower() == "http:" else None
    if host is None:
        return
    message = insecure_http_refusal(httpx.URL(text), proxies_disabled=True)
    if message is not None:
        raise future_agi_host_refusal(AgentCCError, message, host)


def _authority(origin: tuple[str, str, int]) -> str:
    _, host, port = origin
    authority = f"[{host}]" if ":" in host else host
    return authority if port == 80 else f"{authority}:{port}"


def validate_destination(
    base_url: str, url: str, *,
    warned_origins: set[tuple[str, str, int]] | None = None,
    warn_plain_http: bool = True,
    allow_insecure_http: bool | None = None,
    in_process: bool = False,
) -> None:
    """Reject cross-origin requests and require opt-in for plain HTTP outside loopback.

    With ``warn_plain_http=True``, a keyed plain HTTP request outside loopback requires the opt-in, which emits
    one notice per process. An explicit ``allow_insecure_http`` takes precedence over ``FI_ALLOW_INSECURE_HTTP``.
    The opt-in does not apply to Future AGI hosts or to requests routed through a proxy.
    Does not resolve a hostname or read a response to choose a destination.
    ``warned_origins`` is accepted for compatibility and unused.
    Settings-only validation can defer the plain HTTP check to credential use.
    ``in_process`` says the caller's client answers ``url`` in the process (:func:`answers_in_process`): a host written
    with non-ASCII characters is read as httpx sends it, and the plain-http rules are not applied (0.8.1).
    """
    if in_process:
        warn_plain_http = False
    try:
        origin = _origin(base_url, in_process)
        target = _origin(url, in_process)
    except AgentCCError:
        _refuse_plain_future_agi(url)
        raise
    if target != origin:
        raise AgentCCError("Gateway requests must use the explicitly configured origin.")
    scheme, host, _ = target
    if scheme == "https":
        return
    if warn_plain_http:
        _refuse_written_url(url, allow_insecure_http=allow_insecure_http)
        if base_url != url:
            _refuse_written_url(base_url, allow_insecure_http=allow_insecure_http)
    if warn_plain_http and not is_loopback_host(host):
        from fi._core.http_security import insecure_http_refusal

        checked = httpx.URL(f"http://{_authority(target)}")  # the library's own error for a host it cannot read
        # A plain-http send is direct; the transport checks the caller's client.
        message = insecure_http_refusal(checked, allow_insecure_http=allow_insecure_http, proxies_disabled=True)
        if message is not None:
            from fi._core.http_security import future_agi_connect_host, future_agi_host_refusal
            from fi._keyed_errors import plain_origin_refusal

            fi_host = future_agi_connect_host(checked)
            if fi_host is not None:
                raise future_agi_host_refusal(AgentCCError, message, fi_host)
            raise plain_origin_refusal(AgentCCError, message)
