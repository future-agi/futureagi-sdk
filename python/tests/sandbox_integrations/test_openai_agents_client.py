"""FutureAGISandboxClient over the frozen-OpenAPI mock, with the Agents SDK faked: the backend id, create
(options to the create body, the settings read first, the instrumented wrapper, an explicit client), the
manifest refusals, resume (a hibernated sandbox resumed once, a missing one replaced), delete or
hibernate at the end (once), the state round trip and the missing-extra error; plus a contract check
against the real SDK that runs only where openai-agents 0.24 is installed. Fake credentials only."""

from __future__ import annotations

import importlib
import inspect
import json
import sys
import types

import httpx
import pytest

from fi.errors import MissingExtraError
from fi.sandbox import ConfigurationError, SandboxError, _connection
from tests.platform._sandbox_mock import FAKE_TOKEN, SBX, MockServer, api, error, example, run

from . import _fake_openai_agents as fake

OTHER = "sbx_" + "c" * 24
ENV = ("OMEGA_BASE_URL", "FI_API_KEY", "FI_SECRET_KEY", "FUTUREAGI_OMEGA_API_KEY", "OMEGA_OS_API_KEY",
       "FI_WORKSPACE_ID", "FI_ORGANIZATION_ID", "FI_ALLOW_INSECURE_HTTP", "FI_BASE_URL",
       "FI_PLATFORM_BASE_URL", "FI_PLATFORM_TOKEN", "FI_ALLOW_CUSTOM_PLATFORM_URL", "FI_EXTRA_HEADERS")


@pytest.fixture(name="adapter")
def adapter_fixture(monkeypatch):
    for name in ENV:
        monkeypatch.delenv(name, raising=False)
    fake.install(monkeypatch)
    return importlib.import_module(fake.ADAPTER)


def environment(monkeypatch, server):
    """A self-hosted EE on loopback (Bearer) with the mock as its transport."""
    monkeypatch.setenv("OMEGA_BASE_URL", "http://127.0.0.1:8787")
    monkeypatch.setenv("FUTUREAGI_OMEGA_API_KEY", FAKE_TOKEN)
    monkeypatch.setattr(_connection, "default_transport", server.transport)


def settings(server, max_timeout=1200):
    body = example(server.spec, server.routes["sandboxes.settings.get"].schema)
    body["caps"]["exec"].update(maxTimeoutSeconds=max_timeout, defaultTimeoutSeconds=60)
    server.on("sandboxes.settings.get", lambda request: httpx.Response(200, json=body))


def record(state="active", ident=SBX):
    body = {"schemaVersion": "omega-workspace-sandboxes/v1", "sandbox": {"id": ident, "state": state, "name": "n"}}
    return lambda request: httpx.Response(200, json=body)


def names(server):
    return [seen.name for seen in server.seen]


def explicit(server):
    return types.SimpleNamespace(sandboxes=api(server, "async"))


def created(adapter, server, **options):
    settings(server)
    client = adapter.FutureAGISandboxClient(client=explicit(server))
    session = run(client.create(options=adapter.FutureAGISandboxClientOptions(**options)))
    server.seen.clear()
    return client, session


def test_backend_id_is_futureagi(adapter):
    client = adapter.FutureAGISandboxClient()
    assert client.backend_id == "futureagi" and client.supports_default_options is True
    assert isinstance(client, fake.BaseSandboxClient)
    options = adapter.FutureAGISandboxClientOptions()
    assert options.type == "futureagi" and options.workdir == "/workspace" and options.exec_timeout_s is None
    assert fake.BaseSandboxClientOptions._subclass_registry["futureagi"].__qualname__ == "FutureAGISandboxClientOptions"
    assert fake.SandboxSessionState._subclass_registry["futureagi"].__qualname__ == "FutureAGISandboxSessionState"
    with pytest.raises(Exception):
        options.template = "x"  # frozen, like every SDK options type


def test_create_maps_options_to_create_body(adapter, monkeypatch):
    server = MockServer()
    environment(monkeypatch, server)
    settings(server)
    client = adapter.FutureAGISandboxClient()
    options = adapter.FutureAGISandboxClientOptions(
        name="agent-1", template="python-data", size="small", idle_ttl_seconds=600, hibernate_on_exit=True)
    session = run(client.create(options=options))
    assert names(server) == ["sandboxes.settings.get", "sandboxes.create"]
    assert server.last.json() == {"name": "agent-1", "template": "python-data", "size": "small", "idleTtlSeconds": 600}
    state = session.state
    assert (state.template, state.size, state.idle_ttl_seconds, state.hibernate_on_exit) == ("python-data", "small", 600, True)
    server.seen.clear()
    run(client.create(options=None))  # the SDK passes None when the run config names no options
    assert names(server) == ["sandboxes.settings.get", "sandboxes.create"] and server.last.json() in ({}, None)
    server.seen.clear()
    server.on("sandboxes.settings.get", lambda request: error(403, "forbidden"))
    with pytest.raises(SandboxError):
        run(client.create(options=options))
    assert names(server) == ["sandboxes.settings.get"]  # nothing was created


