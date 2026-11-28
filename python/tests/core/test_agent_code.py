"""Offline transport-contract tests; not a real-backend or browser acceptance receipt."""
from __future__ import annotations

import copy
import json
import os

import httpx
import pytest

from fi import FutureAGIClient
from fi._cli.main import main
from fi._core.platform_base import PlatformCore
from fi._core.transport import PlatformShared
from fi.agents.definition import SCHEMA, diff, validate
from fi.agents.files import locked, read_json, write_json
from fi.errors import ConfigurationError, ConflictError

DOCUMENT = {"schemaVersion": SCHEMA, "spec": {"name": "Analyst", "role": "Researcher",
    "purpose": "Answer from supplied context.", "responsibilities": ["Cite evidence"],
    "workMode": "on_demand", "connectorBindingIds": []}}


@pytest.fixture
def rig(monkeypatch):
    monkeypatch.setenv("FI_AGENT_CODE_ENABLED", "1")
    client = FutureAGIClient(api_key="test-key", secret_key="test-secret", base_url="http://127.0.0.1:1",
                            platform_base_url="http://127.0.0.1:1", organization_id="org-a", workspace_id="workspace-a")
    rows, calls = {}, []
    race = {"enabled": False}

    def envelope(aid):
        spec, version = rows[aid]
        agent = {**copy.deepcopy(spec), "id": aid, "version": version, "status": "idle",
                 "connectorBindings": [{"id": v} for v in spec["connectorBindingIds"]]}
        agent.pop("connectorBindingIds")
        if "environmentId" in agent:
            agent["environment"] = {"id": agent.pop("environmentId"), "revision": agent.pop("environmentRevision")}
        return {"schemaVersion": "omega-workforce/v1", "agent": agent}

    def respond(request):
        calls.append(request)
        assert request.headers["X-Workspace-Id"] == "workspace-a"
        assert request.headers["X-Organization-Id"] == "org-a"
        if request.method == "GET" and request.url.path == "/workspace/workforce":
            return httpx.Response(200, json={"schemaVersion": "omega-workforce/v1", "agents": [envelope(i)["agent"] for i in rows]})
        aid = request.url.path.rsplit("/", 1)[1]
        if request.method == "GET":
            return httpx.Response(200, json=envelope(aid)) if aid in rows else httpx.Response(404, json={"code": "not_found"})
        body = json.loads(request.content)
        if request.method == "POST":
            aid = f"agent-{len(rows) + 1}"
            rows[aid] = (body, 1)
        elif request.method == "PATCH":
            # EE treats an environment reference as one atomic pair, including detach.
            if ("environmentId" in body) != ("environmentRevision" in body):
                return httpx.Response(400, json={"message": "environmentId and environmentRevision must be supplied together"})
            expected = body.pop("expectedVersion")
            if race["enabled"]:
                rows[aid] = (rows[aid][0], rows[aid][1] + 1)
            if expected != rows[aid][1]:
                return httpx.Response(409, json={"code": "conflict"})
            updated = {**rows[aid][0], **body}
            if updated.get("environmentId", 1) is None:
                updated.pop("environmentId")
                updated.pop("environmentRevision")
            rows[aid] = (updated, expected + 1)
        else:
            raise AssertionError(request.method)
        return httpx.Response(201 if request.method == "POST" else 200, json=envelope(aid))

    client.__dict__["_platform"] = PlatformCore(PlatformShared(client._resolve_platform_origin, retries=0, transport=httpx.MockTransport(respond)))
    yield client, rows, calls, race
    client.close()


