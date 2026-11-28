"""The headers an OTLP span exporter sends to Future AGI.

OpenTelemetry's OTLP exporters read ``OTEL_EXPORTER_OTLP_HEADERS`` and
``OTEL_EXPORTER_OTLP_TRACES_HEADERS`` while they are built, and the HTTP exporter in 1.45 merges
those values into the headers it is given. Those settings are meant for the user's own backend.
An exporter that sends to a Future AGI endpoint must send the SDK's headers and nothing from
the environment, so a foreign ``Authorization`` stays out of requests to Future AGI.

:func:`pin_headers` runs once, right after the exporter is built. It replaces the exporter's
resolved headers with exactly the SDK's dict, plus the headers the transport itself sets
(content type, user agent, content encoding). It does not read or change ``os.environ``.
The exporter reads its headers when it sends a batch, from the attribute set here, so a variable
set after construction has no effect:

* ``opentelemetry-exporter-otlp-proto-http`` 1.45: ``OTLPSpanExporter._client._headers``, passed to
  the transport on every request (``opentelemetry/exporter/otlp/common/http.py``, ``_submit``).
* ``opentelemetry-exporter-otlp-proto-http`` 1.39: ``OTLPSpanExporter._session.headers``, which
  ``_export`` posts with (``trace_exporter/__init__.py``). The constructor copies the resolved
  headers into the session once.
* ``opentelemetry-exporter-otlp-proto-grpc`` 1.39 and 1.45: ``OTLPSpanExporter._headers``, a tuple
  of pairs sent as call metadata (``exporter.py``).

An exporter whose headers are kept anywhere else cannot be pinned, so ``pin_headers`` raises
:class:`fi.errors.ConfigurationError` (code ``unsupported_otlp_exporter``) instead of leaving ambient
headers in place. The message names the exporter class and the supported versions and holds no
header or environment values.

The HTTP exporter's session also stays clear of two other ambient sources of credentials. The HTTP
exporters take a session from the credential provider named in
``OTEL_PYTHON_EXPORTER_OTLP_HTTP_TRACES_CREDENTIAL_PROVIDER`` (or the shared
``OTEL_PYTHON_EXPORTER_OTLP_HTTP_CREDENTIAL_PROVIDER``) whenever the caller passes none:
``session or _load_session_from_envvar(...)`` in ``trace_exporter/__init__.py`` for 1.45 (line 150) and
for 1.39 (lines 120-125). A caller that builds an exporter for Future AGI therefore passes
:func:`futureagi_session`, a fresh session of the SDK's own, as ``session=``; the experiments run exporter
does the same with its ``ExportSession``. And ``requests`` adds Basic auth for a host from the user's netrc
file when a session has no ``auth``. :func:`pin_headers` gives the session an auth that does nothing, which
turns that off. The session keeps ``trust_env``, so the proxy and CA settings the user configured
apply to ``https://`` requests; turning ``trust_env`` off would drop those too. A request to an ``http://``
endpoint is the exception: the SDK's keys are on it, so it goes straight to its target and the proxy settings of
the environment are not used (:func:`plain_session_proxies`). The same holds for a gRPC channel without TLS
(``grpc.enable_http_proxy`` is ``0``).

An exporter that sends to an endpoint the user chose is not passed here, and keeps the standard
OpenTelemetry environment behaviour.
"""

from __future__ import annotations

import collections
import ipaddress
import logging
import os
import re
import threading
from collections.abc import Mapping
from typing import Any
from urllib.parse import unquote, urlparse, urlsplit

from fi.errors import ConfigurationError

_LOG = logging.getLogger(__name__)
SUPPORTED_EXPORTER_VERSIONS = "1.39.1 to 1.45.x"
_FALLBACK_DEFAULTS = {"content-type": "application/x-protobuf"}


DEFAULT_FUTUREAGI_HOSTS = ("api.futureagi.com", "grpc.futureagi.com")
_HOST_VARIABLES = ("FI_BASE_URL", "FI_TRACES_URL", "FI_GRPC_URL")


def _normalized_host(host: str) -> str | None:
    """The one ASCII spelling of a DNS name, or ``None`` when it has none.

    The name is lower-cased and stripped of exactly one trailing dot, and a label with a non-ASCII
    character is encoded with ``idna.encode(label, strict=True, std3_rules=True)``, the call ``urllib3``
    makes for the host it connects to, so ß and ss stay different names, as they are to ``requests``.
    A name that fails any step (an IDNA error, an empty label, a second trailing dot, an invalid
    character) has no spelling, and ``None`` equals nothing, so such a name is not a Future AGI host."""
    host = str(host).strip().lower().removesuffix(".")
    if not host or host.endswith(".") or host.startswith("."):
        return None
    labels = []
    for label in host.split("."):
        if not label.isascii():
            try:
                import idna

                label = idna.encode(label, strict=True, std3_rules=True).decode("ascii")
            except (ImportError, UnicodeError, ValueError):
                return None
        labels.append(label)
    if any(not label or len(label) > 63 for label in labels):
        return None
    if not all(re.fullmatch(r"[a-z0-9_]([a-z0-9_-]*[a-z0-9_])?", label) for label in labels):
        return None
    return ".".join(labels)


def _ambiguous(text: str) -> bool:
    """True when an authority could be read as more than one host: a backslash, a percent sign, white
    space, a control character, or user information (an ``@``). ``urllib3`` and the standard library
    disagree on some of these, and ``requests`` connects to the ``urllib3`` reading."""
    return (
        "\\" in text
        or "%" in text
        or "@" in text
        or any(ord(char) <= 0x20 or ord(char) == 0x7F or char.isspace() for char in text)
    )


def _url_host(text: str) -> str | None:
    """The host of ``scheme://authority/...``, read by ``urllib3`` and by the standard library; ``None``
    when the authority is ambiguous or the two parsers do not give the same host."""
    authority = text.split("://", 1)[1]
    for stop in "/?#":
        authority = authority.split(stop, 1)[0]
    if _ambiguous(authority):
        return None
    try:
        from urllib3.util import parse_url

        connects = parse_url(text).host
        reads = urlsplit(text).hostname
    except ValueError:  # urllib3's LocationParseError is one: requests refuses the URL too
        return None
    if not connects or not reads:
        return None
    connects, reads = _normalized_host(connects), _normalized_host(reads)
    return connects if connects is not None and connects == reads else None


_GRPC_SCHEME = re.compile(r"^([a-z][a-z0-9+.-]*):", re.IGNORECASE)
_GRPC_NAMED_SCHEMES = ("ipv4", "ipv6", "unix", "unix-abstract", "vsock")


