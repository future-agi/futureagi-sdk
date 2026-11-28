#!/usr/bin/env python3
"""Equality of the Python keyed senders across two source trees (a released line and this one).

Every keyed sender the released line has is driven through the same scenarios against loopback listeners only: a
``socket.getaddrinfo`` shim maps three names (Future AGI, a self-managed instance, and another origin) to
127.0.0.1, any other non-loopback name is refused and counted, and no real host is contacted. Planted marker keys are
counted as raw bytes at every sink (the target, the redirect target, a CONNECT-aware proxy) together with the connections
each sink accepted.

Modes:

    keyed_sender_equality.py emit OUT.json                       # run in the tree on PYTHONPATH
    keyed_sender_equality.py compare A.json B.json               # a table of A vs B, exit 1 on an unexplained difference
    keyed_sender_equality.py run OLD_PYTHON_DIR NEW_PYTHON_DIR   # emit for both trees, then compare

A cell records the outcome (the exception class, its error code, the status; or "sent"), the names of the SDK error
classes the exception is an instance of (what an ``except`` clause of the older line catches), and the sink counts.
A difference between the two trees is reported with a reason when it is one of

  base-class      the newer exception has the same code and is an instance of every class the older one was, and more;
  flag-exact-1    a plain-http send to a non-loopback, non-Future-AGI host reaches the host only with
                  FI_ALLOW_INSECURE_HTTP exactly "1" (the older line sent without it);
  refined-code    the newer outcome carries an error code and reaches no sink the older one did not (a refusal that
                  names its code, or one that reaches fewer sinks);
  direct-send     the older line sent through a proxy and the newer one sends straight to the host (loopback, or a
                  plain-http send with FI_ALLOW_INSECURE_HTTP exactly "1"): no proxy receives bytes or a connection;
  stricter        a documented stricter refusal (STRICTER below).

Any other difference is "UNEXPLAINED".
"""

from __future__ import annotations

import asyncio
import contextlib
import datetime
import json
import os
import select
import socket
import socketserver
import ssl
import subprocess
import sys
import tempfile
import threading
import warnings
from typing import Any, Callable, Optional

warnings.filterwarnings("ignore")

API_MARKER = "FIKEYAPI-7f3a91c2d4e8"
SECRET_MARKER = "FIKEYSECRET-b52e08a61d9c"
FI_HOST = "api.futureagi.com"
SELF_HOST = "gw.selfhosted.example"
SECOND_HOST = "second.other.example"
SHIMMED = {FI_HOST, SELF_HOST, SECOND_HOST, "a.b.futureagi.com", "api.futureagi.com.lookalike.example"}
ENV_NAMES = ("HTTP_PROXY", "http_proxy", "HTTPS_PROXY", "https_proxy", "ALL_PROXY", "all_proxy", "NO_PROXY", "no_proxy",
             "FI_ALLOW_INSECURE_HTTP", "REQUESTS_CA_BUNDLE", "CURL_CA_BUNDLE", "SSL_CERT_FILE", "SSL_CERT_DIR",
             "FI_BASE_URL", "FI_API_KEY", "FI_SECRET_KEY", "FI_PLATFORM_BASE_URL", "FI_GATEWAY_URL", "FI_GATEWAY_API_KEY",
             "AGENTCC_API_KEY", "AGENTCC_BASE_URL", "REQUEST_METHOD")

# Documented stricter refusals of the newer line: (sender prefix, scenario id) -> reason (each is in python/CHANGELOG.md).
# A difference not covered by a rule is reported as UNEXPLAINED.
STRICTER: dict[tuple[str, str], str] = {
    ("gateway", "answer-304-without-location"): "the gateway clients and helpers refuse every 3xx answer to a keyed request",
    ("gateway", "plain-loopback-userinfo"): "the gateway clients and helpers refuse a base URL with user info",
    ("gateway", "plain-loopback-userinfo-flag1"): "the gateway clients and helpers refuse a base URL with user info",
    ("httpclient", "plain-loopback-userinfo"): "every sender refuses a base URL with user info",
    ("httpclient", "plain-loopback-userinfo-flag1"): "every sender refuses a base URL with user info",
    ("kb-", "plain-loopback-userinfo"): "every sender refuses a base URL with user info",
    ("kb-", "plain-loopback-userinfo-flag1"): "every sender refuses a base URL with user info",
    ("platform", "plain-loopback-userinfo"): "every sender refuses a base URL with user info",
    ("platform", "plain-loopback-userinfo-flag1"): "every sender refuses a base URL with user info",
    ("httpclient", "plain-fi-fullwidth-idna"): "a Future AGI name httpx cannot encode is refused with ConfigurationError",
    ("kb-", "plain-fi-fullwidth-idna"): "a Future AGI name httpx cannot encode is refused with ConfigurationError",
    ("platform", "plain-fi-fullwidth-idna"): "a Future AGI name httpx cannot encode is refused by httpx before any byte (InvalidURL)",
    ("platform", "caller-client-mock-transport-plain-loopback"): "an httpx.MockTransport reaches no network, so it is not read as a proxy",
}


