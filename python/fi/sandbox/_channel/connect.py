"""From a mint reply to a connection: the URL and subprotocols to offer, the ``Origin`` to send,
how a refused upgrade becomes a sandbox error, and the argv rule checked before any request."""

from __future__ import annotations

import inspect
import json
import logging
import re
from dataclasses import InitVar, dataclass
from urllib.parse import urlsplit
from typing import Any, Callable, ClassVar, List, Mapping, Optional, Tuple

import httpx
from fi import errors as e
from fi._core.loopback import LOCALHOST_ADDRESSES, is_localhost_name, is_loopback_host
from fi._core.redact import scrub_value
from fi._core.transport import MAX_ERROR_BODY

from ..channel_errors import ChannelProtocolError, clean_server_text, is_unsafe_text_char
from ..errors import ConfigurationError, translate
from . import constants as c

OPERATION = "sandboxes.commands.execStream"
MINT_OPERATION = "sandboxes.commands.channelToken"


def origin_of(url: Any) -> str:
    """``scheme://host[:port]`` of an API base URL: what a non-browser client sends as ``Origin``
    (no path, the default port left out)."""
    parsed = httpx.URL(str(url))
    host = parsed.host
    if ":" in host:
        host = f"[{host}]"
    port = f":{parsed.port}" if parsed.port is not None else ""
    return f"{parsed.scheme}://{host}{port}"


@dataclass(frozen=True, eq=False)
class ConnectionPlan:
    """What to connect to: ``url`` and the ``origin`` header, plus the ``protocols`` to offer
    (exactly the reply's) and the ``token`` (kept only to scrub it from any message). The token is
    one of the protocols, so both are held in a closure rather than in a field: ``repr``, ``str``,
    ``dataclasses.asdict`` and ``vars`` show neither, and reading them is for connecting. Plans
    compare by identity, since their fields do not hold all they connect with."""

    _held: ClassVar[Callable[[], Tuple[Tuple[str, ...], str]]]
    url: str
    origin: str
    secret: InitVar[Tuple[List[str], str]]

    def __post_init__(self, secret: Tuple[List[str], str]) -> None:
        protocols, token = tuple(secret[0]), secret[1]
        object.__setattr__(self, "_held", lambda: (protocols, token))

    @property
    def protocols(self) -> List[str]:
        return list(self._held()[0])

    @property
    def token(self) -> str:
        return self._held()[1]


class _TokenFilter(logging.Filter):
    """Drops a record that holds the data token's protocol entry, whatever its level."""

    def filter(self, record: logging.LogRecord) -> bool:
        return c.TOKEN_PROTOCOL_PREFIX not in record.getMessage()


def socket_logger() -> logging.Logger:
    """The logger a channel connection hands to ``websockets``. The library logs the handshake
    headers at DEBUG, and ``Sec-WebSocket-Protocol`` carries the data token, so this logger keeps
    DEBUG off and drops any record that holds the token entry. It is scoped to channel
    connections: the ``websockets`` loggers themselves are not touched, and warnings and errors
    reach the handlers the application set up."""
    logger = logging.getLogger("fi.sandbox.channel.websocket")
    logger.setLevel(logging.INFO)
    if not any(isinstance(f, _TokenFilter) for f in logger.filters):
        logger.addFilter(_TokenFilter())
    return logger


def keepalive_options(connect: Callable[..., Any]) -> Mapping[str, Any]:
    """No library keepalive pings. The server defers its pongs while the client owes it output
    credit, so a ping timeout would close a slow reader's connection (1011) in the middle of a
    transfer. Liveness is the transport's own: TCP, the server's close frames and the reader's
    errors. websockets 16 has no client keepalive to turn off; 17 sets it on by default."""
    accepted = inspect.signature(connect).parameters
    return {k: None for k in ("ping_interval", "ping_timeout") if k in accepted}


def _is_loopback(host: str) -> bool:
    """Whether a channel URL's own host is the local machine (``fi._core.loopback``, the one rule). The API
    URL's scheme does not matter: only the host the token travels to does."""
    return is_loopback_host(host)