def _grpc_target_host(text: str) -> str | None:
    """The host gRPC dials for ``dns:[//resolver/]host[:port]``; ``None`` for a scheme that names an
    address or a socket rather than a host name."""
    rest = text[len("dns:"):]
    if rest.startswith("//"):
        resolver, _, rest = rest[2:].partition("/")
        if _ambiguous(resolver):
            return None
    if not rest or _ambiguous(rest) or "/" in rest:
        return None
    return _url_host(f"https://{rest}")


AMBIGUOUS_ENDPOINT_MESSAGE = (
    "The exporter endpoint has an authority that can be read as more than one host, so no exporter "
    "was built for it. Use a plain host name or address (insecure_http_origin)"
)


def _hosts_disagree(url: str) -> bool:
    """True when ``urllib3`` (which ``requests`` connects with) and the standard library read different
    hosts from ``url``, or either one cannot read it."""
    from urllib3.util import parse_url

    try:
        connects = parse_url(url).host
        reads = urlsplit(url).hostname
    except ValueError:
        return True
    if not connects and not reads:
        return False
    if not connects or not reads:
        return True
    connects = connects.strip("[]").lower()
    if not reads.isascii():
        try:
            import idna

            reads = ".".join(
                idna.encode(label, strict=True, std3_rules=True).decode("ascii") if not label.isascii() else label
                for label in reads.lower().split(".")
            )
        except (ImportError, UnicodeError, ValueError):
            return True
    return connects != reads.lower()


def is_ambiguous_endpoint(endpoint: Any, *, tls: bool = False) -> bool:
    """True when the host part of an endpoint (a URL, ``host:port``, or a ``dns:`` gRPC target) can be
    read as more than one host: a backslash, a percent sign, white space, a control character or user
    information (``@``) in its authority, an ``@`` in the path, an empty authority (``https:///host``,
    whose host is not read from the path), or two parsers that disagree about the host. An address or
    socket target (``ipv4:``, ``ipv6:``, ``unix:``) has no host name to read. An empty endpoint is no endpoint, and an
    endpoint of only white space is ambiguous. The host is read from the authority: white space or a control character
    in the path is outside this check."""
    text = str(endpoint or "")
    if not text:
        return False  # no endpoint: the caller uses its default
    if text != text.strip():
        # White space around an endpoint, or an endpoint of only white space, is ambiguous, not something to clean
        # up: ``requests`` refuses it.
        return True
    scheme = _GRPC_SCHEME.match(text)
    name = scheme.group(1).lower() if scheme else ""
    if name in _GRPC_NAMED_SCHEMES:
        return False
    if name == "dns":
        rest = text[len("dns:"):]
        if rest.startswith("//"):
            resolver, _, rest = rest[2:].partition("/")
            if _ambiguous(resolver):
                return True
        if not rest:
            return False
        if _ambiguous(rest) or "/" in rest:
            return True
        url = f"https://{rest}"
    else:
        # ``//host[:port]`` is an authority with no scheme.
        url = text if "://" in text else (f"https:{text}" if text.startswith("//") else f"https://{text}")
    after_scheme = url.split("://", 1)[1]
    authority = after_scheme
    for stop in "/?#":
        authority = authority.split(stop, 1)[0]
    # An empty authority has no host to read, and the host is not taken from the path after it; an ``@``
    # anywhere after the scheme is a delimiter some parsers read as user information.
    # An authority with a port and no host (``:4318``) has no host to read either. An ``@`` in the path is read as
    # user information by some parsers, which matters for a plain target; a target that uses TLS (``tls=True``)
    # is judged on its authority, which the parsers read alike.
    return (not authority or authority.startswith(":") or ("@" in after_scheme and not tls) or _ambiguous(authority)
            or _hosts_disagree(url))


def refuse_ambiguous_endpoint(endpoint: Any, *, tls: bool = False) -> None:
    """Raise :class:`fi.errors.ConfigurationError` (code ``insecure_http_origin``) for an ambiguous
    endpoint (see :func:`is_ambiguous_endpoint` for ``tls``). The message is constant and holds no part of
    the endpoint."""
    if is_ambiguous_endpoint(endpoint, tls=tls):
        raise ConfigurationError(AMBIGUOUS_ENDPOINT_MESSAGE, code="insecure_http_origin")


def _host(url: Any) -> str | None:
    """The normalised host an endpoint connects to (a URL, a ``host:port`` pair, or a gRPC target);
    ``None`` when there is none, it is ambiguous, or it does not normalise."""
    text = str(url or "")
    # White space around the text is ambiguous, not something to clean up: ``requests`` refuses such a URL.
    if not text or text != text.strip():
        return None
    scheme = _GRPC_SCHEME.match(text)
    if scheme and scheme.group(1).lower() == "dns":
        return _grpc_target_host(text)
    if scheme and scheme.group(1).lower() in _GRPC_NAMED_SCHEMES:
        return None
    if "://" not in text:
        text = f"https://{text}"
    return _url_host(text)


def _configured_host(name: str) -> str | None:
    value = os.environ.get(name)
    if not str(value or "").strip():
        return None
    host = _host(value)
    if host is None:
        host = _configured_ipv6_host(value)
    if host is None:
        _LOG.warning("%s does not name a valid host, so it is not treated as a Future AGI host.", name)
    return host


