"""Public Console facades exercised through real policy executors and mock HTTP."""
from __future__ import annotations

import asyncio
import json
from pathlib import Path

import httpx
import pytest
from fi import AsyncFutureAGIClient, FutureAGIClient, errors
from fi._core.platform_async import AsyncPlatformCore
from fi._core.platform_base import PlatformCore
from fi._core.transport import PlatformShared
from fi.generated.platform.policy import OPERATIONS

ROOT = Path(__file__).resolve().parents[3]
# Public API names and wire paths are independent of the generated policy table.
CASES = [
    ("agents.list", (), "GET", "/workspace/workforce", None, False),
    ("agents.get", ("a b",), "GET", "/workspace/workforce/agents/a%20b", None, False),
    ("agents.create", (), "POST", "/workspace/workforce/agents", {"name": "Agent", "role": "Analyst", "purpose": "Review", "responsibilities": [], "workMode": "on_demand", "connectorBindingIds": []}, False),
    ("agents.update", ("a",), "PATCH", "/workspace/workforce/agents/a", {"purpose": "New", "expectedVersion": 2, "environmentId": None, "environmentRevision": None}, False),
    ("agents.retire", ("a",), "DELETE", "/workspace/workforce/agents/a", None, False),
    ("agents.draft", (), "POST", "/workspace/workforce/agent-drafts", {"message": "Draft an analyst"}, True),
    ("agents.revisions", ("a",), "GET", "/workspace/workforce/agents/a/revisions", None, False),
    ("agents.rollback_revision", ("a", 2), "POST", "/workspace/workforce/agents/a/revisions/2/rollback", {"expectedVersion": 3}, True),
    ("agents.releases", ("a",), "GET", "/workspace/workforce/agents/a/deployments", None, False),
    ("agents.rollback_release", ("a", 2), "POST", "/workspace/workforce/agents/a/deployments/2/rollback", {"expectedDeploymentVersion": 3, "expectedProcessId": "p"}, True),
    ("agents.schedules.list", (), "GET", "/workspace/schedules", None, False),
    ("agents.schedules.get", ("s",), "GET", "/workspace/schedules/s", None, False),
    ("agents.schedules.create", (), "POST", "/workspace/schedules", {"prompt": "Review", "cadence": "daily", "enabled": False}, True),
    ("agents.schedules.update", ("s",), "PATCH", "/workspace/schedules/s", {"enabled": False}, False),
    ("agents.schedules.delete", ("s",), "DELETE", "/workspace/schedules/s", None, False),
    ("agents.schedules.run_now", ("s",), "POST", "/workspace/schedules/s/run", {}, True),
    ("environments.list", (), "GET", "/workspace/environments", None, False),
    ("environments.get", ("e",), "GET", "/workspace/environments/e", None, False),
    ("environments.create", (), "POST", "/workspace/environments", {"name": "Local", "sandboxKind": "local", "resourcePreset": "small", "browserOrigins": [], "credentialBindingIds": []}, True),
    ("environments.revisions", ("e",), "GET", "/workspace/environments/e/revisions", None, False),
    ("environments.get_revision", ("e", 2), "GET", "/workspace/environments/e/revisions/2", None, False),
    ("environments.revise", ("e",), "POST", "/workspace/environments/e/revisions", {"name": "Local", "sandboxKind": "local", "resourcePreset": "small", "browserOrigins": [], "credentialBindingIds": [], "baseRevision": 1}, True),
    ("environments.control", ("e",), "POST", "/workspace/environments/e/control", {"action": "pause", "expectedRevision": 2}, True),
]


def lookup(client, name):
    for part in name.split("."):
        client = getattr(client, part)
    return client


def client_with_transport(asynchronous, handler, retries=0):
    cls = AsyncFutureAGIClient if asynchronous else FutureAGIClient
    client = cls(api_key="person-key", secret_key="person-secret", base_url="http://127.0.0.1:1",
                 organization_id="org-a", workspace_id="ws-a", retries=retries)
    shared = PlatformShared(client._resolve_platform_origin, transport=httpx.MockTransport(handler),
                            retries=retries, sleep=lambda _: None)
    client.__dict__["_platform"] = (AsyncPlatformCore if asynchronous else PlatformCore)(shared)
    return client


def invoke(client, name, args=(), kwargs=None):
    value = lookup(client, name)(*args, **(kwargs or {}))
    return asyncio.run(value) if asyncio.iscoroutine(value) else value


def close(client):
    if isinstance(client, AsyncFutureAGIClient):
        asyncio.run(client.aclose())
    else:
        client.close()


