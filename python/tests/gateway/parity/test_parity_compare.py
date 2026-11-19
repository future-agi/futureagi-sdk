"""The comparator: conformance cases, the rules proven on real goldens
(1.0.0 -> 1.0.1 is exactly D-01, ESM equals CJS), and negative controls that
tamper a real golden and must be reported."""

from __future__ import annotations

import copy

import pytest

from ._fixtures import FIXTURES, GOLDEN, load, stream_error_cases
from .compare import compare, compare_cases, load_recording

INTENDED = load("intended-differences.json")["differences"]
CONFORMANCE = load("comparator-cases.json")["cases"]


@pytest.mark.parametrize("case", CONFORMANCE, ids=[c["name"] for c in CONFORMANCE])
def test_conformance(case: dict) -> None:
    report = compare_cases(case["golden"], case["new"], case["intended"], case["label"])
    got = {
        "ok": report["ok"],
        "unlisted": [[d["path"], d["kind"], d["planned"]] for d in report["unlisted"]],
        "covered": report["covered"],
        "unobserved_proven": report["unobserved_proven"],
        "unobserved_planned": report["unobserved_planned"],
    }
    assert got == case["expect"]


def _report(old: str, new: str, intended: list | None = None) -> dict:
    a, b = load_recording(GOLDEN / old)["cases"], load_recording(GOLDEN / new)["cases"]
    return compare_cases(
        a, b, INTENDED if intended is None else intended, f"{old}->{new}"
    )


def test_ts_1_0_0_to_1_0_1_is_exactly_d01() -> None:
    report = _report("ts-client-1.0.0-esm", "ts-client-1.0.1-esm")
    assert report["ok"], report["unlisted"][:5]
    assert set(report["covered"]) == {"D-01a", "D-01b", "D-01c"}


def test_ts_cjs_1_0_0_to_1_0_1_is_d01d() -> None:
    report = _report("ts-client-1.0.0-cjs", "ts-client-1.0.1-cjs")
    assert report["ok"], report["unlisted"][:5]
    assert "D-01d" in report["covered"]


def test_negative_control_without_d01c_the_version_change_is_unlisted() -> None:
    without = [d for d in INTENDED if d["id"] != "D-01c"]
    report = _report("ts-client-1.0.0-esm", "ts-client-1.0.1-esm", without)
    assert not report["ok"]
    assert any(d["path"].endswith("/headers/user-agent") for d in report["unlisted"])


def test_negative_control_a_proven_rule_must_be_observed() -> None:
    report = _report(
        "ts-client-1.0.1-esm",
        "ts-client-1.0.1-esm",
        [{**copy.deepcopy(INTENDED[0]), "applies_to": ["*"]}],
    )
    assert report["unobserved_proven"] == ["D-01a"] and not report["ok"]


def test_negative_control_d01a_does_not_mask_a_changed_stream_chunk() -> None:
    old = load_recording(GOLDEN / "ts-client-1.0.0-esm")["cases"]
    new = copy.deepcopy(load_recording(GOLDEN / "ts-client-1.0.1-esm")["cases"])
    item = new["stream.fixture.normal_stream.iter"]["result"]["items"][0]
    item["choices"][0]["delta"]["content"] = "tampered"
    report = compare_cases(
        old, new, INTENDED, "ts-client-1.0.0-esm->ts-client-1.0.1-esm"
    )
    assert [d["path"] for d in report["unlisted"]] == [
        "stream.fixture.normal_stream.iter/result/items/0/choices/0/delta/content"
    ]


def _tampered(name: str, edit) -> tuple[dict, dict]:
    golden = load_recording(GOLDEN / name)["cases"]
    new = copy.deepcopy(golden)
    edit(new)
    return golden, new


def _unlisted(report: dict) -> list[tuple[str, str, list[str]]]:
    return [(d["path"], d["kind"], d["planned"]) for d in report["unlisted"]]


# A planned entry has no evidence, test id or reviewer, so it covers nothing
# (regression check, finding 1: D-02, D-07 and D-16 hid these three tampers).
def test_regression_planned_d02_does_not_hide_a_changed_python_stream_chunk() -> None:
    def edit(cases: dict) -> None:
        item = cases["stream.fixture.normal_stream.iter[sync]"]["result"]["items"][0]
        item["data"]["choices"][0]["delta"]["content"] = "TAMPERED"

    golden, new = _tampered("py-agentcc-1.0.0", edit)
    report = compare_cases(golden, new, INTENDED, "py-agentcc-1.0.0->e-new-py")
    assert not report["ok"] and report["covered"] == {}
    assert _unlisted(report) == [
        (
            "stream.fixture.normal_stream.iter[sync]/result/items/0/data/choices/0/delta/content",
            "changed",
            ["D-02"],
        )
    ]


def test_regression_planned_d07_does_not_hide_a_request_to_another_host() -> None:
    def edit(cases: dict) -> None:
        for request in cases["env.base_url.localhost[async]"]["requests"]:
            request["host"] = "attacker.example"

    golden, new = _tampered("py-agentcc-1.0.0", edit)
    report = compare_cases(golden, new, INTENDED, "py-agentcc-1.0.0->e-new-py")
    assert not report["ok"] and report["covered"] == {}
    sent = len(golden["env.base_url.localhost[async]"]["requests"])
    assert _unlisted(report) == [
        (f"env.base_url.localhost[async]/requests/{i}/host", "changed", ["D-07"])
        for i in range(sent)
    ]


