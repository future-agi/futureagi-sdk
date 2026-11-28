"""Plain-HTTP policy, independent of credential resolution and retry routing."""
from __future__ import annotations

import os
import re
import sys
import threading
from dataclasses import dataclass
from typing import Callable, Mapping, Optional, Union

import httpx

from fi._core.header_key_scan import UNSCANNED_NOTE
from fi._core.proxy_routing import (  # noqa: F401  (re-exported)
    _bypassed,
    _no_proxy_value,
    _proxied,
    _written_port,
    carries_credentials,
    cpython_env_proxied,
    env_proxied,
    httpx_client_proxied,
    httpx_client_sdk_built,
    judge_credentials,
    library_env_proxied,
    requests_session_proxied,
    requests_session_sdk_built,
)
from fi._core.key_refusal_rules import authority_readable, spelling_problem
from fi.errors import ConfigurationError, InsecureHttpRefusedError, KeyedProxyRefusedError

ALLOW_INSECURE_HTTP_ENV = "FI_ALLOW_INSECURE_HTTP"
_warned: set[tuple[str, str, int]] = set()  # holds one entry once the opt-in notice was written
_lock = threading.Lock()


def is_loopback_url_text(parsed: Optional[httpx.URL], written: str) -> bool:
    """Whether the host is loopback: httpx's host as written when the URL parsed, else the text's own host."""
    from fi._core.loopback import is_loopback_host, is_loopback_url

    return is_loopback_url(parsed) if parsed is not None else is_loopback_host(written)


def is_insecure_http(url: httpx.URL) -> bool:
    """Plain HTTP to anything other than loopback (TypeScript's ``isInsecureHttp``)."""
    from fi._core.loopback import is_loopback_url

    return url.scheme == "http" and not is_loopback_url(url)


def insecure_http_allowed(
    allow_insecure_http: Optional[bool] = None,
    environ: Optional[Mapping[str, str]] = None,
) -> bool:
    """Whether plain HTTP to a non-loopback host is opted into: an explicit argument, else ``FI_ALLOW_INSECURE_HTTP``
    set to exactly ``1``. The argument opts in as ``True`` or as the text ``1``; ``False`` opts out whatever the environment
    says, and any other value (``"yes"``, ``"true"``, a number, a container) is not an opt-in."""
    if allow_insecure_http is not None:
        return allow_insecure_http is True or (isinstance(allow_insecure_http, str) and allow_insecure_http == "1")
    env = os.environ if environ is None else environ
    return env.get(ALLOW_INSECURE_HTTP_ENV) == "1"



_SCHEME_PREFIX = re.compile(r"^[A-Za-z][A-Za-z0-9+.-]*://")


def _written_host(text: str) -> str:
    """The host as ``text`` writes it, lower-case, without user info, brackets or port (the trailing dot of a name
    kept): what is judged when the URL cannot be parsed."""
    match = _SCHEME_PREFIX.match(text.strip())
    rest = text.strip()[match.end():] if match else text.strip()
    authority = re.split(r"[/?#]", rest, maxsplit=1)[0].rsplit("@", 1)[-1]
    if authority.startswith("["):
        end = authority.find("]")
        return authority[1:end].lower() if end > 0 else ""
    return authority.rsplit(":", 1)[0].lower() if ":" in authority else authority.lower()


_CONTROL = re.compile(r"[\x00-\x1f\x7f]")


def _written_oddly(text: str) -> bool:
    """Whether a plain-HTTP URL text carries whitespace around it or a control character anywhere. The sending libraries
    strip these (``requests`` strips leading whitespace; URL parsers drop tabs and newlines), so the scheme and host they
    send to are not the ones a reader of the text finds."""
    if not _CONTROL.sub("", text).strip().lower().startswith("http:"):
        return False
    return text != text.strip() or _CONTROL.search(text) is not None


