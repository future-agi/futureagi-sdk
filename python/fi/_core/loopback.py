"""The one rule for "this host is the local machine", shared by the platform transport, the sandbox channel, the gateway
clients, the requests session, tracing export and the plain-HTTP policy."""

from __future__ import annotations

import ipaddress
import socket
from typing import Any, Iterable, Optional

import httpcore
import httpx

LOCALHOST_ADDRESSES = ("127.0.0.1", "::1")


def is_loopback_host(host: str) -> bool:
    """Whether a URL's own host is the local machine: the exact name ``localhost``, an address in
    127.0.0.0/8 or ``::1``. ``host`` is the parsed host (any case, with or without brackets). A name with a
    trailing dot is not ``localhost``: it would go to name resolution."""
    name = host.strip("[]").lower()
    if name == "localhost":
        return True
    try:
        address = ipaddress.ip_address(name)
    except ValueError:
        return False  # not an address as written: a dotted address, a short form and a name all land here
    # An IPv4-mapped IPv6 address is refused, whatever the Python version says about it.
    if isinstance(address, ipaddress.IPv4Address):
        return address in ipaddress.ip_network("127.0.0.0/8")
    return address == ipaddress.IPv6Address("::1")


def mapped_loopback_address(host: str) -> Optional[str]:
    """The IPv4 address of ``host`` when it is an IPv4-mapped IPv6 address in 127.0.0.0/8 (``::ffff:127.x.y.z``, with
    or without brackets, no zone id), else ``None``. A socket dials such an address to that IPv4 address on this
    machine. The plain channels of the trace exporters take it as loopback; :func:`is_loopback_host`, the table shared
    with the TypeScript client, does not."""
    try:
        mapped = None if "%" in host else ipaddress.IPv6Address(host.strip("[]")).ipv4_mapped
    except ValueError:
        return None
    return str(mapped) if mapped is not None and mapped in ipaddress.ip_network("127.0.0.0/8") else None


def unmapped_loopback_url(text: str) -> str:
    """``text`` (``scheme://authority...``) with a host written as an IPv4-mapped loopback address in brackets written
    as its IPv4 address (:func:`mapped_loopback_address`); any other text is returned as it is."""
    scheme, separator, rest = text.partition("://")
    host, bracket, tail = rest[1:].partition("]") if rest.startswith("[") else ("", "", "")
    address = mapped_loopback_address(host) if separator and bracket else None
    return f"{scheme}://{address}{tail}" if address is not None else text


def is_loopback_url(url: httpx.URL) -> bool:
    """:func:`is_loopback_host` for the host httpx connects to, as written: the trailing dot of a name is kept."""
    return is_loopback_host(url.raw_host.decode("ascii", "replace"))

def is_localhost_name(host: Optional[str]) -> bool:
    """Whether ``host`` is the name ``localhost`` as written (any case, brackets ignored). Such a name is dialed to
    :data:`LOCALHOST_ADDRESSES`, not to what the system resolver answers; ``localhost.`` and ``app.localhost``
    are other names."""
    return host is not None and host.strip("[]").lower() == "localhost"


class LocalhostBackend(httpcore.NetworkBackend):
    """An ``httpcore`` network backend that dials the name ``localhost`` to 127.0.0.1, then ``::1``, without asking the
    system resolver. The origin of the request, so the ``Host`` header, the TLS server name and the certificate check,
    stays as the caller wrote it. The wrapped backend receives any other host as supplied."""

    def __init__(self, inner: httpcore.NetworkBackend) -> None:
        self._inner = inner

    def connect_tcp(self, host: str, port: int, timeout: Optional[float] = None,
                    local_address: Optional[str] = None, socket_options: Optional[Iterable[Any]] = None) -> Any:
        if not is_localhost_name(host):
            return self._inner.connect_tcp(host, port, timeout=timeout, local_address=local_address,
                                           socket_options=socket_options)
        failure: Optional[BaseException] = None
        for address in LOCALHOST_ADDRESSES:
            try:
                return self._inner.connect_tcp(address, port, timeout=timeout, local_address=local_address,
                                               socket_options=socket_options)
            except httpcore.ConnectError as error:
                failure = error
        assert failure is not None
        raise failure

    def connect_unix_socket(self, path: str, timeout: Optional[float] = None,
                            socket_options: Optional[Iterable[Any]] = None) -> Any:
        return self._inner.connect_unix_socket(path, timeout=timeout, socket_options=socket_options)

    def sleep(self, seconds: float) -> None:
        self._inner.sleep(seconds)


class AsyncLocalhostBackend(httpcore.AsyncNetworkBackend):
    """:class:`LocalhostBackend` for an ``httpcore`` async connection pool."""

    def __init__(self, inner: httpcore.AsyncNetworkBackend) -> None:
        self._inner = inner

    async def connect_tcp(self, host: str, port: int, timeout: Optional[float] = None,
                          local_address: Optional[str] = None, socket_options: Optional[Iterable[Any]] = None) -> Any:
        if not is_localhost_name(host):
            return await self._inner.connect_tcp(host, port, timeout=timeout, local_address=local_address,
                                                 socket_options=socket_options)
        failure: Optional[BaseException] = None
        for address in LOCALHOST_ADDRESSES:
            try:
                return await self._inner.connect_tcp(address, port, timeout=timeout, local_address=local_address,
                                                     socket_options=socket_options)
            except httpcore.ConnectError as error:
                failure = error
        assert failure is not None
        raise failure

    async def connect_unix_socket(self, path: str, timeout: Optional[float] = None,
                                  socket_options: Optional[Iterable[Any]] = None) -> Any:
        return await self._inner.connect_unix_socket(path, timeout=timeout, socket_options=socket_options)

    async def sleep(self, seconds: float) -> None:
        await self._inner.sleep(seconds)


