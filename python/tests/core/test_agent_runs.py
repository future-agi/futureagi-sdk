"""Public run facades against a mock transport and the generated operation table."""
import inspect
import json
from pathlib import Path

import httpx
import pytest

from fi.agents.runs import AsyncRatings, AsyncRun, AsyncRuns, Ratings, Run, Runs
from fi._core.platform_async import AsyncPlatformCore
from fi._core.platform_base import PlatformCore
from fi._core.resumable import StreamBounds
from fi._core.transport import PlatformShared
from fi.errors import APITimeoutError, ConfigurationError, PermissionDeniedError, StreamInterruptedError
from fi.generated.platform.policy import OPERATIONS
from tests.core._support import Recorder, origin, respond, sse
from tests.core.test_resumable import dropped, status, DONE


async def call(value):
    return await value if inspect.isawaitable(value) else value


def setup(mode, rec, retries=0):
    shared = PlatformShared(lambda: origin("http://127.0.0.1:9000/omega/api"),
        table=OPERATIONS, transport=httpx.MockTransport(rec), retries=retries, sleep=lambda _: None)
    core = AsyncPlatformCore(shared) if mode == "async" else PlatformCore(shared)
    return (AsyncRuns(core), AsyncRun, AsyncRatings(core)) if mode == "async" else (Runs(core), Run, Ratings(core))


@pytest.fixture(params=["async", "sync"])
def mode(request):
    return request.param


def raw(state="active", id="run-a"):
    return {"conversation": {"id": id, "status": state, "managedExecution": {"taskId": "task-a"}},
            "receipt": {"auditEntryId": "audit-a"}, "unknownFutureField": True}


CASES = [
    ("runs.create", "runs", "create", (), {"input": "hello", "idempotency_key": "stable-run-key"}),
    ("runs.list", "runs", "list", (), {"limit": 2, "agent_id": "a", "agent_version": 1, "deployment_version": 2,
        "channel_id": "c", "provider_event_id": "p", "external_correlation_id": "e", "status": "active", "cursor": "opaque"}),
    ("runs.get", "runs", "get", ("run-a",), {}),
    ("runs.delete", "runs", "delete", ("run-a",), {}),
    ("runs.send", "run", "send", (), {"input": "next", "idempotency_key": "stable-run-key"}),
    ("runs.cancel", "run", "cancel", (), {}),
    ("runs.interrupt", "run", "interrupt", (), {}),
    ("runs.continue", "run", "resume", (), {"idempotency_key": "stable-run-key"}),
    ("runs.retry", "run", "retry", (), {"reason": "retry", "idempotency_key": "stable-run-key"}),
    ("runs.fork", "run", "fork", (), {"up_to_message_id": "message-a", "idempotency_key": "stable-run-key"}),
    ("runs.tree", "run", "tree", (), {}),
    ("runs.observations", "run", "observations", (), {"task_id": "task-a", "kind": "tool.started", "limit": 20}),
    ("runs.evidence", "run", "evidence", (), {}),
    ("runs.proofPack", "run", "proof_pack", (), {}),
    ("runs.controlStatus", "run", "control_status", (), {}),
    ("runs.approvals", "run", "approvals", (), {}),
    ("runs.rating.get", "rating", "get", (), {}),
    ("runs.rating.set", "rating", "set", (), {"rating": None, "message_id": "message-a"}),
    ("platform.approvals.list", "runs", "list_approvals", (), {"conversation_id": "run-a", "state": "decided", "limit": 2, "cursor": "opaque"}),
    ("platform.ratings.summary", "ratings", "summary", (), {}),
    ("platform.ratings.trajectory", "ratings", "trajectory", (), {}),
]