class Sink:
    """A loopback listener: counts connections and raw marker bytes, answers each connection by ``respond``."""

    def __init__(self, respond: Callable[[str], bytes], tls: Optional[ssl.SSLContext] = None, connect_tunnel: bool = False) -> None:
        self.received = bytearray()
        self.connections = 0
        self.connects = 0
        self.lock = threading.Lock()
        self.tunnel_to: Optional[int] = None
        outer = self

        class Handler(socketserver.BaseRequestHandler):
            def handle(self) -> None:
                conn = self.request
                if tls is not None:
                    try:
                        conn = tls.wrap_socket(conn, server_side=True)
                    except (OSError, ssl.SSLError):
                        return
                conn.settimeout(3)
                data = b""
                try:
                    while b"\r\n\r\n" not in data:
                        chunk = conn.recv(65536)
                        if not chunk:
                            break
                        data += chunk
                    head, _, body = data.partition(b"\r\n\r\n")
                    line = head.split(b"\r\n")[0].decode("latin-1", "replace")
                    if connect_tunnel and line.startswith("CONNECT "):
                        with outer.lock:
                            outer.connections += 1
                            outer.connects += 1
                            outer.received.extend(data)
                        outer.tunnel(conn)
                        return
                    length = 0
                    for each in head.split(b"\r\n")[1:]:
                        name, _, value = each.partition(b":")
                        if name.strip().lower() == b"content-length":
                            length = int(value.strip() or 0)
                    while len(body) < length:
                        chunk = conn.recv(65536)
                        if not chunk:
                            break
                        body += chunk
                        data += chunk
                    with outer.lock:
                        outer.connections += 1
                        outer.received.extend(data)
                    conn.sendall(respond(line))
                except (OSError, ssl.SSLError):
                    with outer.lock:
                        outer.received.extend(data)

        class Server(socketserver.ThreadingTCPServer):
            daemon_threads = True
            allow_reuse_address = True

        self.server = Server(("127.0.0.1", 0), Handler)
        self.port = self.server.server_address[1]
        threading.Thread(target=self.server.serve_forever, kwargs={"poll_interval": 0.01}, daemon=True).start()

    def tunnel(self, client: socket.socket) -> None:
        """CONNECT: answer 200 and pipe to the loopback port the proxy was told to reach; the bytes are counted raw."""
        if self.tunnel_to is None:
            client.sendall(b"HTTP/1.1 502 Bad Gateway\r\nContent-Length: 0\r\nConnection: close\r\n\r\n")
            return
        upstream = socket.create_connection(("127.0.0.1", self.tunnel_to), timeout=3)
        client.sendall(b"HTTP/1.1 200 Connection established\r\n\r\n")
        pair = [client, upstream]
        try:
            while True:
                ready, _, _ = select.select(pair, [], [], 3)
                if not ready:
                    break
                for src in ready:
                    chunk = src.recv(65536)
                    if not chunk:
                        return
                    if src is client:
                        with self.lock:
                            self.received.extend(chunk)
                    (upstream if src is client else client).sendall(chunk)
        except OSError:
            pass
        finally:
            upstream.close()

    def markers(self) -> int:
        raw = bytes(self.received)
        return raw.count(API_MARKER.encode()) + raw.count(SECRET_MARKER.encode())

    def close(self) -> None:
        self.server.shutdown()
        self.server.server_close()


