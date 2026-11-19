"""E-NEW: fi.gateway against the agentcc 1.0.0 golden.

The golden pins library behaviour: pydantic's error text and its
errors.pydantic.dev/<version> links, httpx's defaults. So the comparison runs
only in the environment the golden was recorded in (Python line and every
library in ``compare.PINNED_DEPS``); anywhere else, including the fixed CI line
(``pip install -e ./python pytest`` resolves the newest pydantic), the test is
skipped with the differences named, never passed. The gate is the pinned run::

    pip install -c tests/fixtures/gateway/e-old/constraints-py.txt -e ./python pytest   # Python 3.12
    PYTHONPATH=python pytest -q python/tests/gateway/parity/test_parity_enew.py -rs
"""

from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from ._fixtures import FIXTURES, GOLDEN, REPO
from .compare import compare, load_recording, pinned_environment_differences
from .record import library_environment

PINNED = "pip install -c tests/fixtures/gateway/e-old/constraints-py.txt on Python 3.12"


def _has_gateway() -> bool:
    try:
        return importlib.util.find_spec("fi.gateway") is not None
    except ModuleNotFoundError:
        return False


def _golden_environment() -> dict:
    return load_recording(GOLDEN / "py-agentcc-1.0.0")["index"]["environment"]


def _skip_reason() -> str | None:
    if not _has_gateway():
        return "fi.gateway is not in this tree yet (the fi.gateway port adds it)"
    differences = pinned_environment_differences(
        _golden_environment(), library_environment()
    )
    if differences:
        return f"not the golden's environment ({'; '.join(differences)}): run with {PINNED}"
    return None


def _record_in_a_fresh_interpreter(out: Path) -> None:
    """A recording reads fi.gateway's namespace (surface.modules), and fi.gateway caches
    each lazy name a caller resolves, so in a process where other tests ran first the
    recording would list names they imported. A fresh interpreter sees what an
    importer sees."""
    env = {k: v for k, v in os.environ.items() if k != "PYTHONPATH"}
    env["PYTHONPATH"] = str(REPO / "python")
    done = subprocess.run(
        [
            sys.executable,
            "-m",
            "parity.record",
            "--root",
            "fi.gateway",
            "--out",
            str(out),
        ],
        cwd=Path(__file__).resolve().parents[1],
        env=env,
        capture_output=True,
        text=True,
    )
    # the recorder's own output, so a failure in it says what failed
    assert done.returncode == 0, (
        f"parity.record exited {done.returncode}\n"
        f"stderr:\n{done.stderr[-4000:]}\nstdout:\n{done.stdout[-2000:]}"
    )


def test_e_new_matches_the_golden_up_to_intended_differences(tmp_path) -> None:
    reason = _skip_reason()
    if reason:
        pytest.skip(reason)
    _record_in_a_fresh_interpreter(tmp_path)
    report = compare(
        GOLDEN / "py-agentcc-1.0.0",
        tmp_path,
        FIXTURES / "intended-differences.json",
        "py-agentcc-1.0.0->e-new-py",
    )
    (tmp_path / "report.json").write_text(
        json.dumps(report, indent=1, sort_keys=True, default=str)
    )
    assert report["ok"], json.dumps(report["unlisted"][:20], default=str)


def test_the_environment_check_names_each_difference() -> None:
    golden = _golden_environment()
    assert pinned_environment_differences(golden, golden) == []
    assert pinned_environment_differences(
        golden, {**golden, "python": "3.12.11"}
    ) == [], "a patch release is the same line"
    ci = {
        **golden,
        "python": "3.10.18",
        "deps": {**golden["deps"], "pydantic": "2.14.0", "httpx": None},
    }
    assert pinned_environment_differences(golden, ci) == [
        "python 3.12 != 3.10",
        "httpx 0.28.1 != None",
        "pydantic 2.10.4 != 2.14.0",
    ]


def test_the_constraints_file_pins_the_golden_libraries() -> None:
    """constraints-py.txt is the pinned run's install line; it must name every
    library version the golden records, or the gate could never run."""
    pins = dict(
        line.split("==")
        for line in (FIXTURES / "e-old" / "constraints-py.txt").read_text().splitlines()
        if "==" in line and not line.startswith("#")
    )
    for dep, version in _golden_environment()["deps"].items():
        if dep not in {"agentcc", "futureagi"} and version is not None:
            assert pins.get(dep) == version, dep


def test_a_present_gateway_in_another_environment_is_skipped_by_name(
    monkeypatch,
) -> None:
    import sys

    module = sys.modules[__name__]
    golden = _golden_environment()
    monkeypatch.setattr(module, "_has_gateway", lambda: True)
    monkeypatch.setattr(
        module,
        "library_environment",
        lambda: {**golden, "deps": {**golden["deps"], "pydantic": "2.14.0"}},
    )
    reason = _skip_reason()
    assert reason and "pydantic 2.10.4 != 2.14.0" in reason and PINNED in reason
    monkeypatch.setattr(module, "library_environment", lambda: golden)
    assert _skip_reason() is None
