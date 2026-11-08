"""The unavailable sandbox surface must be absent, not a callable placeholder."""
from __future__ import annotations

import asyncio
import importlib
import json
import re
from pathlib import Path

import pytest

from fi import AsyncFutureAGIClient, FutureAGIClient
from fi._cli.main import main
from fi._core.policy import lookup
from fi.errors import PlatformNotConfiguredError
from fi.generated.platform.policy import OPERATIONS

ROOT = Path(__file__).resolve().parents[3]


def test_sandbox_operations_are_not_offered_in_either_language():
    mapping = json.loads((ROOT / "openapi/platform/wrapper-map.json").read_text())
    entries = {k: v for k, v in mapping["operations"].items() if k.startswith("sandboxes.")}
    assert len(entries) == 23
    assert "Sandbox" not in mapping["handles"]
    for name, entry in entries.items():
        assert entry["languages"] == {"py": "NOT-OFFERED", "ts": "NOT-OFFERED"}
        assert entry["unwrapped"]
        assert "methods" not in entry
        assert name not in OPERATIONS
        with pytest.raises(PlatformNotConfiguredError):
            lookup(OPERATIONS, name)
    assert entries["sandboxes.settings.update"]["until"] == "never"
    scope = json.loads((ROOT / "openapi/platform/scope.json").read_text())
    assert not any(name.startswith("sandboxes.") for name in scope["operations"])


@pytest.mark.parametrize("module", ["fi.sandboxes", "fi.sandboxes.types", "fi.sandboxes._cli"])
def test_sandbox_imports_fail(module):
    with pytest.raises(ModuleNotFoundError) as exc:
        importlib.import_module(module)
    assert exc.value.name == "fi.sandboxes"


def test_sync_and_async_clients_have_no_sandbox_accessor():
    options = {"base_url": "http://127.0.0.1:9", "api_key": "test-key", "secret_key": "test-secret"}
    for cls in (FutureAGIClient, AsyncFutureAGIClient):
        client = cls(**options)
        try:
            for view in (client, client.with_options(retries=0)):
                assert not hasattr(view, "sandboxes")
                with pytest.raises(AttributeError):
                    getattr(view, "sandboxes")
        finally:
            if isinstance(client, AsyncFutureAGIClient):
                asyncio.run(client.aclose())
            else:
                client.close()
    import fi
    assert not any(hasattr(fi, name) for name in ("Sandbox", "AsyncSandbox", "SandboxesClient", "AsyncSandboxesClient"))


def test_sandbox_cli_is_not_registered(capsys):
    assert main(["--help"]) == 0
    assert "sandboxes" not in capsys.readouterr().out.lower()
    assert main(["sandboxes", "--help"]) == 2
    captured = capsys.readouterr()
    assert "invalid choice" in captured.err
    assert "Traceback" not in captured.err


def test_release_tree_and_documentation_have_no_sandbox_namespace():
    for relative in ("python/fi/sandboxes", "typescript/futureagi/src/sandboxes"):
        assert not (ROOT / relative).exists()
    for relative in ("README.md", "CONVENTIONS.md", "python/README.md", "typescript/futureagi/README.md", "python/fi/generated/platform/types.py"):
        text = (ROOT / relative).read_text()
        for public_path in ("client.sandboxes", "fi.sandboxes", "@future-agi/sdk/sandboxes", "futureagi sandboxes"):
            assert public_path not in text, (relative, public_path)
    # Package-internal guides ship too, not just the top-level README files.
    documents = list((ROOT / "python/fi").rglob("*.md"))
    assert ROOT / "python/fi/_cli/README.md" in documents
    for document in documents:
        assert not re.search(r"\bsandbox(?:es)?\b", document.read_text(), re.IGNORECASE), document
    from fi.generated.platform import types
    assert not any("Sandbox" in title or title.startswith("OmegaExec") for title in types.TITLES)