def _ok(line: str) -> bytes:
    path = line.split(" ")[1] if " " in line else ""
    if "chat/completions" in path:
        body = b'data: {"id":"c","object":"chat.completion.chunk","created":1,"model":"m","choices":[]}\n\ndata: [DONE]\n\n'
        ctype = b"text/event-stream"
    elif "/files/" in path:
        body, ctype = b"file-bytes", b"application/octet-stream"
    else:
        body = b'{"status": true, "result": {}, "object": "list", "data": []}'
        ctype = b"application/json"
    return b"HTTP/1.1 200 OK\r\nContent-Type: %s\r\nContent-Length: %d\r\nConnection: close\r\n\r\n%s" % (ctype, len(body), body)


def _redirect(status: int, location: Callable[[], str]) -> Callable[[str], bytes]:
    return lambda _line: b"HTTP/1.1 %d Redirect\r\nLocation: %s\r\nContent-Length: 0\r\nConnection: close\r\n\r\n" % (status, location().encode())


class Authority:
    """A certificate authority and one server certificate for the shimmed names, made with ``cryptography``."""

    def __init__(self, directory: str) -> None:
        from cryptography import x509
        from cryptography.hazmat.primitives import hashes, serialization
        from cryptography.hazmat.primitives.asymmetric import rsa
        from cryptography.x509.oid import NameOID

        now = datetime.datetime.now(datetime.timezone.utc)
        ca_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        ca_name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "compat-harness-ca")])
        ca = (x509.CertificateBuilder().subject_name(ca_name).issuer_name(ca_name).public_key(ca_key.public_key())
              .serial_number(x509.random_serial_number()).not_valid_before(now - datetime.timedelta(days=1))
              .not_valid_after(now + datetime.timedelta(days=2)).add_extension(x509.BasicConstraints(ca=True, path_length=None), True)
              .sign(ca_key, hashes.SHA256()))
        key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        sans = [x509.DNSName(name) for name in sorted(SHIMMED)] + [x509.DNSName("localhost")]
        cert = (x509.CertificateBuilder().subject_name(x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, FI_HOST)]))
                .issuer_name(ca_name).public_key(key.public_key()).serial_number(x509.random_serial_number())
                .not_valid_before(now - datetime.timedelta(days=1)).not_valid_after(now + datetime.timedelta(days=2))
                .add_extension(x509.SubjectAlternativeName(sans), False).sign(ca_key, hashes.SHA256()))
        self.ca_path = os.path.join(directory, "ca.pem")
        self.cert_path = os.path.join(directory, "server.pem")
        self.key_path = os.path.join(directory, "server.key")
        with open(self.ca_path, "wb") as fh:
            fh.write(ca.public_bytes(serialization.Encoding.PEM))
        with open(self.cert_path, "wb") as fh:
            fh.write(cert.public_bytes(serialization.Encoding.PEM))
        with open(self.key_path, "wb") as fh:
            fh.write(key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.TraditionalOpenSSL, serialization.NoEncryption()))

    def server_context(self) -> ssl.SSLContext:
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.load_cert_chain(self.cert_path, self.key_path)
        return context


REFUSED_NAMES: list[str] = []
real_getaddrinfo = socket.getaddrinfo


def _numeric_loopback(name: str) -> bool:
    """A numeric spelling the system resolver itself reads as an address in 127.0.0.0/8 (127.1, 0x7f.0.0.1, 2130706433)."""
    try:
        return socket.inet_aton(name)[0] == 127
    except OSError:
        return False


def _shim(host: Any, *args: Any, **kwargs: Any) -> Any:
    name = host.decode("ascii", "replace") if isinstance(host, bytes) else host
    if isinstance(name, str):
        bare = name.lower().rstrip(".")
        if bare in SHIMMED or bare in ("localhost", "127.0.0.1"):
            return real_getaddrinfo("127.0.0.1", *args, **kwargs)
        if not _numeric_loopback(bare) and bare != "::1":
            REFUSED_NAMES.append(bare)
            raise socket.gaierror(f"harness: refused to resolve {bare}")
    return real_getaddrinfo(host, *args, **kwargs)


