"""The platform origin, the credential it gets, and the host guard.

The origin comes from ``fi._credentials.resolve()``: ``platform_base_url=``, then
``FI_PLATFORM_BASE_URL``, then the saved login's (only with the login's own keys), else it is
**derived** from the base URL as ``{base_url}/omega/api``. One ``FI_BASE_URL`` covers both origins.

Credential modes:

- **keys** (hosted, and self-hosted FA): ``X-Api-Key`` / ``X-Secret-Key``, plus
  ``X-Workspace-Id`` / ``X-Organization-Id`` when set. When no selector is set none is sent, and
  the server uses the key's own workspace.
- **bearer** (self-hosted EE): ``Authorization: Bearer <FI_PLATFORM_TOKEN>``, plus
  ``X-Omega-Workspace`` / ``X-Omega-Org``. A token together with a key pair from arguments or the
  environment raises :class:`~fi.errors.MixedCredentialsError`.

The key pair comes from one place (the shared resolver): both arguments, both environment variables or
the saved login; with one key as an argument the other half is never taken from the environment,
and a half pair raises ``CredentialsMissingError``. TypeScript's ``origins.ts`` takes the pair the
same way, so the guard's "same source as the keys" names one source for both keys in both languages.

The host guard (keys mode only) lets the keys go to the platform origin when it is derived, when
it comes from the **same explicit source** as the keys (both arguments, both the environment, or
both the saved login), or when it is HTTPS in the ``futureagi.com`` zone or HTTP on loopback.
Anything else raises :class:`~fi.errors.HostNotAllowedError`, unless
``allow_custom_platform_url=True`` or ``FI_ALLOW_CUSTOM_PLATFORM_URL=1`` is set, which prints one
stderr warning per origin. Bearer mode does not use the keys' provenance exemption, but
nonloopback HTTP requires ``allow_insecure_http=True`` / ``FI_ALLOW_INSECURE_HTTP=1`` and warns
once per canonical origin. Keys-mode HTTP remains compatible and warns before transport.
A saved login's keys are never sent to an origin from another source (the guard, plus the shared
binding of the login to its base URL).
"""

from __future__ import annotations

import os
import re
import sys
from dataclasses import dataclass, field
from typing import Mapping, Optional

import httpx

from fi._credentials import PLATFORM_BASE_URL_ENV, PLATFORM_TOKEN_ENV, Credentials
from fi._core.http_security import check_http_security, is_insecure_http
from fi.errors import (
    HostNotAllowedError,
    MixedCredentialsError,
    PlatformNotConfiguredError,
)

ALLOW_CUSTOM_ENV = "FI_ALLOW_CUSTOM_PLATFORM_URL"
FUTURE_AGI_ZONE = "futureagi.com"
LOOPBACK_HOSTS = frozenset({"127.0.0.1", "::1", "localhost"})
_EXPLICIT_SOURCES = frozenset({"argument", "env", "login"})
_warned: set[str] = set()
# Raw-string rules, the same in TypeScript's origins.ts (tests/fixtures/platform-origins): httpx and the
# WHATWG URL parser disagree on these inputs, so neither parser decides them.
_SCHEME_AUTHORITY = re.compile(r"^[A-Za-z][A-Za-z0-9+.\-]*://([^/?#]*)")
_DOTS = re.compile("[.\u3002\uff0e\uff61]")  # the separators IDNA maps to "."
_OCTET = r"(25[0-5]|2[0-4][0-9]|1[0-9]{2}|[1-9]?[0-9])"
_IPV4 = re.compile(rf"^{_OCTET}(\.{_OCTET}){{3}}$")
_HEX_LABEL = re.compile(r"^0[xX][0-9a-fA-F]*$")


def _raw_problem(raw: str) -> Optional[str]:
    """What makes ``raw`` unusable before a parser sees it: a space, a control character or a
    backslash anywhere; no ``scheme://`` or an empty host; a percent sign in the host."""
    if any(ord(ch) <= 0x20 or ord(ch) == 0x7F for ch in raw) or "\\" in raw:
        return "must not contain spaces, control characters or a backslash"
    match = _SCHEME_AUTHORITY.match(raw)
    if match is None or match.group(1) == "":
        return "must be an absolute https:// URL (or http:// to loopback)"
    if "%" in match.group(1):
        return "must not percent-encode its host"
    return None


