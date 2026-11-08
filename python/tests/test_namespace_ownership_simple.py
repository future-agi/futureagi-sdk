"""SIMPLE-state allowlist regressions; runtime proof belongs to SDK U22."""
from __future__ import annotations

from importlib.util import cache_from_source
from pathlib import Path

import pytest

from fi._core import namespace_footprint as footprint
from fi._core import namespace_ownership as ownership
from test_namespace_ownership_aliases import add_distutils_script
from test_namespace_ownership_footprint import BOUNDED_FOLLOW_UP, installed
from test_namespace_ownership_repair import SUPPORTED
from test_namespace_ownership_safety import assert_manual_only


def simple_sdk(site):
    # No implicit wrapper metadata: these regressions isolate filesystem hazards.
    return installed(site, "futureagi", "0.7.0", payload={"fi/__init__.py": b"# sdk\n"})


def forbidden_owner(site, *, claims=(), entries=None):
    return installed(site, "foreign-runtime", payload={"fi/cli/foreign.py": b"# foreign\n"},
                     claims=claims, entries=entries)


@pytest.mark.parametrize("name,version,path", SUPPORTED)
@pytest.mark.parametrize("damage", ["omitted-row", "missing"])
def test_descendant_namespace_symlink_requires_manual_repair(tmp_path, name, version, path, damage):
    site = tmp_path.resolve() / "site"
    own = simple_sdk(site)
    root = (site / path).parent
    root.mkdir(parents=True, exist_ok=True)
    physical = site / "payload"
    physical.mkdir()
    (root / "external").symlink_to(physical, target_is_directory=True)
    shared = str(Path(path).parent / "external/shared.py")
    companion = installed(site, name, version, payload={shared: b"# supported\n"},
                          record="missing" if damage == "missing" else "complete", omitted=[shared])
    claim = "payload/shared.py"
    offender = forbidden_owner(site, claims=[claim])
    assert shared not in (companion.read_text("RECORD") or "")
    assert offender.locate_file(claim).resolve() == companion.locate_file(shared).resolve()

    result = ownership.inspect_installed([own, companion, offender])

    assert_manual_only(result, [name, "foreign-runtime"], claim)
    assert (physical / "shared.py").read_bytes() == b"# supported\n"


@pytest.mark.parametrize("effect", ["script", "cache", "namespace-bin"])
def test_implicit_distutils_removal_and_sidecar_require_manual_repair(tmp_path, effect):
    site = tmp_path.resolve() / "site"
    own = simple_sdk(site)
    script = "shared.py"
    if effect == "namespace-bin":
        path = "agentcc/shared.py"
    elif effect == "cache":
        path = str(Path(cache_from_source(str(site / "bin/shared.py"))).relative_to(site))
    else:
        path = "bin/shared.py"
    companion = installed(site, "agentcc", "2.0.0", payload={path: b"# supported\n"},
                          omitted=[path] if effect == "namespace-bin" else [])
    if effect == "namespace-bin":
        (site / "bin").symlink_to(site / "agentcc", target_is_directory=True)
    offender = forbidden_owner(site)
    add_distutils_script(offender, script)
    assert "bin/" not in offender.read_text("RECORD")
    assert (site / path).is_file()

    result = ownership.inspect_installed([own, companion, offender])

    assert_manual_only(result, ["foreign-runtime"], script)
    assert (site / path).read_bytes() == b"# supported\n"


@pytest.mark.parametrize("suffix", ["pyc", "cache"])
def test_final_component_symlink_cannot_hide_derived_bytecode(tmp_path, suffix):
    site = tmp_path.resolve() / "site"
    own = simple_sdk(site)
    path = ("agentcc/worker.pyc" if suffix == "pyc" else
            str(Path(cache_from_source(str(site / "agentcc/worker.py"))).relative_to(site)))
    companion = installed(site, "agentcc", "2.0.0", payload={path: b"# supported bytecode\n"})
    foreign = site / "foreign"
    foreign.mkdir()
    (foreign / "worker.bin").write_bytes(b"# unrelated\n")
    (site / "agentcc/worker.py").symlink_to(foreign / "worker.bin")
    (site / "alias").symlink_to(site / "agentcc", target_is_directory=True)
    claim = "alias/worker.py"
    offender = forbidden_owner(site, claims=[claim])
    assert offender.locate_file(claim).resolve() == foreign / "worker.bin"
    assert path in companion.read_text("RECORD")

    result = ownership.inspect_installed([own, companion, offender])

    assert_manual_only(result, ["agentcc", "foreign-runtime"], claim)
    assert (site / path).read_bytes() == b"# supported bytecode\n"


