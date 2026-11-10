"""CLI scope and project selection regressions; HTTP is mocked at its boundary."""
from __future__ import annotations

import json
import subprocess
import sys
from uuid import UUID

import httpx
import pytest
from fi.context import __main__ as cli
from fi.context.lock import CONTEXT_LOCK
from fi.platform import Client
from fi.skills.__main__ import main as skills_main
from test_materializer import apply, bundle, plan


@pytest.fixture
def project(tmp_path, monkeypatch):
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    path = tmp_path / "repo"
    path.mkdir()
    return path


@pytest.mark.parametrize("command", ["verify", "update", "remove"])
@pytest.mark.parametrize("caller_lock", [False, True])
def test_default_lock_follows_project(project, tmp_path, monkeypatch, capsys, command, caller_lock):
    source = bundle()
    apply(plan(source, project))
    monkeypatch.chdir(tmp_path)
    if caller_lock:
        # A caller's unrelated lock must never participate in project selection.
        (tmp_path / CONTEXT_LOCK).write_text("not this project's lock")
    monkeypatch.setattr(cli.Registry, "__init__", lambda self: None)
    monkeypatch.setattr(cli.Registry, "check_scope", lambda self, identity: None)
    monkeypatch.setattr(cli.Registry, "resolve", lambda self, *a, **kw: source)
    monkeypatch.setattr(cli.Registry, "close", lambda self: None)
    args = [command, "--project", str(project)]
    if command == "update":
        args += ["--check"]
    elif command == "remove":
        args += ["--plan", str(tmp_path / "remove.json")]
    assert cli.main(args) == 0
    result = json.loads(capsys.readouterr().out)
    if command == "verify":
        assert result["verified"]
    elif command == "update":
        assert result["update_available"] is False
    else:
        assert (tmp_path / "remove.json").is_file()


@pytest.mark.parametrize("command", ["verify", "remove"])
def test_isolated_cli_from_outside_project(project, tmp_path, command):
    apply(plan(bundle(), project))
    args = [sys.executable, "-I", "-m", "fi.context", command, "--project", str(project)]
    if command == "remove":
        args += ["--plan", str(tmp_path / "remove.json")]
    result = subprocess.run(args, cwd=tmp_path, capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "error" not in json.loads(result.stdout)


@pytest.mark.parametrize("command", ["verify", "restore"])
@pytest.mark.parametrize("lock_name", [CONTEXT_LOCK, "retained.json"])
def test_explicit_lock_stays_caller_relative(project, tmp_path, monkeypatch, capsys, command, lock_name):
    source = bundle()
    apply(plan(source, project))
    retained = tmp_path / lock_name
    retained.write_bytes((project / CONTEXT_LOCK).read_bytes())
    if command == "verify":
        # External-lock verification must not need the default project lock.
        (project / CONTEXT_LOCK).unlink()
    else:
        # Restore keeps current ownership but resolves the retained older release.
        apply(plan(bundle(version=2), project, operation="update"))
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(cli.Registry, "__init__", lambda self: None)
    monkeypatch.setattr(cli.Registry, "check_scope", lambda self, identity: None)
    resolved = []
    def resolve(self, name, **kwargs):
        resolved.append((name, kwargs))
        return source
    monkeypatch.setattr(cli.Registry, "resolve", resolve)
    monkeypatch.setattr(cli.Registry, "close", lambda self: None)
    args = [command, "--project", str(project), "--lock", lock_name]
    if command == "restore":
        args += ["--allow-preview", "--plan", str(tmp_path / "restore.json")]
    assert cli.main(args) == 0
    result = json.loads(capsys.readouterr().out)
    if command == "verify":
        assert result["verified"]
    else:
        assert resolved == [(source.identity.name, {"version": source.identity.version})]
        assert (tmp_path / "restore.json").is_file()


def configure(monkeypatch):
    for key, value in {
        "ORIGIN": "https://registry.example.invalid",
        "ORGANIZATION_ID": str(UUID(int=1)),
        "WORKSPACE_ID": str(UUID(int=2)),
        "CREDENTIAL": "synthetic-scoped-credential",
    }.items():
        monkeypatch.setenv("FI_CONTEXT_" + key, value)


@pytest.mark.parametrize("main", [cli.main, skills_main], ids=["context", "skill"])
def test_wrong_organization_is_sent_and_denied_before_plan(project, tmp_path, monkeypatch, capsys, main):
    configure(monkeypatch)
    wrong_org = str(UUID(int=99))
    monkeypatch.setenv("FI_CONTEXT_ORGANIZATION_ID", wrong_org)
    requests = []
    def handle(request):
        requests.append(request)
        assert request.headers["Authorization"] == "Context synthetic-scoped-credential"
        assert request.headers["X-Workspace-Id"] == str(UUID(int=2))
        assert request.headers["X-Organization-Id"] == wrong_org
        return httpx.Response(403, json={"code": "context_scope_mismatch"})
    with httpx.Client(transport=httpx.MockTransport(handle)) as http:
        monkeypatch.setattr(cli, "Client", lambda **kwargs: Client(http_client=http, **kwargs))
        output = tmp_path / "plan.json"
        assert main(["plan", "--name", "team-policy", "--client", "codex", "--project", str(project), "--allow-preview", "--out", str(output)]) == 3
    assert len(requests) == 1
    assert json.loads(capsys.readouterr().out)["error"]["code"] == "context_scope_mismatch"
    assert not output.exists()
    assert list(project.iterdir()) == []


@pytest.mark.parametrize("main", [cli.main, skills_main], ids=["context", "skill"])
@pytest.mark.parametrize("scope", ["ORGANIZATION_ID", "WORKSPACE_ID"])
@pytest.mark.parametrize("value", ["not-a-uuid", "bad\r\nInjected: value"])
def test_invalid_scope_fails_before_transport(project, tmp_path, monkeypatch, capsys, main, scope, value):
    configure(monkeypatch)
    monkeypatch.setenv("FI_CONTEXT_" + scope, value)
    def unexpected_client(**kwargs):
        pytest.fail("Invalid scope must be rejected before constructing the transport")
    monkeypatch.setattr(cli, "Client", unexpected_client)
    assert main(["plan", "--name", "team-policy", "--client", "codex", "--project", str(project), "--out", str(tmp_path / "plan.json")]) == 3
    output = capsys.readouterr().out
    assert json.loads(output)["error"]["code"] == "configuration_invalid"
    assert value not in output


def test_scope_uuids_are_canonicalized(monkeypatch):
    configure(monkeypatch)
    monkeypatch.setenv("FI_CONTEXT_ORGANIZATION_ID", "{AAAAAAAA-AAAA-4AAA-8AAA-AAAAAAAAAAAA}")
    captured = {}
    monkeypatch.setattr(cli, "Client", lambda **kwargs: captured.update(kwargs))
    registry = cli.Registry()
    assert registry.organization_id == "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"
    assert captured["default_headers"] == {"X-Organization-Id": registry.organization_id}
    assert captured["workspace_id"] == str(UUID(int=2))