def _ipv4_problem(raw: str) -> Optional[str]:
    """A host whose last label is a number is an IPv4 address to the WHATWG parser (``127.1``,
    ``2130706433``, ``0x7f.1``); only the canonical dotted quad is accepted, so both languages agree."""
    match = _SCHEME_AUTHORITY.match(raw)
    host = match.group(1).rsplit("@", 1)[-1] if match else ""
    if host.startswith("["):
        return None
    host = _DOTS.sub(".", re.sub(r":[0-9]*$", "", host))
    host = host[:-1] if host.endswith(".") else host
    last = host.rsplit(".", 1)[-1]
    if not (last.isdecimal() or _HEX_LABEL.match(last)) or _IPV4.match(host):
        return None
    return "must write an IPv4 address as four decimal numbers (like 127.0.0.1)"


def ascii_host(url: httpx.URL) -> str:
    """The host httpx connects to, lower-case ASCII (IDNA), without a trailing dot."""
    host = url.raw_host.decode("ascii", "replace").lower()
    return host[:-1] if host.endswith(".") else host


def display_host(url: httpx.URL) -> str:
    """``host[:port]`` for messages: never the path, never a credential."""
    host = ascii_host(url)
    host = f"[{host}]" if ":" in host else host
    return f"{host}:{url.port}" if url.port is not None else host


def is_loopback(host: str) -> bool:
    return host in LOOPBACK_HOSTS


def in_future_agi_zone(host: str) -> bool:
    return host == FUTURE_AGI_ZONE or host.endswith("." + FUTURE_AGI_ZONE)


def parse_origin(raw: str) -> httpx.URL:
    """The platform origin as a URL; refuses non-HTTP schemes, a user name, a query or a fragment,
    and the raw forms the two languages' parsers read differently (:func:`_raw_problem`)."""
    problem = _raw_problem(raw)
    if problem is not None:
        raise PlatformNotConfiguredError(f"{PLATFORM_BASE_URL_ENV} {problem}", code="invalid_platform_url")
    try:
        url = httpx.URL(raw)
    except Exception:
        raise PlatformNotConfiguredError(
            f"{PLATFORM_BASE_URL_ENV} is not a valid URL", code="invalid_platform_url"
        ) from None
    if url.scheme not in ("https", "http") or not url.raw_host:
        raise PlatformNotConfiguredError(
            f"{PLATFORM_BASE_URL_ENV} must be an absolute https:// URL (or http:// to loopback)",
            code="invalid_platform_url",
        )
    if url.userinfo:
        raise PlatformNotConfiguredError(
            f"{PLATFORM_BASE_URL_ENV} must not contain a user name or password (host {display_host(url)})",
            code="invalid_platform_url",
        )
    if url.query or url.fragment or "?" in raw or "#" in raw:
        raise PlatformNotConfiguredError(
            f"{PLATFORM_BASE_URL_ENV} must not contain a query or a fragment", code="invalid_platform_url"
        )
    problem = _ipv4_problem(raw)
    if problem is not None:
        raise PlatformNotConfiguredError(f"{PLATFORM_BASE_URL_ENV} {problem}", code="invalid_platform_url")
    return url


def host_allowed(url: httpx.URL) -> bool:
    """HTTPS in the Future AGI zone, or HTTP(S) on loopback."""
    host = ascii_host(url)
    if is_loopback(host):
        return True
    return url.scheme == "https" and in_future_agi_zone(host)


@dataclass(frozen=True)
class PlatformOrigin:
    """The resolved platform origin and what every request to it carries."""

    url: httpx.URL
    #: ``keys`` or ``bearer``.
    mode: str
    #: Where the origin came from: ``argument``, ``env``, ``login`` or ``derived``.
    source: str
    headers: dict[str, str] = field(repr=False)
    #: Every secret the requests carry, for scrubbing reflected error text.
    secrets: tuple[str, ...] = field(repr=False, default=())
    #: True when the origin is outside the guard and the allow flag let it through.
    custom: bool = False

    @property
    def base(self) -> str:
        """The origin as a string, without a trailing slash."""
        return str(self.url).rstrip("/")


def _allow_flag(allow: Optional[bool], environ: Mapping[str, str]) -> bool:
    if allow is not None:
        return bool(allow)
    return environ.get(ALLOW_CUSTOM_ENV, "").strip().lower() in ("1", "true", "yes")


