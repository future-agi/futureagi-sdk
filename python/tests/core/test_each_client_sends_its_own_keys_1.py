"""Each dataset caller sends its own keys: ``Dataset.get_dataset_config`` and the class helpers built on it.

Two callers with keys built at runtime (``secrets.token_hex``) work on one dataset name against loopback
listeners, one after another and from 8 threads at once. Every request names its caller in the body (the
column name), so each request is checked against the keys of the caller that made it: the keys it carries,
the listener it reached, and 0 bytes of the other caller's keys anywhere at that listener.
"""

from __future__ import annotations

import json
import secrets
import threading
import uuid
from concurrent.futures import ThreadPoolExecutor
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Dict, List
from urllib.parse import parse_qs, urlparse

import pytest

from fi.datasets import dataset as dataset_module
from fi.datasets.dataset import Dataset
from fi.utils.routes import Routes

NAME = "shared-dataset-name"
THREADS = 8


class Caller:
    def __init__(self, tag: str, base_url: str) -> None:
        self.tag = tag
        self.api_key = f"tenant-{tag}-api-{secrets.token_hex(12)}"
        self.secret_key = f"tenant-{tag}-secret-{secrets.token_hex(12)}"
        self.base_url = base_url

    @property
    def markers(self) -> tuple:
        return (self.api_key.encode(), self.secret_key.encode())

    def kwargs(self) -> Dict[str, str]:
        return {"fi_api_key": self.api_key, "fi_secret_key": self.secret_key, "fi_base_url": self.base_url}

    def column(self) -> dict:
        return {"name": f"column-of-{self.tag}", "data_type": "text"}


class Sink:
    """A loopback HTTP listener that answers the dataset routes and keeps every request it receives."""

    def __init__(self) -> None:
        sink = self
        self.requests: List[bytes] = []
        self.lock = threading.Lock()
        self.dataset_id = str(uuid.uuid4())

        class Handler(BaseHTTPRequestHandler):
            def _record(self) -> bytes:
                length = int(self.headers.get("Content-Length") or 0)
                body = self.rfile.read(length) if length else b""
                raw = self.requestline.encode() + b"\r\n" + bytes(self.headers) + body
                with sink.lock:
                    sink.requests.append(raw)
                return body

            def _answer(self, payload: dict) -> None:
                data = json.dumps(payload).encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)

            def do_GET(self) -> None:  # noqa: N802
                self._record()
                parsed = urlparse(self.path)
                if parsed.path.endswith(Routes.dataset_names.value):
                    name = parse_qs(parsed.query).get("search_text", [""])[0]
                    self._answer({"result": {"datasets": [
                        {"dataset_id": sink.dataset_id, "name": name, "model_type": "GenerativeLLM"},
                    ]}})
                else:
                    self._answer({"status": True})

            def do_POST(self) -> None:  # noqa: N802
                self._record()
                self._answer({"status": True})

            def do_DELETE(self) -> None:  # noqa: N802
                self._record()
                self._answer({"status": True})

            def log_message(self, *args) -> None:
                pass

        self.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.server.daemon_threads = True
        self.base_url = f"http://127.0.0.1:{self.server.server_address[1]}"
        threading.Thread(target=self.server.serve_forever, kwargs={"poll_interval": 0.01}, daemon=True).start()

    def close(self) -> None:
        self.server.shutdown()
        self.server.server_close()

    def snapshot(self) -> List[bytes]:
        with self.lock:
            return list(self.requests)


@pytest.fixture(autouse=True)
def _fresh_cache(monkeypatch):
    monkeypatch.setattr(Dataset, "_dataset_instance_cache", dataset_module.LRUCache(capacity=100))
    monkeypatch.delenv("FI_EXTRA_HEADERS", raising=False)


@pytest.fixture
def sinks():
    made: List[Sink] = []

    def make() -> Sink:
        sink = Sink()
        made.append(sink)
        return sink

    yield make
    for sink in made:
        sink.close()


def _add_columns(caller: Caller) -> Dataset:
    return Dataset.add_dataset_columns(NAME, [caller.column()], **caller.kwargs())


def _tally(sink: Sink, callers: List[Caller]) -> Dict[str, Dict[str, int]]:
    """Per caller: requests at this listener that name it in the body, how many carry its own keys,
    and the bytes of every other caller's keys found at this listener."""
    received = sink.snapshot()
    counts: Dict[str, Dict[str, int]] = {}
    for caller in callers:
        others = [m for other in callers if other is not caller for m in other.markers]
        tagged = [raw for raw in received if f"column-of-{caller.tag}".encode() in raw]
        counts[caller.tag] = {
            "requests": len(tagged),
            "with_own_keys": sum(all(m in raw for m in caller.markers) for raw in tagged),
            "other_key_bytes_in_own_requests": sum(raw.count(m) * len(m) for raw in tagged for m in others),
        }
    return counts


def _expect(counts: Dict[str, Dict[str, int]], tag: str, calls: int) -> None:
    assert counts[tag] == {
        "requests": calls, "with_own_keys": calls, "other_key_bytes_in_own_requests": 0,
    }, f"caller {tag}: {counts}"


def _no_foreign_key_bytes(sink: Sink, owner: Caller, other: Caller) -> None:
    raw = b"".join(sink.snapshot())
    foreign = sum(raw.count(m) * len(m) for m in other.markers)
    assert foreign == 0, f"{foreign} bytes of caller {other.tag}'s keys reached caller {owner.tag}'s listener"