@pytest.mark.parametrize("kind", ["legacy-bytecode", "cache-directory", "cache-file"])
def test_derived_bytecode_symlink_components_are_checked(tmp_path, kind):
    site = tmp_path.resolve() / "site"
    own = simple_sdk(site)
    path = "agentcc/supported.pyc"
    companion = installed(site, "agentcc", "2.0.0", payload={path: b"# supported bytecode\n"})
    offender = forbidden_owner(site, claims=["scratch/worker.py"])
    source = site / "scratch/worker.py"
    source.parent.mkdir()
    source.write_bytes(b"# unrelated\n")
    cache = Path(cache_from_source(str(source)))
    if kind == "legacy-bytecode":
        source.with_suffix(".pyc").symlink_to(site / path)
    elif kind == "cache-directory":
        cache.parent.symlink_to(site / "agentcc", target_is_directory=True)
    else:
        cache.parent.mkdir()
        cache.symlink_to(site / path)

    result = ownership.inspect_installed([own, companion, offender])

    assert_manual_only(result, ["foreign-runtime"], "scratch/worker.py")
    assert (site / path).read_bytes() == b"# supported bytecode\n"


@pytest.mark.parametrize("entry", ["console_scripts", "gui_scripts", "empty-scripts-directory"])
def test_disjoint_implicit_scripts_are_not_simple(tmp_path, entry):
    site = tmp_path.resolve() / "site"
    own = simple_sdk(site)
    offender = forbidden_owner(site, entries=None if entry == "empty-scripts-directory"
                               else {entry: ["unrelated-tool"]})
    if entry == "empty-scripts-directory":
        (offender._path / "scripts").mkdir()

    result = ownership.inspect_installed([own, offender])

    assert_manual_only(result, ["foreign-runtime"], "script")


@pytest.mark.parametrize("failure", ["walk-error", "entry-limit", "depth-limit"])
def test_namespace_walk_errors_and_bounds_fail_closed(tmp_path, monkeypatch, failure):
    site = tmp_path.resolve() / "site"
    own = simple_sdk(site)
    companion = installed(site, "agentcc", "2.0.0", payload={"agentcc/deep/leaf.py": b"# supported\n"})
    offender = forbidden_owner(site)
    if failure == "walk-error":
        original = Path.iterdir

        def inaccessible(path):
            if path == site / "agentcc/deep":
                raise PermissionError("fixture namespace walk is unreadable")
            return original(path)

        monkeypatch.setattr(Path, "iterdir", inaccessible)
    elif failure == "entry-limit":
        monkeypatch.setattr(footprint, "MAX_SCAN_ENTRIES", 1, raising=False)
    else:
        monkeypatch.setattr(footprint, "MAX_SCAN_DEPTH", 0, raising=False)

    result = ownership.inspect_installed([own, companion, offender])

    assert_manual_only(result, ["agentcc", "foreign-runtime"], "namespace")


@pytest.mark.parametrize("name,version,path", SUPPORTED)
def test_simple_state_keeps_owner_specific_commands(tmp_path, name, version, path):
    site = tmp_path.resolve() / "site"
    own = simple_sdk(site)
    companion = installed(site, name, version, payload={path: b"# supported\n"})
    offender = forbidden_owner(site)

    result = ownership.inspect_installed([own, companion, offender])

    assert result["issues"] == [{"kind": "unowned-path", "distribution": "foreign-runtime",
                                 "path": "fi/cli/foreign.py"}]
    commands = result["repair_commands"]
    assert len(commands) == 3
    assert commands[0].startswith("pip uninstall ")
    assert commands[0].split()[-1] == "foreign-runtime"
    assert commands[1:] == BOUNDED_FOLLOW_UP
    assert not any(name in step or "Manual repair" in step for step in commands)
    assert (site / path).read_bytes() == b"# supported\n"


@pytest.mark.parametrize("state", ["simple", "multiple-owners", "sdk-only", "implicit-script"])
def test_no_emitted_command_anywhere_uses_yes_flag(tmp_path, monkeypatch, state):
    from fi._cli import ownership as section

    site = tmp_path.resolve() / "site"
    own = simple_sdk(site)
    distributions = [own]
    if state == "sdk-only":
        (site / "fi/__init__.py").write_bytes(b"# damaged\n")
    else:
        distributions.append(forbidden_owner(site, entries={"console_scripts": ["fi"]}
                                             if state == "implicit-script" else None))
        if state == "multiple-owners":
            distributions.append(installed(site, "ai-evaluation", "1.1.0"))
    monkeypatch.setattr(ownership.metadata, "distributions", lambda: distributions)

    result = ownership.inspect_installed(distributions)
    lines = section.section(None)

    assert result["status"] == "FAIL"
    assert "-y" not in "\n".join(result["repair_commands"])
    assert "-y" not in "\n".join(lines)
    assert "-y" not in "\n".join(ownership.manifest()["repair_commands"])
    assert lines[-1] == "futureagi-py doctor --offline"