def proxy_options(connect: Callable[..., Any], url: str) -> Mapping[str, Any]:
    """No environment proxy for a channel on a loopback host (:func:`_is_loopback`, the one rule),
    ``ws://`` or ``wss://``: the data token travels in the handshake's ``Sec-WebSocket-Protocol``
    header, and a credential meant for this machine is not handed to a proxy because ``HTTP_PROXY``
    or ``ALL_PROXY`` is set (over ``ws://`` it would also cross unencrypted). websockets 15 and later
    read those variables by default (``proxy=True``) and take ``proxy=None`` to connect directly; an
    older version has no such option and reads no proxy. A ``wss://`` channel on another host keeps the
    library default: a proxy gets a ``CONNECT`` tunnel and the token stays inside TLS."""
    try:
        host = urlsplit(url).hostname
    except ValueError:
        host = None
    if host is not None and _is_loopback(host) and "proxy" in inspect.signature(connect).parameters:
        return {"proxy": None}
    return {}


def localhost_dials(url: str, *, asynchronous: bool) -> list[Mapping[str, Any]]:
    """The connection options to try, in order, for a channel URL. The name ``localhost`` is dialed to 127.0.0.1,
    then ``::1``, and not to what the system resolver answers; the URL's own host names the server in the
    handshake and in the certificate check. Any other host has one entry with no options."""
    try:
        parts = urlsplit(url)
        host, port = parts.hostname, parts.port
    except ValueError:
        return [{}]
    if not is_localhost_name(host):
        return [{}]
    port = port or (443 if parts.scheme.lower() == "wss" else 80)
    return [{"host": a, "port": port} if asynchronous else {"address": (a, port)} for a in LOCALHOST_ADDRESSES]


def next_address_may_answer(error: BaseException) -> bool:
    """Whether a failed dial of one loopback address leaves the other worth trying: the connection was refused, or
    the address family is not available. A TLS or handshake failure is the server's answer and ends the attempt."""
    import errno
    import ssl

    if isinstance(error, ssl.SSLError):
        return False
    return isinstance(error, ConnectionRefusedError) or (
        isinstance(error, OSError) and error.errno in (errno.ENETUNREACH, errno.EHOSTUNREACH, errno.EADDRNOTAVAIL, errno.EAFNOSUPPORT)
    )


_PORT = re.compile(r"[0-9]{1,5}")


def _port_problem(url: str) -> Optional[str]:
    """Why the port in ``url``'s authority is refused, or ``None`` when it has none or a usable one. The port is
    whatever follows the last ``:`` outside brackets; it must be 1 to 5 ASCII digits, 1 to 65535."""
    rest = url.split("://", 1)[1] if "://" in url else url
    authority = re.split(r"[/?#]", rest, maxsplit=1)[0].rsplit("@", 1)[-1]
    if authority.startswith("["):
        end = authority.find("]")
        tail = authority[end + 1 :] if end >= 0 else ""
        if end < 0 or (tail != "" and not tail.startswith(":")):
            return "the host in brackets is not closed before the port"
        port = tail[1:] if tail else None
    elif ":" in authority:
        port = authority.rsplit(":", 1)[1]
    else:
        port = None
    if port is None:
        return None
    if _PORT.fullmatch(port) is None:
        return "a port is 1 to 5 ASCII digits (1-65535), with no sign, space, separator or empty form"
    if int(port) == 0:
        return "port 0 cannot be connected to (use 1-65535)"
    if int(port) > 65535:
        return "a port is a number from 1 to 65535"
    return None


