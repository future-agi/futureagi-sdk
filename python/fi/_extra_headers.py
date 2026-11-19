"""``FI_EXTRA_HEADERS``: extra HTTP headers on every request to the Future AGI platform.

One setting for every platform client in the SDK. A team environment behind a proxy that wants its
own header on each request (Google IAP's ``Proxy-Authorization: Bearer <identity token>``) sets it
once, and every platform request carries it: the dataset/eval/prompt clients (``fi.api.auth``), the
typed clients (``FutureAGIClient``, ``AsyncFutureAGIClient``), ``fi.webhooks``, the experiment
upload and read paths, the trace exporter of an uploaded run, and the ``futureagi-py`` CLI.

The rules:

- **Format.** ``Name=value`` entries separated by newlines or ``;``. Spaces around a name and its
  value are dropped and empty entries are skipped. Only the first ``=`` of an entry splits it, so a
  value may hold ``=``; a value cannot hold ``;`` (pass ``extra_headers=`` in code for that).
- **Names** must be HTTP tokens (RFC 9110 section 5.6.2): no ``:``, whitespace or control
  character. A name given twice is refused. In a mapping the name must be exactly a token (no
  surrounding spaces either).
- **Values** must be visible ASCII or spaces, and not empty. A control character anywhere in a
  name or value (CR, LF, NUL, tab or any other, before any trimming) is refused, so a value can
  never start a second header line. A value that is only an auth scheme (``Bearer``) is refused:
  the shell variable holding the token was probably empty.
- **The SDK's own auth headers cannot be set this way:** ``X-Api-Key``, ``X-Secret-Key`` and
  ``Authorization`` are refused, with an error naming the setting.
- **Precedence.** Where a client is constructed, ``extra_headers=`` (a mapping, or a string in the
  same format) is added to the setting and wins over it for the same name (names compare without
  case). A header the caller sets explicitly on the client or the request wins over both.
- **Scope.** The headers go only to the client's own base URL: the same scheme, host and port, and
  a path under the base URL's path. Never to any other URL: a judge model, a webhook receiver, a
  redirect to another host.
- **Secrecy.** Values are never logged, printed, journaled or traced. Errors name the setting, the
  entry's number and, for a valid name, the header's name; never a value.
- **When it is read.** The environment is read when each request is sent, so a script that refreshes
  ``os.environ["FI_EXTRA_HEADERS"]`` (an identity token lasts one hour) needs no new client. The
  trace exporter of an uploaded run reads it once, when the run starts.

Imports nothing from ``fi.utils`` or ``fi.api``.
"""

from __future__ import annotations

import functools
import os
import re
from typing import Any, Iterable, Mapping, MutableMapping, Optional, Union
from urllib.parse import urlsplit

from fi._sdk_exception import SDKException

ENV_VAR = "FI_EXTRA_HEADERS"
ARGUMENT = "extra_headers="
RESERVED = frozenset({"x-api-key", "x-secret-key", "authorization"})
# fullmatch only: re's '$' also matches before a trailing '\n', which must never pass
_TOKEN = re.compile(r"[!#$%&'*+\-.^_`|~0-9A-Za-z]+")
_VALUE = re.compile(r"[\x20-\x7e]+")
_CONTROL = re.compile(r"[\x00-\x1f\x7f]")
_BARE_SCHEME = re.compile(r"(bearer|basic|token)", re.IGNORECASE)
_SEPARATORS = re.compile(r"[;\r\n]")

ExtraHeadersInput = Union[Mapping[str, str], str, None]


class ExtraHeadersError(SDKException, ValueError):
    """``FI_EXTRA_HEADERS`` (or ``extra_headers=``) is malformed. The message names the setting and
    the entry, never a header value. The CLI exits 3 (setup)."""

    exit_code = 3

    def get_message(self) -> str:
        return str(getattr(self, "custom_message", None) or f"{ENV_VAR} is malformed")

    def get_error_code(self) -> str:
        return "EXTRA_HEADERS_INVALID"


