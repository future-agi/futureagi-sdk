"""Scenario lifecycle, validation and run readiness on client.simulation, against an in-process
httpx MockTransport (no backend)."""

from __future__ import annotations

import json

import fi.platform as fp
import httpx
import pytest

BASE = "http://backend.test"
ENV = "11111111-1111-4111-8111-11111111111a"
H = f"/simulate/api/harness-environments/{ENV}/"


def _client(sent: list[httpx.Request], result: dict, status: int = 200, **kw) -> fp.Client:
    def handler(request: httpx.Request) -> httpx.Response:
        sent.append(request)
        return httpx.Response(status, json={"status": True, "result": result})

    http = httpx.Client(transport=httpx.MockTransport(handler))
    return fp.Client(api_key="k", secret_key="s", base_url=BASE, http_client=http, **kw)


def test_scenario_list_filters_by_lifecycle():
    sent: list[httpx.Request] = []
    client = _client(sent, {"results": [], "lifecycle_counts": {"archived": 2}})

    client.simulation.jobs.scenarios.list(ENV, lifecycle="archived")

    assert sent[0].url.path == f"/simulate/api/harness-jobs/{ENV}/scenarios/"
    assert sent[0].url.params["lifecycle"] == "archived"


def test_validate_names_the_keys_and_returns_the_job():
    sent: list[httpx.Request] = []
    client = _client(sent, {"state": "running", "job_id": "j1"}, status=202)

    started = client.simulation.environments.scenarios.validate(ENV, keys=["refund-flow"], reprove_all=False)
    client.simulation.environments.scenarios.validation_status(ENV, job_id=started.job_id)

    assert (sent[0].method, sent[0].url.path) == ("POST", H + "scenarios/validate/")
    assert json.loads(sent[0].content) == {"keys": ["refund-flow"], "reprove_all": False}
    assert started.job_id == "j1"
    assert (sent[1].method, sent[1].url.path) == ("GET", H + "scenarios/validate/")
    assert sent[1].url.params["job_id"] == "j1"


@pytest.mark.parametrize(
    "call,path,body",
    [
        (lambda s: s.archive(ENV, "refund-flow", reason="duplicate"), "scenarios/refund-flow/archive/", {"reason": "duplicate"}),
        (lambda s: s.restore(ENV, "refund-flow"), "scenarios/refund-flow/restore/", {}),
    ],
)
def test_archive_and_restore_post_to_the_scenario(call, path, body):
    sent: list[httpx.Request] = []
    client = _client(sent, {"scenario_key": "refund-flow", "lifecycle": {"state": "archived"}, "live": False})

    result = call(client.simulation.environments.scenarios)

    assert (sent[0].method, sent[0].url.path) == ("POST", H + path)
    assert json.loads(sent[0].content) == body
    assert result.scenario_key == "refund-flow"


def test_readiness_sends_the_pairing_and_every_key():
    sent: list[httpx.Request] = []
    report = {
        "answer": {"kind": "ready", "worst": "supported"},
        "areas": [],
        "rows": [],
        "workers": [],
        "blockers": 0,
        "catalog_version": "c1",
        "rules_version": "r1",
        "computed_at": "2026-11-26T00:00:00Z",
    }
    client = _client(sent, report, strict_responses=True)

    report = client.simulation.environments.readiness.get(ENV, suite_version_id="s1", keys=["a", "b"], trials=3)

    assert (sent[0].method, sent[0].url.path) == ("GET", H + "capabilities/")
    assert sent[0].url.params.get_list("keys") == ["a", "b"]
    assert sent[0].url.params["suite_version_id"] == "s1"
    assert sent[0].url.params["trials"] == "3"
    assert report.answer.kind == "ready"


def test_recheck_reads_its_202_receipt_and_is_not_retried():
    sent: list[httpx.Request] = []
    client = _client(sent, {"validation": {"state": "pending"}}, status=202)

    receipt = client.simulation.environments.readiness.recheck(ENV)

    assert [(r.method, r.url.path) for r in sent] == [("POST", H + "capabilities/recheck/")]
    assert receipt.validation is not None


