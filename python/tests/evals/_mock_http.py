"""A recording fake of the Future AGI eval API, installed under ``requests`` (no socket is opened).

The fake replaces ``requests.adapters.HTTPAdapter.send``, so every request ``fi.evals`` makes, through
the shared ``FuturesSession`` or a plain ``requests.get``, is answered here and recorded. The same file
runs against the published ai-evaluation 1.1.0 (``record_upstream.py`` writes its answers as the
golden file) and against this package (``test_compat_examples.py`` compares the two), so it imports
nothing but ``requests`` and the standard library.
"""

from __future__ import annotations

import contextlib
import dataclasses
import enum
import json
import re
import threading
from typing import Any, Callable, Dict, Iterator, List, Optional, Tuple
from urllib.parse import parse_qsl, urlsplit

import requests
from requests.adapters import HTTPAdapter

KEY, SECRET = "key-A", "secret-A"
BASE_URL = "http://127.0.0.1:9"

# The eval registry the fake serves at GET sdk/api/v1/get-evals/ (the cloud registry and
# Evaluator.list_evaluations read it).
REGISTRY: List[Dict[str, Any]] = [
    {"name": "toxicity", "eval_id": 15, "id": "tmpl-toxicity", "config": {"required_keys": ["output"]}},
    {"name": "tone", "eval_id": 16, "id": "tmpl-tone", "config": {"required_keys": ["output"]}},
    {"name": "groundedness", "eval_id": 47, "id": "tmpl-groundedness", "config": {"required_keys": ["output", "context"]}},
    {"name": "name-of-your-eval", "eval_id": 0, "id": "tmpl-custom", "config": {"required_keys": ["input", "output"]}},
]

Answer = Tuple[int, Any]
Route = Callable[[Dict[str, Any]], Answer]


def _evaluation(name: str, model: Any, eval_id: str = "e-1") -> Dict[str, Any]:
    return {
        "name": name,
        "output": "Passed",
        "reason": "fake reason for " + str(name),
        "runtime": 12,
        "output_type": "Pass/Fail",
        "eval_id": eval_id,
        "model": model,
    }


def _new_eval(call: Dict[str, Any]) -> Answer:
    body = call["json"] or {}
    if body.get("is_async"):
        return 200, {"status": True, "result": [{"evaluations": [
            {"name": body.get("eval_name"), "output_type": "Pass/Fail", "eval_id": "exec-1"}]}]}
    return 200, {"status": True, "result": [{"evaluations": [_evaluation(body.get("eval_name"), body.get("model"))]}]}


def _eval_status(call: Dict[str, Any]) -> Answer:
    eval_id = dict(call["query"]).get("eval_id", "")
    return 200, {"status": True, "result": {"eval_status": "completed",
                                            "result": _evaluation("toxicity", "turing_flash", eval_id)}}


def _protect(call: Dict[str, Any]) -> Answer:
    body = call["json"] or {}
    names = list((body.get("config") or {}).keys()) or ["?"]
    return 200, {"status": True, "result": [{"evaluations": [_evaluation("protect-" + str(names[0]), None, str(names[0]))]}]}


def default_routes() -> Dict[Tuple[str, str], Route]:
    return {
        ("GET", "/sdk/api/v1/get-evals/"): lambda call: (200, {"status": True, "result": REGISTRY}),
        ("POST", "/sdk/api/v1/new-eval/"): _new_eval,
        ("GET", "/sdk/api/v1/new-eval/"): _eval_status,
        ("POST", "/sdk/api/v1/eval/"): _protect,
        ("POST", "/sdk/api/v1/evaluate-pipeline/"): lambda call: (200, {"status": True, "result": {"accepted": True}}),
        ("GET", "/sdk/api/v1/evaluate-pipeline/"): lambda call: (200, {"status": True, "result": {"versions": []}}),
        ("GET", "/model-hub/eval-templates/list/"): lambda call: (200, {"status": True, "result": {
            "items": [{"id": "tmpl-tone", "name": "tone"}], "total": 1, "page": 0, "page_size": 25}}),
        ("POST", "/model-hub/eval-templates/list/"): lambda call: (200, {"status": True, "result": {
            "items": [{"id": "tmpl-tone", "name": "tone"}], "total": 1, "page": 0, "page_size": 25}}),
    }