def test_round_trip_exact_diff_and_second_apply_is_byte_exact_noop(rig, tmp_path):
    client, rows, calls, _ = rig
    lock = tmp_path / "agent.lock.json"
    code = client.agents.code
    assert code.validate(DOCUMENT) == validate(DOCUMENT)
    planned = code.plan(DOCUMENT, lockfile=lock)
    assert planned["action"] == "create" and planned["changes"] == diff({}, validate(DOCUMENT)["spec"])
    assert not lock.exists() and rows == {}
    applied = code.apply(DOCUMENT, lockfile=lock)
    assert applied["changed"] is True
    before = lock.read_bytes(), lock.stat().st_mtime_ns
    writes = len([r for r in calls if r.method != "GET"])
    assert code.apply(DOCUMENT, lockfile=lock)["action"] == "noop"
    assert (lock.read_bytes(), lock.stat().st_mtime_ns) == before
    assert len([r for r in calls if r.method != "GET"]) == writes
    exported = code.export(applied["agentId"])
    assert exported == validate(DOCUMENT)
    imported = code.import_definition(exported, agent_id=applied["agentId"], lockfile=tmp_path / "import.lock")
    assert imported["changed"] is False
    assert code.plan(exported, lockfile=tmp_path / "import.lock")["changes"] == []
    desired = copy.deepcopy(exported)
    desired["spec"]["purpose"] = "Return a concise, cited answer."
    plan = code.plan(desired, lockfile=lock)
    assert plan["changes"] == [{"op": "replace", "path": "/purpose", "old": DOCUMENT["spec"]["purpose"], "value": desired["spec"]["purpose"]}]
    code.apply(desired, lockfile=lock)
    assert rows[applied["agentId"]][1] == 2
    patch = json.loads([r for r in calls if r.method == "PATCH"][-1].content)
    assert patch == {"purpose": desired["spec"]["purpose"], "expectedVersion": 1}


def test_drift_refuses_even_when_local_matches_remote_unless_force(rig, tmp_path):
    client, rows, calls, _ = rig
    lock = tmp_path / "state"
    aid = client.agents.code.apply(DOCUMENT, lockfile=lock)["agentId"]
    rows[aid][0]["purpose"] = "Console edit"
    rows[aid] = (rows[aid][0], 2)
    before = lock.read_bytes()
    with pytest.raises(ConfigurationError, match="--force") as error:
        client.agents.code.apply(DOCUMENT, lockfile=lock)
    assert error.value.code == "agent_drift"
    assert lock.read_bytes() == before
    assert not any(r.method == "PATCH" for r in calls)
    client.agents.code.apply(DOCUMENT, lockfile=lock, force=True)
    assert rows[aid][1] == 3
    assert json.loads(calls[-1].content)["expectedVersion"] == 2


def test_force_does_not_bypass_concurrent_edit_cas(rig, tmp_path):
    client, rows, calls, race = rig
    lock = tmp_path / "state"
    client.agents.code.apply(DOCUMENT, lockfile=lock)
    modified = copy.deepcopy(DOCUMENT)
    modified["spec"]["purpose"] = "Local edit"
    race["enabled"] = True
    with pytest.raises(ConflictError):
        client.agents.code.apply(modified, lockfile=lock, force=True)
    assert read_json(lock)["status"] == "pending"
    before = len(calls)
    with pytest.raises(ConfigurationError, match="unresolved"):
        client.agents.code.apply(modified, lockfile=lock, force=True)
    assert len(calls) == before


@pytest.mark.parametrize("change", ["origin", "organizationId", "workspaceId"])
def test_lock_target_is_not_forceable(rig, tmp_path, change):
    client, _, calls, _ = rig
    lock = tmp_path / "state"
    client.agents.code.apply(DOCUMENT, lockfile=lock)
    state = read_json(lock)
    state["target"][change] = "different"
    write_json(lock, state, replace=True)
    before = len(calls)
    with pytest.raises(ConfigurationError, match="different backend"):
        client.agents.code.apply(DOCUMENT, lockfile=lock, force=True)
    assert len(calls) == before


def test_missing_lock_never_adopts_by_name(rig, tmp_path):
    client, _, _, _ = rig
    client.agents.code.apply(DOCUMENT, lockfile=tmp_path / "a")
    with pytest.raises(ConfigurationError, match="explicit ID"):
        client.agents.code.apply(DOCUMENT, lockfile=tmp_path / "b", force=True)


def test_import_mismatch_and_lock_corruption_fail_closed(rig, tmp_path):
    client, _, _, _ = rig
    lock = tmp_path / "a"
    aid = client.agents.code.apply(DOCUMENT, lockfile=lock)["agentId"]
    other = copy.deepcopy(DOCUMENT)
    other["spec"]["name"] = "Different"
    with pytest.raises(ConfigurationError, match="does not match"):
        client.agents.code.import_definition(other, agent_id=aid, lockfile=tmp_path / "b")
    lock.write_text("{malformed")
    with pytest.raises(ConfigurationError):
        client.agents.code.apply(DOCUMENT, lockfile=lock, force=True)


