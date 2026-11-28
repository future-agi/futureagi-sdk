"""Result size regressions using the server's ASCII-escaped JSON convention.

The POST recorder below is a mock, not a live API or a server implementation. It
accepts any payload so assertions can inspect exactly what the uploader emitted.
Only pre-existing upload entry points are imported, including on the old source.
"""

import asyncio
import hashlib
import json

import pytest

from fi.experiments._journal import Journal, JournalRecord, load
from fi.experiments._upload import BATCH_MAX_BYTES, UploadRefusedError, Uploader, bounded, project_item
from fi.experiments.evaluators.binding import Binding


FIELD_LIMIT = 262_144
ITEM_LIMIT = 1_048_576
BATCH_LIMIT = 2_097_152
RUN_ID = "00000000-0000-4000-8000-000000000001"


def _server_json(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def _journal_bytes(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
                      allow_nan=False).encode("utf-8")


def _legacy_bounded(value):
    """Frozen pre-repair projection, used only for server-accepted compatibility cases."""
    data = _journal_bytes(value)
    if len(data) <= FIELD_LIMIT:
        return value
    return {"fi_truncated": True, "sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data),
            "prefix": data[:200_000].decode("utf-8", errors="ignore")}


def _record(index, *, output=None, scores=None):
    item = {"example_id": f"00000000-0000-4000-8000-{index:012d}", "trial_number": 1,
            "status": "completed", "output": output, "scores": scores or {}}
    # Synthetic opaque receipts: the uploader must forward them, not recompute them.
    return JournalRecord(item["example_id"], 1, item["status"], f"receipt-{index:04d}", _journal_bytes(item))


def _scores(count):
    bindings, scores = {}, {}
    for index in range(count):
        name = f"score-{index:03d}"
        bindings[name] = Binding(name, f"00000000-0000-4000-8001-{index:012d}", "external", "numeric",
                                 evaluator_version_id=f"00000000-0000-4000-8002-{index:012d}")
        scores[name] = {"status": "assessed", "value": index / 100, "explanation": "x" * 16_384}
    return bindings, scores


def _journal(root, records):
    journal = Journal(RUN_ID, root)
    journal.create({"items": [{"example_id": r.example_id, "trial": r.trial} for r in records]})
    for record in records:
        journal.append(record)
    return journal


async def _no_sleep(_):
    pass


def _recorder(monkeypatch, bindings, on_ack, *, fail_first=False):
    posted = []

    class Unavailable(Exception):
        status_code = 503

    def post(body):
        posted.append(body)
        if fail_first and len(posted) == 1:
            raise Unavailable("temporary mock outage")
        return {"run": {"status": "completed"}}

    uploader = Uploader(object(), RUN_ID, bindings, on_ack=on_ack, sleep=_no_sleep)
    monkeypatch.setattr(uploader, "_post", post)
    return uploader, posted


async def _cleanup(uploader):
    uploader.abort()
    if uploader._task is not None:
        await asyncio.gather(uploader._task, return_exceptions=True)


@pytest.mark.parametrize("value", [
    "é" * 43_690,
    "é" * 43_691,
    "é" * 43_690 + "aa",
    "é" * 43_690 + "aaa",
    "é" * 50_000,
], ids=["last-fitting-character", "first-over-character", "exact-byte-limit", "one-byte-over", "50000-characters"])
def test_non_ascii_field_uses_server_size(value):
    projected = bounded(value)
    if len(_server_json(value)) <= FIELD_LIMIT:
        assert projected is value
    else:
        assert isinstance(projected, dict)
        assert projected["fi_truncated"] is True
        assert projected["sha256"] == hashlib.sha256(_journal_bytes(value)).hexdigest()
        assert projected["bytes"] == len(_journal_bytes(value))
    assert len(_server_json(projected)) <= FIELD_LIMIT
    assert _server_json(bounded(value)) == _server_json(projected)


def test_backslash_marker_is_bounded_without_changing_full_value_digest():
    value = "\\" * 140_000
    original = _legacy_bounded(value)
    assert len(_server_json(original)) > FIELD_LIMIT
    projected = bounded(value)
    assert projected["fi_truncated"] is True
    assert projected["sha256"] == original["sha256"]
    assert projected["bytes"] == original["bytes"] == len(_journal_bytes(value))
    assert original["prefix"].startswith(projected["prefix"])
    assert len(_server_json(projected)) <= FIELD_LIMIT
    # Keep as much of the old prefix as fits, without changing any other field.
    end = len(projected["prefix"])
    assert 0 < end < len(original["prefix"])
    assert len(_server_json({**projected, "prefix": original["prefix"][:end + 1]})) > FIELD_LIMIT
    assert bounded(value) == projected


def test_non_ascii_batches_fit_server_envelope_without_losing_receipts(monkeypatch):
    records = [_record(i, output="é" * 40_000) for i in range(20)]
    projected = [project_item(r.item_bytes, r.receipt_key, {}) for r in records]
    assert all(len(_server_json(p["output"])) <= FIELD_LIMIT for p in projected)
    assert len(_journal_bytes({"items": projected})) < BATCH_MAX_BYTES
    assert len(_server_json({"items": projected})) > BATCH_LIMIT
    acked = []
    uploader, posted = _recorder(monkeypatch, {}, acked.extend)

    async def go():
        uploader.start()
        try:
            for record in records:
                uploader.submit(record.receipt_key, record.item_bytes)
            return await uploader.close()
        finally:
            await _cleanup(uploader)

    stats = asyncio.run(go())
    assert len(posted) >= 3
    assert all(len(_server_json(body)) <= BATCH_LIMIT for body in posted)
    assert all(len(body["items"]) <= 100 for body in posted)
    assert [p for body in posted for p in body["items"]] == projected
    receipts = [r.receipt_key for r in records]
    assert acked == receipts
    assert len(set(acked)) == len(records)
    assert stats.sent == stats.acked == len(records)
    assert stats.pending == 0


@pytest.mark.parametrize("resumed", [False, True], ids=["new", "resumed"])
def test_oversized_scores_refuse_locally_and_keep_journal(monkeypatch, tmp_path, resumed):
    bindings, scores = _scores(65)
    before = _record(1, output="already queued")
    oversized = _record(2, scores=scores)
    after = _record(3, output="submitted after refusal")
    records = [before, oversized, after]
    payload = project_item(oversized.item_bytes, oversized.receipt_key, bindings)
    assert ITEM_LIMIT < len(_server_json(payload)) < BATCH_MAX_BYTES
    assert len(payload["score_refs"]) == 65
    for ref, name in zip(payload["score_refs"], sorted(scores)):
        assert ref == {"metric_id": bindings[name].metric_id,
                       "evaluator_version_id": bindings[name].evaluator_version_id,
                       "status": "assessed", "value": scores[name]["value"], "explanation": "x" * 16_384}
    journal = _journal(tmp_path, records)
    if resumed:
        journal.close()
        records = list(journal.reopen().records.values())
    uploader, posted = _recorder(monkeypatch, bindings, journal.ack)

    async def go():
        uploader.start()
        try:
            # Resume submits synchronously before the engine enters its main try/finally.
            # A local refusal must record a fatal, not raise out of this submission loop.
            for record in records:
                uploader.submit(record.receipt_key, record.item_bytes)
            assert isinstance(uploader.fatal, UploadRefusedError)
            fatal = uploader.fatal
            assert "1048576" in str(fatal)
            assert "full result remains in the journal" in str(fatal)
            assert uploader.stats.error == str(fatal)
            with pytest.raises(UploadRefusedError) as caught:
                await uploader.close()
            assert caught.value is fatal
            assert uploader._task.done()
            # close flushes only valid items queued BEFORE the refusal. Later submissions
            # stay journaled, but are neither uploaded nor acknowledged by this uploader.
            assert [p["receipt_key"] for body in posted for p in body["items"]] == [before.receipt_key]
            assert uploader.stats.sent == uploader.stats.acked == 1
            assert uploader.stats.pending == 2
            with pytest.raises(UploadRefusedError):
                await uploader.close()
            assert uploader.stats.pending == 2
        finally:
            await _cleanup(uploader)

    try:
        asyncio.run(go())
    finally:
        journal.close()
    saved = load(RUN_ID, tmp_path)
    for record in records:
        stored = saved.records[(record.example_id, record.trial)]
        assert stored.item_bytes == record.item_bytes
        assert stored.receipt_key == record.receipt_key
        assert stored.acked is (record.receipt_key == before.receipt_key)
    assert saved.records[(oversized.example_id, 1)].item["scores"] == scores


@pytest.mark.parametrize("delta", [-1, 0, 1], ids=["one-byte-under", "exact-limit", "one-byte-over"])
def test_item_limit_is_independent_of_batch_limit(monkeypatch, delta):
    bindings, scores = _scores(60)
    empty = _record(1, output="", scores=scores)
    overhead = len(_server_json(project_item(empty.item_bytes, empty.receipt_key, bindings)))
    padding = ITEM_LIMIT + delta - overhead
    assert 0 < padding < FIELD_LIMIT - 2
    record = _record(1, output="x" * padding, scores=scores)
    payload = project_item(record.item_bytes, record.receipt_key, bindings)
    assert len(_server_json(payload)) == ITEM_LIMIT + delta
    assert len(_server_json({"items": [payload]})) < BATCH_MAX_BYTES
    acked = []
    uploader, posted = _recorder(monkeypatch, bindings, acked.extend)

    async def go():
        uploader.start()
        try:
            uploader.submit(record.receipt_key, record.item_bytes)
            if delta > 0:
                assert isinstance(uploader.fatal, UploadRefusedError)
                with pytest.raises(UploadRefusedError):
                    await uploader.close()
                assert posted == acked == []
                assert uploader.stats.pending == 1
            else:
                assert uploader.fatal is None
                stats = await uploader.close()
                assert posted == [{"items": [payload]}]
                assert acked == [record.receipt_key]
                assert stats.acked == 1 and stats.pending == 0
            assert uploader._task.done()
        finally:
            await _cleanup(uploader)

    asyncio.run(go())


@pytest.mark.parametrize("value", ["plain ASCII", {"text": "café", "count": 2}, "é" * 43_690, "x" * 300_000],
                         ids=["ascii", "unicode-object", "unicode-boundary", "accepted-ascii-marker"])
def test_accepted_projection_receipt_and_journal_survive_retry_and_resume(monkeypatch, tmp_path, value):
    record = _record(1, output=value)
    expected = {"example_id": record.example_id, "trial_number": 1, "receipt_key": record.receipt_key,
                "status": "completed", "output": _legacy_bounded(value), "error": None,
                "trace_id": None, "root_span_id": None, "latency_ms": None, "token_usage": None,
                "cost": None, "score_refs": []}
    assert len(_server_json(expected["output"])) <= FIELD_LIMIT
    assert len(_server_json(expected)) <= ITEM_LIMIT
    assert _server_json(project_item(record.item_bytes, record.receipt_key, {})) == _server_json(expected)
    journal = _journal(tmp_path, [record])
    # Simulate an accepted upload with no acknowledgment recorded in the journal.
    first_acks = []
    first, first_posts = _recorder(monkeypatch, {}, first_acks.extend, fail_first=True)

    async def send(uploader, item):
        uploader.start()
        try:
            uploader.submit(item.receipt_key, item.item_bytes)
            return await uploader.close()
        finally:
            await _cleanup(uploader)

    try:
        stats = asyncio.run(send(first, record))
        assert stats.retries == 1 and stats.acked == 1
        assert first_acks == [record.receipt_key]
    finally:
        journal.close()
    resumed = journal.reopen().records[(record.example_id, 1)]
    assert not resumed.acked
    assert resumed.item_bytes == record.item_bytes
    assert resumed.receipt_key == record.receipt_key
    second, second_posts = _recorder(monkeypatch, {}, journal.ack)
    try:
        stats = asyncio.run(send(second, resumed))
        assert stats.retries == 0 and stats.acked == 1
    finally:
        journal.close()
    expected_body = _server_json({"items": [expected]})
    assert len(first_posts) == 2 and len(second_posts) == 1
    assert all(_server_json(body) == expected_body for body in first_posts + second_posts)
    saved = load(RUN_ID, tmp_path).records[(record.example_id, 1)]
    assert saved.acked
    assert saved.item_bytes == record.item_bytes
    assert saved.receipt_key == record.receipt_key
    assert _server_json(project_item(saved.item_bytes, saved.receipt_key, {})) == _server_json(expected)
