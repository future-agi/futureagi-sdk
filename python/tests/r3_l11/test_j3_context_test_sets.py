"""Whole-set context tests keep every per-context guard: own fingerprint, own flagged files, explicit review."""

import json
from uuid import uuid4

import pytest

from fi.context import testing

A, B = str(uuid4()), str(uuid4())
RUNS = {A: str(uuid4()), B: str(uuid4())}
DIGEST = "sha256:" + "d" * 64


class Fake:
    """Server stand-in: previews per context, records creations, answers run polls."""

    def __init__(self):
        self.calls = []
        self.flagged = {A: True, B: True}

    def request(self, method, path, body=None, query=None, options=None):
        self.calls.append((method, path, body, options))
        if path == "/model-hub/skills/testing-options/":
            return {"models": [{"model_id": "m-off", "can_run": False}, {"model_id": "m-on", "can_run": True}],
                    "limits": {"profiles": {"quick": {"max_total_tokens": 1000}}}}
        context = A if A in path else B
        if path.endswith("/draft/"):
            return {"revision": 3 if context == A else 5, "digest": DIGEST}
        if path.endswith("/preview/"):
            files = [{"path": "ref.md", "sha256": "sha256:" + "1" * 64, "flags": ["evaluation_artifact"]}] if self.flagged[context] else []
            return {"fingerprint": "sha256:" + ("a" if context == A else "b") * 64, "attempt_count": 2,
                    "estimate": {"upper_bound_usd": "0.10"}, "provider_disclosure": {"task_provider": "openai"},
                    "inventory": [{"skill_id": "s", "files": files + [{"path": "SKILL.md", "sha256": "sha256:" + "2" * 64, "flags": []}]}],
                    "outbound_findings": []}
        if method == "POST" and path.endswith("/test-runs/"):
            return {"id": RUNS[context]}
        if path.endswith("/results/"):
            return {"results": [{"variants": [{"variant": "context", "attempts": [{"answer_verdict": "pass"}]}]}]}
        return {"status": "completed", "candidate": {"digest": DIGEST}}


def plan(fake):
    return testing.plan_set(testing.ContextTestingClient(fake), [A, B], request="ask", expect="ok", reviewed_case=True)


def run(fake, document, **change):
    arguments = dict(reviewed_plan=document["plan_digest"], reviewed_inventory=True, no_known_answer_keys=True,
                     classify_flagged="reference_material", reason="reference only",
                     acknowledge_provider_processing=True, wait_seconds=1)
    return testing.run_set(testing.ContextTestingClient(fake), document, **{**arguments, **change})


def test_each_context_keeps_its_own_candidate_fingerprint_and_flagged_files():
    document = plan(Fake())
    candidates = [row["configuration"]["candidate"] for row in document["contexts"]]
    assert candidates == [{"kind": "draft", "revision": 3, "digest": DIGEST}, {"kind": "draft", "revision": 5, "digest": DIGEST}]
    assert document["contexts"][0]["fingerprint"] != document["contexts"][1]["fingerprint"]
    assert all(len(row["flagged"]) == 1 for row in document["contexts"])
    assert document["contexts"][0]["configuration"]["model"]["model_id"] == "m-on"


def test_run_creates_one_scoped_review_per_context_and_replays_with_stable_keys():
    fake = Fake()
    document = plan(fake)
    first = run(fake, document)
    second = run(fake, document)
    created = [(path, body, options) for method, path, body, options in fake.calls if method == "POST" and path.endswith("/test-runs/")]
    assert len(created) == 4
    assert created[0][2].idempotency_key == created[2][2].idempotency_key != created[1][2].idempotency_key
    for path, body, _ in created[:2]:
        context = A if A in path else B
        assert body["expected_fingerprint"] == document["contexts"][0 if context == A else 1]["fingerprint"]
        assert body["inventory_review"]["fingerprint"] == body["expected_fingerprint"]
        assert [item["path"] for item in body["inventory_review"]["classifications"]] == ["ref.md"]
        assert body["acknowledge_provider_processing"] is True
    assert first == second and [row["status"] for row in first["runs"]] == ["completed", "completed"]
    assert first["runs"][0]["verdicts"] == [{"variant": "context", "answer": "pass"}]


@pytest.mark.parametrize("change", [
    {"reviewed_plan": "sha256:" + "0" * 64}, {"reviewed_inventory": False}, {"no_known_answer_keys": False},
    {"acknowledge_provider_processing": False}, {"classify_flagged": None}, {"reason": " "},
])
def test_no_implicit_review_or_consent(change):
    fake = Fake()
    document = plan(fake)
    before = len(fake.calls)
    with pytest.raises(ValueError):
        run(fake, document, **change)
    assert len(fake.calls) == before


def test_edited_plan_is_refused_before_any_paid_request():
    fake = Fake()
    document = plan(fake)
    document["contexts"][0]["flagged"] = []
    before = len(fake.calls)
    with pytest.raises(ValueError):
        run(fake, document)
    assert len(fake.calls) == before


def test_case_review_is_required_to_plan_and_unflagged_sets_need_no_classification():
    fake = Fake()
    with pytest.raises(ValueError):
        testing.plan_set(testing.ContextTestingClient(fake), [A], request="ask", expect="ok", reviewed_case=False)
    fake.flagged = {A: False, B: False}
    document = plan(fake)
    assert run(fake, document, classify_flagged=None, reason=None)["runs"][0]["status"] == "completed"


def test_cli_writes_a_private_plan_and_prints_the_shown_digest(tmp_path, monkeypatch, capsys):
    fake = Fake()
    monkeypatch.setenv("FI_ORGANIZATION_ID", str(uuid4()))
    monkeypatch.setenv("FI_WORKSPACE_ID", str(uuid4()))

    class Transport:
        def __init__(self, **kwargs):
            pass

        def __enter__(self):
            return fake

        def __exit__(self, *args):
            pass
    monkeypatch.setattr(testing, "Client", Transport)
    out = tmp_path / "plan.json"
    assert testing.main(["plan-set", A, B, "--request", "ask", "--expect", "ok", "--reviewed-case", "--out", str(out)]) == 0
    shown = json.loads(capsys.readouterr().out)
    assert shown["plan_digest"] == json.loads(out.read_text())["plan_digest"]
    assert (out.stat().st_mode & 0o777) == 0o600
    assert testing.main(["run-set", "--plan", str(out), "--reviewed-plan", shown["plan_digest"],
                         "--reviewed-inventory", "--no-known-answer-keys", "--classify-flagged", "reference_material",
                         "--reason", "reference only"]) == 2
