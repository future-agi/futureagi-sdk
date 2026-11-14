"""Where sandbox calls go, with which credential and scope headers (contract section 2, v2 items 1-2).

``Sandbox.create`` / ``connect`` / ``list`` / ``settings`` read the environment only:

- ``OMEGA_BASE_URL``: hosted is ``https://<gateway-host>/omega/api``; a self-hosted EE is its origin
  with its port. There is no default host: without it a
  :class:`~fi.sandbox.errors.ConfigurationError` names ``OMEGA_BASE_URL``. The URL is used as given,
  but the hosted key pair goes only to a Future AGI host (HTTPS in the ``futureagi.com`` zone) or to
  loopback, the core's host guard; another host needs ``FI_ALLOW_CUSTOM_PLATFORM_URL=1``.
- Hosted: ``FI_API_KEY`` + ``FI_SECRET_KEY``, sent as ``X-Api-Key`` / ``X-Secret-Key``.
- Self-host: ``FUTUREAGI_OMEGA_API_KEY``, sent as ``Authorization: Bearer``.
- Both modes set is a configuration error: both are never sent. ``OMEGA_OS_API_KEY`` is never read.
- Scope: ``FI_WORKSPACE_ID`` / ``FI_ORGANIZATION_ID`` (the client's own variables), sent by mode
  (OpenAPI ``info.x-omega-scope-headers``): hosted ``X-Workspace-Id`` / ``X-Organization-Id``,
  self-host ``x-omega-workspace`` / ``x-omega-org``.
- ``FI_EXTRA_HEADERS``: exactly as ``FutureAGIClient`` sends it (the same ``fi._http`` path), read
  from the process environment when each request is sent, only to URLs under ``OMEGA_BASE_URL``
  (same scheme, host and port, a path under its path), never over a header the SDK sets, and
  never in an error. A malformed value is refused before anything is sent. A scope header of
  either mode named there is dropped, so only ``FI_WORKSPACE_ID`` / ``FI_ORGANIZATION_ID`` choose
  the scope.

To pass keys, a base URL, a workspace or an organization in code, build ``FutureAGIClient`` /
``AsyncFutureAGIClient`` and call ``client.sandboxes.create(...)`` / ``.connect(id)``: the client's
own origin rules apply there and it sends the same scope headers.

The hosted keys' host rule is the core's (:func:`fi._core.origins.host_allowed`, with loopback
exactly as the core reads it): a key pair for any other host is refused before anything is sent
(``custom_base_url_not_allowed``, naming only ``host[:port]``) unless the environment sets
``FI_ALLOW_CUSTOM_PLATFORM_URL`` (read as the core reads it) or the command line passes
``--allow-custom-base-url``; either prints the core's one-time notice.

Every sandbox call, from either path, also passes :class:`OriginRule` first: a client given no base
URL is refused (``missing_base_url``: its derived default host is not a sandbox host); plain HTTP to a
host that is not loopback is refused (``insecure_sandbox_origin``, whatever ``allow_insecure_http``
says); and a self-host Bearer token goes to a host that is not loopback only when the client was
built with the constructor-only ``allow_custom_base_url=True`` (OpenAPI ``servers[1]``), or the
command line passes ``--allow-custom-base-url``; the environment can never allow that. No key
appears in a ``repr``, a log line or an error.

Closing an environment connection forgets its HTTP client, so a handle that shares it (a restored or
listed sandbox) opens a new one on its next call instead of failing.
"""

from __future__ import annotations

import ipaddress
import os
from dataclasses import dataclass, replace
from typing import Any, Dict, List, Mapping, Optional

import httpx

from fi._core.http_security import is_insecure_http
from fi._core.origins import (
    ALLOW_CUSTOM_ENV,
    FUTURE_AGI_ZONE,
    PlatformOrigin,
    _allow_flag,
    _warn_once,
    ascii_host,
    display_host,
    host_allowed,
)
from fi._core.platform_async import AsyncPlatformCore
from fi._core.platform_base import PlatformCore
from fi._core.redact import scrub_value
from fi._core.transport import PlatformShared, _AttemptRecorder
from fi._http import (
    ExtraHeaders,  # the client's class, as fi._http's LazyKeyAuth takes it
)

