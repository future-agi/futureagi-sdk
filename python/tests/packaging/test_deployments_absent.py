"""Disabled deployments must be absent, not a visible failing placeholder."""
from __future__ import annotations

import importlib
import importlib.util
import json
from pathlib import Path
import socket

import httpx
import pytest

ROOT = Path(__file__).resolve().parents[3]
SPEC = importlib.util.spec_from_file_location(
    "deployment_archive_gate", ROOT / "scripts/packaging/check_deployments_absent.py"
)
GATE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GATE)


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    def refuse(*args, **kwargs):
        raise AssertionError("Absence checks must not send a request")
    monkeypatch.setattr(socket.socket, "connect", refuse)
    monkeypatch.setattr(socket, "getaddrinfo", refuse)
    monkeypatch.setenv("FI_LOGIN_FILE", "/nonexistent/deployment-absence-login.json")
    for name in ("FI_API_KEY", "FI_SECRET_KEY", "FI_EXTRA_HEADERS", "FI_PLATFORM_TOKEN"):
        monkeypatch.delenv(name, raising=False)


def test_python_namespace_and_root_exports_are_absent():
    import fi
    for name in ("deployments", "Deployment", "AsyncDeployment", "Deployments", "AsyncDeployments"):
        assert name not in fi.__all__
        assert not hasattr(fi, name)
    assert importlib.util.find_spec("fi.deployments") is None
    with pytest.raises(ModuleNotFoundError) as caught:
        importlib.import_module("fi.deployments")
    assert caught.value.name == "fi.deployments"


@pytest.mark.asyncio
async def test_sync_async_and_copied_clients_have_no_accessor(monkeypatch):
    from fi import AsyncFutureAGIClient, FutureAGIClient
    calls = []
    def transport(*args, **kwargs):
        calls.append(args)
        raise AssertionError("Unexpected transport call")
    monkeypatch.setattr(httpx.Client, "send", transport)
    monkeypatch.setattr(httpx.AsyncClient, "send", transport)
    options = dict(base_url="http://127.0.0.1:9")
    with FutureAGIClient(**options) as sync:
        for client in (sync, sync.with_options(retries=0)):
            assert not hasattr(client, "deployments")
            with pytest.raises(AttributeError):
                getattr(client, "deployments")
    async with AsyncFutureAGIClient(**options) as async_client:
        for client in (async_client, async_client.with_options(retries=0)):
            assert not hasattr(client, "deployments")
            with pytest.raises(AttributeError):
                getattr(client, "deployments")
    assert calls == []


def test_cli_has_no_deployment_group_or_install_extra(capsys):
    from fi._cli.main import main
    from fi._cli.registry import source_tree_groups
    assert "deployments" not in source_tree_groups()
    assert main(["--help"]) == 0
    assert "deployments" not in capsys.readouterr().out.lower()
    assert main(["deployments", "list"]) == 2
    assert "invalid choice" in capsys.readouterr().err
    project = (ROOT / "python/pyproject.toml").read_text()
    assert '"fi/deployments"' in project.split("exclude = [", 1)[1].split("]", 1)[0]
    extras = project.split("[tool.poetry.extras]", 1)[1].split("\n[", 1)[0]
    assert "deployments" not in extras


def test_wrapper_map_marks_both_languages_not_offered():
    mapping = json.loads((ROOT / "openapi/platform/wrapper-map.json").read_text())
    availability = mapping["families"]["deployments"]["availability"]
    assert availability["py"] == availability["ts"] == "NOT-OFFERED"
    assert availability["reason"]
    operations = {name for name in mapping["operations"] if name.startswith("deployments.")}
    assert operations == {
        "deployments.create", "deployments.list", "deployments.get", "deployments.delete",
        "deployments.health", "deployments.logs", "deployments.rollback", "deployments.rotateAccessToken",
    }


def test_source_modules_and_documentation_are_absent():
    for root in (ROOT / "python/fi", ROOT / "typescript/futureagi/src"):
        assert not any(GATE._namespace(p.relative_to(root).as_posix()) for p in root.rglob("*"))
    for directory in (ROOT / "python/fi", ROOT / "typescript/futureagi/src", ROOT / "docs"):
        for file in directory.rglob("*.md"):
            assert not GATE.API_REFERENCE.search(file.read_text()), file
    for file in (ROOT / "python/README.md", ROOT / "typescript/futureagi/README.md"):
        assert not GATE.API_REFERENCE.search(file.read_text()), file


@pytest.mark.parametrize("file", sorted(ROOT.glob("*.md")), ids=lambda file: file.name)
def test_repository_root_documentation_is_absent(file):
    assert not GATE.API_REFERENCE.search(file.read_text()), file


@pytest.mark.parametrize("path,kind", [
    ("fi/deployments/__init__.py", "wheel"),
    ("fi/deployments.py", "wheel"),
    ("futureagi-0.7.0/fi/deployments/client.py", "sdist"),
    ("package/dist/esm/deployments/index.js", "npm"),
    ("package/dist/src/deployments.js", "npm"),
    ("package/dist/esnext/deployments.d.ts", "npm"),
])
def test_inventory_rejects_accidentally_shipped_modules(path, kind):
    files = {"package/package.json": b'{"exports": {".": "./dist/src/index.js"}}', path: b""}
    assert any("deployment module" in item for item in GATE.check_files(files, kind))


@pytest.mark.parametrize("reference", [
    "from fi.deployments import Deployment", "client.deployments.create()",
    "import '@future-agi/sdk/deployments'", "futureagi deployments list",
    'pip install "futureagi[deployments]"',
    "**Handles.** `Deployment`, `Sandbox` and `Run` exist in both languages with the same verbs:\n"
    "field access (`.id`, `.status`).",
    "`AsyncDeployment` is the asynchronous handle.",
    "`Deployments` provides the collection methods.",
    "`AsyncDeployments` provides the asynchronous collection methods.",
])
def test_inventory_rejects_advertised_api(reference):
    assert GATE.check_files({"fi/README.md": reference.encode()}, "wheel")


@pytest.mark.parametrize("package", [
    {"exports": {"./deployments": "./dist/deployments.js"}},
    {"exports": {"./*": "./dist/*.js"}},
    {"typesVersions": {"*": {"deployments": ["./dist/deployments.d.ts"]}}},
    {"typesVersions": {"*": {"*": ["./dist/*.d.ts"]}}},
    {"scripts": {"build:deployments": "tsc"}},
])
def test_inventory_rejects_exports_types_and_build_entries(package):
    assert GATE.check_files({"package/package.json": json.dumps(package).encode()}, "npm")


def test_inventory_rejects_plugin_and_extra():
    files = {
        "futureagi.dist-info/entry_points.txt": b"[futureagi.cli]\ndeployments = fi.deployments._cli\n",
        "futureagi.dist-info/METADATA": b"Provides-Extra: deployments\n",
    }
    assert len(GATE.check_files(files, "wheel")) == 2


def test_inventory_accepts_unrelated_deployment_terminology():
    assert GATE.check_files({"fi/README.md": b"Prompt deployment labels and self-hosted deployments."}, "wheel") == []
    assert GATE.check_files({"package/package.json": b'{"exports": {".": "./dist/index.js"}}'}, "npm") == []
