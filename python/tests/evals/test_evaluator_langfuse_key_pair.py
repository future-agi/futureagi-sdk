"""``Evaluator`` takes the Langfuse key pair from one source, not one key from each.

The environment names Langfuse project B (``LANGFUSE_PUBLIC_KEY`` / ``LANGFUSE_SECRET_KEY``). The
caller names project A through ``langfuse_public_key=`` / ``langfuse_secret_key=``. The pair is
resolved the way the Future AGI key pair is: the two arguments go as one pair; with neither
argument the environment pair is used; an empty string counts as not given when the source is
picked. A pair with one key and not the other raises :class:`fi.errors.AuthError` from the
Langfuse configuration call (``evaluate(..., platform="langfuse")``), so the loopback listener
receives no request and 0 bytes of either project's keys. A full pair from either source reaches the listener whole, with 0 bytes of the other project.

Every key is built at runtime with ``secrets.token_hex``, one distinct pair per project.
"""

from __future__ import annotations

import json
import secrets
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Dict, Iterator, List, Optional

import pytest

from fi.errors import AuthError
from fi.evals import Evaluator

TRACE_ID = "0af7651916cd43dd8448eb211c80319c"
SPAN_ID = "b7ad6b7169203331"
ENV_NAMES = ("LANGFUSE_PUBLIC_KEY", "LANGFUSE_SECRET_KEY", "LANGFUSE_HOST")


class Project:
    def __init__(self, tag: str) -> None:
        self.public_key = f"MARKERKEY-{tag}-LFPK-{secrets.token_hex(12)}"
        self.secret_key = f"MARKERKEY-{tag}-LFSK-{secrets.token_hex(12)}"

    @property
    def markers(self) -> tuple:
        return (self.public_key.encode(), self.secret_key.encode())


class Sink:
    """A loopback listener that counts connections and keeps the raw bytes of each request."""

    def __init__(self) -> None:
        sink = self
        self.requests: List[bytes] = []
        self.bodies: List[dict] = []
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
                    sink.bodies.append(json.loads(body or b"{}"))
                data = json.dumps({"status": True, "result": "Evaluation configured."}).encode()
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

    def marker_bytes(self, project: Project) -> int:
        with self.lock:
            return sum(len(m) * raw.count(m) for raw in self.requests for m in project.markers)


@pytest.fixture
def world(monkeypatch: pytest.MonkeyPatch) -> Iterator[Dict[str, object]]:
    pytest.importorskip("opentelemetry.trace")
    projects = {"a": Project("A"), "b": Project("B")}
    sink = Sink()
    for name in ENV_NAMES:
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("LANGFUSE_PUBLIC_KEY", projects["b"].public_key)
    monkeypatch.setenv("LANGFUSE_SECRET_KEY", projects["b"].secret_key)
    monkeypatch.setenv("FI_BASE_URL", sink.base_url)
    try:
        yield {"projects": projects, "sink": sink, "monkeypatch": monkeypatch}
    finally:
        sink.close()


def _configure(kwargs: Dict[str, Optional[str]]) -> Evaluator:
    evaluator = Evaluator(**kwargs)
    evaluator.evaluate(
        "toxicity", {"output": "x"}, model_name="turing_flash", platform="langfuse",
        custom_eval_name="answer-check", trace_id=TRACE_ID, span_id=SPAN_ID,
    )
    return evaluator


def _counts(world: Dict[str, object]) -> Dict[str, object]:
    sink, projects = world["sink"], world["projects"]
    return {
        "connections": sink.connections,
        "requests": len(sink.requests),
        "marker_bytes": {tag: sink.marker_bytes(project) for tag, project in projects.items()},
    }


# Each case builds the constructor arguments from project A; the environment is project B.
MIXED_ARGUMENTS = {
    "a_public_with_env_b_secret": ("langfuse_secret_key", lambda a: {"langfuse_public_key": a.public_key}),
    "a_secret_with_env_b_public": ("langfuse_public_key", lambda a: {"langfuse_secret_key": a.secret_key}),
    "a_public_with_empty_secret": (
        "langfuse_secret_key", lambda a: {"langfuse_public_key": a.public_key, "langfuse_secret_key": ""}),
    "empty_public_with_a_secret": (
        "langfuse_public_key", lambda a: {"langfuse_public_key": "", "langfuse_secret_key": a.secret_key}),
}


@pytest.mark.parametrize("case", sorted(MIXED_ARGUMENTS))
def test_one_langfuse_key_from_the_caller_raises_auth_error_before_any_connection(world, case: str) -> None:
    projects = world["projects"]
    missing, build = MIXED_ARGUMENTS[case]
    kwargs = build(projects["a"])

    with pytest.raises(AuthError) as raised:
        _configure(kwargs)

    message = str(raised.value)
    assert message.endswith(f"Missing: {missing}")
    assert all(m.decode() not in message for p in projects.values() for m in p.markers)
    assert _counts(world) == {"connections": 0, "requests": 0, "marker_bytes": {"a": 0, "b": 0}}


@pytest.mark.parametrize("present", ["LANGFUSE_PUBLIC_KEY", "LANGFUSE_SECRET_KEY"])
def test_one_langfuse_key_in_the_environment_raises_auth_error_before_any_connection(world, present: str) -> None:
    projects = world["projects"]
    other = "LANGFUSE_SECRET_KEY" if present == "LANGFUSE_PUBLIC_KEY" else "LANGFUSE_PUBLIC_KEY"
    world["monkeypatch"].setenv(other, "")

    with pytest.raises(AuthError) as raised:
        _configure({})

    assert str(raised.value).endswith(f"Missing: {other}")
    assert _counts(world) == {"connections": 0, "requests": 0, "marker_bytes": {"a": 0, "b": 0}}


def test_a_full_argument_pair_reaches_the_listener_whole(world) -> None:
    a = world["projects"]["a"]

    evaluator = _configure({"langfuse_public_key": a.public_key, "langfuse_secret_key": a.secret_key})

    assert (evaluator.langfuse_public_key, evaluator.langfuse_secret_key) == (a.public_key, a.secret_key)
    [body] = world["sink"].bodies
    assert (body["langfuse_public_key"], body["langfuse_secret_key"]) == (a.public_key, a.secret_key)
    assert _counts(world)["marker_bytes"] == {"a": len(a.public_key) + len(a.secret_key), "b": 0}


@pytest.mark.parametrize("arguments", [{}, {"langfuse_public_key": "", "langfuse_secret_key": ""}],
                         ids=["no-arguments", "empty-arguments"])
def test_the_environment_pair_reaches_the_listener_whole(world, arguments: Dict[str, str]) -> None:
    b = world["projects"]["b"]

    evaluator = _configure(arguments)

    assert (evaluator.langfuse_public_key, evaluator.langfuse_secret_key) == (b.public_key, b.secret_key)
    [body] = world["sink"].bodies
    assert (body["langfuse_public_key"], body["langfuse_secret_key"]) == (b.public_key, b.secret_key)
    assert _counts(world)["marker_bytes"] == {"a": 0, "b": len(b.public_key) + len(b.secret_key)}


def test_an_evaluator_without_langfuse_keys_builds_with_none(world) -> None:
    world["monkeypatch"].delenv("LANGFUSE_PUBLIC_KEY")
    world["monkeypatch"].delenv("LANGFUSE_SECRET_KEY")

    evaluator = Evaluator()

    assert (evaluator.langfuse_public_key, evaluator.langfuse_secret_key) == (None, None)
    assert _counts(world)["connections"] == 0
