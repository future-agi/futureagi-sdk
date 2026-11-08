"""Mutations prove the sandbox archive guard does not just check root exports."""
import json

import pytest

from ._gates_support import load


@pytest.mark.parametrize("label,path,content", [
    ("wheel", "fi/sandboxes/__init__.py", b""),
    ("wheel", "fi/sandboxes.py", b""),
    ("sdist", "futureagi/fi/sandboxes/_async_client.py", b""),
    ("npm", "package/dist/esm/sandboxes/index.js", b""),
    ("npm", "package/dist/src/sandboxes.d.ts", b""),
    ("wheel", "fi/generated/platform/policy.py", b'"sandboxes.create"'),
    ("wheel", "fi/generated/platform/types.py", b"import fi.sandboxes.types"),
    ("npm", "package/dist/esm/generated/platform/sdk.gen.js", b"createWorkspaceSandbox"),
    ("wheel", "fi/futureagi_client.py", b"def sandboxes(self): pass"),
    ("npm", "package/dist/esm/futureagi-client.d.ts", b"sandboxes: object"),
    ("wheel", "futureagi.dist-info/entry_points.txt", b"sandboxes = fi.sandboxes._cli"),
    ("npm", "package/README.md", b"client.sandboxes.create()"),
])
def test_guard_rejects_each_artifact_leak(label, path, content):
    guard = load("sandbox_artifact_guard", "scripts/packaging/check_sandbox_absence.py")
    archives = {"wheel": {}, "sdist": {}, "npm": {"package/package.json": b'{"exports": {".": "./index.js"}}'}}
    guard.check_sandbox_absence(**{"wheel": archives["wheel"], "source": archives["sdist"], "npm": archives["npm"]})
    archives[label][path] = content
    with pytest.raises(AssertionError):
        guard.check_sandbox_absence(archives["wheel"], archives["sdist"], archives["npm"])


@pytest.mark.parametrize("label,prefix", [
    ("wheel", "fi/"),
    ("sdist", "futureagi/fi/"),
    ("npm", "package/"),
])
@pytest.mark.parametrize("document", [
    "_cli/README.md", "docs/commands.md", "reference/commands.mdx",
    "reference/commands.rst", "reference/commands.html", "reference/commands.txt",
    "reference/commands.markdown", "reference/commands.adoc", "reference/commands.htm",
    "docs/README", "reference/COMMANDS.MD",
])
@pytest.mark.parametrize("reference", [
    b"Platform (`agents`, `deployments`, `sandboxes`, later `connectors`, `gateway`)",
    b"sandboxes  Manage isolated computers\n",
    b"# Sandboxes\n", b"## Sandbox reference\n",
    b"client.sandboxes.create()", b"futureagi sandboxes list",
    b"from fi.sandboxes import Sandbox", b"@future-agi/sdk/sandboxes",
])
def test_guard_rejects_sandbox_references_in_all_shipped_documentation(label, prefix, document, reference):
    guard = load("sandbox_artifact_guard", "scripts/packaging/check_sandbox_absence.py")
    archives = {"wheel": {}, "sdist": {}, "npm": {"package/package.json": b"{}"}}
    path = prefix + document
    archives[label][path] = b"Commands: agents, deployments, gateway."
    guard.check_sandbox_absence(archives["wheel"], archives["sdist"], archives["npm"])
    archives[label][path] = reference
    with pytest.raises(AssertionError, match="sandbox.*documentation") as exc:
        guard.check_sandbox_absence(archives["wheel"], archives["sdist"], archives["npm"])
    assert label in str(exc.value) and path in str(exc.value)


@pytest.mark.parametrize("label,path", [
    ("wheel", "futureagi.dist-info/METADATA"),
    ("sdist", "futureagi/PKG-INFO"),
])
def test_guard_checks_readme_embedded_in_package_metadata(label, path):
    guard = load("sandbox_artifact_guard", "scripts/packaging/check_sandbox_absence.py")
    archives = {"wheel": {}, "sdist": {}, "npm": {"package/package.json": b"{}"}}
    archives[label][path] = b"Metadata-Version: 2.1\n\nCommands: `sandboxes`"
    with pytest.raises(AssertionError, match="sandbox.*documentation"):
        guard.check_sandbox_absence(archives["wheel"], archives["sdist"], archives["npm"])


def test_guard_keeps_shared_error_names_and_non_documentation():
    guard = load("sandbox_artifact_guard", "scripts/packaging/check_sandbox_absence.py")
    guard.check_sandbox_absence(
        {"fi/errors.py": b"class SandboxStateError: pass", "fi/README.md": b"SandboxStateError"},
        {"futureagi/tests/test_absence.py": b'assert "sandboxes" not in commands'},
        {"package/package.json": b"{}", "package/README.md": b"SandboxStateError"},
    )


@pytest.mark.parametrize("field,value", [
    ("exports", {"./sandboxes": "./sandbox.js"}),
    ("typesVersions", {"*": {"sandboxes": ["sandbox.d.ts"]}}),
])
def test_guard_rejects_manifest_registrations(field, value):
    guard = load("sandbox_artifact_guard", "scripts/packaging/check_sandbox_absence.py")
    with pytest.raises(AssertionError):
        guard.check_sandbox_absence({}, {}, {"package/package.json": json.dumps({field: value}).encode()})