def _warn_once(url: httpx.URL) -> None:
    if is_insecure_http(url):
        # One cleartext warning also covers the custom-host exemption, without
        # duplicating it when the request reaches the shared platform executor.
        # Loopback HTTP (any 127/8) gets the ordinary custom-host warning, as in TypeScript.
        check_http_security(url, "keys")
        return
    key = str(url)
    if key in _warned:
        return
    _warned.add(key)
    sys.stderr.write(
        f"futureagi: sending your keys to {display_host(url)}, outside the Future AGI zone, because "
        f"allow_custom_platform_url / {ALLOW_CUSTOM_ENV} is set.\n"
    )


def resolve_platform(
    creds: Credentials,
    *,
    allow_custom_platform_url: Optional[bool] = None,
    allow_insecure_http: Optional[bool] = None,
    environ: Optional[Mapping[str, str]] = None,
) -> PlatformOrigin:
    """Decide the origin and credential for platform requests, or raise before anything is sent.

    Raises :class:`~fi.errors.MixedCredentialsError`, :class:`~fi.errors.PlatformNotConfiguredError`,
    :class:`~fi.errors.HostNotAllowedError` or ``CredentialsMissingError`` (no keys and no token)."""
    env = os.environ if environ is None else environ
    url = parse_origin(creds.platform_base_url)
    if creds.platform_token:
        if creds.keys_source in ("argument", "env"):
            raise MixedCredentialsError(
                f"both {PLATFORM_TOKEN_ENV} (a self-host Bearer token, from {creds.platform_token_source}) and an API key pair "
                f"(from {creds.keys_source}) are set; pass one or the other",
                code="mixed_credentials",
            )
        check_http_security(url, "bearer", allow_insecure_http=allow_insecure_http, environ=env)
        headers = {"Authorization": f"Bearer {creds.platform_token}"}
        if creds.workspace_id:
            headers["X-Omega-Workspace"] = creds.workspace_id
        if creds.organization_id:
            headers["X-Omega-Org"] = creds.organization_id
        return PlatformOrigin(url, "bearer", creds.platform_base_url_source, headers, (creds.platform_token,))
    keys = _require(creds, env)
    source = creds.platform_base_url_source
    exempt = source == "derived" or (source in _EXPLICIT_SOURCES and source == creds.keys_source)
    custom = False
    if not exempt and not host_allowed(url):
        if not _allow_flag(allow_custom_platform_url, env):
            why = "plain http to a host that is not loopback" if url.scheme == "http" else "outside the Future AGI zone"
            raise HostNotAllowedError(
                f"refusing to send your API keys (from {keys.keys_source}) to {display_host(url)} ({why}); the platform origin "
                f"came from {source}, not from the same place as the keys. Pass allow_custom_platform_url=True or set "
                f"{ALLOW_CUSTOM_ENV}=1 if you trust it",
                code="host_not_allowed",
            )
        custom = True
        _warn_once(url)
    check_http_security(url, "keys")
    headers = {"X-Api-Key": str(keys.api_key), "X-Secret-Key": str(keys.secret_key)}
    if keys.workspace_id:
        headers["X-Workspace-Id"] = keys.workspace_id
    if keys.organization_id:
        headers["X-Organization-Id"] = keys.organization_id
    secrets = tuple(s for s in (keys.api_key, keys.secret_key) if s)
    return PlatformOrigin(url, "keys", source, headers, secrets, custom)


def _require(creds: Credentials, env: Mapping[str, str]) -> Credentials:
    """The complete key pair, or ``CredentialsMissingError``. The pair comes from one place (the shared
    resolver): with one key as an argument, the other half is never taken from the environment, and
    the message says so when it is there."""
    from fi._credentials import CredentialsMissingError

    if creds.complete:
        return creds
    missing = tuple(n for n, v in (("FI_API_KEY", creds.api_key), ("FI_SECRET_KEY", creds.secret_key)) if not v)
    hint = f"For a self-hosted Omega EE, set {PLATFORM_TOKEN_ENV} instead."
    unpaired = [n for n in missing if env.get(n)] if creds.keys_source == "argument" else []
    if unpaired:
        given = "an api_key" if creds.api_key else "a secret_key"
        hint = (
            f"The key pair comes from one place: {' and '.join(unpaired)} in the environment is not paired with "
            f"{given} argument; pass both arguments or set both variables. " + hint
        )
    raise CredentialsMissingError(creds.base_url, missing, creds.login_skipped, hint=hint)
