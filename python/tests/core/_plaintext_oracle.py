"""Shared parts of the sealed plain-HTTP and proxy rule oracle tests: the vendored oracle, the loopback listeners with
byte counters, and the driver that sends one row the SDK's own way (see test_plaintext_oracle_conformance)."""

from __future__ import annotations

import os as _os

_os.environ.setdefault("GRPC_DNS_RESOLVER", "native")  # the loopback names below resolve through the system resolver

import collections
import gzip
import hashlib
import itertools
import json
import os
import socket
import socketserver
import threading
from pathlib import Path
from typing import Any, Iterator, Optional
from unittest import mock

import httpx
import pytest

from fi._credentials import Credentials
from fi._http import ClientRetryingTransport, LazyKeyAuth
from fi.errors import ConfigurationError

FIXTURE = Path(__file__).resolve().parents[3] / "tests" / "fixtures" / "plaintext-oracle" / "plaintext-rule-oracle.json.gz"
GZ_SHA256 = "bb75798b5c34c68e428ca9b31a17c8df33bfdede43844dd36ff728f70552d1eb"
JSON_SHA256 = "c2072ae9e74dc80543e10fabaf54da26554bf12d3033c7bbe46067cf8aac4f1e"
MARKER_KEY = "FIMARKERKEY-7f3a91c2"
MARKER_SECRET = "FIMARKERSECRET-5d08be44"
MARKERS = (MARKER_KEY.encode(), MARKER_SECRET.encode())
PROXY_NAMES = ("HTTP_PROXY", "http_proxy", "HTTPS_PROXY", "https_proxy", "ALL_PROXY", "all_proxy", "NO_PROXY", "no_proxy",
               "GRPC_PROXY", "grpc_proxy", "FI_ALLOW_INSECURE_HTTP", "REQUEST_METHOD")
TRANSPORTS = ("http", "eval-config")  # the oracle's transports for httpx and requests; the gRPC rows are driven in the exporter test
# The three plain-HTTP sources (the URL's scheme, the insecure argument, the OTEL insecure env) reach the SDK as the
# same final state (the decision uses the final key set), so one is driven and the others are checked
# against it at the oracle level.
DRIVEN_SOURCE = "http_scheme"

RAW = gzip.decompress(FIXTURE.read_bytes())
ORACLE = json.loads(RAW)
HOSTS = ORACLE["dimensions"]["hosts"]
ENV_VALUES = ORACLE["dimensions"]["env_values"]
OPT_IN = ORACLE["dimensions"]["opt_in"]
CALLERS = ORACLE["dimensions"]["callers"]

# The SDK rejects plain HTTP and plain gRPC URLs with an @ in the path, query or fragment; the oracle
# sees one host across parsers and allows those URLs with the opt-in. TLS rows match the oracle.
# Only the rows without TLS count as exceptions.
RULING = "at sign after authority without TLS"
RULED_EXCEPTION_HOSTS = {"s1_at_in_path": RULING}
RULED_EXCEPTIONS: dict[str, str] = {}
# Hosts written in a form the 0.8.1 line refuses whatever the opt-in says (a trailing dot, or an IPv4 address in a short,
# decimal, hex or octal form). This SDK follows 0.8.1 there, where the sealed oracle builds
# with the opt-in: such a cell counts only when the SDK refuses it with no byte at any sink and no connection.
SPELLING_HOSTS = frozenset({"wnl_127_1", "wnl_127_dot", "wnl_decimal", "wnl_hex", "wnl_localhost_dot", "wnl_octal"})


def is_spelling_refusal(row: dict, outcome: str, counts: Optional[dict] = None, dialed: Optional[str] = None) -> bool:
    """Whether a cell of :data:`SPELLING_HOSTS` was refused before any byte or connection (the 0.8.1 rule)."""
    return (row["host"] in SPELLING_HOSTS and str(outcome).startswith("refused")
            and not any((counts or {}).values()) and dialed is None)


def is_excepted(row: dict, scheme: str = "http") -> bool:
    """Whether the cell qualifies for an exception by ID or host. TLS cells are ineligible."""
    return scheme != "https" and (row_id(row) in RULED_EXCEPTIONS or row["host"] in RULED_EXCEPTION_HOSTS)


def row_id(row: dict) -> str:
    return "|".join(str(row[k]) for k in ("transport", "host", "source", "opt_in", "caller", "env", "no_proxy"))


