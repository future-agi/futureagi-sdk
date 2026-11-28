"""A gateway's 3xx answer is refused, not taken for success: the clients send with ``follow_redirects=False``, so an
unfollowed redirect would otherwise come back as an empty success (or a parse failure). The error asks for the
base URL to be set to the final address, is not retried, and does not echo the ``Location`` value, which can carry a token or an internal address.

A remote host here is a made-up name that resolves to the local server (the no-egress guard allows only loopback
addresses), so the same server answers for the loopback and the remote case.
"""

from __future__ import annotations

import asyncio
import socket
import threading
import warnings
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest

from fi.gateway import AgentCC, AsyncAgentCC
from fi.gateway._exceptions import APIConnectionError, AgentCCError

REMOTE = "redirecting-gateway.test"
SECRET = "location-secret-token-not-real"


class _Redirector:
    def __init__(self, status: int = 302) -> None:
        self.hits: list[str] = []
        outer = self

        class Handler(BaseHTTPRequestHandler):
            def _answer(self):
                length = int(self.headers.get("content-length") or 0)
                self.rfile.read(length)
                outer.hits.append(self.path)
                self.send_response(status)
                self.send_header("Location", f"http://elsewhere.test/{SECRET}")
                self.send_header("Content-Length", "0")
                self.end_headers()

            do_GET = do_POST = _answer

            def log_message(self, *args):
                pass

        self._http = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.port = self._http.server_address[1]
        threading.Thread(target=self._http.serve_forever, daemon=True).start()

    def close(self) -> None:
        self._http.shutdown()
        self._http.server_close()


@pytest.fixture(name="redirector")
def redirector_fixture(monkeypatch):
    monkeypatch.setenv("FI_ALLOW_INSECURE_HTTP", "1")  # the remote case is plain http to a name that is not loopback
    for name in ("HTTP_PROXY", "http_proxy", "HTTPS_PROXY", "https_proxy", "ALL_PROXY", "all_proxy"):
        monkeypatch.delenv(name, raising=False)
    server = _Redirector()
    real = socket.getaddrinfo

    def resolve(host, *args, **kwargs):
        name = host.decode() if isinstance(host, bytes) else host
        return real("127.0.0.1" if name == REMOTE else host, *args, **kwargs)

    monkeypatch.setattr(socket, "getaddrinfo", resolve)
    yield server
    server.close()


HOSTS = [pytest.param("127.0.0.1", id="loopback"), pytest.param(REMOTE, id="remote")]
CHAT = {"model": "m", "messages": [{"role": "user", "content": "hi"}]}


def _call(asynchronous: bool, base_url: str, action: str):
    def use(client):
        if action == "models":
            return client.models.list()
        return client.chat.completions.create(**CHAT, stream=action == "stream")

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")  # an http:// remote gateway is warned about; that is not under test here
        if not asynchronous:
            client = AgentCC(api_key="sk-test-gateway-key", base_url=base_url, max_retries=2)
            try:
                result = use(client)
                if action == "stream":
                    list(result)
                return result
            finally:
                client.close()

        async def go():
            client = AsyncAgentCC(api_key="sk-test-gateway-key", base_url=base_url, max_retries=2)
            try:
                result = await use(client)
                if action == "stream":
                    async for _ in result:
                        pass
                return result
            finally:
                await client.aclose()

        return asyncio.run(go())


@pytest.mark.parametrize("action", ["models", "chat", "stream"])
@pytest.mark.parametrize("asynchronous", [False, True], ids=["sync", "async"])
@pytest.mark.parametrize("host", HOSTS)
def test_a_redirect_is_refused_once_without_echoing_its_location(redirector, host, asynchronous, action):
    with pytest.raises(APIConnectionError) as info:
        _call(asynchronous, f"http://{host}:{redirector.port}", action)
    assert isinstance(info.value, AgentCCError)
    assert str(info.value) == "The gateway answered with a redirect. Set the base URL to the final address."
    assert SECRET not in str(info.value) and SECRET not in repr(info.value)
    assert SECRET not in repr(vars(info.value))
    assert len(redirector.hits) == 1  # a refusal is not retried, and nothing is followed