def test_create_returns_wrapped_session(adapter):
    server = MockServer()
    settings(server, max_timeout=1200)
    instrumentation = object()
    client = adapter.FutureAGISandboxClient(client=explicit(server), instrumentation=instrumentation)
    session = run(client.create(options=adapter.FutureAGISandboxClientOptions(exec_timeout_s=60)))
    inner = session._inner
    assert fake.BaseSandboxClient.wrapped == [inner] and isinstance(session, fake.SandboxSession)
    assert isinstance(inner, adapter.FutureAGISandboxSession) and session.instrumentation is instrumentation
    assert inner.sandbox_id == SBX and inner.max_timeout_s == 1200 and inner.state.exec_timeout_s == 60
    assert inner.state.manifest.root == "/workspace" and inner.state.workspace_root_ready is False
    assert isinstance(inner.state.snapshot, fake.NoopSnapshot) and inner.state.snapshot.id == str(inner.state.session_id)


def test_create_with_explicit_client(adapter):
    server = MockServer()
    settings(server)
    client = adapter.FutureAGISandboxClient(client=explicit(server))
    manifest = fake.Manifest(root="/workspace/proj", entries={"README.md": fake.File(content=b"hi"),
                                                              "src": fake.Dir(children={"a.py": fake.File()})})
    session = run(client.create(manifest=manifest, options=adapter.FutureAGISandboxClientOptions(template="base")))
    assert names(server) == ["sandboxes.settings.get", "sandboxes.create"]
    assert server.last.json() == {"template": "base"}
    assert session.state.manifest is manifest and session._inner.sandbox._owns_pool is False
    body = example(server.spec, server.routes["sandboxes.settings.get"].schema)
    body["caps"]["exec"].pop("maxTimeoutSeconds")
    server.on("sandboxes.settings.get", lambda request: httpx.Response(200, json=body))
    with pytest.raises(ConfigurationError) as caught:
        run(client.create(options=None))
    assert caught.value.code == "missing_exec_limit"


@pytest.mark.parametrize("manifest,match", [
    (lambda: fake.Manifest(entries={"repo": fake.GitRepo()}), "'git_repo' is not supported"),
    (lambda: fake.Manifest(entries={"data": fake.S3Mount()}), "'s3_mount' is not supported"),
    (lambda: fake.Manifest(entries={"src": fake.Dir(children={"bucket": fake.S3Mount()})}), "'src/bucket'"),
    (lambda: fake.Manifest(entries={"a.txt": fake.File(group=fake.User(name="bob"))}), "names an owner"),
    (lambda: fake.Manifest(users=[fake.User(name="bob")]), "users and groups"),
    (lambda: fake.Manifest(environment=fake.Environment(value={"MODE": "x"})), "environment variables"),
    (lambda: fake.Manifest(root="/home/agent"), "workspace root must be /workspace"),
    (lambda: fake.Manifest(root="/workspace-other"), "workspace root must be /workspace"),
])
def test_unsupported_manifest_entry_refused(adapter, manifest, match):
    server = MockServer()
    settings(server)
    client = adapter.FutureAGISandboxClient(client=explicit(server))
    with pytest.raises(NotImplementedError, match=match):
        run(client.create(manifest=manifest(), options=None))
    with pytest.raises(ValueError, match="differ"):
        run(client.create(manifest=fake.Manifest(), options=adapter.FutureAGISandboxClientOptions(workdir="/workspace/x")))
    with pytest.raises(TypeError):
        run(client.create(options=types.SimpleNamespace(type="other")))
    assert server.seen == []


def test_resume_hibernated_calls_resume_once(adapter):
    server = MockServer()
    client, session = created(adapter, server, template="base")
    state = session.state
    server.on("sandboxes.getInfo", record("hibernated"))
    server.on("sandboxes.resume", record("active"))
    resumed = run(client.resume(state))
    assert names(server) == ["sandboxes.settings.get", "sandboxes.getInfo", "sandboxes.resume"]
    inner = resumed._inner
    assert inner.sandbox_id == SBX and inner.sandbox.state == "active"
    assert inner._start_workspace_state_preserved is True and inner._start_system_state_preserved is False
    server.seen.clear()
    server.on("sandboxes.getInfo", record("active"))
    again = run(client.resume(state))
    assert names(server) == ["sandboxes.settings.get", "sandboxes.getInfo"]
    assert again._inner._start_system_state_preserved is True
    server.seen.clear()
    server.on("sandboxes.getInfo", record("recovery_required"))
    with pytest.raises(SandboxError, match="recovery_required"):
        run(client.resume(state))
    assert names(server) == ["sandboxes.settings.get", "sandboxes.getInfo"]
    with pytest.raises(TypeError):
        run(client.resume(fake.SandboxSessionState(type="other", snapshot=fake.NoopSnapshot(), manifest=fake.Manifest())))


