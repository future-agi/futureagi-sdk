"""A comparison's label must describe its two recordings (regression check, finding 4).

The hole: a new TypeScript recording compared with ``ts-client-1.0.0-esm``
under the label ``ts-client-1.0.0-esm->ts-client-1.0.1-esm`` would get D-01's
rules, which are proven only between the two fixed goldens.
"""

from __future__ import annotations

import json
import shutil

import pytest

from ._fixtures import FIXTURES, GOLDEN, load
from .compare import compare, main
from .labels import LabelError, label_problems

INTENDED = FIXTURES / "intended-differences.json"
CATALOG = load("catalog.json")


def _copy(tmp_path, name: str, edit=None):
    dest = tmp_path / name
    shutil.copytree(GOLDEN / name, dest)
    if edit:  # index.json keeps the old hashes: only the area file changes
        area = dest / "resources.json"
        data = json.loads(area.read_text())
        edit(data["cases"])
        area.write_text(json.dumps(data))
    return dest


def _drop_first_item(cases: dict) -> None:
    for value in cases.values():
        if isinstance(value, dict) and value.get("requests"):
            value["requests"].pop()
            return
    raise AssertionError("no case with requests")


def test_a_fresh_copy_of_the_1_0_1_golden_passes_under_the_d01_label(tmp_path) -> None:
    fresh = _copy(tmp_path, "ts-client-1.0.1-esm")
    report = compare(
        GOLDEN / "ts-client-1.0.0-esm",
        fresh,
        INTENDED,
        "ts-client-1.0.0-esm->ts-client-1.0.1-esm",
    )
    assert report["ok"] and sorted(report["covered"]) == ["D-01a", "D-01b", "D-01c"]


def test_a_port_recording_cannot_borrow_the_d01_label(tmp_path) -> None:
    port = _copy(tmp_path, "ts-client-1.0.1-esm", _drop_first_item)
    with pytest.raises(LabelError, match="byte for byte"):
        compare(
            GOLDEN / "ts-client-1.0.0-esm",
            port,
            INTENDED,
            "ts-client-1.0.0-esm->ts-client-1.0.1-esm",
        )


@pytest.mark.parametrize(
    ("golden", "label", "reason"),
    [
        (
            "ts-client-1.0.1-esm",
            "ts-client-1.0.0-esm->e-new-ts-esm",
            "not the committed golden",
        ),
        (
            "ts-client-1.0.0-esm",
            "ts-client-1.0.0-esm->e-new-ts-esm",
            "judged against ts-client-1.0.1-esm",
        ),
        ("py-agentcc-1.0.0", "py-agentcc-1.0.0->e-new-ts-esm", "judged against"),
        ("ts-client-1.0.1-cjs", "ts-client-1.0.1-cjs->e-new-ts-esm", "judged against"),
        (
            "py-agentcc-1.0.0",
            "py-agentcc-1.0.0->my-port",
            "neither a golden nor a new recording",
        ),
        ("py-agentcc-1.0.0", "py-agentcc-1.0.0", "is not <golden>-><new>"),
        ("py-agentcc-1.0.0", "agentcc-1.0.0->e-new-py", "is not a golden"),
    ],
)
def test_a_label_that_does_not_fit_is_refused(
    golden: str, label: str, reason: str
) -> None:
    problems = label_problems(label, GOLDEN / golden, GOLDEN / golden)
    assert any(reason in p for p in problems), problems
    with pytest.raises(LabelError):
        compare(GOLDEN / golden, GOLDEN / golden, INTENDED, label)


def test_a_modified_golden_under_the_golden_name_is_refused(tmp_path) -> None:
    fake = _copy(tmp_path, "py-agentcc-1.0.0", _drop_first_item)
    assert label_problems(
        "py-agentcc-1.0.0->e-new-py", fake, GOLDEN / "py-agentcc-1.0.0"
    ) == [f"--golden {fake} is not the committed golden py-agentcc-1.0.0"]


def test_every_documented_comparison_is_accepted() -> None:
    for new, baselines in CATALOG["comparisons"]["new_recordings"].items():
        for old in baselines:
            assert CATALOG["goldens"][old]["runs_cases"], old
            assert label_problems(f"{old}->{new}", GOLDEN / old, GOLDEN / old) == []


def test_the_cli_exits_2_on_a_refused_label(tmp_path, capsys) -> None:
    port = _copy(tmp_path, "ts-client-1.0.1-esm", _drop_first_item)
    code = main(
        [
            "--golden", str(GOLDEN / "ts-client-1.0.0-esm"),
            "--new", str(port),
            "--label", "ts-client-1.0.0-esm->ts-client-1.0.1-esm",
        ]
    )  # fmt: skip
    assert code == 2 and "refused" in capsys.readouterr().err