@pytest.mark.anyio
@pytest.mark.parametrize("op,target,method,args,kwargs", CASES)
async def test_every_json_operation_uses_generated_policy(mode, op, target, method, args, kwargs):
    rec = Recorder(respond(200, {**raw(), "conversations": [], "approvals": []}))
    runs, RunType, ratings = setup(mode, rec)
    run = RunType(runs, raw())
    value = await call(getattr({"runs": runs, "run": run, "rating": run.rating, "ratings": ratings}[target], method)(*args, **kwargs))
    request = rec.requests[0]
    policy = OPERATIONS[op]
    assert request.method == policy.method
    assert request.url.path == "/omega/api" + policy.path.replace("{id}", "run-a")
    assert request.extensions["fi.retry"]["class"] == policy.retry_class
    assert request.headers.get("Idempotency-Key") == ("stable-run-key" if policy.idempotent else None)
    assert request.headers["X-Api-Key"] == "k-test-1234"
    assert request.headers["X-Secret-Key"] == "s-test-1234"
    bodies = {
        "runs.create": {"input": "hello"}, "runs.send": {"input": "next"},
        "runs.retry": {"reason": "retry"}, "runs.fork": {"upToMessageId": "message-a"},
        "runs.rating.set": {"rating": None, "messageId": "message-a"},
    }
    if op in bodies:
        assert json.loads(request.content) == bodies[op]
    if op == "runs.observations":
        assert dict(request.url.params) == {"taskId": "task-a", "kind": "tool.started", "limit": "20"}
    if op == "runs.list":
        assert set(request.url.params) == set(OPERATIONS[op].query)
    if op == "platform.approvals.list":
        assert dict(request.url.params) == {"conversationId": "run-a", "state": "decided", "limit": "2", "cursor": "opaque"}
    if op in ("runs.create", "runs.get", "runs.fork"):
        assert isinstance(value, RunType) and value.id == "run-a"
        assert value.response["receipt"] == {"auditEntryId": "audit-a"}
    if mode == "async":
        await runs._core.shared.aclose()
    else:
        runs._core.shared.close()


def test_case_inventory_matches_run_scope_and_language_twins():
    operations = {row[0] for row in CASES} | {"runs.events"}
    assert operations == {name for name in OPERATIONS if name.startswith("runs.") or name.startswith("platform.ratings.") or name == "platform.approvals.list"}
    for sync, async_ in [(Run, AsyncRun), (Runs, AsyncRuns), (Ratings, AsyncRatings)]:
        assert {n for n in dir(sync) if not n.startswith("_")} == {n for n in dir(async_) if not n.startswith("_")}
        assert not any(hasattr(sync, n) for n in ("approve", "deny", "decide"))


@pytest.mark.anyio
async def test_create_body_wait_refresh_and_envelope(mode):
    rec = Recorder(respond(201, raw()), respond(200, raw("done")))
    runs, _, _ = setup(mode, rec)
    run = await call(runs.create(input="hello", title="title", mode="agent", agent_id="a", agent_session_id="s",
        model_id="fixture-model", message_mode="chat", attachments=[{"itemId": "item-a"}], metadata={"channelId": "c"},
        wait=True, timeout=0, idempotency_key="stable-run-key"))
    assert run.status == "done" and run.identity == {"taskId": "task-a"}
    assert run.response["unknownFutureField"] is True
    assert json.loads(rec.requests[0].content) == {"input":"hello", "title":"title", "mode":"agent", "agentId":"a",
        "agentSessionId":"s", "modelId":"fixture-model", "messageMode":"chat", "attachments":[{"itemId":"item-a"}], "metadata":{"channelId":"c"}}
    assert len(rec.requests) == 2


@pytest.mark.anyio
async def test_waiting_approval_and_unknown_status_are_not_terminal(mode):
    for state in ("waiting_approval", "future-state"):
        rec = Recorder(lambda _: respond(200, raw(state)))
        runs, RunType, _ = setup(mode, rec)
        with pytest.raises(APITimeoutError):
            await call(RunType(runs, raw(state)).wait(timeout=0))
        assert [r.method for r in rec.requests] == ["GET"]


REACTIVATING = [("send", {"input": "next"}), ("retry", {}), ("resume", {})]