def _host_shape_problem(text: str, parsed: Optional[httpx.URL]) -> Optional[str]:
    """Why the host of an ``http://`` URL is not the one every reader would find: no host at all; a backslash
    or a percent-encoded backslash in the part before the path (readers split there differently); brackets in the user
    info (readers disagree about where the host starts); user info in the authority (a credentials URL has none, and
    the message names the shape, not its text); an ``@`` after the authority (a path, query or fragment holding one); a
    percent sign in the host of a plain-HTTP URL (readers decode it, so the name sent to is not the one written).
    ``parsed`` is ``None`` when the URL cannot be
    parsed; the host is then read from the text."""
    if _written_oddly(text):
        return "has whitespace around it or a control character"
    if (not parsed.raw_host) if parsed is not None else (not _written_host(text)):
        return "has no host"
    match = _SCHEME_PREFIX.match(text.strip())
    if match is None:
        return None
    rest = text.strip()[match.end():]
    authority = re.split(r"[/?#]", rest, maxsplit=1)[0]
    if "\\" in authority or "%5c" in authority.lower():
        return "writes its host with a backslash"
    if "@" in authority and re.search(r"[\[\]]|%5[bd]", authority.rsplit("@", 1)[0], re.IGNORECASE):
        return "has brackets in its user info"
    if "@" in authority:
        return "has user info before the host"
    if not text.strip().lower().startswith("https:") and "@" in rest[len(authority):]:
        return "has an @ after the host"
    if not text.strip().lower().startswith("https:") and "%" in authority.rsplit("@", 1)[-1]:
        return "writes its host with a percent-encoded character"
    return None


@dataclass(frozen=True)
class PlaintextDecision:
    """The outcome of :func:`plaintext_decision`: whether credentials may go to the URL and why.

    ``reason`` is one of ``not_plain_http`` (https, wss or any other scheme), ``loopback``, ``ambiguous_host``,
    ``future_agi_host``, ``not_opted_in``, ``env_proxy``, ``caller_proxy`` (all refusals but the first two;
    ``ambiguous_host`` is a plain-HTTP URL with no host or a host written two ways), ``opted_in`` (allowed by
    the opt-in, which owes the one per-process notice) or ``unparsable`` (left to the caller's own validation).
    """

    allowed: bool
    reason: str


def plaintext_decision(
    url: "httpx.URL | str",
    *,
    allow_insecure_http: Optional[bool] = None,
    environ: Optional[Mapping[str, str]] = None,
    caller_proxied: bool = False,
    proxies_disabled: bool = False,
) -> PlaintextDecision:
    """Whether credentials may go over ``url``; no output and no side effect.

    ``proxies_disabled`` says the transport that sends the request is built by the SDK with every proxy turned
    off for plain HTTP, so the environment's proxy variables cannot route it and are not consulted. Without it
    the environment check (:func:`env_proxied`) applies. A transport the caller supplies is described by
    ``caller_proxied`` (see :func:`httpx_client_proxied` and :func:`requests_session_proxied`).

    Anything but plain HTTP passes, and so does loopback (judged on the host as written). Plain HTTP to another
    host passes only with the opt-in (``allow_insecure_http``, else ``FI_ALLOW_INSECURE_HTTP`` exactly ``1`` in
    ``environ``), not to a Future AGI host, and not when an environment proxy (:func:`env_proxied`) or the
    caller's client or session (``caller_proxied``) routes the request.
    """
    from fi._core.origins import ascii_host, in_future_agi_zone

    text = str(url)
    if _written_oddly(text):
        return PlaintextDecision(False, "ambiguous_host")
    try:
        parsed: Optional[httpx.URL] = url if isinstance(url, httpx.URL) else httpx.URL(text)
        scheme = parsed.scheme  # type: ignore[union-attr]
    except Exception:
        # A URL httpx cannot parse (an octal host, say) is judged, on the host as written: it is refused or
        # allowed as any other plain-HTTP URL would be, and the sending library then fails on it before a byte.
        parsed = None
        match = _SCHEME_PREFIX.match(text.strip())
        scheme = match.group(0)[:-3].lower() if match else ""
        if scheme not in ("http", "https"):
            return PlaintextDecision(True, "unparsable")
    if scheme not in ("http", "https"):
        return PlaintextDecision(True, "not_plain_http")
    if _host_shape_problem(text, parsed) is not None:
        return PlaintextDecision(False, "ambiguous_host")
    if scheme != "http":
        return PlaintextDecision(True, "not_plain_http")
    written = _written_host(text)
    # Loopback is decided on the host as written: a host with a non-ASCII character (the ideographic and fullwidth full
    # stops that URL parsers read as a dot, say) is a name, not an address in 127.0.0.0/8.
    loopback = authority_readable(text) and written.isascii() and is_loopback_url_text(parsed, written)
    if loopback:
        if caller_proxied:
            return PlaintextDecision(False, "caller_proxy")  # a request the caller's own proxy carries is not direct
        return PlaintextDecision(True, "loopback")
    zone_host = ascii_host(parsed) if parsed is not None else written[:-1] if written.endswith(".") else written
    if in_future_agi_zone(zone_host):
        return PlaintextDecision(False, "future_agi_host")
    if not insecure_http_allowed(allow_insecure_http, environ):
        return PlaintextDecision(False, "not_opted_in")
    if not proxies_disabled and env_proxied(url, environ):
        return PlaintextDecision(False, "env_proxy")
    if caller_proxied:
        return PlaintextDecision(False, "caller_proxy")
    if spelling_problem(text, written) is not None:  # 0.8.1: the opt-in does not unlock such a host
        return PlaintextDecision(False, "ambiguous_host")
    return PlaintextDecision(True, "opted_in")