def _check(name: Any, value: Any, where: str, *, padded: bool) -> tuple[str, str]:
    """``padded``: text form, where spaces (only U+0020) around the name are part of the format."""
    if not isinstance(name, str) or not _TOKEN.fullmatch(name.strip(" ") if padded else name):
        raise ExtraHeadersError(
            f"{where}: the name is not a valid HTTP header name (write Name=value; a name has no ':', "
            "whitespace or control character)"
        )
    name = name.strip(" ")
    if name.lower() in RESERVED:
        raise ExtraHeadersError(
            f"{where}: {name} cannot be set here; the SDK sends its own X-Api-Key, X-Secret-Key and Authorization"
        )
    if not isinstance(value, str):
        raise ExtraHeadersError(f"{where} ({name}): the value must be a string")
    if _CONTROL.search(value):  # before any trimming: a CR, LF or NUL is refused, never dropped
        raise ExtraHeadersError(
            f"{where} ({name}): the value has a control character such as CR, LF, NUL or tab (not visible ASCII)"
        )
    value = value.strip(" ")
    if not value:
        raise ExtraHeadersError(f"{where} ({name}): the value is empty")
    if not _VALUE.fullmatch(value):
        raise ExtraHeadersError(f"{where} ({name}): the value has a character that is not visible ASCII")
    if _BARE_SCHEME.fullmatch(value):
        raise ExtraHeadersError(
            f"{where} ({name}): the value is only an auth scheme with no token (was the token variable empty?)"
        )
    return name, value


def _add(out: dict[str, tuple[str, str]], name: str, value: str, where: str) -> None:
    if name.lower() in out:
        raise ExtraHeadersError(f"{where}: {name} is given twice")
    out[name.lower()] = (name, value)


@functools.lru_cache(maxsize=16)
def _parse_cached(text: str, source: str) -> tuple[tuple[str, str], ...]:
    out: dict[str, tuple[str, str]] = {}
    number = 0
    for raw in _SEPARATORS.split(text):
        if not raw.strip(" "):  # spaces only: an entry of a tab or another control character is refused
            continue
        number += 1
        where = f"{source} entry {number}"
        if "=" not in raw:
            raise ExtraHeadersError(f"{where} has no '=' (write Name=value; separate entries with ';' or newlines)")
        name, _, value = raw.partition("=")
        name, value = _check(name, value, where, padded=True)
        _add(out, name, value, where)
    return tuple(out.values())


def parse(text: str, *, source: str = ENV_VAR) -> dict[str, str]:
    """``Name=value`` entries (newlines or ``;`` between them) as a dict; raises :class:`ExtraHeadersError`."""
    if not isinstance(text, str):
        raise ExtraHeadersError(f"{source} must be a string of Name=value entries")
    return dict(_parse_cached(text, source))


def validate(headers: ExtraHeadersInput, *, source: str = ARGUMENT) -> dict[str, str]:
    """A client's ``extra_headers=`` argument, checked by the same rules as the setting."""
    if headers is None:
        return {}
    if isinstance(headers, str):
        return parse(headers, source=source)
    if not isinstance(headers, Mapping):
        raise ExtraHeadersError(f"{source} must be a mapping of header names to values, or 'Name=value' text")
    out: dict[str, tuple[str, str]] = {}
    for number, (name, value) in enumerate(headers.items(), start=1):
        where = f"{source} entry {number}"
        name, value = _check(name, value, where, padded=False)
        _add(out, name, value, where)
    return dict(out.values())


def from_env(environ: Optional[Mapping[str, str]] = None) -> dict[str, str]:
    """The setting's headers (``{}`` when unset or blank)."""
    env = os.environ if environ is None else environ
    return parse(env.get(ENV_VAR) or "")