from ._state import keep_state
from .errors import ConfigurationError

BASE_URL_ENV = "OMEGA_BASE_URL"
API_KEY_ENV = "FI_API_KEY"
SECRET_KEY_ENV = "FI_SECRET_KEY"
BEARER_ENV = "FUTUREAGI_OMEGA_API_KEY"
WORKSPACE_ENV = "FI_WORKSPACE_ID"
ORGANIZATION_ENV = "FI_ORGANIZATION_ID"
#: (workspace header, organization header) per credential mode.
SCOPE_HEADERS = {
    "keys": ("X-Workspace-Id", "X-Organization-Id"),
    "bearer": ("x-omega-workspace", "x-omega-org"),
}


def scope_headers(
    mode: str, workspace: Optional[str], organization: Optional[str]
) -> Dict[str, str]:
    """The scope selectors as the mode sends them; an unset one is not sent."""
    names = SCOPE_HEADERS[mode]
    pairs = zip(names, (workspace, organization))
    return {name: value for name, value in pairs if value}


def _env(env: Mapping[str, str], name: str) -> Optional[str]:
    return env.get(name, "").strip() or None


def _url(raw: str) -> httpx.URL:
    problem = None
    try:
        url = httpx.URL(raw)
    except Exception:
        url, problem = None, "is not a valid URL"
    if url is not None:
        if url.scheme not in ("https", "http") or not url.host:
            problem = "must be an absolute https:// (or http:// to loopback) URL"
        elif url.userinfo:
            problem = "must not contain a user name or password"
        elif url.query or url.fragment or "?" in raw or "#" in raw:
            problem = "must not contain a query or a fragment"
    if problem is not None or url is None:
        raise ConfigurationError(
            f"the sandbox base URL ({BASE_URL_ENV}) {problem}", code="invalid_base_url"
        )
    return url


#: What a refusal of the hosted keys to another host tells an environment user to do.
KEYS_HINT = (
    f"set {ALLOW_CUSTOM_ENV}=1 if you trust it. A self-hosted EE takes {BEARER_ENV} instead"
)


def _keys_zone(
    origin: PlatformOrigin,
    env: Mapping[str, str],
    allow: Optional[bool],
    hint: str,
) -> PlatformOrigin:
    """The hosted keys go only where the core's host guard sends them (HTTPS in the Future AGI
    zone, or loopback as the core reads it). Another host needs ``allow`` (None: the environment's
    ``FI_ALLOW_CUSTOM_PLATFORM_URL``, read by the core's own parser) and then gets the core's
    one-time notice. Plain HTTP off loopback is left to :class:`OriginRule`, which refuses it
    whatever is allowed."""
    url = origin.url
    if origin.mode != "keys" or is_insecure_http(url) or host_allowed(url):
        return origin
    if not _allow_flag(allow, env):
        raise ConfigurationError(
            f"{API_KEY_ENV} and {SECRET_KEY_ENV} go only to Future AGI hosts "
            f"({FUTURE_AGI_ZONE} over HTTPS) or loopback; refusing to send them to "
            f"{display_host(url)}: {hint}",
            code="custom_base_url_not_allowed",
        )
    _warn_once(url)
    return replace(origin, custom=True)