def test_regression_planned_d16_does_not_hide_replaced_events() -> None:
    def edit(cases: dict) -> None:
        cases["stream.fixture.normal_stream.events[sync]"] = {
            "result": "anything at all"
        }

    golden, new = _tampered("py-agentcc-1.0.0", edit)
    report = compare_cases(golden, new, INTENDED, "py-agentcc-1.0.0->e-new-py")
    assert not report["ok"] and report["covered"] == {}
    paths = [d["path"] for d in report["unlisted"]]
    assert "stream.fixture.normal_stream.events[sync]/result" in paths
    assert all("D-16" in d["planned"] for d in report["unlisted"])


# D-01a matches only what 1.0.1 changed (regression check, finding 2).
def test_regression_d01a_does_not_cover_a_dropped_stream_chunk() -> None:
    old = load_recording(GOLDEN / "ts-client-1.0.0-esm")["cases"]
    _, new = _tampered(
        "ts-client-1.0.1-esm",
        lambda c: c["stream.fixture.normal_stream.iter"]["result"]["items"].pop(),
    )
    report = compare_cases(
        old, new, INTENDED, "ts-client-1.0.0-esm->ts-client-1.0.1-esm"
    )
    assert _unlisted(report) == [
        ("stream.fixture.normal_stream.iter/result/items/2", "removed", [])
    ]


def test_regression_d01a_does_not_cover_a_changed_message_or_final() -> None:
    def edit(cases: dict) -> None:
        consumed = cases["stream.malformed.choices_null.final"]["result"]["consumed"]
        consumed["drainedError"]["message"] = "TAMPERED"
        consumed["final"] = {"ok": "a completion"}

    old = load_recording(GOLDEN / "ts-client-1.0.0-esm")["cases"]
    _, new = _tampered("ts-client-1.0.1-esm", edit)
    report = compare_cases(
        old, new, INTENDED, "ts-client-1.0.0-esm->ts-client-1.0.1-esm"
    )
    case = "stream.malformed.choices_null.final/result/consumed"
    assert _unlisted(report) == [
        (f"{case}/drainedError/message", "changed", []),
        (f"{case}/final/ok", "added", []),
        (f"{case}/final/raised", "removed", []),
    ]


def test_regression_d01_never_applies_to_a_new_recording_against_1_0_0() -> None:
    def edit(cases: dict) -> None:
        cases["stream.fixture.normal_stream.iter"]["result"]["items"].pop()
        consumed = cases["stream.malformed.choices_null.final"]["result"]["consumed"]
        consumed["drainedError"]["message"] = "TAMPERED"

    golden, new = _tampered("ts-client-1.0.0-esm", edit)
    report = compare_cases(golden, new, INTENDED, "ts-client-1.0.0-esm->e-new-ts-esm")
    assert report["covered"] == {} and len(report["unlisted"]) == 2


def _frame_violations(cases: dict) -> list[str]:
    """Where a golden departs from stream-error-frames.json's expectations."""
    out = []
    for fixture in stream_error_cases():
        expect = fixture["expect"]
        result = cases[f"stream.fixture.{fixture['name']}.iter"]["result"]
        error, items = result["error"], result["items"]
        if not expect["raises"]:
            if error is not None or len(items) != expect["chunks"]:
                out.append(fixture["name"])
            continue
        attrs = (error or {}).get("attrs", {})
        if (
            (error or {}).get("class") != "StreamError"
            or attrs.get("type") != expect["type"]
            or attrs.get("code") != expect["code"]
            or error.get("message") != expect["message"]
            or len(items) != expect["chunks_before_error"]
        ):
            out.append(fixture["name"])
    return out


@pytest.mark.parametrize("name", ["ts-client-1.0.1-esm", "ts-client-1.0.1-cjs"])
def test_d01a_behaviour_is_what_the_1_0_1_goldens_record(name: str) -> None:
    """Each error frame raises StreamError(type, code, message) after exactly the
    chunks before it. A per-difference rule cannot see this: an error frame
    swallowed without a raise would differ from 1.0.0 only by the frame item's
    removal, which D-01a covers."""
    assert _frame_violations(load_recording(GOLDEN / name)["cases"]) == []


def test_negative_control_a_swallowed_error_frame_is_caught() -> None:
    def edit(cases: dict) -> None:
        cases["stream.fixture.guardrail_block_first_frame.iter"]["result"]["error"] = None

    _, new = _tampered("ts-client-1.0.1-esm", edit)
    assert _frame_violations(new) == ["guardrail_block_first_frame"]


def test_ts_1_0_1_esm_and_cjs_record_the_same_behaviour() -> None:
    report = _report("ts-client-1.0.1-esm", "ts-client-1.0.1-cjs", [])
    assert report["ok"] and report["unlisted"] == []


def test_python_golden_compares_clean_with_itself_through_the_cli_path() -> None:
    """The golden against itself has no difference, so nothing is unlisted; every
    proven entry that applies to e-new-py then covers nothing, and the comparator's
    rule (a proven entry must be observed where it applies) reports each one."""
    label = "py-agentcc-1.0.0->e-new-py"
    report = compare(
        GOLDEN / "py-agentcc-1.0.0",
        GOLDEN / "py-agentcc-1.0.0",
        FIXTURES / "intended-differences.json",
        label,
    )
    assert report["unlisted"] == [] and report["environment_differences"] == []
    applying = sorted(
        d["id"]
        for d in INTENDED
        if d["status"] == "proven" and label in d["applies_to"]
    )
    assert report["unobserved_proven"] == applying
    assert report["ok"] == (applying == [])