def _warn_opted_in(url: Optional[httpx.URL], shown: str = "") -> None:
    """The one notice per process that plain HTTP is in use through the opt-in. It names the setting and the
    origin; it carries no path and no credential."""
    from fi._core.origins import display_host

    shown = shown or (display_host(url) if url is not None else "that host")
    with _lock:
        if _warned:
            return
        _warned.add(("opt-in", "", 0))
    sys.stderr.write(
        f"futureagi: {ALLOW_INSECURE_HTTP_ENV} allows credentials over plain HTTP to "
        f"http://{shown}. Use an https:// address to turn this off.\n"
    )


def insecure_http_refusal(
    url: "httpx.URL | str",
    *,
    setting: str = "the base URL",
    allow_insecure_http: Optional[bool] = None,
    environ: Optional[Mapping[str, str]] = None,
    caller_proxied: bool = False,
    proxies_disabled: bool = False,
) -> Optional[str]:
    """The refusal message when credentials may not go to ``url``, else ``None`` (and, when the opt-in is what
    allows it, the one per-process notice is written). The decision is :func:`plaintext_decision`.

    HTTPS and loopback pass. Plain HTTP to another host passes only with the opt-in
    (``FI_ALLOW_INSECURE_HTTP=1``, or ``allow_insecure_http=True`` where the caller offers it) and only when the
    host is not a Future AGI host (``futureagi.com`` or a subdomain) and no proxy routes the request:
    ``caller_proxied`` says the caller's own client or session does.
    """
    from fi._core.origins import display_host

    decision = plaintext_decision(
        url, allow_insecure_http=allow_insecure_http, environ=environ, caller_proxied=caller_proxied,
        proxies_disabled=proxies_disabled,
    )
    if decision.allowed and decision.reason != "opted_in":
        return None
    try:
        parsed: Optional[httpx.URL] = url if isinstance(url, httpx.URL) else httpx.URL(str(url))
    except Exception:
        parsed = None
    shown = display_host(parsed) if parsed is not None else (_written_host(str(url)) or "that host")
    if decision.allowed:
        _warn_opted_in(parsed, shown)
        return None
    base = f"Credentials are not sent over http:// to {shown}. Set {setting} to an https:// address"
    if decision.reason == "ambiguous_host":
        problem = _host_shape_problem(str(url), parsed) or spelling_problem(str(url), _written_host(str(url))) or "has no host"
        kind = "an https:// URL" if str(url).strip().lower().startswith("https:") else "an http:// URL"
        return f"Credentials are not sent to {kind} that {problem}. Set {setting} to an https:// address."
    if decision.reason == "future_agi_host":
        return f"{base}; {ALLOW_INSECURE_HTTP_ENV} does not apply to a Future AGI host."
    if decision.reason == "not_opted_in":
        return f"{base}, or set {ALLOW_INSECURE_HTTP_ENV}=1."
    if decision.reason == "env_proxy":
        return (f"{base}, or add this host to no_proxy; {ALLOW_INSECURE_HTTP_ENV} does not apply to a request "
                "routed through an environment proxy.")
    return (f"{base}, or send without a proxy; {ALLOW_INSECURE_HTTP_ENV} does not apply to a request routed "
            "through a proxy of the client or session.")