def resolve_origin(
    environ: Optional[Mapping[str, str]] = None,
    *,
    allow_custom_base_url: Optional[bool] = None,
    keys_hint: str = KEYS_HINT,
) -> PlatformOrigin:
    """The origin, the one credential and the scope headers every request carries, from the
    environment only; a configuration error before anything is sent. ``allow_custom_base_url``
    lets the hosted keys go to a host outside the Future AGI zone (None: the environment's
    ``FI_ALLOW_CUSTOM_PLATFORM_URL`` decides; False: never)."""
    env = os.environ if environ is None else environ
    raw = _env(env, BASE_URL_ENV)
    if raw is None:
        raise ConfigurationError(
            f"no sandbox base URL: set {BASE_URL_ENV} (hosted: https://<gateway-host>/omega/api; "
            "self-hosted: your EE origin with its port), or pass it to FutureAGIClient and use "
            "client.sandboxes. There is no default host.",
            code="missing_base_url",
        )
    url = _url(raw)
    api_key, secret_key = _env(env, API_KEY_ENV), _env(env, SECRET_KEY_ENV)
    bearer = _env(env, BEARER_ENV)
    if bearer and (api_key or secret_key):
        raise ConfigurationError(
            f"both a self-host Bearer token ({BEARER_ENV}) and an API key pair ({API_KEY_ENV}, "
            f"{SECRET_KEY_ENV}) are set; set exactly one",
            code="mixed_credentials",
        )
    if bearer:
        mode, headers = "bearer", {"Authorization": f"Bearer {bearer}"}
        secrets: tuple = (bearer,)
    elif api_key and secret_key:
        mode, headers = "keys", {"X-Api-Key": api_key, "X-Secret-Key": secret_key}
        secrets = (api_key, secret_key)
    else:
        pair = ((API_KEY_ENV, api_key), (SECRET_KEY_ENV, secret_key))
        missing = [name for name, value in pair if not value]
        raise ConfigurationError(
            f"no sandbox credential: set {' and '.join(missing)} (hosted) or {BEARER_ENV} "
            "(self-hosted EE)",
            code="missing_credentials",
        )
    scope = scope_headers(mode, _env(env, WORKSPACE_ENV), _env(env, ORGANIZATION_ENV))
    origin = PlatformOrigin(url, mode, "env", {**headers, **scope}, secrets)
    return _keys_zone(origin, env, allow_custom_base_url, keys_hint)


def is_loopback(host: str) -> bool:
    """localhost, any 127.0.0.0/8 address or ::1."""
    host = host.strip("[]").lower()
    if host == "localhost":
        return True
    try:
        return ipaddress.ip_address(host).is_loopback
    except ValueError:
        return False


CLIENT_HINT = (
    "pass allow_custom_base_url=True to FutureAGIClient / AsyncFutureAGIClient if you trust it"
)
#: What a connection error tells the user to check, per path.
CLIENT_SETTING = "platform_base_url / FI_PLATFORM_BASE_URL"
NO_BASE_URL = (
    "client.sandboxes has no sandbox API host: this client was given no base URL, and its default "
    "host is not a sandbox host. Pass base_url (hosted: https://<gateway-host>) or "
    "platform_base_url (hosted: https://<gateway-host>/omega/api; self-hosted EE: its origin with "
    "the port) to the client, or set FI_BASE_URL or FI_PLATFORM_BASE_URL. There is no default "
    "host. (Sandbox.create, connect, list and settings read OMEGA_BASE_URL.)"
)
ENVIRONMENT_HINT = (
    "Sandbox.create / connect / list / settings read only the environment, which never allows "
    "that; build FutureAGIClient(platform_token=..., platform_base_url=..., "
    "allow_custom_base_url=True) and call client.sandboxes.create(...) or .connect(id)"
)


@dataclass(frozen=True)
class OriginRule:
    """What a sandbox call checks about its origin before anything is sent. ``no_base_url``: the
    client was given no base URL (argument or ``FI_BASE_URL``), so a derived origin is its default
    host. ``setting`` is what a connection error tells the user to check."""

    allow_custom_base_url: bool = False
    hint: str = CLIENT_HINT
    no_base_url: bool = False
    setting: str = CLIENT_SETTING

    def problem(self, origin: PlatformOrigin) -> Optional[ConfigurationError]:
        """The refusal for ``origin``, or None. Returned, not raised, so the caller raises it
        outside any ``except`` block (no chained exception)."""
        local = is_loopback(ascii_host(origin.url))
        where = display_host(origin.url)
        if self.no_base_url and origin.source == "derived":
            return ConfigurationError(NO_BASE_URL, code="missing_base_url")
        if origin.url.scheme != "https" and not local:
            return ConfigurationError(
                f"sandbox calls never send credentials over plain HTTP to a host that is not "
                f"loopback ({where}); use https://",
                code="insecure_sandbox_origin",
            )
        if origin.mode == "bearer" and not local and not self.allow_custom_base_url:
            return ConfigurationError(
                f"refusing to send a self-host Bearer token to {where}, which is not loopback: "
                f"{self.hint}",
                code="custom_base_url_not_allowed",
            )
        return None