def _checked(reply: Any, api_url: Any) -> Any:
    """The :class:`ConnectionPlan` for a mint reply, or the error to raise for it. This returns the
    error instead of raising it, so the frame that raises not held the token in a local."""
    channel = reply.get("channel") if isinstance(reply, Mapping) else None
    transport = channel.get("transport") if isinstance(channel, Mapping) else None
    url = channel.get("url") if isinstance(channel, Mapping) else None
    token = channel.get("token") if isinstance(channel, Mapping) else None
    protocols = transport.get("protocols") if isinstance(transport, Mapping) else None
    if (
        not isinstance(url, str)
        or not isinstance(token, str)
        or not isinstance(protocols, list)
        or not all(isinstance(p, str) for p in protocols)
    ):
        return ChannelProtocolError("the channel token reply has no url, token or transport protocols")
    if c.SUBPROTOCOL not in protocols or (c.TOKEN_PROTOCOL_PREFIX + token) not in protocols:
        return ChannelProtocolError("the channel token reply's protocols do not carry the token")
    try:
        parsed = httpx.URL(url)
    except httpx.InvalidURL:
        return ChannelProtocolError("the channel url is not a valid url")
    if parsed.query or parsed.fragment or parsed.userinfo:
        return ChannelProtocolError("the channel url must carry no query, fragment or credential")
    # The check and the connection must name one host: websockets reads the URL with urllib, this check
    # with httpx. A host the two read differently is refused, and so is one outside ASCII (an IDN: the
    # name that is resolved is not the name that was checked), not guessed.
    try:
        connecting = urlsplit(url).hostname
    except ValueError:
        connecting = None
    if connecting is None or not connecting.isascii() or connecting != parsed.host.strip("[]"):
        return ChannelProtocolError("the channel url names a host that is not read the same way everywhere")
    # The port is read here, from the authority, and not through urlsplit: that accepts forms ('+80', ' 80',
    # '8_0') a connection would read differently. It is 1 to 5 ASCII digits naming 1-65535; port 0 cannot be
    # connected to.
    problem = _port_problem(url)
    if problem is not None:
        return ChannelProtocolError(f"the channel url's port is refused: {problem}")
    if parsed.scheme != "wss" and not (parsed.scheme == "ws" and _is_loopback(parsed.host)):
        return ConfigurationError(
            f"refusing to open the channel over {parsed.scheme}://: the token would travel in plain text "
            "(the channel url must be wss://, or ws:// to a loopback host)",
            code="insecure_channel_origin",
            operation=OPERATION,
        )
    return ConnectionPlan(url, origin_of(httpx.URL(str(api_url))), (list(protocols), token))


def plan(reply: Mapping[str, Any], api_url: Any) -> ConnectionPlan:
    """The connection for a mint reply (the response body: ``{"channel": {...}}``). The client does
    not build the URL: it connects to ``channel.url`` and offers exactly ``transport.protocols``.
    The reply's URL must be ``wss://``, or ``ws://`` when the channel URL's own host is loopback
    (``localhost``, 127.0.0.0/8, ``::1``; no other spelling of them): whatever the API URL's scheme is, the token does not cross
    plain text to another host. A refusal is raised from this frame after the reply is dropped, so no
    frame of its traceback holds the token."""
    outcome = _checked(reply, api_url)
    del reply
    if isinstance(outcome, BaseException):
        raise outcome
    return outcome


def check_argv(argv: Any) -> List[str]:
    """``argv`` as a list of strings the contract accepts: 1 to 512 strings, no NUL, ``argv[0]`` a
    non-empty program name that does not start with ``-``. A string is refused (it is a list: the
    server runs it with every argument quoted, nothing is split or interpreted by a shell)."""
    problem = None
    if isinstance(argv, (str, bytes)) or not isinstance(argv, (list, tuple)):
        problem = "argv is a list of strings (one program and its arguments), not one string"
    elif not 1 <= len(argv) <= c.MAX_ARGV:
        problem = f"argv holds 1 to {c.MAX_ARGV} strings, not {len(argv)}"
    elif not all(isinstance(item, str) for item in argv):
        problem = "every argv item is a string"
    elif any("\x00" in item for item in argv):
        problem = "an argv item holds a NUL character"
    elif not argv[0] or argv[0].startswith("-"):
        problem = "argv[0] is a program name: not empty and not starting with -"
    if problem:
        raise ConfigurationError(f"exec_stream: {problem}", code="invalid_argv", operation=OPERATION)
    return list(argv)