def test_history_revisions_and_source_changes_are_reads():
    sent: list[httpx.Request] = []
    client = _client(sent, {})

    client.simulation.environments.readiness.history(ENV, cursor=2)
    client.simulation.environments.scenarios.revisions(ENV, "refund-flow")
    client.simulation.environments.scenarios.running_validation(ENV)
    client.simulation.environments.versions.source_changes(ENV, "v9")

    assert [(r.method, r.url.path) for r in sent] == [
        ("GET", H + "capabilities/history/"),
        ("GET", H + "scenarios/refund-flow/revisions/"),
        ("GET", H + "scenarios/validate/running/"),
        ("GET", H + "versions/environment/v9/source-changes/"),
    ]
    assert sent[0].url.params["cursor"] == "2"


def test_readiness_for_many_scenarios_cases_and_records():
    sent: list[httpx.Request] = []
    client = _client(sent, {})
    keys = [f"case-{n}" for n in range(250)]

    client.simulation.environments.readiness.get_for_scenarios(ENV, scenario_ids=keys, trials=2)
    client.simulation.environments.readiness.cases(ENV, bucket="blocked", cursor=10)
    client.simulation.environments.scenarios.records(ENV, "refund-flow", table="orders")

    assert [(r.method, r.url.path) for r in sent] == [
        ("POST", H + "capabilities/"),
        ("GET", H + "capabilities/cases/"),
        ("GET", H + "scenarios/refund-flow/records/"),
    ]
    assert json.loads(sent[0].content) == {"scenario_ids": keys, "trials": 2}
    assert (sent[1].url.params["bucket"], sent[1].url.params["cursor"]) == ("blocked", "10")
    assert sent[2].url.params["table"] == "orders"


def test_save_the_validated_candidates_and_plan_a_selection():
    sent: list[httpx.Request] = []
    client = _client(sent, {})

    client.simulation.environments.drafts.save(
        ENV, idempotency_key="save-1", candidates={"environment_version_id": "e2", "suite_version_id": "s2"}, expected_review_digest="d1", name="after validation"
    )
    client.simulation.environments.run_plan(ENV, scenario_keys="refund-flow,book-ride")

    assert (sent[0].method, sent[0].url.path) == ("POST", H + "drafts/save/")
    assert json.loads(sent[0].content) == {
        "idempotency_key": "save-1", "candidates": {"environment_version_id": "e2", "suite_version_id": "s2"}, "expected_review_digest": "d1", "name": "after validation"
    }
    assert (sent[1].method, sent[1].url.path) == ("GET", H + "run-plan/")
    assert sent[1].url.params.get_list("scenario_keys") == ["refund-flow,book-ride"]


def test_an_actor_change_is_reviewed_validated_then_its_candidates_saved():
    """Where a plain save is refused (validation_required), the draft goes review, validate, save candidates."""
    sent: list[httpx.Request] = []
    review = {"drafts": {}, "changes": [], "counts": {}, "review_digest": "d1", "can_save": True}
    client = _client(sent, review)
    drafts = client.simulation.environments.drafts

    seen = drafts.review(ENV)
    drafts.validate(ENV, expected_revisions={"environment": 3}, expected_review_digest=seen.review_digest)

    assert seen.review_digest == "d1"
    assert (sent[0].method, sent[0].url.path) == ("GET", H + "drafts/review/")
    assert (sent[1].method, sent[1].url.path) == ("POST", H + "drafts/validate/")
    assert json.loads(sent[1].content) == {"expected_revisions": {"environment": 3}, "expected_review_digest": "d1"}


def test_validation_and_candidates_are_read_from_the_drafts_list():
    sent: list[httpx.Request] = []
    listed = {
        "environment": None, "suite": None, "set_aside": [], "validation_required": True,
        "validation": {"state": "ready", "job_id": None},
        "candidates": {"environment_version_id": "e2", "suite_version_id": "s2"},
    }
    client = _client(sent, listed)

    drafts = client.simulation.environments.drafts.list(ENV)

    assert drafts.validation_required is True
    assert drafts.validation.state == "ready"
    assert (drafts.candidates.environment_version_id, drafts.candidates.suite_version_id) == ("e2", "s2")
