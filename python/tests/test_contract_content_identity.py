"""Content provenance hashes source bytes without newline normalization."""
import importlib.util
from pathlib import Path
from types import SimpleNamespace


def test_git_source_preserves_carriage_returns(monkeypatch):
    root = Path(__file__).resolve().parents[2]
    spec = importlib.util.spec_from_file_location(
        "contract_content", root / "scripts/snapshot-annotation-queue-contract.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    def read_bytes(*args, **kwargs):
        assert not kwargs.get("text")
        return SimpleNamespace(stdout=b"first\r\nsecond\n")

    monkeypatch.setattr(module.subprocess, "run", read_bytes)
    assert module.git("unused", "show", "HEAD:example.py") == "first\r\nsecond\n"