def pin_localhost(transport: Any) -> Any:
    """Make an httpx transport dial the name ``localhost`` to 127.0.0.1, then ``::1`` (:class:`LocalhostBackend`).
    A transport that holds no connection pool of its own is returned as it is."""
    pool = getattr(transport, "_pool", None)
    backend = getattr(pool, "_network_backend", None)
    if isinstance(backend, httpcore.AsyncNetworkBackend):
        pool._network_backend = AsyncLocalhostBackend(backend)
    elif isinstance(backend, httpcore.NetworkBackend):
        pool._network_backend = LocalhostBackend(backend)
    return transport


def localhost_connection(port: int, timeout: Any, source_address: Any, socket_options: Any) -> socket.socket:
    """A connected TCP socket to ``localhost``'s port: 127.0.0.1, then ``::1``."""
    from urllib3.util.connection import create_connection

    failure: Optional[BaseException] = None
    for address in LOCALHOST_ADDRESSES:
        try:
            return create_connection((address, port), timeout, source_address=source_address,
                                     socket_options=socket_options)
        except socket.timeout:
            raise
        except OSError as error:
            failure = error
    assert failure is not None
    raise failure


def grpc_channel_options(endpoint: str | None, *, plaintext: bool = False) -> tuple[tuple[str, int], ...]:
    """The gRPC channel options a connection to ``endpoint`` (``host:port`` or a URL) needs: none for a remote
    host, which keeps ``grpc_proxy`` / ``http_proxy`` and ``no_proxy``; ``grpc.enable_http_proxy=0`` for a
    loopback host, so the connection goes straight to this machine. A ``plaintext`` channel the SDK builds also
    gets ``grpc.enable_http_proxy=0``, whatever the host: the exporter passes ``plaintext`` for a plain channel that
    carries keys, and such a channel is not routed through a proxy."""
    from urllib.parse import urlsplit

    if plaintext:
        return (("grpc.enable_http_proxy", 0),)
    target = endpoint or ""
    target = target if "://" in target else "//" + target
    try:
        host = urlsplit(target).hostname or ""
    except ValueError:
        return ()
    return (("grpc.enable_http_proxy", 0),) if is_loopback_host(host) else ()


def _localhost_family(port: int) -> str:
    """The loopback address a channel to ``localhost`` on ``port`` dials: 127.0.0.1, and ``::1`` when nothing accepts on
    127.0.0.1 and something accepts on ``::1``. The attempts open and close a connection; no byte is sent."""
    for address, family in (("127.0.0.1", socket.AF_INET), ("::1", socket.AF_INET6)):
        try:
            with socket.socket(family, socket.SOCK_STREAM) as probe:
                probe.settimeout(0.5)
                probe.connect((address, port))
            return address
        except OSError:
            continue
    return LOCALHOST_ADDRESSES[0]


def grpc_dial_target(endpoint: Optional[str]) -> tuple[Optional[str], tuple[tuple[str, str], ...]]:
    """The gRPC target and channel options for ``endpoint`` (``host:port`` or a URL). For the name ``localhost`` the
    target names a loopback address (:data:`LOCALHOST_ADDRESSES`) so the system resolver is not asked, and the options
    keep the authority and the certificate name as written (``localhost``). Any other endpoint is returned as given,
    with no options."""
    from urllib.parse import urlsplit

    if not endpoint:
        return endpoint, ()
    text = endpoint if "://" in endpoint else "//" + endpoint
    try:
        parts = urlsplit(text)
        host, port = parts.hostname, parts.port
    except ValueError:
        return endpoint, ()
    if not is_localhost_name(host) or parts.username is not None or parts.password is not None:
        return endpoint, ()
    address = _localhost_family(port or 443)
    netloc = f"[{address}]" if ":" in address else address
    if port is not None:
        netloc += f":{port}"
    rebuilt = parts._replace(netloc=netloc).geturl()
    rebuilt = rebuilt if "://" in endpoint else rebuilt[2:]
    authority = "localhost" + (f":{port}" if port is not None else "")
    return rebuilt, (("grpc.default_authority", authority), ("grpc.ssl_target_name_override", "localhost"))


def dial_localhost_channels(exporter_class: Any) -> Any:
    """``exporter_class`` as it is for an HTTP exporter. For an OTLP gRPC exporter class, a subclass whose channel to the
    name ``localhost`` dials 127.0.0.1 or ``::1`` (:func:`grpc_dial_target`), whatever the system resolver answers."""
    if ".grpc." not in getattr(exporter_class, "__module__", "") and ".grpc." not in getattr(
            exporter_class.__mro__[1], "__module__", ""):
        return exporter_class

    class _Dialing(exporter_class):  # type: ignore[misc, valid-type]
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            if isinstance(kwargs.get("endpoint"), str):
                kwargs["endpoint"], options = grpc_dial_target(kwargs["endpoint"])
                if options:
                    kwargs["channel_options"] = (*(kwargs.get("channel_options") or ()), *options)
            super().__init__(*args, **kwargs)

    _Dialing.__name__ = _Dialing.__qualname__ = exporter_class.__name__
    return _Dialing
