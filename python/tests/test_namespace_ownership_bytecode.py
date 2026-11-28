"""Bytecode SIMPLE-state escapes; executed red/green is reserved for SDK U22."""
from __future__ import annotations

from importlib.util import cache_from_source
from pathlib import Path
import sys

import pytest

from fi._core import namespace_footprint as footprint
from fi._core import namespace_ownership as ownership
from test_namespace_ownership_footprint import BOUNDED_FOLLOW_UP, installed
from test_namespace_ownership_safety import assert_manual_only
from test_namespace_ownership_simple import forbidden_owner, simple_sdk


@pytest.mark.parametrize("suffix", [".pyc", ".pyo"])
def test_hidden_py_filename_protects_pip_derived_siblings(tmp_path, suffix):
    site = tmp_path.resolve() / "site"
    own = simple_sdk(site)
    source = "scratch/.py"
    shared = "scratch/" + suffix
    companion = installed(site, "agentcc", "2.0.0", payload={shared: b"# supported bytecode\n"})
    (site / source).write_bytes(b"# foreign source\n")
    offender = forbidden_owner(site, claims=[source])
    assert Path(source).suffix == ""
    assert source.endswith(".py")
    assert shared in companion.read_text("RECORD")
    assert not (site / source).is_symlink()
    assert not (site / shared).is_symlink()

    result = ownership.inspect_installed([own, companion, offender])

    assert_manual_only(result, ["agentcc", "foreign-runtime"], source)
    assert shared in "\n".join(result["repair_commands"])
    assert (site / shared).read_bytes() == b"# supported bytecode\n"


@pytest.mark.parametrize("source_first", [False, True], ids=["real-row-first", "source-first"])
def test_derived_display_label_cannot_overwrite_a_real_record_claim(tmp_path, source_first):
    site = tmp_path.resolve() / "site"
    own = simple_sdk(site)
    source = "scratch/worker.py"
    bytecode = site / "scratch/worker.pyc"
    # This display label is ALSO a legal, unrelated POSIX RECORD filename.
    shared = f"{source} -> {bytecode}"
    companion = installed(site, "agentcc", "2.0.0", payload={shared: b"# supported real row\n"})
    (site / source).write_bytes(b"# foreign source\n")
    bytecode.write_bytes(b"# foreign bytecode\n")
    claims = [source, shared] if source_first else [shared, source]
    offender = forbidden_owner(site, claims=claims)
    assert shared in offender.read_text("RECORD")
    assert shared in companion.read_text("RECORD")
    assert offender.locate_file(shared) == companion.locate_file(shared)
    assert offender.locate_file(shared) != bytecode

    result = ownership.inspect_installed([own, companion, offender])

    assert_manual_only(result, ["agentcc", "foreign-runtime"], shared)
    assert (site / shared).read_bytes() == b"# supported real row\n"
    assert bytecode.read_bytes() == b"# foreign bytecode\n"


@pytest.mark.parametrize("optimization", ["3", "10"])
@pytest.mark.parametrize("redirected_cache", [False, True], ids=["standard-cache", "cache-prefix"])
def test_active_optimization_bytecode_symlink_requires_manual_repair(
        tmp_path, monkeypatch, optimization, redirected_cache):
    site = tmp_path.resolve() / "site"
    if redirected_cache:
        monkeypatch.setattr(sys, "pycache_prefix", str(site / "cache-prefix"))
    own = simple_sdk(site)
    shared = "outside/supported.pyc"
    companion = installed(site, "agentcc", "2.0.0", payload={shared: b"# supported bytecode\n"})
    source = site / "scratch/worker.py"
    source.parent.mkdir()
    source.write_bytes(b"# foreign source\n")
    cache = Path(cache_from_source(str(source), optimization=optimization))
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.symlink_to(site / shared)
    offender = forbidden_owner(site, claims=["scratch/worker.py"])

    # Model PYTHONOPTIMIZE > 2 at the stdlib boundary without spawning an
    # interpreter or replacing the scanner. Explicit optimization values keep
    # their real semantics; only a default call sees the active setting.
    def active_cache_from_source(path, debug_override=None, *, optimization=None):
        return cache_from_source(path, debug_override, optimization=(
            active_optimization if optimization is None else optimization))

    active_optimization = optimization
    monkeypatch.setattr(footprint, "cache_from_source", active_cache_from_source)
    assert cache.is_symlink()
    assert str(cache) not in offender.read_text("RECORD")
    assert not any(Path(cache_from_source(str(source), optimization=opt)).is_symlink()
                   for opt in ("", "1", "2"))

    result = ownership.inspect_installed([own, companion, offender])

    assert_manual_only(result, ["foreign-runtime"], "scratch/worker.py")
    assert str(cache) in "\n".join(result["repair_commands"])
    assert (site / shared).read_bytes() == b"# supported bytecode\n"


@pytest.mark.parametrize("kind", ["ordinary-source", "hidden-source", "display-label-row"])
def test_disjoint_bytecode_claims_keep_simple_owner_specific_commands(tmp_path, kind):
    site = tmp_path.resolve() / "site"
    own = simple_sdk(site)
    shared = "outside/keep.pyc"
    companion = installed(site, "agentcc", "2.0.0", payload={shared: b"# supported bytecode\n"})
    source = "scratch/.py" if kind == "hidden-source" else "scratch/worker.py"
    (site / source).parent.mkdir()
    (site / source).write_bytes(b"# foreign source\n")
    claims = [source]
    if kind == "display-label-row":
        label_row = f"{source} -> {site / 'scratch/worker.pyc'}"
        (site / label_row).parent.mkdir(parents=True)
        (site / label_row).write_bytes(b"# foreign real row\n")
        claims.append(label_row)
    offender = forbidden_owner(site, claims=claims)

    result = ownership.inspect_installed([own, companion, offender])

    assert result["issues"] == [{"kind": "unowned-path", "distribution": "foreign-runtime",
                                 "path": "fi/cli/foreign.py"}]
    assert result["repair_commands"] == ["pip uninstall foreign-runtime", *BOUNDED_FOLLOW_UP]
    assert "-y" not in "\n".join(result["repair_commands"])
    assert not any("agentcc" in step or "Manual repair" in step for step in result["repair_commands"])
    assert (site / shared).read_bytes() == b"# supported bytecode\n"