def _configured_ipv6_host(value: str) -> str | None:
    """The bracketed IPv6 address a setting names (``[::1]:4317``, ``http://[::ffff:127.0.0.1]:4317``,
    ``dns:///[::1]:4317``, ``dns://resolver/[::1]:4317``, ``ipv6:[::1]:4317``), in the compressed form
    :func:`_plain_grpc_host` gives the address a channel dials, else ``None``. The standard library must read the same
    address from the URL form, and an authority with any other ambiguous character names no address. A loopback
    address written with a zone id (``[::1%25lo]:4317``, ``[::1%lo]:4317``) names the address without it, so a setting
    written that way binds the loopback address as ``[::1]`` does; another address with a zone id names none."""
    text = str(value)
    if text != text.strip():
        return None
    scheme = _GRPC_SCHEME.match(text)
    if scheme and scheme.group(1).lower() == "ipv6":
        # ``ipv6:[//]/[addr]:port``, one address: gRPC drops the query, percent-decodes the path and drops one slash.
        rest = re.split(r"[?#]", text[len("ipv6:"):], maxsplit=1)[0]
        # The slash after an empty authority starts the path, so the path keeps it and one slash is dropped.
        authority, slash, path = rest[2:].partition("/") if rest.startswith("//") else ("", "", rest)
        if not authority:
            return _ipv6_scheme_path_host(slash + path)
        # gRPC dials no ``ipv6://authority`` target; the setting is read as a URL, so ``ipv6://[::1]:4317`` binds
        # ``[::1]`` as ``[::1]:4317`` does.
    begin, stop = _authority_span(text)
    zoned = re.fullmatch(r"\[(?P<address>[0-9A-Fa-f:.]+)(?:%25|%)[A-Za-z0-9_.~-]+\](?P<port>:[0-9]{1,5})?", text[begin:stop])
    if zoned is not None:
        # The setting is read with the zone id taken out of its host; only a loopback address read that way is named.
        host = _configured_ipv6_host(f"{text[:begin]}[{zoned.group('address')}]{zoned.group('port') or ''}{text[stop:]}")
        return host if host is not None and _loopback_host(host) else None
    if scheme and scheme.group(1).lower() == "dns":
        # ``dns:[//resolver/]host[:port]``: the host is the one after the resolver authority, as gRPC reads it.
        rest = text[len("dns:"):]
        if rest.startswith("//"):
            resolver, _, rest = rest[2:].partition("/")
            if _ambiguous(resolver):
                return None
        if not rest or "/" in rest:
            return None
        url = f"https://{rest}"
    elif text.startswith("//"):
        url = f"https:{text}"
    else:
        url = text if "://" in text else f"https://{text}"
    authority = url.split("://", 1)[1]
    for stop in "/?#":
        authority = authority.split(stop, 1)[0]
    if _ambiguous(authority) or not re.fullmatch(r"[A-Za-z][A-Za-z0-9+.-]*", url.split("://", 1)[0]):
        return None
    written = _plain_grpc_written_host(authority)
    address = _ipv6_address(written) if written is not None and ":" in written else None
    try:
        reads = urlsplit(url).hostname
    except ValueError:
        return None
    if address is None or reads is None or _ipv6_address(reads) != address:
        return None
    return str(address)


def _ipv6_scheme_path_host(path: str) -> str | None:
    """The address an ``ipv6:`` setting with no authority names: gRPC percent-decodes the path and drops one slash."""
    path = unquote(path)
    path = path[1:] if path.startswith("/") else path
    match = re.fullmatch(r"\[(?P<address>[0-9A-Fa-f:.]+(?:%[A-Za-z0-9_.~-]+)?)\]:(?P<port>[0-9]{1,5})", path)
    if match is None or not 1 <= int(match.group("port")) <= 65535:
        return None
    return _zoned_loopback(match.group("address"))


def _authority_span(text: str) -> tuple[int, int]:
    """Where the host part of a setting is: after ``scheme://``, ``//`` or a ``dns:`` resolver authority, up to the
    first ``/``, ``?`` or ``#``."""
    begin = 0
    if text[:4].lower() == "dns:":
        begin = 4
        if text.startswith("//", 4):
            slash = text.find("/", 6)
            begin = len(text) if slash < 0 else slash + 1
    elif "://" in text:
        begin = text.index("://") + 3
    elif text.startswith("//"):
        begin = 2
    stops = [index for index in (text.find(char, begin) for char in "/?#") if index >= 0]
    return begin, min(stops, default=len(text))


def _zoned_loopback(address: str) -> str | None:
    """The compressed form of an IPv6 address; one written with a zone id names an address only when it is loopback,
    and it is given without the zone id."""
    plain, percent, zone = address.partition("%")
    parsed = _ipv6_address(plain)
    if parsed is None or (percent and not (zone and _loopback_host(str(parsed)))):
        return None
    return str(parsed)


def future_agi_hosts() -> set[str]:
    """The hosts that are Future AGI: the default hosts, and the hosts named in FI_BASE_URL,
    FI_TRACES_URL and FI_GRPC_URL that normalise."""
    hosts = {_configured_host(name) for name in _HOST_VARIABLES}
    hosts |= {_normalized_host(host) for host in DEFAULT_FUTUREAGI_HOSTS}
    return {host for host in hosts if host}


def is_future_agi_endpoint(endpoint: Any) -> bool:
    """True when ``endpoint`` (a URL, or ``host:port`` for gRPC) is on a Future AGI host."""
    host = _host(endpoint)
    return host is not None and host in future_agi_hosts()


# ``host[:port]``, or a bracketed IPv6 address with an optional zone id (``[2001:db8::1%eth0]``) and an optional port.
_PLAIN_GRPC_TARGET = re.compile(
    r"(?:(?P<host>[A-Za-z0-9_.-]+)|\[(?P<ipv6>[0-9A-Fa-f:.]+(?:%[A-Za-z0-9_.~%-]+)?)\])(?::(?P<port>[0-9]{1,5}))?"
)
_PLAIN_GRPC_FORMS = (
    # host[:port], dns:///host[:port] (an empty authority), http(s)://host[:port][/] and //host[:port]
    re.compile(r"(?:dns:///|(?i:https?)://|//)?(?P<hostport>[A-Za-z0-9_.-]+(?::[0-9]{1,5})?)/?"),
    # the same forms for a bracketed IPv6 address (an IPv4-mapped one included), with no zone id
    re.compile(r"(?:dns:///|(?i:https?)://|//)?(?P<hostport>\[[0-9A-Fa-f:.]+\](?::[0-9]{1,5})?)/?"),
)
INSECURE_GRPC_MESSAGE = (
    "A gRPC exporter for Future AGI always uses TLS, so insecure=True is not accepted for it. "
    "To send without TLS, set the endpoint to your own collector (INSECURE_HTTP_REFUSED)"
)
INSECURE_LOOPBACK_GRPC_MESSAGE = (
    "A gRPC exporter bound to the SDK's keys by FI_BASE_URL, FI_TRACES_URL or FI_GRPC_URL always uses TLS, so "
    "insecure=True is not accepted when that setting names a loopback address. Serve TLS on the collector, or "
    "unset the setting if the keys are not meant for it (insecure_loopback_grpc)"
)
ENDPOINT_TLS_FILE_MESSAGE = (
    "A file named by {name} cannot be read, so no exporter was built. Fix the file or unset {name} (unreadable_tls_file)"
)
INSECURE_HTTP_MESSAGE = (
    "{setting} names a Future AGI host over http://, which is not accepted, so no exporter was built. "
    "Use an https:// address. http:// is accepted for a loopback host, and for a self-hosted target "
    "when FI_ALLOW_INSECURE_HTTP=1 (INSECURE_HTTP_REFUSED)"
)
PLAIN_OPT_IN_ENV = "FI_ALLOW_INSECURE_HTTP"
INSECURE_TARGET_CODE = "insecure_http_origin"
INSECURE_TARGET_MESSAGE = (
    "{setting} names a self-hosted target that would receive the SDK's keys over a plain transport, so nothing "
    "was sent. Put TLS on the collector, or set FI_ALLOW_INSECURE_HTTP=1 on a trusted network "
    "(insecure_http_origin)"
)
_PLAIN_OPT_IN_WARNED = False
_PLAIN_OPT_IN_LOCK = threading.Lock()


