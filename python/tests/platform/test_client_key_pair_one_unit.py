"""``fi.Client`` / ``fi.AsyncClient`` take the key pair as one unit.

Both keys come from the arguments, or (when neither argument is given) both come from
``FI_API_KEY`` / ``FI_SECRET_KEY``. One key given without the other, an empty key, or a missing
pair raises :class:`fi.errors.MissingAuthError` before any request. Each tenant has its own
planted marker keys, generated here, and a raw loopback sink counts the marker bytes it receives,
so a request that carries one tenant's key with the other tenant's secret is visible.
"""

from __future__ import annotations

import asyncio
import secrets
import socket
import socketserver
import threading

import fi
import pytest
from fi.errors import MissingAuthError

ALLOW_INSECURE_HTTP_ENV = "FI_ALLOW_INSECURE_HTTP"
OPT_IN_HOST = "tenant-a-platform.test"


def _marker(tenant: str, kind: str) -> str:
    return f"mk{tenant}{kind}{secrets.token_hex(12)}"


@pytest.fixture(name="keys")
def keys_fixture():
    # tenant A passes its pair as arguments, tenant B sits in the environment
    return {"KA": _marker("A", "api"), "SA": _marker("A", "sec"), "KB": _marker("B", "api"), "SB": _marker("B", "sec")}


class _Sink:
    """A raw loopback HTTP sink: keeps every byte it reads and answers ``{"result": {}}``."""

    def __init__(self, host: str = "127.0.0.1") -> None:
        self.raw: list[bytes] = []
        outer = self

        class Handler(socketserver.BaseRequestHandler):
            def handle(self):
                data = b""
                self.request.settimeout(5)
                try:
                    while b"\r\n\r\n" not in data:
                        chunk = self.request.recv(65536)
                        if not chunk:
                            break
                        data += chunk
                finally:
                    outer.raw.append(data)
                body = b'{"result": {}}'
                self.request.sendall(
                    b"HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nConnection: close\r\n"
                    + f"Content-Length: {len(body)}\r\n\r\n".encode()
                    + body
                )

        family = socket.AF_INET6 if ":" in host else socket.AF_INET
        server_class = type("Server", (socketserver.ThreadingTCPServer,), {"address_family": family, "daemon_threads": True})
        self._server = server_class((host, 0), Handler)
        self.port = self._server.server_address[1]
        self.url = f"http://[{host}]:{self.port}" if ":" in host else f"http://{host}:{self.port}"
        threading.Thread(target=self._server.serve_forever, args=(0.05,), daemon=True).start()

    def marker_bytes(self, keys) -> int:
        blob = b"".join(self.raw)
        return sum(blob.count(value.encode()) * len(value.encode()) for value in keys.values())

    def pairs(self, keys) -> list[tuple[str, str]]:
        """The (api key, secret key) marker names each request carried."""
        found = []
        for request in self.raw:
            text = request.decode("latin-1").lower()
            api = next((n for n in ("KA", "KB") if keys[n].lower() in text), "-")
            sec = next((n for n in ("SA", "SB") if keys[n].lower() in text), "-")
            found.append((api, sec))
        return found

    def close(self) -> None:
        self._server.shutdown()
        self._server.server_close()


@pytest.fixture(name="sink")
def sink_fixture():
    sink = _Sink()
    yield sink
    sink.close()


def _call(asynchronous: bool, **kwargs):
    if not asynchronous:
        with fi.Client(max_retries=0, **kwargs) as client:
            return client.request("GET", "/probe/", unwrap=None)

    async def go():
        async with fi.AsyncClient(max_retries=0, **kwargs) as client:
            return await client.request("GET", "/probe/", unwrap=None)

    return asyncio.run(go())


MODES = pytest.mark.parametrize("asynchronous", [False, True], ids=["sync", "async"])
ENVS = {"env_none": (), "env_both": ("KB", "SB"), "env_api_only": ("KB",), "env_secret_only": ("SB",)}
ARGS = {
    "args_api_only": ("KA", None),
    "args_secret_only": (None, "SA"),
    "args_api_and_empty_secret": ("KA", ""),
    "args_empty_api_and_secret": ("", "SA"),
    "args_both": ("KA", "SA"),
    "args_none": (None, None),
}


def _expected(env: tuple, args: tuple):
    """The pair that must arrive, or None where MissingAuthError is raised."""
    api, sec = args
    if api or sec:
        return ("KA", "SA") if api and sec else None
    return ("KB", "SB") if env == ("KB", "SB") else None


def _set_env(monkeypatch, keys, env: tuple) -> None:
    monkeypatch.delenv("FI_API_KEY", raising=False)
    monkeypatch.delenv("FI_SECRET_KEY", raising=False)
    for name in env:
        monkeypatch.setenv("FI_API_KEY" if name.startswith("K") else "FI_SECRET_KEY", keys[name])