@pytest.mark.parametrize("asynchronous", [False, True])
@pytest.mark.parametrize("case", CASES, ids=[c[0] for c in CASES])
def test_every_public_operation_round_trips(asynchronous, case):
    name, args, method, path, body, keyed = case
    calls = []
    response = {"schemaVersion": "future-version", "unknown": {"kept": True}, "items": []}
    def handler(request):
        calls.append(request)
        assert request.method == method
        assert request.url.raw_path.decode() == "/omega/api" + path
        assert request.headers["X-Api-Key"] == "person-key"
        assert request.headers["X-Secret-Key"] == "person-secret"
        assert request.headers["X-Organization-Id"] == "org-a"
        assert request.headers["X-Workspace-Id"] == "ws-a"
        assert ("Idempotency-Key" in request.headers) is keyed
        assert (json.loads(request.content) if request.content else None) == body
        assert request.extensions["timeout"]["read"] == 4
        return httpx.Response(200, json=response)
    client = client_with_transport(asynchronous, handler)
    kwargs = {"timeout": 4}
    if body is not None:
        kwargs["body"] = body
    if keyed:
        kwargs["idempotency_key"] = "retry-the-same-write"
    try:
        assert invoke(client, name, args, kwargs) == response
        assert len(calls) == 1
    finally:
        close(client)


@pytest.mark.parametrize("asynchronous", [False, True])
@pytest.mark.parametrize("case", CASES, ids=[c[0] for c in CASES])
def test_raw_response_preserves_data_and_metadata_for_every_operation(asynchronous, case):
    from uuid import UUID

    from fi._core.raw import RawResponse

    name, args, _, _, body, keyed = case
    namespace, method = name.rsplit(".", 1)
    calls = []
    response = {"schemaVersion": "future-version", "unknown": {"kept": True}, "items": []}

    def handler(request):
        calls.append(request)
        return httpx.Response(200, json=response, headers={
            "x-request-id": "request-" + str(len(calls)),
            "x-ratelimit-remaining": "9",
            "set-cookie": "session=private",
        })

    client = client_with_transport(asynchronous, handler)
    kwargs = {"body": body} if body is not None else {}
    try:
        assert invoke(client, name, args, kwargs) == response
        raw = invoke(client, namespace + ".with_raw_response." + method, args, kwargs)
        assert isinstance(raw, RawResponse)
        assert raw.data == response and raw.parse() == response
        assert raw.request_id == "request-2" and raw.status_code == 200
        assert raw.headers["x-request-id"] == "request-2"
        assert raw.rate_limit == {"x-ratelimit-remaining": "9"}
        assert raw.headers["set-cookie"] == "[redacted]"
        assert raw.meta.attempts == 1 and not raw.meta.idempotent_replay
        assert raw.idempotency_key == calls[1].headers.get("Idempotency-Key")
        if keyed:
            assert UUID(raw.idempotency_key).version == 4
            assert raw.idempotency_key != calls[0].headers["Idempotency-Key"]
        else:
            assert raw.idempotency_key is None
        # The raw proxy must not leak response metadata into the next plain call.
        assert invoke(client, name, args, kwargs) == response
        assert len(calls) == 3
    finally:
        close(client)


@pytest.mark.parametrize("asynchronous", [False, True])
@pytest.mark.parametrize("name,args,body", [
    ("agents.with_raw_response.draft", (), {"message": "Draft"}),
    ("agents.schedules.with_raw_response.create", (), {"prompt": "Review", "cadence": "daily"}),
    ("environments.with_raw_response.create", (), CASES[18][4]),
    ("agents.schedules.with_raw_response.run_now", ("s",), {"idempotencyKey": "caller-write-key"}),
])
def test_raw_response_reports_the_callers_key_after_a_retry(asynchronous, name, args, body):
    calls = []

    def handler(request):
        calls.append(request)
        assert request.headers["Idempotency-Key"] == "caller-write-key"
        # Environment writes are keyed-not-durable: only 429 is retryable after a response.
        return httpx.Response(429 if len(calls) == 1 else 200, json={"ok": True}, headers={
            "x-request-id": "attempt-" + str(len(calls)),
            "x-omega-idempotent-replayed": "true",
        })

    client = client_with_transport(asynchronous, handler, retries=1)
    kwargs = {"body": body}
    if "idempotencyKey" not in body:
        kwargs["idempotency_key"] = "caller-write-key"
    try:
        raw = invoke(client, name, args, kwargs)
        assert raw.data == {"ok": True} and raw.request_id == "attempt-2"
        assert raw.idempotency_key == "caller-write-key"
        assert raw.meta.attempts == 2 and raw.meta.idempotent_replay
        assert len(calls) == 2
    finally:
        close(client)


@pytest.mark.parametrize("asynchronous", [False, True])
@pytest.mark.parametrize("case", CASES, ids=[c[0] for c in CASES])
@pytest.mark.parametrize("status,expected", [(400, errors.BadRequestError), (401, errors.AuthenticationError),
    (403, errors.PermissionDeniedError), (404, errors.NotFoundError), (409, errors.ConflictError),
    (422, errors.UnprocessableEntityError), (429, errors.RateLimitError), (503, errors.ServerError)])
