"""Set publication and release requests keep each context's own review, fingerprint and guard."""

import json
from uuid import uuid4

import pytest
from fi.context import release

A, B, REVIEWER = str(uuid4()), str(uuid4()), str(uuid4())
DIGEST = {A: "sha256:" + "a" * 64, B: "sha256:" + "b" * 64}


class Fake:
    def __init__(self):
        self.calls = []
        self.moved = False

    def request(self, method, path, body=None, query=None, options=None):
        self.calls.append((method, path, body, options))
        context = A if A in path else B
        if path.endswith("/draft/"):
            return {"revision": 4, "resolved_lock": {"links": [{"mount": "skills/p/", "version": 8, "version_id": "v8", "digest": "d8", "requested": {"label": "production"}}]}}
        if path.endswith("/release/review/"):
            fingerprint = "fp-" + context[:4] + ("-moved" if self.moved else "")
            file = {"path": "AGENTS.md", "status": "modified", "from_sha256": "x", "to_sha256": "y"}
            return {"review_fingerprint": fingerprint, "candidate": {"revision": 4, "digest": DIGEST[context]},
                    "changes": {"files": [file, {"path": "same", "status": "unchanged"}], "total_pages": 1},
                    "head_changes": {"files": [], "total_pages": 1}, "checks": {"summary": {"errors": 0, "warnings": 1}},
                    "head_review": {"draft_revision": 4, "candidate_digest": DIGEST[context], "base_version": 1,
                                    "expected_head_version": 1, "head_digest": "h", "review_fingerprint": fingerprint}}
        if path.endswith("/acknowledge-head/"):
            return {"revision": 5, "digest": DIGEST[context], "expected_head_version": 1, "review_fingerprint": "ack-" + context[:4], "base_version": 1}
        if path.endswith("/draft/publish/"):
            return {"version": {"version": 2, "digest": DIGEST[context]}}
        if "/versions/" in path:
            return {"manifest": {"version_id": "v-" + context[:4], "digest": DIGEST[context]}}
        if path.endswith("/release-requests/preview/"):
            context = body["resource_id"]
            return {"fingerprint": "rf-" + context[:4], "packet": {"candidate_version_id": body["candidate_version_id"], "candidate_digest": DIGEST[context],
                    "transition": {"label": body["label"], "expected_version": 1, "version": 2, "expected_release_revision": 3, "expected_security_revision": 1}}}
        if path.endswith("/release-requests/"):
            return {"id": "req-" + body["packet"]["candidate_version_id"], "status": "pending"}
        raise AssertionError(path)


def publish_args(plan, **change):
    return {**dict(reviewed_plan=plan["plan_digest"], reviewed_changes=True, acknowledge_warnings=True, note="n"), **change}


def test_publish_set_reviews_each_context_then_acknowledges_and_publishes_it_separately():
    fake = Fake()
    plan = release.plan_publish(fake, [A, B])
    assert [row["changed_from_origin"][0]["path"] for row in plan["contexts"]] == ["AGENTS.md", "AGENTS.md"]
    assert all(len(row["changed_from_origin"]) == 1 for row in plan["contexts"])
    assert plan["contexts"][0]["accepted_lock"] == [{"mount": "skills/p/", "version": 8, "version_id": "v8", "digest": "d8", "requested": {"label": "production"}}]
    result = release.publish_set(fake, plan, **publish_args(plan))
    assert [row["version"] for row in result["published"]] == [2, 2]
    writes = [(path.rsplit("/", 2)[-2], body) for method, path, body, _ in fake.calls if method == "POST" and not path.endswith("/release/review/")]
    assert [name for name, _ in writes] == ["acknowledge-head", "publish", "acknowledge-head", "publish"]
    assert writes[1][1]["review_fingerprint"] == "ack-" + A[:4] and writes[1][1]["revision"] == 5
    assert writes[1][1]["acknowledge_warnings"] is True
    keys = [options.idempotency_key for method, path, body, options in fake.calls if path.endswith("/draft/publish/")]
    assert len(set(keys)) == 2


@pytest.mark.parametrize("change", [
    {"reviewed_plan": "sha256:" + "0" * 64}, {"reviewed_changes": False}, {"acknowledge_warnings": False},
])
def test_publication_needs_the_exact_digest_review_and_warning_acknowledgment(change):
    fake = Fake()
    plan = release.plan_publish(fake, [A])
    before = len(fake.calls)
    with pytest.raises(ValueError):
        release.publish_set(fake, plan, **publish_args(plan, **change))
    assert len(fake.calls) == before


def test_moved_draft_or_edited_plan_publishes_nothing():
    fake = Fake()
    plan = release.plan_publish(fake, [A, B])
    fake.moved = True
    with pytest.raises(ValueError):
        release.publish_set(fake, plan, **publish_args(plan))
    assert not any(path.endswith(("/acknowledge-head/", "/draft/publish/")) for _, path, _, _ in fake.calls)
    plan["contexts"][0]["warnings"] = 0
    with pytest.raises(ValueError):
        release.publish_set(fake, plan, **publish_args(plan))


def test_release_requests_are_per_context_independent_and_never_move_a_label():
    fake = Fake()
    plan = release.plan_release(fake, [A, B], version=2)
    assert [(row["from_version"], row["to_version"], row["label"]) for row in plan["contexts"]] == [(1, 2, "production")] * 2
    result = release.request_set(fake, plan, reviewed_plan=plan["plan_digest"], reviewer=REVIEWER, confirm_request_only=True)
    assert [row["context_id"] for row in result["requests"]] == [A, B]
    sent = [(body, options) for method, path, body, options in fake.calls if method == "POST" and path.endswith("/release-requests/")]
    assert [body["recipient_ids"] for body, _ in sent] == [[REVIEWER], [REVIEWER]]
    assert [body["expected_fingerprint"] for body, _ in sent] == ["rf-" + A[:4], "rf-" + B[:4]]
    assert sent[0][1].idempotency_key != sent[1][1].idempotency_key
    assert not any("/labels/" in path for _, path, _, _ in fake.calls)


@pytest.mark.parametrize("change", [
    {"reviewed_plan": "sha256:" + "0" * 64}, {"confirm_request_only": False}, {"reviewer": "not-a-user"},
])
def test_release_request_needs_exact_digest_confirmation_and_a_valid_reviewer(change):
    fake = Fake()
    plan = release.plan_release(fake, [A], version=2)
    before = len(fake.calls)
    arguments = dict(reviewed_plan=plan["plan_digest"], reviewer=REVIEWER, confirm_request_only=True)
    with pytest.raises(ValueError):
        release.request_set(fake, plan, **{**arguments, **change})
    assert len(fake.calls) == before


def test_cli_prints_the_digest_it_wrote_and_hides_the_signed_packet(tmp_path, monkeypatch, capsys):
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
    monkeypatch.setattr(release, "Client", Transport)
    out = tmp_path / "plan.json"
    assert release.main(["plan-release", A, "--version", "2", "--out", str(out)]) == 0
    shown = json.loads(capsys.readouterr().out)
    assert shown["plan_digest"] == json.loads(out.read_text())["plan_digest"]
    assert "packet" not in shown["contexts"][0]
    assert (out.stat().st_mode & 0o777) == 0o600
    assert release.main(["request-set", "--plan", str(out), "--reviewed-plan", shown["plan_digest"], "--reviewer", REVIEWER]) == 2