@pytest.mark.anyio
@pytest.mark.parametrize("method,kwargs", REACTIVATING)
@pytest.mark.parametrize("state", ["done", "error", "canceled"])
async def test_wait_after_reactivation_reads_the_new_turn(mode, method, kwargs, state):
    receipt = {"accepted": True, "receipt": {"id": "new-turn"}}
    fresh = {**raw("done"), "messages": [{"id": "new-message"}]}
    rec = Recorder(respond(200, raw(state)), respond(202, receipt),
                   respond(200, raw("active")), respond(200, fresh))
    runs, _, _ = setup(mode, rec)
    run = await call(runs.get("run-a"))
    assert await call(getattr(run, method)(**kwargs)) == receipt
    # The last server snapshot remains available, but is no longer completion evidence.
    assert run.status == state and run.response == raw(state)
    assert await call(run.wait(timeout=1, sleep=lambda _: None)) is run
    assert run.response == fresh and run.status == "done"
    assert [r.method for r in rec.requests] == ["GET", "POST", "GET", "GET"]
    assert await call(run.wait(timeout=0)) is run
    assert len(rec.requests) == 4


@pytest.mark.anyio
@pytest.mark.parametrize("method,kwargs", REACTIVATING)
async def test_failed_reactivation_keeps_terminal_snapshot(mode, method, kwargs):
    rec = Recorder(respond(403, {"error": "scope_denied"}))
    runs, RunType, _ = setup(mode, rec)
    run = RunType(runs, raw("done"))
    with pytest.raises(PermissionDeniedError):
        await call(getattr(run, method)(**kwargs))
    assert await call(run.wait(timeout=0)) is run
    assert run.response == raw("done")
    assert [r.method for r in rec.requests] == ["POST"]


@pytest.mark.anyio
async def test_reactivation_read_failure_and_timeout_never_reuse_old_completion(mode):
    rec = Recorder(respond(202, {"accepted": True}), respond(403, {"error": "scope_denied"}),
                   respond(200, raw("active")), respond(200, raw("done")))
    runs, RunType, _ = setup(mode, rec)
    run = RunType(runs, raw("done"))
    await call(run.send(input="next"))
    with pytest.raises(PermissionDeniedError):
        await call(run.wait(timeout=0))
    with pytest.raises(APITimeoutError):
        await call(run.wait(timeout=0))
    assert await call(run.wait(timeout=0)) is run
    assert [r.method for r in rec.requests] == ["POST", "GET", "GET", "GET"]


@pytest.mark.anyio
async def test_pagination_keeps_opaque_cursors_and_filters(mode):
    rec = Recorder(respond(200, {"conversations":[raw()["conversation"]], "nextCursor":"opaque+/="}),
                   respond(200, {"conversations":[raw(id="run-b")["conversation"]], "nextCursor":"opaque+/="}))
    runs, _, _ = setup(mode, rec)
    page = await call(runs.list(agent_id="a", limit=1))
    values = [r.id async for r in page] if mode == "async" else [r.id for r in page]
    assert values == ["run-a", "run-b"]
    assert rec.requests[1].url.params["cursor"] == "opaque+/="
    assert rec.requests[1].url.params["agentId"] == "a"


@pytest.mark.anyio
async def test_events_resume_after_drop_without_duplicates_and_close(mode):
    rec = Recorder(dropped(status(2, "active")), sse(status(2, "active"), status(3, "done"), DONE))
    runs, RunType, _ = setup(mode, rec)
    events = RunType(runs, raw()).events(after=1, bounds=StreamBounds(idle_timeout=7))
    values = [e async for e in events] if mode == "async" else list(events)
    assert [e.get("seq") for e in values] == [2, 3, None]
    assert [r.headers["Last-Event-ID"] for r in rec.requests] == ["1", "2"]
    assert rec.requests[0].extensions["timeout"]["read"] == 7
    assert values[-1]["type"] == "done"


@pytest.mark.anyio
async def test_event_resume_is_bounded_and_reconnect_denials_are_terminal(mode):
    for code in (200, 403):
        rec = Recorder(lambda _: respond(code, b"", {"content-type": "text/event-stream"}))
        runs, RunType, _ = setup(mode, rec)
        events = RunType(runs, raw()).events(after=0, bounds=StreamBounds(max_reconnects=0))
        with pytest.raises(StreamInterruptedError if code == 200 else PermissionDeniedError):
            if mode == "async":
                [e async for e in events]
            else:
                list(events)
        assert len(rec.requests) == 1
        assert rec.requests[0].headers["Last-Event-ID"] == "0"