def grpc_dial_target(endpoint: Any) -> str:
    """The exact target string the OpenTelemetry gRPC exporter hands to gRPC.

    The exporter (1.39 to 1.45) replaces the endpoint with ``urlparse(endpoint).netloc`` when that is not
    empty and uses the endpoint as given otherwise. gRPC then reads the result with its own target grammar,
    so for ``https://collector.example:4317/path`` the exporter hands gRPC ``collector.example:4317``. Raises
    :class:`ValueError` for text ``urlparse`` cannot read."""
    text = str(endpoint)
    return urlparse(text).netloc or text


def _plain_grpc_written_host(target: str) -> str | None:
    """The host of a ``host[:port]`` or ``dns:///host[:port]`` target exactly as it is written (lower-cased), else
    ``None``. A bracketed IPv6 host is given without its brackets, and only when it is a valid address."""
    rest = target.removeprefix("dns:///")
    match = _PLAIN_GRPC_TARGET.fullmatch(rest)
    if match is None:
        return None
    port = match.group("port")
    if port is not None and not 1 <= int(port) <= 65535:
        return None
    if match.group("ipv6") is not None:
        written = match.group("ipv6").lower()
        return written if _ipv6_address(written) is not None else None
    return match.group("host").lower()


def _ipv6_address(written: str) -> ipaddress.IPv6Address | None:
    try:
        return ipaddress.IPv6Address(written)
    except ValueError:
        return None


def _plain_grpc_host(target: str) -> str | None:
    """The normalised host of a ``host[:port]`` or ``dns:///host[:port]`` target, else ``None``. An IPv6 address is
    given in its compressed form (with its zone id)."""
    written = _plain_grpc_written_host(target)
    if written is None:
        return None
    address = _ipv6_address(written) if ":" in written else None
    return str(address) if address is not None else _normalized_host(written)


def _mentions_future_agi_host(text: str) -> bool:
    lowered = {text.lower(), unquote(text).lower()}
    # An IPv6 address is matched with its brackets, so ``::1`` is not read inside ``[2001:db8::1]``.
    written = {f"[{host}]" if ":" in host else host for host in future_agi_hosts()}
    return any(host in value for host in written for value in lowered)


def _refuse_ambiguous() -> None:
    raise ConfigurationError(AMBIGUOUS_ENDPOINT_MESSAGE, code="insecure_http_origin")


def resolved_http_endpoint() -> str | None:
    """The endpoint an OTLP HTTP trace exporter built with no endpoint uses: the traces setting as given,
    else the general one with ``/v1/traces`` added, else ``None`` (the exporter's own local default).
    A setting that is empty or only white space counts as unset."""
    traces = os.environ.get("OTEL_EXPORTER_OTLP_TRACES_ENDPOINT")
    if traces and traces.strip():
        return traces
    general = os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT")
    if general and general.strip():
        return general.rstrip("/") + "/v1/traces" if not general.endswith("/") else general + "v1/traces"
    return None


def refuse_unreadable_exporter_target(exporter: Any) -> None:
    """Check the target of an OTLP exporter someone else built, the way the SDK checks its own.

    An OpenTelemetry OTLP exporter (HTTP or gRPC) whose endpoint is ambiguous, or whose target cannot be read,
    is refused with :class:`fi.errors.ConfigurationError` (code ``insecure_http_origin``). An exporter of
    any other kind is not the SDK's to read and is left alone."""
    module = type(exporter).__module__ or ""
    if not module.startswith("opentelemetry.exporter.otlp"):
        return
    target = getattr(exporter, "_endpoint", None)
    if not isinstance(target, str) or not target:
        _refuse_ambiguous()
    if ".grpc" in module:
        # ``_endpoint`` already holds the string gRPC received.
        classify_grpc_endpoint(target)
    else:
        refuse_ambiguous_endpoint(target)


def _loopback_host(host: str) -> bool:
    """The one loopback rule (:func:`fi._core.loopback.is_loopback_host`), on the host as it is written, and an
    IPv4-mapped address in 127.0.0.0/8 (:func:`fi._core.loopback.mapped_loopback_address`), which a socket dials to
    this machine."""
    from fi._core.loopback import is_loopback_host, mapped_loopback_address

    return is_loopback_host(host) or mapped_loopback_address(host) is not None


def _is_future_agi_domain(host: str | None) -> bool:
    return host is not None and (host == "futureagi.com" or host.endswith(".futureagi.com"))


def _require_plain_opt_in(setting: str) -> None:
    """Allow a plain transport to a self-managed target, or raise :class:`fi.errors.ConfigurationError` (code
    ``insecure_http_origin``). ``FI_ALLOW_INSECURE_HTTP`` must be exactly ``1``; any other value, including
    ``" 1"`` and ``true``, counts as unset. A transport the SDK builds for such a send ignores the proxy settings of
    the environment (see :func:`plain_session_proxies` and the gRPC channel option in the exporter factory), so
    they do not decide it. The first use logs one warning for the process; the warning holds no host."""
    global _PLAIN_OPT_IN_WARNED
    if os.environ.get(PLAIN_OPT_IN_ENV) != "1":
        raise ConfigurationError(INSECURE_TARGET_MESSAGE.format(setting=setting), code=INSECURE_TARGET_CODE)
    with _PLAIN_OPT_IN_LOCK:
        if _PLAIN_OPT_IN_WARNED:
            return
        _PLAIN_OPT_IN_WARNED = True
    _LOG.warning(
        "%s=1 lets the SDK's keys go to a self-hosted target over a plain transport. Use TLS on the collector "
        "where you can.",
        PLAIN_OPT_IN_ENV,
    )