@pytest.mark.parametrize("operation", ["plan", "apply", "force", "import", "bind"])
def test_json_null_lock_refuses_before_network_and_preserves_state(rig, tmp_path, operation):
    client, rows, calls, _ = rig
    lock = tmp_path / "agent.lock.json"
    aid = client.agents.code.apply(DOCUMENT, lockfile=lock)["agentId"]
    # A lost identity must not allow a renamed definition to create another agent.
    document = copy.deepcopy(DOCUMENT)
    document["spec"]["name"] = "Renamed analyst"
    lock.write_bytes(b" \nnull\t\n")
    before = lock.read_bytes(), lock.stat().st_mtime_ns
    previous_rows = copy.deepcopy(rows)
    calls.clear()
    with pytest.raises(ConfigurationError):
        if operation == "plan":
            client.agents.code.plan(document, lockfile=lock)
        elif operation == "bind":
            client.agents.code.import_definition(DOCUMENT, agent_id=aid, lockfile=lock)
        elif operation == "import":
            client.agents.code.import_definition(document, lockfile=lock)
        else:
            client.agents.code.apply(document, lockfile=lock, force=operation == "force")
    assert calls == []
    assert rows == previous_rows
    assert (lock.read_bytes(), lock.stat().st_mtime_ns) == before


@pytest.mark.parametrize("field,value", [("environmentRevision", 2), ("environmentId", "env-b")])
def test_environment_reference_updates_send_complete_pair(rig, tmp_path, field, value):
    client, rows, calls, _ = rig
    lock = tmp_path / "state"
    document = copy.deepcopy(DOCUMENT)
    document["spec"].update(environmentId="env-a", environmentRevision=1)
    aid = client.agents.code.apply(document, lockfile=lock)["agentId"]
    desired = copy.deepcopy(document)
    desired["spec"][field] = value
    planned = client.agents.code.plan(desired, lockfile=lock)
    assert planned["changes"] == [{"op": "replace", "path": "/" + field,
                                   "old": document["spec"][field], "value": value}]
    applied = client.agents.code.apply(desired, lockfile=lock)
    assert applied["changes"] == planned["changes"]
    assert json.loads(calls[-1].content) == {
        "environmentId": desired["spec"]["environmentId"],
        "environmentRevision": desired["spec"]["environmentRevision"], "expectedVersion": 1}
    assert rows[aid][1] == 2
    assert read_json(lock)["status"] == "applied"
    assert client.agents.code.export(aid) == validate(desired)
    before = lock.read_bytes(), lock.stat().st_mtime_ns
    writes = sum(r.method != "GET" for r in calls)
    assert client.agents.code.apply(desired, lockfile=lock)["changed"] is False
    assert (lock.read_bytes(), lock.stat().st_mtime_ns) == before
    assert sum(r.method != "GET" for r in calls) == writes


def test_environment_detachment_is_explicit_and_noop_after(rig, tmp_path):
    client, _, calls, _ = rig
    lock = tmp_path / "state"
    document = copy.deepcopy(DOCUMENT)
    document["spec"].update(environmentId="env-a", environmentRevision=1)
    client.agents.code.apply(document, lockfile=lock)
    client.agents.code.apply(DOCUMENT, lockfile=lock)
    assert json.loads(calls[-1].content) == {"environmentId": None, "environmentRevision": None, "expectedVersion": 1}
    assert client.agents.code.apply(DOCUMENT, lockfile=lock)["changed"] is False


@pytest.mark.parametrize("field,value", [("name", ""), ("purpose", "a\nb"), ("workMode", "weekly"),
    ("unattended", 1), ("connectorBindingIds", ["a", "a"]), ("responsibilities", ["x"] * 65),
    ("modelId", " "), ("environmentId", "env"), ("unknown", 1), ("examples", [{"prompt": "p"}]),
    ("sharing", {"mode": "selected", "accountIds": []}), ("skills", [{"id": "x", "revision": True}])])
def test_invalid_definitions_fail_before_network(rig, field, value, tmp_path):
    client, _, calls, _ = rig
    document = copy.deepcopy(DOCUMENT)
    document["spec"][field] = value
    with pytest.raises(ConfigurationError):
        client.agents.code.apply(document, lockfile=tmp_path / "state")
    assert calls == []


def test_no_lossy_reset_of_model_or_policy(rig, tmp_path):
    client, _, _, _ = rig
    document = copy.deepcopy(DOCUMENT)
    document["spec"]["modelId"] = "test-model"
    client.agents.code.apply(document, lockfile=tmp_path / "state")
    with pytest.raises(ConfigurationError, match="cannot clear modelId"):
        client.agents.code.plan(DOCUMENT, lockfile=tmp_path / "state")