def future_agi_connect_host(url: "httpx.URL | str") -> Optional[str]:
    """The host ``url`` connects to (IDNA A-label, lower case, trailing dot dropped) when it is ``futureagi.com`` or a name
    under it, else ``None``. A URL the parser cannot read has no host to name."""
    from fi._core.origins import ascii_host, in_future_agi_zone

    try:
        host = ascii_host(url if isinstance(url, httpx.URL) else httpx.URL(str(url).strip()))
    except Exception:
        return None
    return host if in_future_agi_zone(host) else None


def future_agi_host_refusal(error_class: type, message: str, host: str) -> Exception:
    """An error that is both ``error_class`` (a package's own error, built from ``message``) and an ``InsecureHttpRefusedError``
    for ``host``, so the package's existing ``except`` clauses and the shared error both catch it."""

    class FutureAgiHostRefused(error_class, InsecureHttpRefusedError):  # type: ignore[misc, valid-type]
        def __init__(self) -> None:
            error_class.__init__(self, message)
            self.host, self.code, self.operation = host, "INSECURE_HTTP_REFUSED", None

        def get_error_code(self) -> str:
            return "INSECURE_HTTP_REFUSED"

    return FutureAgiHostRefused()


def require_secure_credentials_url(
    url: "httpx.URL | str",
    *,
    setting: str = "the base URL",
    allow_insecure_http: Optional[bool] = None,
    environ: Optional[Mapping[str, str]] = None,
    caller_proxied: bool = False,
    proxies_disabled: bool = False,
    lead: Union[str, Callable[[], str]] = "",
) -> None:
    """Raise ``ConfigurationError`` when credentials may not go to ``url`` (see :func:`insecure_http_refusal`).

    HTTPS and loopback URLs (judged by the host as written) pass. ``setting`` names the option the error tells
    the user to change, and ``lead`` opens the message (a callable is called only for a refusal). A URL that cannot be
    parsed passes: the caller's own URL validation reports it.
    """
    message = insecure_http_refusal(
        url, setting=setting, allow_insecure_http=allow_insecure_http, environ=environ, caller_proxied=caller_proxied,
        proxies_disabled=proxies_disabled,
    )
    if message is not None:
        message = (lead() if callable(lead) else lead) + message
        # A request a proxy would carry is the keyed-proxy refusal (`KEYED_PROXY_REFUSED`); the other refusals keep their code.
        reason = plaintext_decision(url, allow_insecure_http=allow_insecure_http, environ=environ, caller_proxied=caller_proxied,
                                    proxies_disabled=proxies_disabled).reason
        if reason in ("env_proxy", "caller_proxy"):
            raise KeyedProxyRefusedError(message)
        # A Future AGI host, by the host the library connects to, is refused whatever setting says otherwise.
        host = future_agi_connect_host(url) if reason in ("future_agi_host", "ambiguous_host") else None
        if host is not None:
            raise InsecureHttpRefusedError(host, message=message)
        raise ConfigurationError(message, code="insecure_http_origin")


def require_secure_written_url(text: object, *, setting: str = "the base URL") -> None:
    """:func:`require_secure_credentials_url` for a plain-HTTP URL text whose host holds a non-ASCII character. ``httpx``
    rewrites such a host (a name with ideographic or fullwidth full stops becomes 127.0.0.1) before a request exists, so the
    URL as the caller wrote it is the one judged. Any other URL text passes here: its request is judged where it is sent."""
    written = str(text or "")
    if written.strip()[:7].lower() == "http://" and not _written_host(written).isascii():
        require_secure_credentials_url(written, setting=setting)