class Sink:
    """A loopback listener that counts every byte it receives, keeps them, and responds with a configured status."""

    def __init__(self, status: bytes = b"200 OK", location: Optional[str] = None) -> None:
        sink = self
        self.status, self.location = status, location
        self.chunks: list[bytes] = []
        self.requests = 0

        class Handler(socketserver.BaseRequestHandler):
            def handle(self) -> None:
                self.request.settimeout(1.0)
                data = b""
                try:
                    while b"\r\n\r\n" not in data:
                        chunk = self.request.recv(65536)
                        if not chunk:
                            break
                        data += chunk
                    head = data.split(b"\r\n\r\n", 1)[0]
                    length = 0
                    for line in head.split(b"\r\n")[1:]:
                        if line.lower().startswith(b"content-length:"):
                            length = int(line.split(b":", 1)[1])
                    body = data.split(b"\r\n\r\n", 1)[1] if b"\r\n\r\n" in data else b""
                    while len(body) < length:
                        more = self.request.recv(65536)
                        if not more:
                            break
                        data += more
                        body += more
                except OSError:
                    pass
                sink.chunks.append(data)
                sink.requests += 1
                extra = f"Location: {sink.location}\r\n".encode() if sink.location else b""
                try:
                    self.request.sendall(b"HTTP/1.1 " + sink.status + b"\r\n" + extra +
                                         b"Content-Length: 2\r\nConnection: close\r\n\r\n{}")
                except OSError:
                    pass

        self.server = socketserver.ThreadingTCPServer(("127.0.0.1", 0), Handler)
        self.server.daemon_threads = True
        self.port = self.server.server_address[1]
        threading.Thread(target=self.server.serve_forever, kwargs={"poll_interval": 0.01}, daemon=True).start()

    def reset(self) -> None:
        self.chunks.clear()
        self.requests = 0

    @property
    def marker_bytes(self) -> int:
        blob = b"".join(self.chunks)
        return sum(blob.count(marker) for marker in MARKERS)

    def close(self) -> None:
        self.server.shutdown()
        self.server.server_close()


@pytest.fixture(scope="module")
def sinks() -> Iterator[dict[str, Sink]]:
    made = {"target": Sink(), "sinkA": Sink(status=b"502 Bad Gateway"), "sinkB": Sink(status=b"502 Bad Gateway")}
    real = socket.create_connection

    def to_loopback(address: tuple, *args: Any, **kwargs: Any) -> socket.socket:
        # a getaddrinfo shim: every name or address the SDK dials is this machine, on the port asked for
        return real(("127.0.0.1", address[1]), *args, **kwargs)

    with mock.patch("socket.create_connection", to_loopback):
        yield made
    for each in made.values():
        each.close()


def _noproxy_env(case: str, authority: str, port: int) -> dict[str, str]:
    host = authority.replace("{T}", "0")
    host = host.rsplit(":", 1)[0] if host.count(":") == 1 or host.endswith(":0") else host
    host = host.strip("[]")
    labels = host.split(".")
    bare = ".".join(labels[-2:]) if len(labels) >= 2 and not host.replace(".", "").isdigit() else host
    return {
        "none": {}, "exact": {"NO_PROXY": host}, "bare": {"NO_PROXY": bare}, "dot_suffix": {"NO_PROXY": "." + bare},
        "star": {"NO_PROXY": "*"}, "host_port": {"NO_PROXY": f"{host}:{port}"}, "cidr": {"NO_PROXY": "127.0.0.0/8,10.0.0.0/8"},
        "empty_both": {"no_proxy": "", "NO_PROXY": ""},
    }[case]


def _expand(row: dict) -> Iterator[tuple[str, str, Optional[str], str]]:
    """The (scheme, opt-in value name, opt-in value, caller) cells a row stands for: '*' is every value."""
    schemes = ["https", "http"] if row["source"] == "*" else ["https" if row["source"] == "tls" else "http"]
    opts = list(OPT_IN) if row["opt_in"] == "*" else [row["opt_in"]]
    callers = list(CALLERS) if row["caller"] == "*" else [row["caller"]]
    for scheme, opt, caller in itertools.product(schemes, opts, callers):
        yield scheme, opt, OPT_IN[opt], caller


class Opaque(httpx.BaseTransport):
    """A caller's transport the SDK cannot see into."""

    def handle_request(self, request: httpx.Request) -> httpx.Response:
        with httpx.HTTPTransport() as inner:  # held nowhere: nothing to look into before the send
            return inner.handle_request(request)


def _send(url: str, caller: str, sinks: dict[str, Sink]) -> str:
    """One key-carrying request the SDK's own way; 'refused' when the SDK stops it before any byte."""
    creds = Credentials(api_key=MARKER_KEY, secret_key=MARKER_SECRET, base_url=url, keys_source="argument", base_url_source="argument")
    auth = LazyKeyAuth(lambda: creds)
    kwargs: dict[str, Any] = {"auth": auth, "timeout": 1.5, "follow_redirects": False}
    if caller == "none":
        kwargs["transport"] = ClientRetryingTransport(retries=0)
    elif caller == "client_with_proxy":
        kwargs["transport"] = httpx.HTTPTransport(proxy=f"http://127.0.0.1:{sinks['sinkA'].port}")
    else:
        kwargs["transport"] = Opaque()
    try:
        with httpx.Client(**kwargs) as client:
            try:
                client.build_request("GET", url)
            except Exception:
                # the sending library cannot make a request of this URL, so no byte can leave; the SDK's own
                # decision on the URL as written is what is compared (a base URL goes through it first)
                from fi._core.http_security import check_http_security

                check_http_security(url, "keys", caller_proxied=caller != "none", proxies_disabled=caller == "none")  # type: ignore[arg-type]
                return "unsendable"
            client.get(url)
    except ConfigurationError as exc:
        return "refused:" + _oracle_error(str(exc))
    except (httpx.TransportError, httpx.InvalidURL):
        # the library failed before the SDK's check ran (a URL it cannot send) or the dial failed: the SDK's own decision
        # on the URL as written still applies
        try:
            from fi._core.http_security import check_http_security

            check_http_security(url, "keys", caller_proxied=caller != "none", proxies_disabled=caller == "none")  # type: ignore[arg-type]
        except ConfigurationError as exc:
            return "refused:" + _oracle_error(str(exc))
        return "sent"
    except Exception as exc:  # anything else is a defect of the path under test, not an outcome
        return f"error:{type(exc).__name__}"
    return "sent"