def test_disabled_sdk_and_cli_are_inert(monkeypatch, capsys):
    monkeypatch.delenv("FI_AGENT_CODE_ENABLED", raising=False)
    with FutureAGIClient(base_url="http://127.0.0.1:1") as client:
        with pytest.raises(ConfigurationError, match="disabled"):
            client.agents.code.validate(DOCUMENT)
    assert main(["--help"]) == 0
    assert "agents" in capsys.readouterr().out
    from fi._cli.main import build_parser
    import argparse

    parser = build_parser()
    groups = next(action for action in parser._actions if isinstance(action, argparse._SubParsersAction))
    agents = groups.choices["agents"]
    commands = next(action for action in agents._actions if isinstance(action, argparse._SubParsersAction))
    assert "runs" in commands.choices
    assert not {"validate", "plan", "apply", "export", "import"}.intersection(commands.choices)


def test_cli_validation_and_all_help_have_no_missing_groups(monkeypatch, capsys, tmp_path):
    monkeypatch.setenv("FI_AGENT_CODE_ENABLED", "1")
    source = tmp_path / "agent.json"
    write_json(source, DOCUMENT)
    assert main(["agents", "validate", str(source), "--json"]) == 0
    assert json.loads(capsys.readouterr().out)["valid"] is True
    for command in ("validate", "plan", "apply", "export", "import"):
        assert main(["agents", command, "--help"]) == 0
        assert "usage:" in capsys.readouterr().out


def test_ambiguous_create_is_not_retried(rig, tmp_path, monkeypatch):
    client, rows, calls, _ = rig
    code = client.agents.code
    original = code._call

    def lost(operation, **kwargs):
        result = original(operation, **kwargs)
        if operation == "create":
            raise RuntimeError("response lost after server committed")
        return result

    monkeypatch.setattr(code, "_call", lost)
    lock = tmp_path / "state"
    with pytest.raises(RuntimeError, match="response lost"):
        code.apply(DOCUMENT, lockfile=lock)
    assert len(rows) == 1 and read_json(lock)["status"] == "pending"
    before = len(calls)
    with pytest.raises(ConfigurationError, match="unresolved"):
        code.apply(DOCUMENT, lockfile=lock, force=True)
    assert len(calls) == before


def test_missing_remote_never_recreates(rig, tmp_path):
    from fi.errors import NotFoundError
    client, rows, calls, _ = rig
    lock = tmp_path / "state"
    aid = client.agents.code.apply(DOCUMENT, lockfile=lock)["agentId"]
    del rows[aid]
    with pytest.raises(NotFoundError):
        client.agents.code.apply(DOCUMENT, lockfile=lock, force=True)
    assert len([r for r in calls if r.method == "POST"]) == 1


def test_wrong_response_version_keeps_pending_journal(rig, tmp_path, monkeypatch):
    client, _, _, _ = rig
    code = client.agents.code
    lock = tmp_path / "state"
    code.apply(DOCUMENT, lockfile=lock)
    original = code._call

    def wrong_version(operation, **kwargs):
        result = original(operation, **kwargs)
        if operation == "update":
            result["agent"]["version"] = 1
        return result

    monkeypatch.setattr(code, "_call", wrong_version)
    document = copy.deepcopy(DOCUMENT)
    document["spec"]["purpose"] = "New purpose"
    with pytest.raises(ConfigurationError, match="different definition or version"):
        code.apply(document, lockfile=lock)
    assert read_json(lock)["status"] == "pending"


def test_special_file_refuses_without_waiting_for_a_writer(tmp_path):
    fifo = tmp_path / "pipe"
    os.mkfifo(fifo)
    with pytest.raises(ConfigurationError, match="regular file"):
        read_json(fifo)


def test_file_safety_and_lock_exclusion(tmp_path):
    original = tmp_path / "definition"
    write_json(original, DOCUMENT)
    with pytest.raises(ConfigurationError):
        write_json(original, {})
    assert read_json(original) == DOCUMENT
    link = tmp_path / "link"
    link.symlink_to(original)
    with pytest.raises(ConfigurationError):
        read_json(link)
    original.write_text('{"spec":{},"spec":{}}')
    with pytest.raises(ConfigurationError):
        read_json(original)
    with locked(tmp_path / "state"):
        with pytest.raises(ConfigurationError, match="Another apply"):
            with locked(tmp_path / "state"):
                pass