def test_each_operation_preserves_typed_errors(asynchronous, case, status, expected):
    name, args, _, _, body, _ = case
    calls = []
    def handler(request):
        calls.append(request)
        return httpx.Response(status, json={"error": {"code": "refused", "message": "refused"}})
    client = client_with_transport(asynchronous, handler)
    try:
        with pytest.raises(expected):
            invoke(client, name, args, {"body": body} if body is not None else {})
        assert len(calls) == 1
    finally:
        close(client)


def test_inventory_covers_every_registered_console_operation():
    mapping = json.loads((ROOT / "openapi/platform/wrapper-map.json").read_text())
    names = {m["py"].removeprefix("client.") for n, e in mapping["operations"].items()
             if n.startswith(("platform.agents.", "platform.schedules.", "platform.environments."))
             for m in e.get("methods", [])}
    assert names == {c[0] for c in CASES}
    for name, entry in mapping["operations"].items():
        if name.startswith(("platform.agents.", "platform.schedules.", "platform.environments.")) and entry.get("methods"):
            assert OPERATIONS[name].pagination is None  # Current contract returns complete envelopes.


def test_console_facades_regenerate_from_the_current_contract(tmp_path):
    import ast
    import subprocess
    import sys
    subprocess.run([sys.executable, str(ROOT / "scripts/platform/generate-console.py"), "--out", str(tmp_path)], check=True)
    for generated in tmp_path.rglob("*"):
        if not generated.is_file():
            continue
        committed = ROOT / generated.relative_to(tmp_path)
        if generated.suffix == ".py":
            assert ast.dump(ast.parse(generated.read_text())) == ast.dump(ast.parse(committed.read_text()))
        else:
            assert generated.read_bytes() == committed.read_bytes()


def test_composite_preview_methods_have_an_explicit_language_disposition():
    mapping = json.loads((ROOT / "openapi/platform/wrapper-map.json").read_text())
    methods = mapping["composite_methods"]
    assert {m["py"].rsplit(".", 1)[1] for m in methods} == {"validate", "plan", "apply", "export", "import_definition"}
    for method in methods:
        assert method["py_async"] == method["py"]
        assert method["ts"] is None and method["ts_status"] == "NOT-OFFERED"
        assert method["reason"]


@pytest.mark.parametrize("asynchronous", [False, True])
@pytest.mark.parametrize("keyed", [False, True])
def test_retry_policy_uses_one_durable_identity(asynchronous, keyed):
    calls = []
    def handler(request):
        calls.append(request)
        return httpx.Response(503 if len(calls) == 1 else 200, json={"ok": True})
    client = client_with_transport(asynchronous, handler, retries=1)
    try:
        if keyed:
            assert invoke(client, "agents.draft", kwargs={"body": {"message": "Draft"}}) == {"ok": True}
            assert len(calls) == 2
            assert calls[0].headers["Idempotency-Key"] == calls[1].headers["Idempotency-Key"]
        else:
            with pytest.raises(errors.ServerError):
                invoke(client, "agents.create", kwargs={"body": CASES[2][4]})
            assert len(calls) == 1
    finally:
        close(client)


@pytest.mark.parametrize("asynchronous", [False, True])
def test_schedule_body_key_is_reused_and_conflicts_are_local(asynchronous):
    calls = []
    def handler(request):
        calls.append(request)
        assert request.headers["Idempotency-Key"] == "durable-body-key"
        return httpx.Response(200, json={})
    client = client_with_transport(asynchronous, handler)
    body = {"idempotencyKey": "durable-body-key"}
    try:
        invoke(client, "agents.schedules.run_now", ("s",), {"body": body})
        with pytest.raises(errors.ConfigurationError):
            invoke(client, "agents.schedules.run_now", ("s",), {"body": body, "idempotency_key": "different"})
        assert len(calls) == 1 and body == {"idempotencyKey": "durable-body-key"}
    finally:
        close(client)


@pytest.mark.parametrize("asynchronous", [False, True])
@pytest.mark.parametrize("version", [True, 0, -1, 1.5, 9007199254740992])
def test_revision_validation_precedes_transport(asynchronous, version):
    def handler(request):
        raise AssertionError("invalid revision made an HTTP request")
    client = client_with_transport(asynchronous, handler)
    try:
        with pytest.raises(errors.ConfigurationError):
            invoke(client, "agents.rollback_revision", ("a", version))
    finally:
        close(client)


@pytest.mark.parametrize("asynchronous", [False, True])
def test_with_options_rebinds_namespace_without_opening_another_pool(asynchronous):
    calls = []
    def handler(request):
        calls.append(request)
        assert request.extensions["timeout"]["read"] == 2
        return httpx.Response(200, json={})
    client = client_with_transport(asynchronous, handler)
    quick = client.with_options(timeout=2)
    try:
        invoke(quick, "agents.list")
        invoke(quick, "environments.list")
        invoke(quick, "agents.schedules.list")
        assert len(calls) == 3 and quick._platform.shared is client._platform.shared
    finally:
        close(quick)
        close(client)