@pytest.mark.parametrize("gone", ["not_found", "destroyed"])
def test_resume_missing_creates_replacement(adapter, gone):
    server = MockServer()
    client, session = created(adapter, server, template="base", size="small", exec_timeout_s=90)
    state = session.state
    state.workspace_root_ready = True
    if gone == "not_found":
        server.on("sandboxes.getInfo", lambda request: error(404, "not_found"))
    else:
        server.on("sandboxes.getInfo", record("destroyed"))
    server.on("sandboxes.create", record("active", OTHER))
    resumed = run(client.resume(state))
    assert names(server) == ["sandboxes.settings.get", "sandboxes.getInfo", "sandboxes.create"]
    assert server.last.json() == {"template": "base", "size": "small"}
    inner = resumed._inner
    assert state.sandbox_id == OTHER and inner.sandbox_id == OTHER and state.workspace_root_ready is False
    assert inner._start_workspace_state_preserved is False and inner.state.exec_timeout_s == 90


def test_delete_and_hibernate_on_exit(adapter):
    server = MockServer()
    client, session = created(adapter, server)
    assert run(client.delete(session)) is session
    run(session._inner.shutdown())
    run(client.delete(session))
    assert names(server) == ["sandboxes.kill"]
    server = MockServer()
    client, session = created(adapter, server, hibernate_on_exit=True)
    server.on("sandboxes.hibernate", record("hibernated"))
    run(session._inner.shutdown())  # the SDK shuts the session down, then calls delete
    run(client.delete(session))
    assert names(server) == ["sandboxes.hibernate"]
    server = MockServer()
    client, session = created(adapter, server, hibernate_on_exit=True)
    server.on("sandboxes.hibernate", lambda request: error(404, "not_found"))
    run(client.delete(session))  # already gone
    assert names(server) == ["sandboxes.hibernate"]
    with pytest.raises(TypeError):
        run(client.delete(object()))


def test_state_round_trip(adapter):
    server = MockServer()
    settings(server)
    client = adapter.FutureAGISandboxClient(client=explicit(server))
    manifest = fake.Manifest(entries={"notes.txt": fake.File(content=b"hello")})
    options = adapter.FutureAGISandboxClientOptions(name="n", template="base", exec_timeout_s=45, hibernate_on_exit=True)
    state = run(client.create(manifest=manifest, options=options)).state
    payload = json.loads(json.dumps(client.serialize_session_state(state)))
    restored = client.deserialize_session_state(payload)
    assert type(restored) is type(state) and restored.type == "futureagi"
    assert restored.model_dump(mode="json") == state.model_dump(mode="json")
    assert (restored.sandbox_id, restored.session_id, restored.hibernate_on_exit) == (SBX, state.session_id, True)
    assert restored.manifest.entries["notes.txt"].content == b"hello"


def test_missing_agents_sandbox_raises_missing_extra(monkeypatch):
    fake.forget_adapter(monkeypatch)
    for name in fake.PACKAGES + fake.LEAVES:
        monkeypatch.setitem(sys.modules, name, None)
    with pytest.raises(MissingExtraError) as caught:
        importlib.import_module(fake.ADAPTER)
    # No extra is declared for this integration yet: the hint installs the Agents SDK directly.
    assert caught.value.extra is None and caught.value.module == "agents.sandbox"
    assert caught.value.install_hint == 'pip install futureagi "openai-agents>=0.24,<0.25"'
    assert caught.value.install_hint in str(caught.value)


def test_real_framework_contract(monkeypatch):
    """Against the installed SDK (openai-agents 0.24, installed directly); skipped where
    ``agents.sandbox`` is missing, as with the 0.4.2 pin."""
    pytest.importorskip("agents.sandbox")
    fake.forget_adapter(monkeypatch)
    adapter = importlib.import_module(fake.ADAPTER)
    from agents.sandbox.session.base_sandbox_session import BaseSandboxSession
    from agents.sandbox.session.sandbox_client import BaseSandboxClient, BaseSandboxClientOptions
    from agents.sandbox.session.sandbox_session_state import SandboxSessionState

    assert issubclass(adapter.FutureAGISandboxSession, BaseSandboxSession)
    assert issubclass(adapter.FutureAGISandboxClient, BaseSandboxClient)
    assert not inspect.isabstract(adapter.FutureAGISandboxSession)
    assert not inspect.isabstract(adapter.FutureAGISandboxClient)
    assert adapter.FutureAGISandboxClient.backend_id == "futureagi"
    parsed = BaseSandboxClientOptions.parse({"type": "futureagi", "template": "base"})
    assert type(parsed).__qualname__ == "FutureAGISandboxClientOptions" and parsed.template == "base"
    assert SandboxSessionState._subclass_registry["futureagi"].__qualname__ == "FutureAGISandboxSessionState"
