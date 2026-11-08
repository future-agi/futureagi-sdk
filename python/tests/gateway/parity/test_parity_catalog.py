"""The parity case catalog is covered by every golden, the goldens are current,
and every method of the recorded client tree has a case."""

from __future__ import annotations

import re

import pytest

from ._fixtures import GOLDEN, load, statuses, stream_error_cases
from .cases import all_cases
from .compare import load_recording

CATALOG = load("catalog.json")
ENVELOPES = (
    "error_object",
    "error_object_minimal",
    "top_level_message",
    "non_json",
    "empty",
)
MODE = re.compile(r"\[(sync|async)\]$")


def _case_ids(name: str) -> list[str]:
    return [k for k in load_recording(GOLDEN / name)["cases"] if k != "<index>"]


def _base(case_id: str) -> str:
    return MODE.sub("", case_id)


def _prefixes(lang: str) -> dict[str, list[str]]:
    return {b["id"]: b.get(lang, []) for b in CATALOG["bullets"] if b.get(lang)}


@pytest.mark.parametrize(
    "name", sorted(n for n, g in CATALOG["goldens"].items() if g["runs_cases"])
)
def test_every_bullet_has_cases_in_every_golden(name: str) -> None:
    ids = [_base(i) for i in _case_ids(name)]
    missing = [
        b
        for b, prefixes in _prefixes(CATALOG["goldens"][name]["lang"]).items()
        if not any(i.startswith(p) for i in ids for p in prefixes)
    ]
    assert not missing, f"{name}: no case for bullets {missing}"


@pytest.mark.parametrize(
    "name", sorted(n for n, g in CATALOG["goldens"].items() if g["runs_cases"])
)
def test_every_recorded_case_belongs_to_a_bullet(name: str) -> None:
    prefixes = [
        p for ps in _prefixes(CATALOG["goldens"][name]["lang"]).values() for p in ps
    ]
    orphans = [
        i for i in _case_ids(name) if not any(_base(i).startswith(p) for p in prefixes)
    ]
    assert not orphans, f"{name}: cases outside the catalog: {orphans[:10]}"


@pytest.mark.parametrize("name", sorted(CATALOG["required"]))
def test_required_items_are_recorded(name: str) -> None:
    need = CATALOG["required"][name]
    ids = set(_case_ids(name))
    bases = {_base(i) for i in ids}
    expected: set[str] = set(need.get("case_ids", []))
    if need.get("statuses_x_envelopes"):
        expected |= {
            f"status.{s}.{e}" for s in statuses() for e in (*ENVELOPES, "headers")
        }
    if need.get("stream_fixture_names"):
        expected |= {f"stream.fixture.{c['name']}.iter" for c in stream_error_cases()}
    expected |= {f"stream.extra.{n}.iter" for n in need.get("stream_extra_names", [])}
    assert not expected - bases, f"{name}: missing {sorted(expected - bases)[:10]}"
    for mode in need.get("modes", []):
        assert any(i.endswith(f"[{mode}]") for i in ids), f"{name}: no {mode} case"


def test_unrunnable_golden_records_its_load_failures() -> None:
    index = load_recording(GOLDEN / "ts-client-1.0.0-cjs")["index"]
    assert index["case_ids"] == []
    assert index["loads"] and all(not v["ok"] for v in index["loads"].values())


def test_python_golden_is_current_with_the_catalog_code() -> None:
    """A case added or renamed in cases/ without re-recording fails here."""
    expected = [f"{c.id}[{m}]" for c in all_cases() for m in c.modes]
    recorded = load_recording(GOLDEN / "py-agentcc-1.0.0")["index"]["case_ids"]
    assert recorded == expected


def test_bullets_and_goldens_are_well_formed() -> None:
    ids = [b["id"] for b in CATALOG["bullets"]]
    assert len(ids) == len(set(ids))
    on_disk = sorted(p.name for p in GOLDEN.iterdir() if p.is_dir())
    assert on_disk == sorted(CATALOG["goldens"])


def _methods(tree: dict, prefix: str = "") -> set[str]:
    out: set[str] = set()
    for name, node in tree.items():
        if "members" in node:
            out |= _methods(node["members"], f"{prefix}{name}.")
        elif "method" in node:
            out.add(prefix + name)
    return out


def test_every_client_method_has_a_case_in_each_mode() -> None:
    """The method list is the golden's own record of the 1.0.0 client
    (surface.client_tree), not a hand list. A resource method (a dotted path)
    needs a resource.* case; a client method (close, aclose, session,
    with_options, reset_cost) needs any case. Each case names what it calls
    with _runner.exercises."""
    tree = load_recording(GOLDEN / "py-agentcc-1.0.0")["cases"][
        "surface.client_tree[sync]"
    ]["result"]
    cases = all_cases()
    for cls, mode in (("AgentCC", "sync"), ("AsyncAgentCC", "async")):
        called = {
            path
            for c in cases
            if mode in c.modes
            for path in getattr(c.fn, "exercises", ())
            if "." not in path or c.id.startswith("resource.")
        }
        missing = sorted(_methods(tree[cls]) - called)
        assert not missing, f"{cls}: no {mode} case calls {missing}"
    known = _methods(tree["AgentCC"]) | _methods(tree["AsyncAgentCC"])
    declared = {p for c in cases for p in getattr(c.fn, "exercises", ())}
    assert declared <= known, f"not client methods: {sorted(declared - known)}"