def refuse_plain_http_futureagi(endpoint: Any, setting: str = "The exporter endpoint", *, keys: bool = False) -> None:
    """Raise :class:`fi.errors.ConfigurationError` for an ``http://`` endpoint that the SDK's keys would reach.

    * an authority that can be read as more than one host (:func:`is_ambiguous_endpoint`): code
      ``insecure_http_origin``. Neither loopback nor a Future AGI host is decided from one parser.
    * ``futureagi.com`` or a host below it: code ``INSECURE_HTTP_REFUSED`` (:class:`fi.errors.InsecureHttpRefusedError`), whatever ``keys`` says. Future AGI
      hosts take https only.
    * with ``keys=True``, another host that is not loopback (a self-managed target): code
      ``insecure_http_origin`` unless :func:`_require_plain_opt_in` allows it. Loopback and ``https://``
      are exempt. Loopback is the host as written: ``localhost.`` and ``127.1`` count as self-managed targets.

    The messages name ``setting`` and hold no part of the endpoint."""
    text = str(endpoint or "")
    if not text.strip().lower().startswith("http://"):
        return
    refuse_ambiguous_endpoint(text)  # white space around the endpoint is refused here
    host = _host(text)
    if _is_future_agi_domain(host):
        from fi._keyed_errors import InsecureHttpRefusedError

        raise InsecureHttpRefusedError(host or "", message=INSECURE_HTTP_MESSAGE.format(setting=setting))
    if not keys:
        return
    try:
        name = (urlsplit(text).hostname or "").lower()
    except ValueError:
        name = "unreadable"  # an authority urlsplit cannot read is not loopback: the opt-in rule applies
    if not name or _loopback_host(name):
        return
    _require_plain_opt_in(setting)


def _cpython_proxied(url: str) -> bool:
    """True when the standard library's reading of the environment routes ``url`` through a proxy: the scheme's own
    ``*_proxy`` is set and ``NO_PROXY`` (read as ``urllib.request.proxy_bypass_environment`` reads it) does not
    list the host. ``ALL_PROXY`` is not a key the standard library applies to a scheme."""
    from urllib.request import getproxies_environment, proxy_bypass_environment

    parts = urlsplit(url)
    proxies = getproxies_environment()
    if not proxies.get(parts.scheme.lower()):
        return False
    host = parts.netloc.rpartition("@")[2]
    return not proxy_bypass_environment(host, proxies)


def session_proxied(session: Any, url: str) -> bool:
    """True when a ``requests`` session that the caller supplied may send ``url`` through a proxy.

    The answer is the union of three readings: the session's own routing (its ``proxies``, the transport adapter it
    uses for the URL, and, while ``trust_env`` is on, the environment as ``requests`` reads it), and the standard
    library's reading of the environment (:func:`_cpython_proxied`). A session whose adapter is not the stock
    ``requests`` HTTP adapter, or that cannot be read at all, counts as proxied: what it does is not visible here."""
    import requests
    import requests.adapters
    from requests.utils import get_environ_proxies, select_proxy

    try:
        adapter = session.get_adapter(url)
        if type(adapter) is not requests.adapters.HTTPAdapter or type(adapter.proxy_manager) is not dict:
            return True
        if select_proxy(url, dict(session.proxies or {})):
            return True
        if getattr(session, "trust_env", True) and select_proxy(url, get_environ_proxies(url, no_proxy=None)):
            return True
        return _cpython_proxied(url)
    except Exception:  # noqa: BLE001 - unknown or uninspectable is proxied
        return True


def carries_key_headers(headers: Mapping[str, str] | None) -> bool:
    """True when ``headers`` holds one of the SDK's key headers, in any form (a mapping, pairs, ``bytes`` names; a name is
    compared with white space removed, in lower case and with ``_`` read as ``-``)."""
    from fi._core.proxy_routing import header_pairs, normalize_header_name

    try:
        return any(normalize_header_name(name) in SDK_KEY_HEADERS for name, _ in header_pairs(headers))
    except Exception:  # noqa: BLE001 - headers that cannot be read count as key headers
        return True


def _grpc_insecure_asked(endpoint: str, insecure: Any) -> bool:
    """Whether the OpenTelemetry gRPC exporter would open a channel without TLS for these arguments: the way it
    reads ``insecure``, then ``OTEL_EXPORTER_OTLP_TRACES_INSECURE`` and ``OTEL_EXPORTER_OTLP_INSECURE``, then the
    scheme."""
    if endpoint.lower().startswith("https://"):
        return False
    if insecure is not None:
        return bool(insecure)
    for name in ("OTEL_EXPORTER_OTLP_TRACES_INSECURE", "OTEL_EXPORTER_OTLP_INSECURE"):
        value = os.environ.get(name)
        if value is not None:
            return value.lower() == "true"
    return endpoint.lower().startswith("http://")


def self_hosted_grpc_target(endpoint: Any) -> bool:
    """True when a gRPC target dials a host that is neither ``futureagi.com`` (or below it) nor loopback. Loopback
    is the host as written; a Future AGI host is matched on its normalised spelling."""
    target = grpc_dial_target(str(endpoint or ""))
    host, written = _plain_grpc_host(target), _plain_grpc_written_host(target)
    return host is not None and not _is_future_agi_domain(host) and not _loopback_host(written or host)


def grpc_loopback_target(endpoint: Any) -> bool:
    """True when a gRPC target dials a loopback host, as written."""
    written = _plain_grpc_written_host(grpc_dial_target(str(endpoint or "")))
    return written is not None and _loopback_host(written)


SDK_KEY_HEADERS = ("x-api-key", "x-secret-key")
_ENV_HEADER_VARIABLES = ("OTEL_EXPORTER_OTLP_TRACES_HEADERS", "OTEL_EXPORTER_OTLP_HEADERS")


def _env_header_names() -> set[str]:
    """The header names in ``OTEL_EXPORTER_OTLP_TRACES_HEADERS`` and ``OTEL_EXPORTER_OTLP_HEADERS``, written as
    :func:`fi._core.proxy_routing.normalize_header_name` writes them; values are not read."""
    names = set()
    for variable in _ENV_HEADER_VARIABLES:
        for pair in os.environ.get(variable, "").split(","):
            if "=" not in pair:
                continue  # OpenTelemetry drops a piece with no "=", so it names no header
            from fi._core.proxy_routing import normalize_header_name

            name = normalize_header_name(unquote(pair.partition("=")[0]))
            if name:
                names.add(name)
    return names


def carries_sdk_keys(headers: Mapping[str, str] | None) -> bool:
    """True when the headers a gRPC exporter sends hold one of the SDK's key headers: the final set is the
    exporter's headers together with the pairs in ``OTEL_EXPORTER_OTLP_TRACES_HEADERS`` and
    ``OTEL_EXPORTER_OTLP_HEADERS``, whichever of them the exporter reads. Headers are read in any form (a mapping, pairs,
    ``bytes`` names); a name is compared with white space removed, in lower case and with ``_`` read as ``-``; values are
    not read."""
    from fi._core.proxy_routing import header_pairs, normalize_header_name

    try:
        names = {normalize_header_name(name) for name, _ in header_pairs(headers)} | _env_header_names()
    except Exception:  # noqa: BLE001 - headers that cannot be read count as key headers
        return True
    return any(name in names for name in SDK_KEY_HEADERS)


