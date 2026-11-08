"""Streaming upload of journaled items to the experiment-run API.

- The run is created (or replayed: same UUID and body → 200) with ``POST /model-hub/experiment-runs/``
  before the first trial. The exact create body is kept in ``plan.json`` so ``--resume`` re-sends it
  byte for byte.
- Each item is journaled first, then queued. A batch goes to ``POST .../{run}/results/`` when 25
  items are ready or 2 s after the first one queued; a batch holds at most 100 items and 2 MiB.
- What is sent for an item is a pure function of its journaled bytes and the run specification's metric bindings
  (``project_item``), so a replay sends the identical payload and the server treats it as a no-op.
  ``receipt_key`` is the journal's receipt over those bytes.
- A 429, a 5xx or a network error is retried with backoff (1, 2, 4 … 30 s) while the run keeps
  journaling; after ``GIVE_UP_S`` of failures the upload stops and the run ends with exit 3 and the
  ``--resume`` line. That includes a gateway's own page for a server that is restarting (an HTML 502).
- A 409 (same identity, different payload) or any other status stops the run at once with the server's
  message. An answer that is not the API's JSON names its HTTP status and the page's title
  (``NonJSONAnswerError``, ``_api_answer``): a proxy's 413 for a batch over its body limit is refused
  at once, not retried until ``GIVE_UP_S``.
- Acked receipts are journaled, so a resume re-sends only what the server never confirmed.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Mapping, Optional, Sequence

from fi.experiments import _debug
from fi.experiments._api_answer import NonJSONAnswerError, post
from fi.experiments.errors import ExperimentError

BATCH_ITEMS = 25
BATCH_MAX_ITEMS = 100
BATCH_MAX_BYTES = 2 * 1024 * 1024 - 4096  # the server's 2 MiB body limit, minus the envelope
FLUSH_EVERY_S = 2.0
FIELD_MAX_BYTES = 262_144  # output / error / token_usage, each
PREFIX_BYTES = 200_000
BACKOFF_S = (1.0, 2.0, 4.0, 8.0, 16.0, 30.0)
GIVE_UP_S = 300.0
EXPLANATION_MAX = 16_384


class UploadConflictError(ExperimentError):
    """The server already holds a different payload for one of these identities (HTTP 409)."""

    code = "UPLOAD_CONFLICT"


class UploadRefusedError(ExperimentError):
    code = "UPLOAD_REFUSED"


class UploadStalledError(ExperimentError):
    code = "UPLOAD_STALLED"


# ---- the projection -------------------------------------------------------------------------------


def _canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")


def bounded(value: Any) -> Any:
    """``value`` itself, or (over 256 KiB as canonical JSON) a marker with its sha256, size and a
    UTF-8-safe prefix. The full value stays in the journal."""
    if value is None:
        return None
    data = _canonical(value)
    if len(data) <= FIELD_MAX_BYTES:
        return value
    return {
        "fi_truncated": True,
        "sha256": hashlib.sha256(data).hexdigest(),
        "bytes": len(data),
        "prefix": data[:PREFIX_BYTES].decode("utf-8", errors="ignore"),
    }


def score_ref(score: Mapping[str, Any], metric_id: str, evaluator_version_id: str) -> dict[str, Any]:
    status = {"assessed": "assessed", "error": "error"}.get(str(score.get("status") or "assessed"), "not_assessed")
    value = score.get("value")
    if value is None and score.get("passed") is not None:
        value = 1.0 if score.get("passed") else 0.0
    ref: dict[str, Any] = {"metric_id": metric_id, "evaluator_version_id": evaluator_version_id, "status": status,
                           "value": float(value) if value is not None and status == "assessed" else None}
    explanation = score.get("explanation") or score.get("label")
    if explanation:
        ref["explanation"] = str(explanation)[:EXPLANATION_MAX]
    return ref


def project_item(item_bytes: bytes, receipt: str, bindings: Mapping[str, Any]) -> dict[str, Any]:
    """The ``ExternalRunResult`` for one journaled item. ``bindings``: score name → Binding."""
    item = json.loads(item_bytes.decode("utf-8"))
    refs = []
    for name in sorted(item.get("scores") or {}):
        b = bindings.get(name)
        if b is not None and b.evaluator_version_id:
            refs.append(score_ref(item["scores"][name], b.metric_id, b.evaluator_version_id))
    out = {
        "example_id": str(item["example_id"]),
        "trial_number": int(item.get("trial_number") or 1),
        "receipt_key": receipt,
        "status": item["status"],
        "output": bounded(item.get("output")),
        "error": bounded(item.get("error")),
        "trace_id": item.get("trace_id") or None,
        "root_span_id": item.get("root_span_id") or None,
        "latency_ms": item.get("latency_ms"),
        "token_usage": bounded(item.get("token_usage")),
        "cost": item.get("cost"),
        "score_refs": refs,
    }
    return out


def create_body(*, run_id: str, dataset_version_id: str, identities: Sequence[tuple[str, int]],
                metric_ids: Sequence[str], experiment_id: Optional[str], model_config: Mapping[str, Any],
                metadata: Mapping[str, Any]) -> dict[str, Any]:
    body: dict[str, Any] = {
        "run_id": run_id,
        "dataset_version_id": dataset_version_id,
        "expected_items": [{"example_id": e, "trial_number": int(t)} for e, t in identities],
        "evaluator_metric_ids": list(dict.fromkeys(metric_ids)),
        "model_config": dict(model_config),
        "metadata": dict(metadata),
    }
    if experiment_id:
        body["experiment_id"] = experiment_id
    return body


def _result(payload: Any) -> Any:
    return payload["result"] if isinstance(payload, Mapping) and "result" in payload else payload


def _status_of(exc: BaseException) -> Optional[int]:
    status = getattr(exc, "status_code", None)
    return status if isinstance(status, int) else None


def _message(exc: BaseException) -> str:
    payload = getattr(exc, "payload", None)
    if isinstance(payload, Mapping):
        for key in ("message", "detail", "error", "result"):
            if payload.get(key):
                return str(payload[key])[:1000]
    return str(exc)[:1000]


def _transient(exc: BaseException) -> bool:
    """A 429, a 5xx (a JSON error or a gateway's page alike) or a network error."""
    status = _status_of(exc)
    if status is not None:
        return status == 429 or status >= 500
    import httpx

    return isinstance(exc, httpx.TransportError)


def _why(exc: BaseException) -> str:
    """``HTTP <status>``, else the error's type."""
    status = _status_of(exc)
    return f"HTTP {status}" if status is not None else type(exc).__name__


# ---- the run ------------------------------------------------------------------------------------


CREATE_RETRY_S = (1.0, 2.0, 4.0)


def create_run(client: Any, body: Mapping[str, Any], *, sleep: Callable[[float], Any] = time.sleep) -> dict[str, Any]:
    """Create or replay the run; returns the header. The same run id and body is a replay (200),
    so a 429, 5xx or network error is retried here (after 1, 2, 4 s), although the transport
    repeats no POST on a 5xx."""
    from fi.generated.openapi_client.api.experiment_runs import create_external_experiment_run as op
    from fi.generated.openapi_client.models.external_run_create_request import ExternalRunCreateRequest
    from fi.generated.openapi_client.models.external_run_create_response import ExternalRunCreateResponse

    for delay in (*CREATE_RETRY_S, None):
        try:
            res = post(client, op, ExternalRunCreateResponse, body=ExternalRunCreateRequest.from_dict(dict(body)))
            break
        except Exception as exc:
            status = _status_of(exc)
            if status == 409:
                raise UploadConflictError(f"the server refused the run plan: {_message(exc)}") from exc
            if isinstance(exc, NonJSONAnswerError) and (delay is None or not _transient(exc)):
                raise UploadRefusedError(f"the run was not created (HTTP {status}): {exc}") from exc
            if status is not None and 400 <= status < 500 and status != 429:
                raise UploadRefusedError(f"the server refused the run (HTTP {status}): {_message(exc)}") from exc
            if delay is None or not _transient(exc):
                raise
            sleep(delay)
    to_dict = getattr(res, "to_dict", None)
    return _result(to_dict() if callable(to_dict) else res)


@dataclass
class UploadStats:
    sent: int = 0
    acked: int = 0
    batches: int = 0
    retries: int = 0
    pending: int = 0
    header: Optional[dict] = None
    error: Optional[str] = None
    receipts: list = field(default_factory=list)


class Uploader:
    """Queues journaled items and streams them in batches on a background task."""

    def __init__(self, client: Any, run_id: str, bindings: Mapping[str, Any], *,
                 on_ack: Callable[[list[str]], None], say: Callable[[str], None] = lambda _: None,
                 clock: Callable[[], float] = time.monotonic, sleep: Callable[[float], Any] = asyncio.sleep) -> None:
        self.client = client
        self.run_id = run_id
        self.bindings = bindings
        self.on_ack = on_ack
        self.say = say
        self.clock = clock
        self.sleep = sleep
        self.stats = UploadStats()
        self.fatal: Optional[BaseException] = None
        self._queue: list[tuple[str, dict, int]] = []
        self._first_at: Optional[float] = None
        self._wake: Optional[asyncio.Event] = None
        self._closing = False
        self._task: Optional[asyncio.Task] = None

    def start(self) -> None:
        self._wake = asyncio.Event()
        self._task = asyncio.ensure_future(self._loop())

    def submit(self, receipt: str, item_bytes: bytes) -> None:
        if self.fatal is not None:
            return
        payload = project_item(item_bytes, receipt, self.bindings)
        self._queue.append((receipt, payload, len(_canonical(payload))))
        if self._first_at is None:
            self._first_at = self.clock()
        if self._wake is not None and len(self._queue) >= BATCH_ITEMS:
            self._wake.set()

    def _take(self) -> list[tuple[str, dict, int]]:
        batch: list[tuple[str, dict, int]] = []
        size = 0
        while self._queue and len(batch) < BATCH_MAX_ITEMS:
            entry = self._queue[0]
            if batch and size + entry[2] > BATCH_MAX_BYTES:
                break
            batch.append(self._queue.pop(0))
            size += entry[2]
        self._first_at = self.clock() if self._queue else None
        return batch

    def _ready(self) -> bool:
        if not self._queue:
            return False
        if self._closing or len(self._queue) >= BATCH_ITEMS:
            return True
        return self._first_at is not None and self.clock() - self._first_at >= FLUSH_EVERY_S

    async def _loop(self) -> None:
        assert self._wake is not None
        while True:
            if self._ready():
                batch = self._take()
                try:
                    await self._send(batch)
                except BaseException as exc:
                    self.fatal = exc
                    self.stats.error = str(exc)
                    self._queue[:0] = batch
                    return
                continue
            if self._closing and not self._queue:
                return
            self._wake.clear()
            try:
                await asyncio.wait_for(self._wake.wait(), timeout=0.25)
            except asyncio.TimeoutError:
                pass

    async def _send(self, batch: list[tuple[str, dict, int]]) -> None:
        body = {"items": [p for _, p, _ in batch]}
        failing_since: Optional[float] = None
        attempt = 0
        while True:
            try:
                res = await asyncio.to_thread(self._post, body)
            except Exception as exc:
                status = _status_of(exc)
                _debug.log.debug("upload batch of %d item(s) -> %s (attempt %d)", len(batch), _why(exc), attempt + 1)
                if status == 409:
                    raise UploadConflictError(
                        f"the server holds a different result for an item in this run ({_message(exc)}). The "
                        "journal no longer matches what was uploaded; start a new run"
                    ) from exc
                if not _transient(exc):
                    raise UploadRefusedError(f"a batch upload failed ({_why(exc)}): {_message(exc)}") from exc
                now = self.clock()
                failing_since = failing_since if failing_since is not None else now
                if now - failing_since >= GIVE_UP_S:
                    raise UploadStalledError(
                        f"uploads failed for {GIVE_UP_S:.0f} s ({_why(exc)}: {_message(exc)})"
                    ) from exc
                delay = BACKOFF_S[min(attempt, len(BACKOFF_S) - 1)]
                attempt += 1
                self.stats.retries += 1
                if attempt == 1:
                    who = " from a gateway or proxy" if isinstance(exc, NonJSONAnswerError) else ""
                    self.say(f"Upload   retrying ({_why(exc)}{who}); the run keeps journaling")
                await self.sleep(delay)
                continue
            receipts = [r for r, _, _ in batch]
            _debug.log.debug("upload batch of %d item(s) -> acked (attempt %d)", len(batch), attempt + 1)
            self.stats.sent += len(batch)
            self.stats.batches += 1
            self.stats.acked += len(batch)
            header = (res or {}).get("run") if isinstance(res, Mapping) else None
            if header:
                self.stats.header = header
            self.on_ack(receipts)
            return

    def _post(self, body: Mapping[str, Any]) -> Any:
        from fi.generated.openapi_client.api.experiment_runs import ingest_external_experiment_results as op
        from fi.generated.openapi_client.models.external_run_results_request import ExternalRunResultsRequest
        from fi.generated.openapi_client.models.external_run_results_response import ExternalRunResultsResponse

        res = post(self.client, op, ExternalRunResultsResponse, str(self.run_id),
                   body=ExternalRunResultsRequest.from_dict(dict(body)))
        to_dict = getattr(res, "to_dict", None)
        return _result(to_dict() if callable(to_dict) else res)

    def abort(self) -> None:
        if self._task is not None and not self._task.done():
            self._task.cancel()

    async def close(self) -> UploadStats:
        """Flush everything queued; raise the upload's fatal error, if any."""
        self._closing = True
        if self._wake is not None:
            self._wake.set()
        if self._task is not None:
            await self._task
        self.stats.pending = len(self._queue)
        if self.fatal is not None:
            raise self.fatal
        return self.stats