def _oracle_error(message: str) -> str:
    if "has no host" in message:
        return "empty_authority"
    if "backslash" in message or "@ after the host" in message or "user info" in message:
        return "disputed_authority"
    if "does not apply to a Future AGI host" in message:
        return "insecure_futureagi_http"
    if "proxy" in message:
        return "proxied"
    if "or set FI_ALLOW_INSECURE_HTTP=1." in message:
        return "insecure_self_hosted_target"
    return "other:" + message[:60]


def _drive(row: dict, scheme: str, opt_value: Optional[str], caller: str, sinks: dict[str, Sink]) -> tuple[str, Optional[str], dict[str, int]]:
    host = HOSTS[row["host"]]
    target = sinks["target"]
    authority = host["authority"].replace("{T}", str(target.port))
    url = f"{scheme}://{authority}{host['path']}"
    env: dict[str, str] = {}
    for name, value in ENV_VALUES[row["env"]].items():
        env[name] = value.replace("{A}", str(sinks["sinkA"].port)).replace("{B}", str(sinks["sinkB"].port))
    env.update(_noproxy_env(row["no_proxy"], host["authority"], target.port))
    if opt_value is not None:
        env["FI_ALLOW_INSECURE_HTTP"] = opt_value
    for each in sinks.values():
        each.reset()
    cleaned = {k: v for k, v in os.environ.items() if k not in PROXY_NAMES}
    with mock.patch.dict(os.environ, {**cleaned, **env}, clear=True):
        outcome = _send(url, caller, sinks)
    counts = {name: each.marker_bytes for name, each in sinks.items()}
    dialed = None
    if sinks["target"].requests:
        dialed = "target"
    if sinks["sinkA"].requests or sinks["sinkB"].requests:
        dialed = "proxy"
    return outcome, dialed, counts


def _plain_rows() -> list[dict]:
    return [r for r in ORACLE["rows"] if r["transport"] == "http" and r["source"] in (DRIVEN_SOURCE, "*")]


def _cells(row: dict) -> tuple:
    return tuple(row[k] for k in ("host", "opt_in", "caller", "env", "no_proxy"))


def _tls_rows() -> list[dict]:
    return [r for r in ORACLE["rows"] if r["transport"] == "http" and r["source"] in ("tls", "*")]


def _check(row: dict, outcome: str, dialed: Optional[str], counts: dict[str, int], cell: tuple) -> Optional[str]:
    rid = row_id(row)
    if is_excepted(row, "http" if row.get("tls") is False else "https"):
        # A ruled cell is not matched to the oracle: the SDK refuses it (the authority is disputed), sends no byte and opens no connection.
        if outcome != "refused:disputed_authority":
            return f"{rid} {cell}: ruled cell answered {outcome}, expected refused:disputed_authority"
        if any(counts.values()) or dialed is not None:
            return f"{rid} {cell}: ruled cell reached a sink {counts} (dialed {dialed})"
        return None
    if row["decision"] == "refuse":
        want = "refused:" + row["error"]
        if outcome != want:
            return f"{rid} {cell}: SDK {outcome}, oracle {want}"
        if any(counts.values()):
            return f"{rid} {cell}: marker bytes at a sink {counts}"
    else:
        if outcome not in ("sent", "unsendable"):
            return f"{rid} {cell}: SDK {outcome}, oracle build"
        if outcome == "sent" and row["tls"] is False and dialed != row["dialed"]:
            return f"{rid} {cell}: dialed {dialed}, oracle {row['dialed']}"
    return None


__all__ = ['CALLERS', 'DRIVEN_SOURCE', 'ENV_VALUES', 'FIXTURE', 'GZ_SHA256', 'HOSTS', 'JSON_SHA256', 'MARKERS', 'MARKER_KEY', 'MARKER_SECRET', 'OPT_IN', 'ORACLE', 'Opaque', 'PROXY_NAMES', 'RAW', 'RULED_EXCEPTIONS', 'RULED_EXCEPTION_HOSTS', 'RULING', 'SPELLING_HOSTS', 'Sink', 'TRANSPORTS', '_cells', '_check', '_drive', '_expand', '_noproxy_env', '_oracle_error', '_plain_rows', '_send', '_tls_rows', 'is_excepted', 'is_spelling_refusal', 'row_id', 'sinks']
