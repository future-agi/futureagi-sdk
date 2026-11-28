"""``Protect`` and the Turing guardrail backend take a key pair from one tenant, not one key from each.

FI_API_KEY, FI_SECRET_KEY and FI_BASE_URL name tenant B and its loopback listener TB. The caller
names tenant A and its loopback listener TA through the constructor arguments. When the caller
gives one of A's keys and leaves the other one out (or passes it as an empty string), the client
must raise :class:`fi.errors.MissingAuthError` before any connection, so TA receives 0 bytes of
B's keys and TB receives 0 bytes of A's keys. A full A pair goes to TA only; no arguments at all
send the full B pair from the environment to TB.

Every key is built at runtime with ``secrets.token_hex``, one distinct pair per tenant.
"""

from __future__ import annotations

import json
import secrets
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Callable, Dict, Iterator, List, Optional

import pytest

from fi.errors import MissingAuthError
from fi.evals.guardrails.backends.turing import TuringBackend
from fi.evals.guardrails.config import GuardrailModel, RailType
from fi.evals.protect import Protect

TEXT = "some text to screen"


class Tenant:
    def __init__(self, tag: str) -> None:
        self.tag = tag
        self.api_key = f"tenant-{tag}-ak-{secrets.token_hex(12)}"
        self.secret_key = f"tenant-{tag}-sk-{secrets.token_hex(12)}"

    @property
    def markers(self) -> tuple:
        return (self.api_key.encode(), self.secret_key.encode())


class Sink:
    """A loopback listener that counts connections and keeps the raw bytes of each request."""

    def __init__(self) -> None:
        sink = self
        self.requests: List[bytes] = []
        self.connections = 0
        self.lock = threading.Lock()

        class Handler(BaseHTTPRequestHandler):
            def setup(self) -> None:
                with sink.lock:
                    sink.connections += 1
                super().setup()

            def do_POST(self) -> None:  # noqa: N802
                length = int(self.headers.get("Content-Length") or 0)
                body = self.rfile.read(length) if length else b""
                with sink.lock:
                    sink.requests.append(self.requestline.encode() + b"\r\n" + bytes(self.headers) + body)
                data = json.dumps({"result": [{"evaluations": [{"output": 1.0, "runtime": 1}]}]}).encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)

            def log_message(self, *args: object) -> None:
                pass

        self.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    @property
    def base_url(self) -> str:
        return f"http://127.0.0.1:{self.server.server_address[1]}"

    def close(self) -> None:
        self.server.shutdown()
        self.server.server_close()

    def marker_bytes(self, tenant: Tenant) -> int:
        with self.lock:
            return sum(len(m) * raw.count(m) for raw in self.requests for m in tenant.markers)

    def requests_with_both_keys_of(self, tenant: Tenant) -> int:
        with self.lock:
            return sum(1 for raw in self.requests if all(m in raw for m in tenant.markers))


@pytest.fixture
def world(monkeypatch: pytest.MonkeyPatch) -> Iterator[Dict[str, object]]:
    tenants = {"a": Tenant("a"), "b": Tenant("b")}
    sinks = {"a": Sink(), "b": Sink()}
    monkeypatch.setenv("FI_API_KEY", tenants["b"].api_key)
    monkeypatch.setenv("FI_SECRET_KEY", tenants["b"].secret_key)
    monkeypatch.setenv("FI_BASE_URL", sinks["b"].base_url)
    try:
        yield {"tenants": tenants, "sinks": sinks}
    finally:
        for sink in sinks.values():
            sink.close()


def _counts(world: Dict[str, object]) -> Dict[str, object]:
    tenants, sinks = world["tenants"], world["sinks"]
    return {
        f"T{tag.upper()}": {
            "connections": sinks[tag].connections,
            "requests": len(sinks[tag].requests),
            "marker_bytes": {other: sinks[tag].marker_bytes(tenants[other]) for other in tenants},
        }
        for tag in sinks
    }


def _run_protect(kwargs: Dict[str, Optional[str]]) -> None:
    client = Protect(**kwargs)
    try:
        client.protect(TEXT, use_flash=True, timeout=5000)
    except MissingAuthError:
        raise
    except Exception:  # the keys at each listener are what this file checks, not the parsed answer
        pass


def _run_turing(kwargs: Dict[str, Optional[str]]) -> None:
    backend = TuringBackend(model=GuardrailModel.TURING_FLASH, **kwargs)
    backend.classify(TEXT, RailType.INPUT)


CLIENTS: Dict[str, Callable[[Dict[str, Optional[str]]], None]] = {
    "protect": _run_protect,
    "turing": _run_turing,
}

# Each case builds the constructor arguments from tenant A and listener TA; the environment is tenant B.
MIXED_CASES = {
    "a_key_with_env_b_secret": lambda a, ta: {"fi_api_key": a.api_key, "fi_base_url": ta},
    "a_secret_with_env_b_key": lambda a, ta: {"fi_secret_key": a.secret_key, "fi_base_url": ta},
    "a_key_with_empty_secret": lambda a, ta: {"fi_api_key": a.api_key, "fi_secret_key": "", "fi_base_url": ta},
    "empty_key_with_a_secret": lambda a, ta: {"fi_api_key": "", "fi_secret_key": a.secret_key, "fi_base_url": ta},
}


@pytest.mark.parametrize("client", sorted(CLIENTS))
@pytest.mark.parametrize("case", sorted(MIXED_CASES))
def test_one_key_from_the_caller_raises_missing_auth_before_any_connection(world, client: str, case: str) -> None:
    tenants, sinks = world["tenants"], world["sinks"]
    kwargs = MIXED_CASES[case](tenants["a"], sinks["a"].base_url)
    raised: Optional[BaseException] = None
    try:
        CLIENTS[client](kwargs)
    except Exception as exc:  # the type is checked below, after the listeners are read
        raised = exc
    counts = _counts(world)
    assert sinks["a"].marker_bytes(tenants["b"]) == 0, counts
    assert sinks["b"].marker_bytes(tenants["a"]) == 0, counts
    assert sinks["a"].connections == 0, counts
    assert sinks["b"].connections == 0, counts
    assert isinstance(raised, MissingAuthError), (repr(raised), counts)


@pytest.mark.parametrize("client", sorted(CLIENTS))
def test_full_caller_pair_goes_to_the_caller_base_url_only(world, client: str) -> None:
    tenants, sinks = world["tenants"], world["sinks"]
    a = tenants["a"]
    CLIENTS[client]({"fi_api_key": a.api_key, "fi_secret_key": a.secret_key, "fi_base_url": sinks["a"].base_url})
    counts = _counts(world)
    assert len(sinks["a"].requests) >= 1, counts
    assert sinks["a"].requests_with_both_keys_of(a) == len(sinks["a"].requests), counts
    assert sinks["a"].marker_bytes(tenants["b"]) == 0, counts
    assert sinks["b"].connections == 0, counts
    assert sinks["b"].marker_bytes(a) == 0, counts


@pytest.mark.parametrize("client", sorted(CLIENTS))
def test_no_arguments_send_the_environment_pair_to_the_environment_base_url(world, client: str) -> None:
    tenants, sinks = world["tenants"], world["sinks"]
    b = tenants["b"]
    CLIENTS[client]({})
    counts = _counts(world)
    assert len(sinks["b"].requests) >= 1, counts
    assert sinks["b"].requests_with_both_keys_of(b) == len(sinks["b"].requests), counts
    assert sinks["b"].marker_bytes(tenants["a"]) == 0, counts
    assert sinks["a"].connections == 0, counts
    assert sinks["a"].marker_bytes(b) == 0, counts
