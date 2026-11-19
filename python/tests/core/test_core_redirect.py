"""The core clients: a 3xx is never followed on a core call
and never parsed as a body. Real loopback sockets: server A answers a redirect to server B, and B must
never see a request. Core generated, raw and async calls raise the same ``UnexpectedRedirectError`` a
platform call raises, naming the target host only (TypeScript: ``core-redirect.test.ts``). And a JSON
success body whose values do not parse (an enum, a UUID) stays the plain ``ValueError`` it was at the
base; only a body that is not JSON is ``invalid_json``."""

from __future__ import annotations

import asyncio
import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Callable

import pytest

import fi.errors as errors
from fi import AsyncFutureAGIClient, FutureAGIClient
from fi._core.core_http import InvalidJSONError
from fi.futureagi_client import _adetailed
from fi.generated.openapi_client.api.annotation_queues import list_annotation_queues
from tests.core._support import OPS

KEYS = {"api_key": "k-redir-aaaa", "secret_key": "s-redir-aaaa"}
Answer = Callable[[BaseHTTPRequestHandler], tuple[int, dict[str, str], bytes]]


class _Server:
    """A loopback HTTP server on its own thread that records every request it sees."""

    def __init__(self, answer: Answer) -> None:
        self.seen: list[tuple[str, str, dict[str, str]]] = []
        seen = self.seen

        class Handler(BaseHTTPRequestHandler):
            def _any(self) -> None:
                length = int(self.headers.get("content-length") or 0)
                if length:
                    self.rfile.read(length)
                seen.append((self.command, self.path, {k.lower(): v for k, v in self.headers.items()}))
                status, headers, body = answer(self)
                self.send_response(status)
                for name, value in headers.items():
                    self.send_header(name, value)
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            do_GET = do_POST = do_PUT = do_PATCH = do_DELETE = _any

            def log_message(self, *args: Any) -> None:
                pass

        self.httpd = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.port = self.httpd.server_address[1]
        self.thread = threading.Thread(target=self.httpd.serve_forever, kwargs={"poll_interval": 0.02}, daemon=True)
        self.thread.start()

    def close(self) -> None:
        self.httpd.shutdown()
        self.httpd.server_close()
        self.thread.join(timeout=5)


@pytest.fixture
def pair():
    state = {"status": 302, "same_origin": False, "body": None}
    b = _Server(lambda h: (200, {"Content-Type": "application/json"}, b'{"stolen": true, "count": 0, "results": []}'))

    def answer_a(h: BaseHTTPRequestHandler) -> tuple[int, dict[str, str], bytes]:
        if state["body"] is not None:
            return 200, {"Content-Type": "application/json"}, state["body"]
        target = f"{h.path}/" if state["same_origin"] else f"http://127.0.0.1:{b.port}/steal"
        return state["status"], {"Location": target, "x-request-id": "req-redir-1"}, b""

    a = _Server(answer_a)
    try:
        yield a, b, state
    finally:
        a.close()
        b.close()


def _client(a: _Server) -> FutureAGIClient:
    client = FutureAGIClient(**KEYS, base_url=f"http://127.0.0.1:{a.port}", retries=0)
    client._platform.shared.table = OPS
    return client


CALLS = {
    "core generated": lambda c: c.annotation_queues.list(),
    "core raw": lambda c: c.users.current(),
    "core raw POST": lambda c: c.datasets.get_row("d1", {"row": 1}),
    "platform": lambda c: c._platform.call("capabilities.get"),
}


@pytest.mark.parametrize("path", sorted(CALLS))
def test_a_302_to_another_origin_is_unexpected_redirect_and_the_target_sees_nothing(pair, path):
    a, b, _ = pair
    client = _client(a)
    if path == "platform":
        client = FutureAGIClient(
            **KEYS,
            base_url=f"http://127.0.0.1:{a.port}",
            platform_base_url=f"http://127.0.0.1:{a.port}/omega/api",
            retries=0,
        )
        client._platform.shared.table = OPS
    with pytest.raises(errors.UnexpectedRedirectError) as info:
        CALLS[path](client)
    err = info.value
    assert (err.status_code, err.target_host, err.request_id) == (302, f"127.0.0.1:{b.port}", "req-redir-1")
    assert "k-redir" not in str(err) and "s-redir" not in str(err) and "/steal" not in str(err)
    assert len(a.seen) == 1 and a.seen[0][2]["x-api-key"] == "k-redir-aaaa"  # the keys reached the base URL only
    assert b.seen == []


@pytest.mark.parametrize("status", [301, 303, 307, 308])
def test_no_redirect_status_is_followed_or_parsed(pair, status):
    a, b, state = pair
    state["status"] = status
    with pytest.raises(errors.UnexpectedRedirectError):
        _client(a).annotation_queues.list()
    with pytest.raises(errors.UnexpectedRedirectError):
        _client(a).users.current()  # used to return None
    assert b.seen == []


def test_a_same_origin_redirect_is_not_followed_either(pair):
    a, b, state = pair
    state["same_origin"] = True
    with pytest.raises(errors.UnexpectedRedirectError) as info:
        _client(a).annotation_queues.list()
    assert info.value.target_host == f"127.0.0.1:{a.port}" and len(a.seen) == 1


def test_async_core_calls_raise_the_same_class(pair):
    a, b, _ = pair

    async def go() -> list[BaseException]:
        found = []
        async with AsyncFutureAGIClient(**KEYS, base_url=f"http://127.0.0.1:{a.port}", retries=0) as client:
            for call in (
                lambda: client.request("GET", "/model-hub/annotation-queues/"),
                lambda: _adetailed(list_annotation_queues.asyncio_detailed, client=client.generated_client),
            ):
                try:
                    await call()
                except BaseException as exc:  # noqa: BLE001 - the test inspects the class
                    found.append(exc)
        return found

    found = asyncio.run(go())
    assert [type(e) for e in found] == [errors.UnexpectedRedirectError] * 2
    assert all(e.target_host == f"127.0.0.1:{b.port}" for e in found)
    assert b.seen == []


def test_a_json_body_whose_values_do_not_parse_is_a_plain_value_error(pair):
    a, _, state = pair
    queue = {"name": "q", "label_ids": [], "id": "not-a-uuid"}
    state["body"] = json.dumps({"count": 1, "results": [queue]}).encode()
    with pytest.raises(ValueError) as info:
        _client(a).annotation_queues.list()
    assert not isinstance(info.value, InvalidJSONError)
    state["body"] = b"<html>not json</html>"
    with pytest.raises(InvalidJSONError) as info:
        _client(a).annotation_queues.list()
    assert info.value.code == "invalid_json" and isinstance(info.value, ValueError)