def carries_final_credentials(headers: Mapping[str, str] | None) -> bool:
    """True when the headers a gRPC channel sends hold a key or a token: the exporter's final headers together with
    the pairs the exporter reads from ``OTEL_EXPORTER_OTLP_TRACES_HEADERS`` and ``OTEL_EXPORTER_OTLP_HEADERS``.
    Names are compared in lower case; a value of the exporter's own headers that holds ``FI_API_KEY`` or
    ``FI_SECRET_KEY`` from the environment counts as a key too."""
    from fi._core.proxy_routing import carries_credentials

    return carries_credentials(headers or ()) or carries_credentials(_env_header_names())

ENV_KEY_HEADERS_CODE = "otel_env_key_headers"
ENV_KEY_HEADERS_MESSAGE = (
    "OTEL_EXPORTER_OTLP_HEADERS or OTEL_EXPORTER_OTLP_TRACES_HEADERS names a Future AGI key header "
    "(x-api-key or x-secret-key) and the exporter is not bound for Future AGI, so no exporter was built. "
    "Remove the key headers from that setting, or point the exporter at Future AGI (otel_env_key_headers)"
)


def refuse_env_key_headers() -> None:
    """Raise :class:`fi.errors.ConfigurationError` (code ``otel_env_key_headers``) when the OpenTelemetry header
    settings name a Future AGI key header. Called for an exporter that is not bound for Future AGI: such an
    exporter reads those settings, and the keys they hold would go to a collector the SDK did not choose. The
    message names the settings and holds no header value."""
    if any(name in _env_header_names() for name in SDK_KEY_HEADERS):
        raise ConfigurationError(ENV_KEY_HEADERS_MESSAGE, code=ENV_KEY_HEADERS_CODE)


def grpc_plain_choice(endpoint: Any, insecure: Any, setting: str = "The exporter endpoint") -> bool:
    """For a gRPC target that is bound for Future AGI: True when the channel is opened without TLS.

    That is only for a self-managed target (not ``futureagi.com``, not loopback) whose ``insecure`` argument,
    environment or scheme asks for a plain channel, and only when :func:`_require_plain_opt_in` allows it;
    otherwise it raises (code ``insecure_http_origin``). A target whose host cannot be read is judged as a
    target that is neither Future AGI nor loopback. Every other bound target keeps a TLS channel."""
    text = str(endpoint or "")
    try:
        target = grpc_dial_target(text)
    except ValueError:
        target = ""  # a target urlparse cannot read has no host to read
    host, written = _plain_grpc_host(target), _plain_grpc_written_host(target)
    if host is not None and (_is_future_agi_domain(host) or _loopback_host(written or host)):
        return False
    if not _grpc_insecure_asked(text, insecure):
        return False
    _require_plain_opt_in(setting)
    return True


def classify_grpc_endpoint(endpoint: Any) -> bool:
    """True when a gRPC exporter built for ``endpoint`` dials a Future AGI host.

    The class follows the host the channel dials: the target string from :func:`grpc_dial_target`. An
    exporter that dials a Future AGI host is built only for a plain form (``host[:port]``,
    ``dns:///host[:port]``, ``http(s)://host[:port]`` or ``//host[:port]``). Any other form that reads as, or
    names, a Future AGI host is refused with :class:`fi.errors.ConfigurationError` (code
    ``insecure_http_origin``): a ``dns://`` authority, user information, a gRPC target prefix such as
    ``ipv4:`` or ``unix:``, another scheme or letter case, a percent-encoded name. A target that dials
    another host is the user's own, and is not touched."""
    text = str(endpoint or "")
    try:
        target = grpc_dial_target(text)
    except ValueError:
        _refuse_ambiguous()
    dialed = _plain_grpc_host(target)
    bound = dialed is not None and dialed in future_agi_hosts()
    if dialed is None:
        if is_future_agi_endpoint(text) or _mentions_future_agi_host(text):
            _refuse_ambiguous()
        return False
    if bound:
        if not any(form.fullmatch(text) for form in _PLAIN_GRPC_FORMS):
            _refuse_ambiguous()
        return True
    if is_future_agi_endpoint(text):
        # The SDK reads a Future AGI host where the exporter dials another one.
        _refuse_ambiguous()
    return False


#: What an OTLP HTTP exporter reads for TLS: the traces setting, else the general one. ``True``: a directory also works.
_HTTP_TLS_SETTINGS = (
    (("OTEL_EXPORTER_OTLP_TRACES_CERTIFICATE", "OTEL_EXPORTER_OTLP_CERTIFICATE"), True),
    (("OTEL_EXPORTER_OTLP_TRACES_CLIENT_KEY", "OTEL_EXPORTER_OTLP_CLIENT_KEY"), False),
    (("OTEL_EXPORTER_OTLP_TRACES_CLIENT_CERTIFICATE", "OTEL_EXPORTER_OTLP_CLIENT_CERTIFICATE"), False),
)


def http_exporter_endpoint(endpoint: Any, kind: str) -> str:
    """The endpoint an OTLP HTTP exporter of the SDK of type ``kind`` (an ``ExporterType`` value) sends to: ``endpoint``
    when given; else for ``futureagi`` the traces path on ``FI_BASE_URL`` (``https://api.futureagi.com`` when unset);
    else for ``otlp_http`` the local default, and for the other types the endpoint read from the environment
    (:func:`resolved_http_endpoint`), then that default."""
    if endpoint:
        return str(endpoint)
    if kind == "futureagi":
        base = os.environ.get("FI_BASE_URL")
        base = base if base is not None and base.strip() else "https://api.futureagi.com"
        return f"{base.rstrip('/')}/tracer/v1/traces"
    return (resolved_http_endpoint() if kind != "otlp_http" else None) or "http://localhost:4318/v1/traces"


def require_readable_http_tls_files(endpoint: Any = None) -> None:
    """Raise :class:`fi.errors.ConfigurationError` (code ``unreadable_tls_file``) when a TLS file that an OTLP HTTP
    exporter sending to ``endpoint`` uses from the environment cannot be read. The message names the setting and holds
    no part of the path.

    For a plain ``http://`` endpoint the exporter reads no CA certificate and no client key, and those settings are not
    checked; a redirect from it to ``https://`` is stopped by ``requests`` before it connects when the CA file is
    missing. ``requests`` checks that the client certificate file exists on every scheme, so for ``http://`` that
    setting is checked the way ``requests`` checks it. With no endpoint every setting is checked."""
    plain = endpoint is not None and str(endpoint).strip().lower().startswith("http://")
    for names, directory_ok in _HTTP_TLS_SETTINGS:
        name = next((each for each in names if os.environ.get(each)), None)
        if name is None or (plain and not name.endswith("CLIENT_CERTIFICATE")):
            continue
        path = os.environ[name]
        if (directory_ok and os.path.isdir(path)) or (plain and os.path.exists(path)):
            continue
        try:
            with open(path, "rb"):
                pass
        except OSError:
            raise ConfigurationError(
                ENDPOINT_TLS_FILE_MESSAGE.format(name=name), code="unreadable_tls_file"
            ) from None