def merge(env_headers: Mapping[str, str], argument: Mapping[str, str]) -> dict[str, str]:
    """The setting, then the argument over it for the same name (names compare without case)."""
    out = {name.lower(): (name, value) for name, value in env_headers.items()}
    out.update({name.lower(): (name, value) for name, value in argument.items()})
    return dict(out.values())


def resolve(extra_headers: ExtraHeadersInput = None, environ: Optional[Mapping[str, str]] = None) -> dict[str, str]:
    """The headers a client built with ``extra_headers=`` sends: the setting, the argument winning."""
    return merge(from_env(environ), validate(extra_headers))


def _origin(url: Any) -> Optional[tuple[str, str, int, str]]:
    try:
        parts = urlsplit(str(url))
        port = parts.port
    except ValueError:
        return None
    scheme = (parts.scheme or "").lower()
    host = (parts.hostname or "").lower()
    if scheme not in ("http", "https") or not host:
        return None
    return scheme, host, port or (443 if scheme == "https" else 80), parts.path or "/"


def on_platform(url: Any, base_url: Any) -> bool:
    """Whether ``url`` is under ``base_url``: same scheme, host and port, and a path under its path."""
    target, base = _origin(url), _origin(base_url)
    if target is None or base is None or target[:3] != base[:3]:
        return False
    prefix = base[3].rstrip("/")
    return not prefix or target[3] == prefix or target[3].startswith(prefix + "/")


class ExtraHeaders:
    """One client's extra headers: its ``extra_headers=`` (checked when the client is built) over the
    setting (read when each request is sent), sent only to URLs under its base URL."""

    __slots__ = ("base_url", "_argument")

    def __init__(self, base_url: Any, extra_headers: ExtraHeadersInput = None) -> None:
        self.base_url = str(base_url or "")
        self._argument = validate(extra_headers)

    def __repr__(self) -> str:  # never the values
        return f"ExtraHeaders(base_url={self.base_url!r}, argument_names={sorted(self._argument)!r})"

    def resolve(self) -> dict[str, str]:
        return merge(from_env(), self._argument)

    def for_url(self, url: Any) -> dict[str, str]:
        """The headers for a request to ``url``: ``{}`` off the base URL (the setting is not even read)."""
        if not on_platform(url, self.base_url):
            return {}
        return self.resolve()

    def apply(self, headers: MutableMapping[str, str], url: Any) -> None:
        """Add the headers for ``url`` to ``headers``, leaving any name the caller already set."""
        present = {str(k).lower() for k in headers.keys()}
        for name, value in self.for_url(url).items():
            if name.lower() not in present:
                headers[name] = value

    def names(self) -> list[str]:
        """The header names a platform request would carry (raises on a malformed setting)."""
        return sorted(self.resolve())


def describe(environ: Optional[Mapping[str, str]] = None) -> dict[str, Any]:
    """For ``futureagi-py doctor``: the setting's header names (never a value), or its error."""
    env = os.environ if environ is None else environ
    if not (env.get(ENV_VAR) or "").strip(" ;\r\n"):  # exactly what parse() skips; a lone tab is an error
        return {"names": [], "source": None}
    try:
        return {"names": sorted(from_env(env)), "source": ENV_VAR}
    except ExtraHeadersError as exc:
        return {"names": [], "source": ENV_VAR, "error": str(exc)}


def secret_values(
    environ: Optional[Mapping[str, str]] = None, extra: Iterable[Mapping[str, str]] = (), min_len: int = 8
) -> list[str]:
    """Every header value of the setting (and of ``extra`` mappings), and the token after an auth
    scheme (``Bearer <token>``), for a redactor. ``[]`` for a malformed setting."""
    try:
        sources = [from_env(environ), *extra]
    except ExtraHeadersError:
        sources = list(extra)
    values: set[str] = set()
    for headers in sources:
        for value in headers.values():
            values.add(value)
            _, _, rest = value.partition(" ")
            if rest.strip():
                values.add(rest.strip())
    return sorted((v for v in values if len(v) >= min_len), key=len, reverse=True)
