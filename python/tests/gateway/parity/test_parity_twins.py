"""Both recorders record the same cases where a rule holds in both languages.

The fold plan's env rules (1.6 D-07 and D-14, 2.1 key order and FI-key guard,
2.2 base-URL order) apply to Python and TypeScript alike. A case one recorder
lacks is a 1.x behaviour with no baseline on that side, so a port could change
it and still pass parity. The Python recorder and the TypeScript recorder are
separate code, so the committed goldens are where the two are held together;
this test runs in the fixed CI line.
"""

from __future__ import annotations

import re

import pytest

from ._fixtures import GOLDEN, load
from .compare import load_recording

CATALOG = load("catalog.json")
TWINS = {k: v for k, v in CATALOG["twins"].items() if k != "about"}
TS_CLIENTS = sorted(
    n for n, g in CATALOG["goldens"].items() if g["lang"] == "ts" and g["runs_cases"]
)
MODE = re.compile(r"\[(sync|async)\]$")


def _ids(name: str, prefix: str) -> set[str]:
    ids = load_recording(GOLDEN / name)["index"]["case_ids"]
    return {MODE.sub("", i) for i in ids if i.startswith(prefix)}


def _unexplained(ids: set[str], allowed: dict[str, str]) -> list[str]:
    return sorted(i for i in ids if not any(i.startswith(p) for p in allowed))


@pytest.mark.parametrize("area", sorted(TWINS))
@pytest.mark.parametrize("ts", TS_CLIENTS)
def test_both_languages_record_the_same_ids(area: str, ts: str) -> None:
    spec = TWINS[area]
    py, other = _ids("py-agentcc-1.0.0", spec["prefix"]), _ids(ts, spec["prefix"])
    assert py and other, f"{area}: no {spec['prefix']} case recorded"
    assert not _unexplained(py - other, spec["py_only"]), f"{ts} lacks Python's"
    assert not _unexplained(other - py, spec["ts_only"]), f"py lacks {ts}'s"


@pytest.mark.parametrize("area", sorted(TWINS))
def test_every_language_only_prefix_is_used(area: str) -> None:
    """An exemption that matches nothing would hide a future gap silently."""
    spec = TWINS[area]
    py = _ids("py-agentcc-1.0.0", spec["prefix"])
    ts = set().union(*(_ids(n, spec["prefix"]) for n in TS_CLIENTS))
    for side, ids, allowed in (
        ("py", py - ts, spec["py_only"]),
        ("ts", ts - py, spec["ts_only"]),
    ):
        for prefix, reason in allowed.items():
            assert reason.strip(), f"{area}: {side}_only {prefix} has no reason"
            assert any(i.startswith(prefix) for i in ids), f"{area}: unused {prefix}"


def test_the_twin_check_bites() -> None:
    """Negative control: a Python env id the TypeScript side lacks is reported,
    and an exempted prefix is not."""
    allowed = TWINS["env_matrix"]["py_only"]
    gap = {"env.key_both_env_differ.url_none", "env.async.key_arg"}
    assert _unexplained(gap, allowed) == ["env.key_both_env_differ.url_none"]