# host: loopback | self | fi, or "hostname" (the host exactly as written in the URL; "b" marks a plain-http host that is
# neither written-loopback nor a Future AGI name, which the newer line sends to only with the opt-in "1");
# scheme: http | https ; redirect: same | cross ; caller: plain | proxy | env | mock ; retries: client retry count
def _forms() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for ident, name, kind in (
        ("fi-trailing-dot", "api.futureagi.com.", "fi"), ("fi-upper-case", "API.FutureAGI.com", "fi"),
        ("fi-fullwidth-idna", "\uff41pi.futureagi.com", "fi"), ("fi-subdomain", "a.b.futureagi.com", "fi"),
        ("fi-userinfo", "user:pw@api.futureagi.com", "fi"), ("fi-lookalike-suffix", "api.futureagi.com.lookalike.example", "b"),
        ("loopback-127.1", "127.1", "b"), ("loopback-hex", "0x7f.0.0.1", "b"), ("loopback-decimal", "2130706433", "b"),
        ("loopback-octal", "0177.0.0.1", "b"), ("loopback-trailing-dot", "127.0.0.1.", "b"),
        ("localhost", "localhost", "loop"), ("localhost-upper", "LOCALHOST", "b"), ("localhost-trailing-dot", "localhost.", "b"),
        ("loopback-userinfo", "user:pw@127.0.0.1", "loop"),
    ):
        base: dict[str, Any] = {"id": "plain-" + ident, "hostname": name}
        if kind == "b":
            base["b"] = True
        rows.append(base)
        if kind in ("b", "loop"):
            rows.append({**base, "id": "plain-" + ident + "-flag1", "env": {"FI_ALLOW_INSECURE_HTTP": "1"}, "b": False})
    return rows


SCENARIOS: list[dict[str, Any]] = [
    {"id": "plain-loopback", "host": "loopback"},
    {"id": "plain-loopback-uppercase-scheme", "host": "loopback", "scheme_text": "HTTP"},
    {"id": "plain-nonloopback-noflag", "host": "self", "b": True},
    {"id": "plain-nonloopback-flag1", "host": "self", "env": {"FI_ALLOW_INSECURE_HTTP": "1"}},
    {"id": "plain-nonloopback-flag-true", "host": "self", "env": {"FI_ALLOW_INSECURE_HTTP": "true"}, "b": True},
    {"id": "plain-nonloopback-flag-0", "host": "self", "env": {"FI_ALLOW_INSECURE_HTTP": "0"}, "b": True},
    {"id": "plain-nonloopback-flag-1-space", "host": "self", "env": {"FI_ALLOW_INSECURE_HTTP": "1 "}, "b": True},
    {"id": "plain-fi-noflag", "host": "fi"},
    {"id": "plain-fi-flag1", "host": "fi", "env": {"FI_ALLOW_INSECURE_HTTP": "1"}},
    {"id": "plain-fi-uppercase-scheme", "host": "fi", "scheme_text": "HTTP"},
    *_forms(),
    {"id": "redirect-same-origin-302", "host": "loopback", "redirect": "same"},
    {"id": "redirect-same-origin-302-retries2", "host": "loopback", "redirect": "same", "retries": 2},
    {"id": "redirect-cross-origin-302", "host": "loopback", "redirect": "cross"},
    {"id": "redirect-cross-origin-302-retries2", "host": "loopback", "redirect": "cross", "retries": 2},
    {"id": "redirect-cross-origin-301-nonloopback-flag1", "host": "self", "redirect": "cross", "status": 301, "env": {"FI_ALLOW_INSECURE_HTTP": "1"}},
    {"id": "redirect-same-origin-303", "host": "loopback", "redirect": "same", "status": 303},
    {"id": "redirect-same-origin-307", "host": "loopback", "redirect": "same", "status": 307},
    {"id": "redirect-same-origin-308", "host": "loopback", "redirect": "same", "status": 308},
    {"id": "redirect-300-with-location", "host": "loopback", "redirect": "same", "status": 300},
    {"id": "answer-304-without-location", "host": "loopback", "status": 304},
    {"id": "proxy-env-plain-loopback", "host": "loopback", "env": {"HTTP_PROXY": "{proxy}", "ALL_PROXY": "{proxy}"}},
    {"id": "proxy-env-lowercase-plain-loopback", "host": "loopback", "env": {"http_proxy": "{proxy}", "all_proxy": "{proxy}"}},
    {"id": "proxy-env-plain-nonloopback-flag1", "host": "self", "env": {"HTTP_PROXY": "{proxy}", "FI_ALLOW_INSECURE_HTTP": "1"}},
    {"id": "proxy-env-plain-nonloopback-noflag", "host": "self", "env": {"HTTP_PROXY": "{proxy}"}, "b": True},
    {"id": "caller-client-with-proxy-plain-loopback", "host": "loopback", "caller": "proxy"},
    {"id": "caller-client-with-proxy-plain-nonloopback-flag1", "host": "self", "caller": "proxy", "env": {"FI_ALLOW_INSECURE_HTTP": "1"}},
    {"id": "caller-client-reads-proxy-env-plain-loopback", "host": "loopback", "caller": "env", "env": {"HTTP_PROXY": "{proxy}"}},
    {"id": "caller-client-plain-loopback", "host": "loopback", "caller": "plain"},
    {"id": "caller-client-plain-nonloopback-flag1", "host": "self", "caller": "plain", "env": {"FI_ALLOW_INSECURE_HTTP": "1"}},
    {"id": "caller-client-plain-nonloopback-noflag", "host": "self", "caller": "plain", "b": True},
    {"id": "caller-client-plain-fi", "host": "fi", "caller": "plain"},
    {"id": "caller-client-mock-transport-plain-loopback", "host": "loopback", "caller": "mock"},
    {"id": "https-fi-shim", "host": "fi", "scheme": "https"},
    {"id": "https-fi-shim-https-proxy", "host": "fi", "scheme": "https", "env": {"HTTPS_PROXY": "{proxy}"}},
    {"id": "https-fi-shim-http-proxy-only", "host": "fi", "scheme": "https", "env": {"HTTP_PROXY": "{proxy}", "ALL_PROXY": "{proxy}"}},
    {"id": "https-fi-shim-same-origin-302", "host": "fi", "scheme": "https", "redirect": "same"},
    {"id": "https-fi-shim-caller-client-with-proxy", "host": "fi", "scheme": "https", "caller": "proxy"},
    {"id": "https-self-shim-flag-unset", "host": "self", "scheme": "https"},
]