def futureagi_grpc_credentials() -> Any:
    """Channel credentials for a gRPC exporter bound for Future AGI.

    The gRPC exporters load a credential provider named in
    ``OTEL_PYTHON_EXPORTER_OTLP_GRPC_[TRACES_]CREDENTIAL_PROVIDER`` whenever the caller passes no
    credentials (``_get_credentials`` in ``exporter.py``, 1.39 and 1.45), and a provider's call
    credentials add their own metadata to every export. A Future AGI exporter passes these instead: TLS,
    read as the OpenTelemetry trace exporter reads it. Only when ``OTEL_EXPORTER_OTLP_TRACES_CERTIFICATE``
    names a file are that certificate and the files named in ``OTEL_EXPORTER_OTLP_TRACES_CLIENT_KEY`` and
    ``OTEL_EXPORTER_OTLP_TRACES_CLIENT_CERTIFICATE`` used; the generic ``OTEL_EXPORTER_OTLP_*`` variables
    are not read, as upstream does not read them for traces either."""
    import grpc

    def read(name: str) -> bytes | None:
        path = os.environ.get(name)
        if not path:
            return None
        try:
            with open(path, "rb") as handle:
                return handle.read()
        except OSError:
            # The message names the variable and holds no part of the path.
            raise ConfigurationError(
                ENDPOINT_TLS_FILE_MESSAGE.format(name=name), code="unreadable_tls_file"
            ) from None

    root = read("OTEL_EXPORTER_OTLP_TRACES_CERTIFICATE")
    if root is None:
        return grpc.ssl_channel_credentials(root_certificates=None, private_key=None, certificate_chain=None)
    return grpc.ssl_channel_credentials(
        root_certificates=root,
        private_key=read("OTEL_EXPORTER_OTLP_TRACES_CLIENT_KEY"),
        certificate_chain=read("OTEL_EXPORTER_OTLP_TRACES_CLIENT_CERTIFICATE"),
    )


class _NoAuth:
    """An auth that adds nothing. A session with an ``auth`` set is not given netrc credentials for its first request,
    and a :class:`fi._core.requests_session.LoopbackDirectSession` with this auth reads none on a redirect either."""

    skips_netrc = True

    def __call__(self, request: Any) -> Any:
        return request


def _session_of(exporter: Any) -> Any:
    session = getattr(exporter, "_session", None)  # 1.39
    if session is None:
        session = getattr(getattr(getattr(exporter, "_client", None), "_transport", None), "_session", None)  # 1.45
    return session


def _stop_netrc(exporter: Any) -> None:
    session = _session_of(exporter)
    if session is not None and getattr(session, "auth", None) is None:
        session.auth = _NoAuth()


_REDIRECT_ERROR: Any = None


def redirect_not_followed_error() -> Any:
    """The error class (a :class:`requests.RequestException` with ``code == "redirect_not_followed"``) raised
    when a request that carries the SDK's keys is answered with a redirect."""
    global _REDIRECT_ERROR
    if _REDIRECT_ERROR is None:
        import requests

        class RedirectNotFollowed(requests.RequestException):
            code = "redirect_not_followed"

        _REDIRECT_ERROR = RedirectNotFollowed
    return _REDIRECT_ERROR


def refuse_redirect(response: Any) -> None:
    """Close ``response`` and raise :func:`redirect_not_followed_error` when it is a redirect."""
    history = getattr(response, "history", None)
    if getattr(response, "is_redirect", False) is True or (isinstance(history, list) and history):
        response.close()
        raise redirect_not_followed_error()(
            "The server answered with a redirect, which is not followed for a request that carries the SDK's keys "
            "(redirect_not_followed)"
        )


def plain_session_proxies(url: Any) -> dict[str, None] | None:
    """The ``proxies`` argument that sends an ``http://`` request to ``url`` directly: every scheme is mapped to
    ``None``, which ``requests`` reads as "no proxy" whatever the environment holds. ``None`` for any other URL,
    which preserves the configured proxy settings, including TLS tunnels through a proxy."""
    if str(url).lower().startswith("http://"):
        return {"http": None, "https": None, "all": None}
    return None