ENVIRONMENT_RULE = OriginRule(
    allow_custom_base_url=False, hint=ENVIRONMENT_HINT, setting=BASE_URL_ENV
)


class ReopeningShared(PlatformShared):
    """The environment connection's shared state: closing it forgets the HTTP client (and the
    transport under it), so a handle that shares it (a restored sandbox, a listed one) opens a new
    client on its next call instead of failing on a closed one."""

    def __init__(
        self, resolve: Any, *, transport: Any = None, extra_headers: Any = None
    ) -> None:
        super().__init__(resolve, transport=transport, extra_headers=extra_headers)
        self._transport = transport

    def _forget(self, attribute: str) -> Any:
        with self._lock:
            client = getattr(self, attribute)
            setattr(self, attribute, None)
            if client is not None:
                self._recorder = _AttemptRecorder(self._transport)
        return client

    def close(self) -> None:
        client = self._forget("_http")
        if client is not None:
            client.close()

    async def aclose(self) -> None:
        client = self._forget("_ahttp")
        if client is not None:
            await client.aclose()


def default_transport() -> Any:
    """The transport under an environment connection (None: httpx's own). Tests replace it."""
    return None


class _Connection:
    core_class: Any = PlatformCore

    def __init__(
        self,
        *,
        environ: Optional[Mapping[str, str]] = None,
        transport: Any = None,
        allow_custom_base_url: Optional[bool] = None,
        keys_hint: str = KEYS_HINT,
    ) -> None:
        self._environ = environ
        self._transport = transport
        self._allow = allow_custom_base_url
        self._keys_hint = keys_hint

    def __repr__(self) -> str:
        return f"{type(self).__name__}()"

    def core(self) -> Any:
        """A platform executor for the environment's settings; resolves (and may refuse) now.
        ``FI_EXTRA_HEADERS`` goes only under the origin's URL, as the client's under its own."""
        origin = resolve_origin(
            self._environ, allow_custom_base_url=self._allow, keys_hint=self._keys_hint
        )
        transport = self._transport
        if transport is None:
            transport = default_transport()
        extra = ExtraHeaders(str(origin.url))
        shared = ReopeningShared(lambda: origin, transport=transport, extra_headers=extra)
        return self.core_class(shared)


class SandboxConnection(_Connection):
    """The environment connection for ``Sandbox`` (sync)."""

    core_class = PlatformCore


class AsyncSandboxConnection(_Connection):
    """The environment connection for ``AsyncSandbox``."""

    core_class = AsyncPlatformCore


class _StateKeepingShared:
    """An executor's shared state as sandbox calls see it: the shared state itself (origin,
    pool, close), except that its error scrubber also keeps a sandbox state the shared
    redactor would hide (:func:`fi.sandbox._state.keep_state`)."""

    def __init__(self, inner: Any) -> None:
        self._inner = inner

    def __getattr__(self, name: str) -> Any:
        if name == "_inner" or name.startswith("__"):
            raise AttributeError(name)
        return getattr(self._inner, name)

    def error_scrubber(self, value: Any, secrets: List[str]) -> Any:
        scrub = self._inner.error_scrubber or scrub_value
        return keep_state(scrub(value, secrets))


def sandbox_core(core: Any) -> Any:
    """``core`` with the sandbox error scrubber: the same executor class, settings and shared
    state. Returned unchanged when it already has it, or is not an executor."""
    shared = getattr(core, "shared", None)
    if shared is None or isinstance(shared, _StateKeepingShared):
        return core
    return type(core)(_StateKeepingShared(shared), core.settings)


def http_of(core: Any) -> Any:
    """The executor's pooled HTTP client: async for an async executor."""
    if isinstance(core, AsyncPlatformCore):
        return core.shared.ahttp()
    return core.shared.http()