def _arg(keys, name):
    return keys[name] if name else name


@MODES
@pytest.mark.parametrize("env_id", list(ENVS))
@pytest.mark.parametrize("args_id", list(ARGS))
def test_the_client_sends_one_tenant_key_pair_or_raises_missing_auth(sink, keys, monkeypatch, asynchronous, env_id, args_id):
    env, args = ENVS[env_id], ARGS[args_id]
    _set_env(monkeypatch, keys, env)
    expected = _expected(env, args)
    kwargs = {"api_key": _arg(keys, args[0]), "secret_key": _arg(keys, args[1]), "base_url": sink.url}

    if expected is None:
        try:
            _call(asynchronous, **kwargs)
            outcome: BaseException | None = None
        except Exception as exc:  # the type is asserted below, after the sink is read
            outcome = exc
        assert sink.marker_bytes(keys) == 0, f"{sink.marker_bytes(keys)} marker bytes reached the sink as {sink.pairs(keys)}"
        assert sink.raw == []
        assert isinstance(outcome, MissingAuthError), f"raised {type(outcome).__name__}"
        text = str(outcome) + repr(outcome)
        assert not any(value in text for value in keys.values())
        return

    assert _call(asynchronous, **kwargs) == {"result": {}}
    assert sink.pairs(keys) == [expected]
    assert sink.marker_bytes(keys) == sum(len(keys[name]) for name in expected)


@MODES
@pytest.mark.parametrize("source", ["arguments", "environment"])
def test_a_complete_pair_reaches_an_ipv6_loopback_sink(keys, monkeypatch, asynchronous, source):
    try:
        sink = _Sink("::1")
    except OSError:
        pytest.skip("no IPv6 loopback on this host")
    try:
        if source == "arguments":
            _set_env(monkeypatch, keys, ("KB", "SB"))
            _call(asynchronous, api_key=keys["KA"], secret_key=keys["SA"], base_url=sink.url)
            assert sink.pairs(keys) == [("KA", "SA")]
        else:
            _set_env(monkeypatch, keys, ("KB", "SB"))
            _call(asynchronous, base_url=sink.url)
            assert sink.pairs(keys) == [("KB", "SB")]
        assert sink.marker_bytes(keys) > 0
    finally:
        sink.close()


@MODES
def test_the_base_url_from_the_environment_carries_the_environment_pair(sink, keys, monkeypatch, asynchronous):
    _set_env(monkeypatch, keys, ("KB", "SB"))
    monkeypatch.setenv("FI_BASE_URL", sink.url)
    _call(asynchronous)
    assert sink.pairs(keys) == [("KB", "SB")]


@MODES
def test_the_plain_http_opt_in_delivers_the_argument_pair_to_a_named_host(sink, keys, monkeypatch, asynchronous):
    real = socket.getaddrinfo

    def resolve(host, *args, **kwargs):
        name = host.decode() if isinstance(host, bytes) else host
        return real("127.0.0.1" if name == OPT_IN_HOST else host, *args, **kwargs)

    monkeypatch.setattr(socket, "getaddrinfo", resolve)
    monkeypatch.setenv(ALLOW_INSECURE_HTTP_ENV, "1")
    _set_env(monkeypatch, keys, ("KB", "SB"))
    _call(asynchronous, api_key=keys["KA"], secret_key=keys["SA"], base_url=f"http://{OPT_IN_HOST}:{sink.port}")
    assert sink.pairs(keys) == [("KA", "SA")]


@MODES
@pytest.mark.parametrize("env_id", ["env_both", "env_api_only", "env_secret_only"])
def test_a_partial_argument_pair_with_a_remote_opt_in_host_sends_nothing(sink, keys, monkeypatch, asynchronous, env_id):
    real = socket.getaddrinfo

    def resolve(host, *args, **kwargs):
        name = host.decode() if isinstance(host, bytes) else host
        return real("127.0.0.1" if name == OPT_IN_HOST else host, *args, **kwargs)

    monkeypatch.setattr(socket, "getaddrinfo", resolve)
    monkeypatch.setenv(ALLOW_INSECURE_HTTP_ENV, "1")
    _set_env(monkeypatch, keys, ENVS[env_id])
    try:
        _call(asynchronous, api_key=keys["KA"], base_url=f"http://{OPT_IN_HOST}:{sink.port}")
        outcome: BaseException | None = None
    except Exception as exc:  # the type is asserted below, after the sink is read
        outcome = exc
    assert sink.marker_bytes(keys) == 0, f"{sink.marker_bytes(keys)} marker bytes reached the sink as {sink.pairs(keys)}"
    assert isinstance(outcome, MissingAuthError), f"raised {type(outcome).__name__}"