class World:
    """The sinks for one cell."""

    def __init__(self, scenario: dict[str, Any], authority: Authority) -> None:
        self.scenario = scenario
        tls = authority.server_context() if scenario.get("scheme") == "https" else None
        self.second = Sink(_ok)
        self.second_url = f"http://{SECOND_HOST}:{self.second.port}/landing"
        kind = scenario.get("redirect")
        status = scenario.get("status", 302)
        if status == 304:
            self.target = Sink(lambda _l: b"HTTP/1.1 304 Not Modified\r\nContent-Length: 0\r\nConnection: close\r\n\r\n", tls)
        elif kind == "same":
            self.target = Sink(_redirect(status, lambda: "/landing"), tls)
        elif kind == "cross":
            self.target = Sink(_redirect(status, lambda: self.second_url), tls)
        else:
            self.target = Sink(_ok, tls)
        self.proxy = Sink(lambda _l: b"HTTP/1.1 502 Bad Gateway\r\nContent-Length: 0\r\nConnection: close\r\n\r\n", connect_tunnel=True)
        self.proxy.tunnel_to = self.target.port
        host = scenario.get("hostname") or {"loopback": "127.0.0.1", "self": SELF_HOST, "fi": FI_HOST}[scenario["host"]]
        self.scheme = scenario.get("scheme", "http")
        self.base = f"{scenario.get('scheme_text', self.scheme)}://{host}:{self.target.port}"
        self.proxy_url = f"http://127.0.0.1:{self.proxy.port}"
        env = {k: v.replace("{proxy}", self.proxy_url) for k, v in scenario.get("env", {}).items()}
        if self.scheme == "https":
            env.update({"REQUESTS_CA_BUNDLE": authority.ca_path, "CURL_CA_BUNDLE": authority.ca_path, "SSL_CERT_FILE": authority.ca_path})
        self.env = env

    def counts(self) -> dict[str, int]:
        return {
            "target_markers": self.target.markers(), "target_conns": self.target.connections,
            "second_markers": self.second.markers(), "second_conns": self.second.connections,
            "proxy_markers": self.proxy.markers(), "proxy_conns": self.proxy.connections, "proxy_connects": self.proxy.connects,
        }

    def close(self) -> None:
        for each in (self.target, self.second, self.proxy):
            each.close()


def _caller_httpx(w: "World", aio: bool) -> Any:
    """The httpx client a caller passes in, by scenario kind: proxy, plain (no environment), env (reads the environment), mock."""
    import httpx

    cls = httpx.AsyncClient if aio else httpx.Client
    kind = w.scenario["caller"]
    if kind == "proxy":
        return cls(proxy=w.proxy_url)
    if kind == "env":
        return cls(trust_env=True)
    if kind == "mock":
        return cls(transport=httpx.MockTransport(lambda request: httpx.Response(200, json={"status": True, "result": {}, "object": "list", "data": []})))
    return cls(trust_env=False)