def check_options(cwd: Any, env: Any, timeout_seconds: Any) -> None:
    if cwd is not None and not isinstance(cwd, str):
        raise ConfigurationError("exec_stream: cwd is a string", code="invalid_option", operation=OPERATION)
    if env is not None and not (
        isinstance(env, Mapping) and all(isinstance(k, str) and isinstance(v, str) for k, v in env.items())
    ):
        raise ConfigurationError(
            "exec_stream: env maps variable names to string values", code="invalid_option", operation=OPERATION
        )
    if timeout_seconds is not None and (
        isinstance(timeout_seconds, bool) or not isinstance(timeout_seconds, int) or timeout_seconds <= 0
    ):
        raise ConfigurationError(
            "exec_stream: timeout_seconds is a whole number above 0", code="invalid_option", operation=OPERATION
        )


def _scrubbed_json(value: Any, scrub: Callable[[str], str], depth: int = 0) -> Any:
    """``value`` with every text passed through ``scrub``, control characters dropped and each text
    cut to the server-text cap: what a refusal payload keeps of the server's answer."""
    if isinstance(value, str):
        return clean_server_text(value, scrub)
    if depth > 6:
        return None
    if isinstance(value, Mapping):
        return {clean_server_text(k, scrub): _scrubbed_json(v, scrub, depth + 1) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_scrubbed_json(v, scrub, depth + 1) for v in value]
    return value


def refusal(
    status: int,
    body: Any,
    headers: Mapping[str, str],
    scrub: Callable[[str], str],
    operation: str = OPERATION,
) -> BaseException:
    """The sandbox error for a refused upgrade (the HTTP answer on the socket: 400, 401, 403, 404,
    409, 429 ...), its text and payload passed through ``scrub``."""
    try:
        payload = json.loads(body) if body else None
    except (ValueError, UnicodeDecodeError):
        payload = None
    payload = _scrubbed_json(payload, scrub)
    nested = payload.get("error") if isinstance(payload, Mapping) else None
    source = nested if isinstance(nested, Mapping) else (payload if isinstance(payload, Mapping) else {})
    code = source.get("code") if isinstance(source.get("code"), str) else None
    said = source.get("message") if isinstance(source.get("message"), str) else None
    text = f"{operation} failed with status {status}" + (f" ({code})" if code else "")
    text += f": {said}" if said else ""
    error = e.FutureAGIAPIError(
        status,
        payload,
        code=code,
        message=text,
        request_id=headers.get("x-request-id"),
        operation=operation,
    )
    return translate(error, operation)


def stream_refusal(error: Any, operation: str = OPERATION, scrub: Optional[Callable[[str], str]] = None) -> BaseException:
    """The sandbox error for a stream's ``error`` frame (``StreamError``): the contract's code
    stands for an HTTP status (``validation`` 400, ``conflict`` 409, ``rate_limited`` 429 ...). The
    server's message and detail pass through ``scrub`` (when given) and the server-text cap."""
    status = c.STREAM_ERROR_STATUS.get(error.code, 500)
    keep = scrub if scrub is not None else (lambda text: text)
    message = clean_server_text(error.message, keep)
    detail = _scrubbed_json(error.detail, keep) if error.detail is not None else None
    payload = {"error": {"code": error.code, "message": message, "detail": detail}}
    raised = e.FutureAGIAPIError(
        status,
        payload,
        code=error.code,
        message=f"{operation} failed with status {status} ({error.code}): {message}",
        operation=operation,
    )
    return translate(raised, operation)


def scrubber(shared: Any, token: str) -> Callable[[str], str]:
    """What the server's text passes through before an error or a caller sees it: unsafe characters
    dropped, the executor's error scrubber over the origin's secrets and the data token, then the
    error-body length cap."""
    secrets = [*shared.origin().secrets, token]
    scrub = shared.error_scrubber or scrub_value

    def private(text: str) -> str:
        # Unsafe characters go first, so a token they split is whole when the scrub looks for it.
        plain = "".join(ch for ch in text if not is_unsafe_text_char(ch))
        clean = scrub(plain, secrets)
        clean = clean if isinstance(clean, str) else str(clean)
        return clean.encode("utf-8")[:MAX_ERROR_BODY].decode("utf-8", "replace")

    return private