def futureagi_session(plain: bool = False) -> Any:
    """A fresh ``requests`` session for an HTTP exporter bound for Future AGI.

    Pass it as ``session=`` so the exporter does not build one from a credential provider in the
    environment. It does not follow redirects: an answer that is a redirect fails the export. It keeps
    ``trust_env``, so the proxy and certificate settings the user configured apply, and netrc
    credentials do not: the session has an auth that does nothing, which is also what :func:`pin_headers`
    gives the session of any exporter it pins.

    Only the SDK's own ``requests`` HTTP adapter can be mounted on it: ``mount`` and replacing
    ``adapters`` raise :class:`fi.errors.ConfigurationError` for any other adapter, since an adapter
    subclass can follow a redirect inside its own ``send``. The ``adapters`` dict is guarded in place
    too: it refuses to store any other adapter (``adapters[prefix] = ...``, ``update``, ``setdefault``,
    ``|=``) and to drop the ones it holds (``clear``, ``pop``, ``popitem``, ``del``), and a copy of the
    session (``copy.copy``, ``copy.deepcopy``) keeps the same guard.

    An answer that is a redirect fails the export with :class:`requests.RequestException` rather than
    counting as accepted, since the exporters treat any status below 400 as delivered."""
    import requests
    import requests.adapters

    def accepted(adapter: Any) -> None:
        # An adapter subclass can follow a redirect inside its own ``send``, past the check in the
        # session's ``send``. Only the SDK's own adapter type is accepted.
        if type(adapter) is not requests.adapters.HTTPAdapter:
            raise ConfigurationError(_ADAPTER_REFUSAL, code="unsupported_session_adapter")

    class GuardedAdapters(collections.OrderedDict):
        """The session's adapters: only plain HTTP adapters go in, and none come out once locked.

        ``requests`` reorders the dict while it mounts (it pops and re-stores shorter prefixes), so the
        session's own ``mount`` opens it for the thread that is mounting. The guard covers the public
        mapping API of the session; it does not stop code in the same process that calls the base class
        methods directly."""

        _locked = False
        _mounting_thread: int | None = None

        def lock(self) -> None:
            self._locked = True

        def _removal(self) -> None:
            if self._locked and self._mounting_thread != threading.get_ident():
                raise ConfigurationError(_ADAPTER_REFUSAL, code="unsupported_session_adapter")

        def mounting(self) -> Any:
            guarded = self

            class Open:
                def __enter__(self) -> None:
                    guarded._mounting_thread = threading.get_ident()

                def __exit__(self, *exc: object) -> None:
                    guarded._mounting_thread = None

            return Open()

        def __setitem__(self, prefix: Any, adapter: Any) -> None:
            accepted(adapter)
            super().__setitem__(prefix, adapter)

        def update(self, *args: Any, **kwargs: Any) -> None:  # type: ignore[override]
            incoming = dict(*args, **kwargs)
            for adapter in incoming.values():
                accepted(adapter)
            for prefix, adapter in incoming.items():
                self[prefix] = adapter

        def setdefault(self, prefix: Any, default: Any = None) -> Any:
            if prefix not in self:
                self[prefix] = default
            return self[prefix]

        def __ior__(self, other: Any) -> Any:
            self.update(other)
            return self

        def __delitem__(self, prefix: Any) -> None:
            self._removal()
            super().__delitem__(prefix)

        def clear(self) -> None:
            self._removal()
            super().clear()

        def pop(self, *args: Any) -> Any:  # type: ignore[override]
            self._removal()
            return super().pop(*args)

        def popitem(self, last: bool = True) -> Any:
            self._removal()
            return super().popitem(last)

        def move_to_end(self, key: Any, last: bool = True) -> None:
            self._removal()
            super().move_to_end(key, last)

    class FutureAgiSession(requests.Session):
        _sealed = False

        def __init__(self) -> None:
            super().__init__()
            # An auth that does nothing: ``requests`` adds netrc credentials only to a request with none.
            self.auth = _NoAuth()
            self._seal()

        def _seal(self) -> None:
            self._adapters.lock()
            self._sealed = True

        def __setstate__(self, state: Any) -> None:
            # A copy is built without ``__init__``; it is sealed again once its state is in place, and
            # its adapters go through the same check as any others.
            self._sealed = False
            super().__setstate__(state)
            self._seal()

        @property
        def adapters(self) -> Any:
            return self._adapters

        @adapters.setter
        def adapters(self, value: Any) -> None:
            # ``requests`` sets this once while it builds the session; after that, replacing the
            # adapters would swap in transports this SDK did not build.
            if self._sealed:
                raise ConfigurationError(_ADAPTER_REFUSAL, code="unsupported_session_adapter")
            guarded = GuardedAdapters()
            guarded.update(value)
            self._adapters = guarded

        def mount(self, prefix: str, adapter: Any) -> None:
            accepted(adapter)
            with self._adapters.mounting():
                super().mount(prefix, adapter)

        def resolve_redirects(self, response: Any, request: Any, *args: Any, yield_requests: bool = False, **kw: Any) -> Any:
            # With redirects off, an unreadable ``Location`` leaves ``Response.next`` unset, so ``send`` refuses the answer.
            from fi._core.requests_session import readable_next

            redirects = super().resolve_redirects(response, request, *args, yield_requests=yield_requests, **kw)
            return readable_next(redirects) if yield_requests else redirects

        def send(self, request: Any, **kwargs: Any) -> Any:
            # Every method (get, post, request, send) ends here, whatever the caller passed.
            kwargs["allow_redirects"] = False
            if plain and (direct := plain_session_proxies(request.url)) is not None:
                kwargs["proxies"] = direct
            from fi._core.requests_session import is_redirect_answer

            response = super().send(request, **kwargs)
            if is_redirect_answer(response) or response.history:
                response.close()
                raise redirect_not_followed_error()(
                    "Future AGI answered with a redirect, which is not followed (redirect_not_followed)"
                )
            return response

    return FutureAgiSession()


_ADAPTER_REFUSAL = (
    "A session that sends to Future AGI accepts only the SDK's own requests HTTPAdapter. "
    "Remove the adapter you mounted, or use the session with its own adapters (unsupported_session_adapter)"
)


def _transport_defaults() -> dict[str, str]:
    try:
        from opentelemetry.exporter.otlp.proto.http import _OTLP_HTTP_HEADERS
    except ImportError:
        return dict(_FALLBACK_DEFAULTS)
    return {key.lower(): value for key, value in _OTLP_HTTP_HEADERS.items()}


def _compression_value(compression: Any) -> str | None:
    value = getattr(compression, "value", None)
    return value if isinstance(value, str) and value.lower() not in ("none", "") else None


def _refusal_message(exporter: Any) -> str:
    """Names the exporter class and package version, and the supported range; no header values."""
    from importlib.metadata import PackageNotFoundError, version

    kind = "grpc" if "grpc" in type(exporter).__module__ else "http"
    package = f"opentelemetry-exporter-otlp-proto-{kind}"
    try:
        installed = f" {version(package)}"
    except PackageNotFoundError:
        installed = ""
    return (
        f"Cannot send traces to Future AGI with {type(exporter).__name__} from {package}{installed}: "
        "its header handling is not one this SDK can set, so settings from OTEL_EXPORTER_OTLP_HEADERS "
        f"could reach Future AGI; supported versions are {SUPPORTED_EXPORTER_VERSIONS} (unsupported_otlp_exporter)"
    )


def pin_headers(exporter: Any, headers: Mapping[str, str] | None) -> Any:
    """Make ``exporter`` send exactly ``headers`` (plus its transport's own); return ``exporter``."""
    from fi._core.proxy_routing import header_pairs, header_text

    wanted = {header_text(key).lower(): value for key, value in header_pairs(headers)}

    client = getattr(exporter, "_client", None)
    if isinstance(getattr(client, "_headers", None), dict):  # HTTP exporter, 1.45 and later
        pinned = _transport_defaults()
        encoding = _compression_value(getattr(client, "_compression", None))
        if encoding:
            pinned["content-encoding"] = encoding
        pinned.update(wanted)
        client._headers = pinned
        _stop_netrc(exporter)
        return exporter

    session = getattr(exporter, "_session", None)
    if session is not None and isinstance(getattr(exporter, "_headers", None), dict):  # HTTP exporter, 1.39
        for key in list(exporter._headers):
            session.headers.pop(key, None)
        session.headers.pop("Content-Encoding", None)
        session.headers.update(_transport_defaults())
        encoding = _compression_value(getattr(exporter, "_compression", None))
        if encoding:
            session.headers["Content-Encoding"] = encoding
        session.headers.update(wanted)
        exporter._headers = dict(wanted)
        _stop_netrc(exporter)
        return exporter

    if isinstance(getattr(exporter, "_headers", None), tuple):  # gRPC exporter
        exporter._headers = tuple(wanted.items())
        return exporter

    raise ConfigurationError(_refusal_message(exporter), code="unsupported_otlp_exporter")