@pytest.mark.anyio
async def test_explicit_replay_key_survives_retries_and_controls_are_not_retried(mode):
    rec = Recorder(respond(503, {"error":"unavailable"}), respond(201, raw()))
    runs, _, _ = setup(mode, rec, retries=1)
    await call(runs.create(input="hello", idempotency_key="stable-run-key"))
    assert rec.keys == ["stable-run-key", "stable-run-key"]
    from fi.errors import ServerError
    for method in ("cancel", "interrupt"):
        rec = Recorder(lambda _: respond(503, {"error":"unavailable"}))
        runs, RunType, _ = setup(mode, rec, retries=1)
        with pytest.raises(ServerError):
            await call(getattr(RunType(runs, raw()), method)())
        assert len(rec.requests) == 1 and rec.keys == [None]


@pytest.mark.anyio
async def test_permission_denial_and_approvals_are_read_only(mode):
    rec = Recorder(respond(403, {"error":"scope_denied"}))
    runs, _, _ = setup(mode, rec)
    with pytest.raises(PermissionDeniedError):
        await call(runs.get("foreign-run"))
    assert len(rec.requests) == 1
    assert rec.requests[0].method == "GET"
    rec = Recorder(respond(200, {"approvals":[{"approval":{"id":"approval-a"}}]}))
    runs, RunType, _ = setup(mode, rec)
    approvals = await call(RunType(runs, raw()).wait_for_approval(timeout=0))
    assert approvals["approvals"] and rec.requests[0].method == "GET"


@pytest.mark.anyio
async def test_context_cleanup_and_invalid_cursor(mode):
    rec = Recorder(respond(200, raw()), respond(202, {"accepted":True}))
    runs, RunType, _ = setup(mode, rec)
    run = RunType(runs, raw())
    if mode == "async":
        async with run:
            pass
    else:
        with run:
            pass
    assert [r.method for r in rec.requests] == ["GET", "POST"]
    for after in (-1, "01", "1\n", True, "", "1.0"):
        with pytest.raises(ConfigurationError):
            run.events(after=after)


@pytest.mark.anyio
async def test_mixed_credentials_fail_before_any_transport(mode):
    from fi import FutureAGIClient, AsyncFutureAGIClient
    from fi.errors import MixedCredentialsError
    rec = Recorder(respond(200, raw()))
    client = (AsyncFutureAGIClient if mode == "async" else FutureAGIClient)(
        api_key="fixture-api", secret_key="fixture-secret", platform_token="fixture-token",
        base_url="http://127.0.0.1:9000")
    shared = PlatformShared(client._resolve_platform_origin, table=OPERATIONS, transport=httpx.MockTransport(rec))
    core = AsyncPlatformCore(shared) if mode == "async" else PlatformCore(shared)
    client.__dict__["_platform"] = core
    with pytest.raises(MixedCredentialsError):
        await call(client.agents.runs.get("run-a"))
    assert rec.requests == []
    if mode == "async":
        await shared.aclose()
    else:
        shared.close()


def test_run_import_does_not_load_legacy_or_optional_modules():
    import subprocess
    import sys
    result = subprocess.run([sys.executable, "-c", "import sys, fi.agents.runs; assert not any(n == 'fi.utils' or n.startswith(('fi.utils.', 'fi.api', 'fi.experiments')) for n in sys.modules)"], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr


def test_one_client_registration_and_cli(monkeypatch, capsys):
    from fi import FutureAGIClient, AsyncFutureAGIClient
    from fi._cli.main import main
    rec = Recorder(respond(201, raw("done")))
    runs, _, _ = setup("sync", rec)
    client = FutureAGIClient(api_key="fixture-api", secret_key="fixture-secret", base_url="http://127.0.0.1:9000")
    client.__dict__["_platform"] = runs._core
    assert isinstance(client.agents.runs, Runs)
    assert isinstance(AsyncFutureAGIClient().agents.runs, AsyncRuns)
    clone = client.with_options(retries=0)
    assert clone.agents.runs._core is clone._platform
    monkeypatch.setattr("fi.FutureAGIClient", lambda: client)
    assert main(["agents","runs","create","--input","hello","--idempotency-key","stable-run-key","--json"]) == 0
    assert json.loads(capsys.readouterr().out)["id"] == "run-a"
    assert rec.keys == ["stable-run-key"]
