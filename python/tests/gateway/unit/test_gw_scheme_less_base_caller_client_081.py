"""A caller's HTTPX base supplies the destination for a gateway //host:port URL."""
# ruff: noqa: F811

from __future__ import annotations

import json
import shutil
import ssl
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import httpx
import pytest

from fi.errors import InsecureHttpRefusedError, KeyedProxyRefusedError
from fi.gateway import AgentCC, AgentCCError, AsyncAgentCC, AsyncGateway, Gateway
from tests.gateway.test_env_proxy_tls import tls_gateway_fixture  # noqa: F401
from tests.test_plain_http_key_guards import KEY, net  # noqa: F401

pytestmark = pytest.mark.filterwarnings("ignore:Gateway and AsyncGateway are deprecated:DeprecationWarning")


@pytest.fixture
def loopback_gateway():
    seen = []

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.respond({"object": "list", "data": []})

        def do_POST(self):
            data = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            if data.get("stream"):
                self.respond(b"data: [DONE]\n\n", "text/event-stream")
            else:
                self.respond({"id": "c", "object": "chat.completion", "created": 0, "model": "m", "choices": []})

        def respond(self, body, content_type="application/json"):
            seen.append((self.path, self.headers.get_all("Authorization")))
            payload = body if isinstance(body, bytes) else json.dumps(body).encode()
            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)

        def log_message(self, *args):
            pass

    with ThreadingHTTPServer(("127.0.0.1", 0), Handler) as server:
        thread = threading.Thread(target=server.serve_forever, kwargs={"poll_interval": 0.01}, daemon=True)
        thread.start()
        try:
            yield server.server_port, seen
        finally:
            server.shutdown()
            thread.join()


async def _call(gateway, operation="models", **kwargs):
    options = dict(api_key=KEY, max_retries=0, timeout=3, **kwargs)
    chat = {"model": "m", "messages": [{"role": "user", "content": "hello"}]}
    if issubclass(gateway, AsyncAgentCC):
        async with gateway(**options) as client:
            if operation == "models":
                await client.models.list()
            elif operation == "raw":
                await client.files.content("file-1")
            elif operation == "chat":
                await client.chat.completions.create(**chat)
            else:
                async for _ in await client.chat.completions.create(stream=True, **chat):
                    pass
    else:
        with gateway(**options) as client:
            if operation == "models":
                client.models.list()
            elif operation == "raw":
                client.files.content("file-1")
            elif operation == "chat":
                client.chat.completions.create(**chat)
            else:
                list(client.chat.completions.create(stream=True, **chat))


@pytest.mark.parametrize("gateway", [AgentCC, AsyncAgentCC, Gateway, AsyncGateway])
@pytest.mark.parametrize("operation", ["models", "chat", "stream"])
@pytest.mark.parametrize("host", ["127.0.0.1", "plain.example.test"])
async def test_caller_http_base_supplies_origin_and_prefix(loopback_gateway, gateway, operation, host, monkeypatch, net):
    port, seen = loopback_gateway
    opt_in = {}
    if host != "127.0.0.1":
        if operation == "models":
            opt_in["allow_insecure_http"] = True
        else:
            monkeypatch.setenv("FI_ALLOW_INSECURE_HTTP", "1")
    settings = {"base_url": f"http://{host}:{port}/caller-prefix", "trust_env": False}
    # The written authority is not the one HTTPX uses, even for the port.
    base_url = "//api.futureagi.com:9/sdk-prefix"
    if issubclass(gateway, AsyncAgentCC):
        async with httpx.AsyncClient(**settings) as http:
            await _call(gateway, operation, base_url=base_url, http_client=http, **opt_in)
    else:
        with httpx.Client(**settings) as http:
            await _call(gateway, operation, base_url=base_url, http_client=http, **opt_in)
    path = "/v1/models" if operation == "models" else "/v1/chat/completions"
    assert seen == [(f"/caller-prefix/sdk-prefix{path}", [f"Bearer {KEY}"])]
    net.nothing_sent()


@pytest.mark.skipif(shutil.which("openssl") is None, reason="openssl is needed for the loopback certificate")
async def test_caller_https_base_supplies_scheme(tls_gateway):
    port, cert, seen = tls_gateway
    context = ssl.create_default_context(cafile=str(cert))
    async with httpx.AsyncClient(base_url=f"https://127.0.0.1:{port}/caller-prefix", verify=context, trust_env=False) as http:
        await _call(AsyncAgentCC, "raw", base_url="//ignored.example.test:9", http_client=http)
    assert seen == [("/caller-prefix/v1/files/file-1/content", f"Bearer {KEY}")]


@pytest.mark.parametrize("opt_in", [False, True])
async def test_caller_future_agi_http_base_is_refused(net, opt_in):
    with (
        httpx.Client(base_url=f"http://api.futureagi.com:{net.target.port}", trust_env=False) as http,
        pytest.raises(InsecureHttpRefusedError),
    ):
        await _call(AgentCC, base_url="//127.0.0.1:9", http_client=http, allow_insecure_http=opt_in)
    net.nothing_sent()


async def test_caller_non_loopback_http_base_without_opt_in_is_refused(net):
    with (
        httpx.Client(base_url=f"http://plain.example.test:{net.target.port}", trust_env=False) as http,
        pytest.raises(AgentCCError, match="FI_ALLOW_INSECURE_HTTP") as refusal,
    ):
        await _call(AgentCC, base_url="//127.0.0.1:9", http_client=http)
    assert refusal.value.code == "insecure_http_origin"
    net.nothing_sent()


async def test_caller_proxied_http_base_is_refused(net):
    with (
        httpx.Client(base_url=f"http://127.0.0.1:{net.target.port}", proxy=f"http://127.0.0.1:{net.proxy.port}") as http,
        pytest.raises(KeyedProxyRefusedError),
    ):
        await _call(AgentCC, base_url="//127.0.0.1:9", http_client=http)
    net.nothing_sent()


@pytest.mark.parametrize("supplied", [False, True], ids=["sdk-built", "caller-without-base"])
async def test_no_absolute_caller_base_stays_refused(net, supplied):
    with (
        httpx.Client(trust_env=False) as http,
        pytest.raises(AgentCCError, match=r"must be an absolute HTTP\(S\) URL"),
    ):
        await _call(Gateway, base_url=f"//127.0.0.1:{net.target.port}", http_client=http if supplied else None)
    net.nothing_sent()