def _platform_sync(w: World) -> Any:
    import fi.platform as fp

    kwargs: dict[str, Any] = {}
    caller = w.scenario.get("caller")
    if caller:
        kwargs["http_client"] = _caller_httpx(w, False)
    with fp.Client(api_key=API_MARKER, secret_key=SECRET_MARKER, base_url=w.base, max_retries=w.scenario.get("retries", 0), timeout=3, **kwargs) as client:
        return client.request("GET", "/probe/")


def _platform_async(w: World) -> Any:
    import fi.platform as fp

    async def go() -> Any:
        kwargs: dict[str, Any] = {}
        caller = w.scenario.get("caller")
        if caller:
            kwargs["http_client"] = _caller_httpx(w, True)
        async with fp.AsyncClient(api_key=API_MARKER, secret_key=SECRET_MARKER, base_url=w.base, max_retries=w.scenario.get("retries", 0), timeout=3, **kwargs) as client:
            return await client.request("GET", "/probe/")

    return asyncio.run(go())


def _http_client(w: World) -> Any:
    from requests_futures.sessions import FuturesSession

    from fi.api.auth import HttpClient
    from fi.api.types import HttpMethod, RequestConfig

    headers = {"X-Api-Key": API_MARKER, "X-Secret-Key": SECRET_MARKER}
    caller = w.scenario.get("caller")
    session = None
    if caller:
        session = FuturesSession()
        if caller == "proxy":
            session.proxies = {"http": w.proxy_url, "https": w.proxy_url}
        elif caller == "plain":
            session.trust_env = False
    client = HttpClient(base_url=w.base, session=session, default_headers=headers)
    return client.request(RequestConfig(method=HttpMethod.GET, url=w.base + "/x", retry_attempts=max(1, w.scenario.get("retries", 0)), timeout=3))


def _kb_create(w: World) -> Any:
    from fi.kb.client import KnowledgeBase

    return KnowledgeBase(fi_api_key=API_MARKER, fi_secret_key=SECRET_MARKER, fi_base_url=w.base).create_kb("kb")


def _kb_delete(w: World) -> Any:
    from fi.kb.client import KnowledgeBase

    return KnowledgeBase(fi_api_key=API_MARKER, fi_secret_key=SECRET_MARKER, fi_base_url=w.base).delete_kb(kb_ids="kb-1")


def _gateway_kwargs(w: World, aio: bool) -> dict[str, Any]:
    kwargs: dict[str, Any] = {"api_key": API_MARKER, "base_url": w.base, "max_retries": w.scenario.get("retries", 0), "timeout": 3}
    if w.scenario.get("caller"):
        kwargs["http_client"] = _caller_httpx(w, aio)
    return kwargs


def _gateway(w: World, use: Callable[[Any], Any]) -> Any:
    from fi.gateway import AgentCC

    client = AgentCC(**_gateway_kwargs(w, False))
    try:
        return use(client)
    finally:
        with contextlib.suppress(Exception):
            client.close()


def _agateway(w: World, use: Callable[[Any], Any]) -> Any:
    from fi.gateway import AsyncAgentCC

    async def go() -> Any:
        client = AsyncAgentCC(**_gateway_kwargs(w, True))
        try:
            return await use(client)
        finally:
            with contextlib.suppress(Exception):
                await client.aclose()

    return asyncio.run(go())


CHAT = {"model": "m", "messages": [{"role": "user", "content": "hi"}]}


async def _models_async(c: Any) -> Any:
    return await c.models.list()


async def _stream_async(c: Any) -> int:
    stream = await c.chat.completions.create(stream=True, **CHAT)
    count = 0
    async for _ in stream:
        count += 1
    return count


async def _raw_async(c: Any) -> Any:
    return await c.files.content("file-1")


def _health(w: World) -> Any:
    from fi.gateway._utils import health_check

    return f"status={health_check(api_key=API_MARKER, base_url=w.base, timeout=3).get('status')}"


def _valid_key(w: World) -> Any:
    from fi.gateway._utils import check_valid_key

    return f"valid={check_valid_key(API_MARKER, w.base)}"