class FakeBackend:
    """Answers every request from a route table and records it. Unknown routes get a 404."""

    def __init__(self, overrides: Optional[Dict[Tuple[str, str], Route]] = None) -> None:
        self.routes = default_routes()
        self.routes.update(overrides or {})
        self.calls: List[Dict[str, Any]] = []
        self._lock = threading.Lock()

    def send(self, request: requests.PreparedRequest) -> requests.Response:
        url = urlsplit(request.url or "")
        body = request.body
        if isinstance(body, bytes):
            body = body.decode("utf-8", "replace")
        try:
            parsed = json.loads(body) if body else None
        except ValueError:
            parsed = {"<non-json body>": True}
        call = {
            "method": request.method,
            "host": url.netloc,
            "path": url.path,
            "query": [list(pair) for pair in sorted(parse_qsl(url.query))],
            "x_api_key": request.headers.get("X-Api-Key"),
            "x_secret_key": request.headers.get("X-Secret-Key"),
            "json": parsed,
        }
        with self._lock:
            self.calls.append(call)
        route = self.routes.get((str(request.method), url.path))
        status, payload = route(call) if route else (404, {"detail": "not found"})
        response = requests.Response()
        response.status_code = status
        response._content = json.dumps(payload).encode("utf-8")
        response.headers["Content-Type"] = "application/json"
        response.encoding = "utf-8"
        response.url = request.url or ""
        response.request = request
        response.reason = "OK" if status < 400 else "Error"
        return response


@contextlib.contextmanager
def serve(backend: FakeBackend) -> Iterator[FakeBackend]:
    original = HTTPAdapter.send

    def send(self: HTTPAdapter, request: requests.PreparedRequest, *args: Any, **kwargs: Any) -> requests.Response:
        return backend.send(request)

    HTTPAdapter.send = send  # type: ignore[method-assign]
    try:
        yield backend
    finally:
        HTTPAdapter.send = original  # type: ignore[method-assign]


VOLATILE = {"time_taken", "latency_ms", "duration_ms", "elapsed", "elapsed_ms", "timestamp", "created_at"}


def dump(obj: Any, depth: int = 0) -> Any:
    """A JSON-able view of a result: pydantic models, dataclasses, enums and containers, with the
    timing fields replaced by a marker so two runs compare equal."""
    if depth > 12:
        return "<deep>"
    if hasattr(obj, "model_dump") and callable(obj.model_dump):
        return dump(obj.model_dump(), depth + 1)
    if dataclasses.is_dataclass(obj) and not isinstance(obj, type):
        return dump({f.name: getattr(obj, f.name) for f in dataclasses.fields(obj)}, depth + 1)
    if isinstance(obj, enum.Enum):
        return dump(obj.value, depth + 1)
    if isinstance(obj, dict):
        return {str(k): ("<volatile>" if str(k) in VOLATILE else dump(v, depth + 1)) for k, v in obj.items()}
    if isinstance(obj, (list, tuple, set, frozenset)):
        items = [dump(v, depth + 1) for v in obj]
        return sorted(items, key=repr) if isinstance(obj, (set, frozenset)) else items
    if isinstance(obj, float):
        return round(obj, 6)
    if obj is None or isinstance(obj, (str, int, bool)):
        return obj
    if callable(obj):
        return {"callable": getattr(obj, "__name__", type(obj).__name__)}
    return {"type": type(obj).__name__}


def _no_paths(text: str) -> str:
    """An error message with the install location of ``fi`` replaced, so two environments compare."""
    return re.sub(r"[^\s'\"()]*/fi/", "<site>/fi/", text)


def run_example(fn: Callable[[], Any], backend: Optional[FakeBackend] = None) -> Dict[str, Any]:
    """Run one example under the fake and return what it sent and what it returned (or raised)."""
    backend = backend or FakeBackend()
    with serve(backend):
        try:
            outcome: Dict[str, Any] = {"result": dump(fn())}
        except BaseException as exc:  # noqa: BLE001 - the outcome of a raising example is the record
            if isinstance(exc, (KeyboardInterrupt, SystemExit)):
                raise
            outcome = {"raised": type(exc).__name__, "message": _no_paths(str(exc))[:500]}
    calls = sorted(backend.calls, key=lambda c: json.dumps(c, sort_keys=True, default=str))
    outcome["requests"] = calls
    return outcome


def reset_caches() -> None:
    """Clear the module-level caches ``fi.evals`` keeps between calls (the cloud registry)."""
    try:
        from fi.evals.core import cloud_registry
    except ImportError:
        return
    with cloud_registry._CACHE_LOCK:
        cloud_registry._CACHE.clear()