def _run_concurrently(callers: List[Caller]) -> List[Dataset]:
    """One call by the first caller, then 8 threads started together, the callers taking turns."""
    _add_columns(callers[0])
    barrier = threading.Barrier(THREADS)
    plan = [callers[i % len(callers)] for i in range(THREADS)]

    def work(caller: Caller) -> Dataset:
        barrier.wait(timeout=10)
        return _add_columns(caller)

    with ThreadPoolExecutor(max_workers=THREADS) as pool:
        return list(pool.map(work, plan))


def test_sequential_callers_with_their_own_listeners(sinks):
    sink_a, sink_b = sinks(), sinks()
    a, b = Caller("a", sink_a.base_url), Caller("b", sink_b.base_url)
    returned = [(caller, _add_columns(caller)) for caller in (a, b, a, b)]

    counts_a, counts_b = _tally(sink_a, [a, b]), _tally(sink_b, [a, b])
    _expect(counts_a, "a", 2)
    _expect(counts_b, "b", 2)
    assert counts_a["b"]["requests"] == 0 and counts_b["a"]["requests"] == 0, (counts_a, counts_b)
    _no_foreign_key_bytes(sink_a, a, b)
    _no_foreign_key_bytes(sink_b, b, a)
    _objects_are_their_callers_own(returned)


def test_concurrent_callers_with_their_own_listeners(sinks):
    sink_a, sink_b = sinks(), sinks()
    a, b = Caller("a", sink_a.base_url), Caller("b", sink_b.base_url)
    results = _run_concurrently([a, b])

    counts_a, counts_b = _tally(sink_a, [a, b]), _tally(sink_b, [a, b])
    _expect(counts_a, "a", THREADS // 2 + 1)
    _expect(counts_b, "b", THREADS // 2)
    assert counts_a["b"]["requests"] == 0 and counts_b["a"]["requests"] == 0, (counts_a, counts_b)
    _no_foreign_key_bytes(sink_a, a, b)
    _no_foreign_key_bytes(sink_b, b, a)
    plan = [[a, b][i % 2] for i in range(THREADS)]
    _objects_are_their_callers_own(list(zip(plan, results)))


def test_sequential_callers_on_one_listener(sinks):
    shared = sinks()
    a, b = Caller("a", shared.base_url), Caller("b", shared.base_url)
    returned = [(caller, _add_columns(caller)) for caller in (a, b, a, b)]
    counts = _tally(shared, [a, b])
    _expect(counts, "a", 2)
    _expect(counts, "b", 2)
    _objects_are_their_callers_own(returned)


def test_concurrent_callers_on_one_listener(sinks):
    shared = sinks()
    a, b = Caller("a", shared.base_url), Caller("b", shared.base_url)
    results = _run_concurrently([a, b])
    counts = _tally(shared, [a, b])
    _expect(counts, "a", THREADS // 2 + 1)
    _expect(counts, "b", THREADS // 2)
    plan = [[a, b][i % 2] for i in range(THREADS)]
    _objects_are_their_callers_own(list(zip(plan, results)))


def test_lookup_returns_a_distinct_object_with_the_callers_keys(sinks):
    a = Caller("a", sinks().base_url)
    b = Caller("b", sinks().base_url)
    first_a = Dataset.get_dataset_config(NAME, **a.kwargs())
    second_a = Dataset.get_dataset_config(NAME, **a.kwargs())
    first_b = Dataset.get_dataset_config(NAME, **b.kwargs())
    assert len({id(first_a), id(second_a), id(first_b)}) == 3
    assert first_b._fi_api_key == b.api_key and first_b._fi_api_key != a.api_key
    assert first_b._fi_secret_key == b.secret_key
    assert first_b._base_url == b.base_url
    assert first_a.dataset_config is not second_a.dataset_config
    # Changing one returned object does not change what the next lookup returns.
    first_a.dataset_config = None
    assert Dataset.get_dataset_config(NAME, **a.kwargs()).dataset_config is not None


def test_a_repeat_lookup_by_one_caller_reuses_its_own_entry(sinks):
    sink = sinks()
    a = Caller("a", sink.base_url)
    Dataset.get_dataset_config(NAME, **a.kwargs())
    Dataset.get_dataset_config(NAME, **a.kwargs())
    names = [raw for raw in sink.snapshot() if Routes.dataset_names.value.encode() in raw]
    assert len(names) == 1


def test_delete_dataset_evicts_the_entry_of_its_own_caller(sinks):
    sink = sinks()
    a, b = Caller("a", sink.base_url), Caller("b", sink.base_url)
    Dataset.get_dataset_config(NAME, **a.kwargs())
    Dataset.get_dataset_config(NAME, **b.kwargs())
    Dataset.delete_dataset(NAME, **a.kwargs())

    def lookups(caller: Caller) -> int:
        return sum(
            Routes.dataset_names.value.encode() in raw and caller.api_key.encode() in raw for raw in sink.snapshot()
        )

    before_a, before_b = lookups(a), lookups(b)
    Dataset.get_dataset_config(NAME, **a.kwargs())
    Dataset.get_dataset_config(NAME, **b.kwargs())
    assert lookups(a) == before_a + 1  # A's entry went with the delete
    assert lookups(b) == before_b  # B's entry stays


def _objects_are_their_callers_own(pairs: List[tuple]) -> None:
    objects = [obj for _, obj in pairs]
    assert len({id(obj) for obj in objects}) == len(objects), "a returned object was handed to two calls"
    for caller, obj in pairs:
        assert obj._fi_api_key == caller.api_key, f"caller {caller.tag} got another caller's object"
        assert obj._fi_secret_key == caller.secret_key
        assert obj._base_url == caller.base_url