SENDERS: dict[str, Callable[[World], Any]] = {
    "platform-sync": _platform_sync,
    "platform-async": _platform_async,
    "httpclient-requests": _http_client,
    "kb-create": _kb_create,
    "kb-delete": _kb_delete,
    "gateway-models-sync": lambda w: _gateway(w, lambda c: c.models.list()),
    "gateway-models-async": lambda w: _agateway(w, _models_async),
    "gateway-chat-sync": lambda w: _gateway(w, lambda c: c.chat.completions.create(**CHAT)),
    "gateway-stream-sync": lambda w: _gateway(w, lambda c: sum(1 for _ in c.chat.completions.create(stream=True, **CHAT))),
    "gateway-stream-async": lambda w: _agateway(w, _stream_async),
    "gateway-raw-sync": lambda w: _gateway(w, lambda c: c.files.content("file-1")),
    "gateway-raw-async": lambda w: _agateway(w, _raw_async),
    "gateway-health": _health,
    "gateway-check-valid-key": _valid_key,
}
CALLER_SENDERS = {"platform-sync", "platform-async", "httpclient-requests", "gateway-models-sync", "gateway-models-async",
                  "gateway-stream-sync", "gateway-stream-async"}


def _catches() -> list[tuple[str, type]]:
    found: list[tuple[str, type]] = []
    from fi.utils import errors as errs

    for name in ("SDKException", "KeyedRedirectRefusedError", "KeyedProxyRefusedError", "InsecureHttpRefusedError"):
        found.append((name, getattr(errs, name)))
    from fi import gateway as gw

    for name in ("APIConnectionError", "AgentCCError"):
        found.append(("gateway." + name, getattr(gw, name)))
    import fi.platform as fp

    if hasattr(fp, "APIError"):
        found.append(("platform.APIError", fp.APIError))
    found.append(("Exception", Exception))
    return found


def _describe(exc: BaseException) -> dict[str, Any]:
    code = None
    with contextlib.suppress(Exception):
        code = exc.get_error_code()  # type: ignore[attr-defined]
    return {
        "outcome": f"{type(exc).__name__}[{code}]" if code else type(exc).__name__,
        "cls": type(exc).__name__, "code": code, "status": getattr(exc, "status_code", None),
        "catches": [name for name, cls in _catches() if isinstance(exc, cls)],
        "mro": [c.__name__ for c in type(exc).__mro__[:-2]],
    }


def run_cell(sender: str, scenario: dict[str, Any], authority: Authority) -> dict[str, Any]:
    world = World(scenario, authority)
    saved = {name: os.environ.pop(name) for name in ENV_NAMES if name in os.environ}
    os.environ.update(world.env)
    os.environ["FI_LOGIN_FILE"] = "/nonexistent/login.json"
    try:
        try:
            value = SENDERS[sender](world)
            cell: dict[str, Any] = {"outcome": value if isinstance(value, str) else "sent", "cls": None, "code": None,
                                    "status": None, "catches": [], "mro": []}
        except Exception as exc:  # every outcome is recorded
            cell = _describe(exc)
        cell.update(world.counts())
        cell["rule_b"] = bool(scenario.get("b"))
        cell["unresolved"] = list(dict.fromkeys(REFUSED_NAMES))
        REFUSED_NAMES.clear()
    finally:
        for name in ENV_NAMES:
            os.environ.pop(name, None)
        os.environ.pop("FI_LOGIN_FILE", None)
        os.environ.update(saved)
        world.close()
    return cell


def emit(out_path: str) -> None:
    import fi

    socket.getaddrinfo = _shim  # type: ignore[assignment]
    cells: dict[str, Any] = {}
    with tempfile.TemporaryDirectory() as directory:
        authority = Authority(directory)
        for sender in SENDERS:
            for scenario in SCENARIOS:
                if scenario.get("caller") and sender not in CALLER_SENDERS:
                    continue
                if scenario.get("caller") == "mock" and sender == "httpclient-requests":
                    continue
                key = f"{sender} @ {scenario['id']}"
                try:
                    cells[key] = run_cell(sender, scenario, authority)
                except Exception as exc:
                    cells[key] = {"outcome": f"HARNESS:{type(exc).__name__}:{exc}", "catches": [], "mro": []}
                print(f"{key}: {cells[key]['outcome']}", file=sys.stderr)
    with open(out_path, "w") as fh:
        json.dump({"fi_file": fi.__file__, "fi_version": getattr(fi, "__version__", None), "cells": cells}, fh, indent=1, sort_keys=True)