def require_secure_credential_headers(
    url: "httpx.URL | str", headers: Optional[Mapping[str, object]], *, setting: str = "the base URL",
    caller_proxied: bool = False, proxies_disabled: bool = False, allow_insecure_http: Optional[bool] = None,
) -> None:
    """:func:`require_secure_credentials_url` for a request whose final ``headers`` carry a Future AGI key
    (:func:`carries_credentials`); a request without one passes. A refusal for a value too long to scan names that rule;
    that note is built only for a refusal, from what the judgement read."""
    if headers and (judgement := judge_credentials(headers)).carried:
        require_secure_credentials_url(url, setting=setting, caller_proxied=caller_proxied, proxies_disabled=proxies_disabled,
                                       allow_insecure_http=allow_insecure_http,
                                       lead=lambda: UNSCANNED_NOTE if judgement.only_unscanned() else "")


def check_http_security(
    url: "httpx.URL | str",
    mode: str,
    *,
    allow_insecure_http: Optional[bool] = None,
    environ: Optional[Mapping[str, str]] = None,
    caller_proxied: bool = False,
    proxies_disabled: bool = False,
) -> None:
    """Refuse credentials over plain HTTP to a non-loopback host unless opted in (see :func:`insecure_http_refusal`).

    Both modes (``keys`` and ``bearer``) follow the same rule. This check does not change the destination.
    Messages carry no path and no credential. An explicit False wins over the environment.
    """
    require_secure_credentials_url(
        url, allow_insecure_http=allow_insecure_http, environ=environ, setting="the platform base URL",
        caller_proxied=caller_proxied, proxies_disabled=proxies_disabled,
    )


def require_secure_grpc_target(endpoint: str, headers: Optional[Mapping[str, object]], *, insecure: bool,
                               setting: str = "the exporter endpoint") -> None:
    """:func:`require_secure_credential_headers` for a gRPC target (``host:port`` or a URL) whose call carries
    credentials in its metadata. ``insecure`` (or an ``http://`` URL) says the channel is plain. Only ``https://`` makes
    it TLS whatever ``insecure`` says, as in the exporter; any other scheme (``grpc://``, ``grpcs://``) leaves a plain
    channel plain, and its host (a bracketed IPv6 address included) is judged as a ``host:port`` target's host is. The
    channel is built by the SDK with proxies off (:func:`fi._core.loopback.grpc_channel_options`), so the environment's
    proxy variables are not consulted. A host written two ways or with no host is refused on a secure channel too. An
    IPv4-mapped loopback host (``[::ffff:127.0.0.1]``) is judged as the IPv4 address a socket dials for it."""
    from fi._core.loopback import unmapped_loopback_url

    scheme, separator, rest = endpoint.strip().partition("://")
    if separator:
        insecure = scheme.lower() != "https" and (bool(insecure) or scheme.lower() == "http")
    text = unmapped_loopback_url(("http://" if insecure else "https://") + (rest if separator else scheme))
    require_secure_credential_headers(text, headers, setting=setting, proxies_disabled=True)


def require_endpoint_with_keys(endpoint: Optional[str], headers: Optional[Mapping[str, object]]) -> None:
    """Raise ``ConfigurationError`` (code ``insecure_http_origin``) when an exporter whose headers carry keys has an empty
    endpoint: an empty authority is refused, and the exporter's own default (a local collector) is not used for it."""
    if (endpoint is None or endpoint.strip() == "") and headers and (judgement := judge_credentials(headers)).carried:
        raise ConfigurationError(
            (UNSCANNED_NOTE if judgement.only_unscanned() else "") + "Credentials are not sent to an exporter whose endpoint is empty (it has no host). Set the exporter endpoint to an https:// address.",
            code="insecure_http_origin",
        )


def require_no_key_headers_in_otel_env(endpoint: str, environ: Optional[Mapping[str, str]] = None, *, plaintext: bool = False) -> None:
    """:func:`fi._core.otel_env_headers.require_no_key_headers_in_otel_env`, imported when called."""
    from fi._core.otel_env_headers import require_no_key_headers_in_otel_env as check

    check(endpoint, environ, plaintext=plaintext)