def _reached(cell: dict[str, Any]) -> tuple:
    """What the sinks saw, reduced to the facts that matter: a key reached the target, the second origin, a proxy; a
    connection was opened to each; a name outside the shim was looked up."""
    return (cell.get("target_markers", 0) > 0, cell.get("target_conns", 0) > 0, cell.get("second_markers", 0) > 0,
            cell.get("second_conns", 0) > 0, cell.get("proxy_markers", 0) > 0, cell.get("proxy_conns", 0) > 0,
            bool(cell.get("unresolved")))


def explain(key: str, old: dict[str, Any], new: dict[str, Any]) -> str:
    scenario = key.split(" @ ")[1]
    if old.get("outcome") == new.get("outcome") and _reached(old) == _reached(new):
        return "equal"
    if (old.get("code") and old.get("code") == new.get("code") and set(old.get("catches", [])) <= set(new.get("catches", []))
            and _reached(old) == _reached(new)):
        return "base-class"
    if new.get("rule_b") and _reached(old)[0] and not _reached(new)[0]:
        return "flag-exact-1"
    if new.get("code") and all(not seen or before for seen, before in zip(_reached(new), _reached(old))):
        return "refined-code"
    if _reached(old)[4] and not (_reached(new)[4] or _reached(new)[5]) and (_reached(new)[0] or _reached(new)[1]):
        return "direct-send"
    for (prefix, rule_scenario), reason in STRICTER.items():
        if key.startswith(prefix) and scenario == rule_scenario:
            return "stricter: " + reason
    return "UNEXPLAINED"


def _show(cell: dict[str, Any]) -> str:
    if not cell:
        return "(absent)"
    seen = [name for name, hit in zip(("T", "2nd", "P"), (cell.get("target_markers", 0) > 0, cell.get("second_markers", 0) > 0,
                                                            cell.get("proxy_markers", 0) > 0)) if hit]
    conns = f"c{cell.get('target_conns', 0)}/{cell.get('second_conns', 0)}/{cell.get('proxy_conns', 0)}"
    return f"{cell.get('outcome')} keys@[{','.join(seen)}] {conns}"


def compare(a_path: str, b_path: str) -> int:
    old, new = json.load(open(a_path)), json.load(open(b_path))
    print(f"old: {old['fi_version']} {old['fi_file']}\nnew: {new['fi_version']} {new['fi_file']}")
    print("keys@ = sinks that received marker bytes (T target, 2nd redirect target, P proxy); cN/N/N = connections target/second/proxy\n")
    print("| cell | old | new | equal? |\n|---|---|---|---|")
    counts: dict[str, int] = {}
    bad = 0
    for key in sorted(set(old["cells"]) | set(new["cells"])):
        o, n = old["cells"].get(key, {}), new["cells"].get(key, {})
        verdict = explain(key, o, n) if o and n else "UNEXPLAINED"
        bad += verdict.startswith("UNEXPLAINED")
        head = verdict.split(":")[0]
        counts[head] = counts.get(head, 0) + 1
        print(f"| {key} | {_show(o)} | {_show(n)} | {verdict} |")
    print(f"\ncells: {sum(counts.values())}; " + ", ".join(f"{k}={v}" for k, v in sorted(counts.items())))
    return 1 if bad else 0


def run_both(old_dir: str, new_dir: str) -> int:
    outs = []
    for label, directory in (("old", old_dir), ("new", new_dir)):
        out = os.path.join(tempfile.gettempdir(), f"keyed-sender-equality-{label}.json")
        env = {**os.environ, "PYTHONPATH": directory}
        subprocess.run([sys.executable, os.path.abspath(__file__), "emit", out], check=True, env=env, stderr=subprocess.DEVNULL, cwd=tempfile.gettempdir())
        outs.append(out)
    return compare(*outs)


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else ""
    if mode == "emit" and len(sys.argv) == 3:
        emit(sys.argv[2])
    elif mode == "compare" and len(sys.argv) == 4:
        sys.exit(compare(sys.argv[2], sys.argv[3]))
    elif mode == "run" and len(sys.argv) == 4:
        sys.exit(run_both(sys.argv[2], sys.argv[3]))
    else:
        print(__doc__)
        sys.exit(2)
