"""Creating several contexts keeps each draft, lock, fingerprint and exception separate and reviewed."""

import json
from uuid import uuid4

import pytest
from fi.context import authoring

SKILLS = [{"id": f"s{n}", "name": f"leaf-{n}", "latest_version": 1 if n < 3 else None} for n in range(4)]
NAMES = ["parent-0", "parent-1"]


class Fake:
    def __init__(self):
        self.calls = []
        self.ids = {name: str(uuid4()) for name in NAMES}

    def request(self, method, path, body=None, query=None, options=None):
        self.calls.append((method, path, body, options))
        if path == "/model-hub/skills/":
            return {"page": query["page"], "count": 4, "total_pages": 1, "results": SKILLS}
        if path == "/model-hub/skills/contexts/":
            return {"context_id": self.ids[body["name"]], "revision": 1}
        context = next(name for name, value in self.ids.items() if value in path)
        if path.endswith("/dependencies/preview/"):
            return {"fingerprint": "fp-" + context, "candidate_digest": "sha256:" + context[-1] * 64,
                    "checks": {"summary": {"errors": 0, "warnings": 0}},
                    "changes": [{"mount": f"skills/{link['skill_id']}/", "after": {"version": link["selector"].get("version", 1), "requested": link["selector"]}} for link in body["links"]]}
        if path.endswith("/dependencies/apply/"):
            return {"files": [], "revision": 2, "digest": "sha256:" + context[-1] * 64}
        raise AssertionError(path)


def plan(fake, **change):
    arguments = dict(description="shared", root="# root", pins={"parent-1": {"leaf-0": 7}})
    return authoring.plan_create(fake, NAMES, **{**arguments, **change})


def test_each_context_links_every_published_skill_with_its_own_exception():
    fake = Fake()
    document = plan(fake)
    first, second = document["contexts"]
    assert [link["skill_id"] for link in first["links"]] == ["s0", "s1", "s2"]
    assert all(link["selector"] == {"label": "production"} for link in first["links"])
    assert second["links"][0] == {"skill_id": "s0", "selector": {"version": 7}}
    assert second["exceptions"] == [{"skill": "leaf-0", "pin": 7}] and first["exceptions"] == []
    assert first["fingerprint"] != second["fingerprint"]
    created = [body for method, path, body, _ in fake.calls if path == "/model-hub/skills/contexts/"]
    assert [body["files"] for body in created] == [[{"path": "AGENTS.md", "content": "# root"}]] * 2
    assert not any(path.endswith(("/dependencies/apply/", "/draft/publish/")) for _, path, _, _ in fake.calls)


def test_apply_uses_each_contexts_own_fingerprint_and_replays_with_stable_keys():
    fake = Fake()
    document = plan(fake)
    kwargs = dict(reviewed_plan=document["plan_digest"], accept_resolved_versions=True)
    assert [row["revision"] for row in authoring.apply_create(fake, document, **kwargs)["applied"]] == [2, 2]
    authoring.apply_create(fake, document, **kwargs)
    applies = [(body, options) for _, path, body, options in fake.calls if path.endswith("/dependencies/apply/")]
    assert [body["expected_fingerprint"] for body, _ in applies[:2]] == [row["fingerprint"] for row in document["contexts"]]
    assert applies[0][1].idempotency_key == applies[2][1].idempotency_key != applies[1][1].idempotency_key


@pytest.mark.parametrize("change", [{"reviewed_plan": "sha256:" + "0" * 64}, {"accept_resolved_versions": False}])
def test_apply_needs_the_exact_digest_and_acceptance(change):
    fake = Fake()
    document = plan(fake)
    before = len(fake.calls)
    with pytest.raises(ValueError):
        authoring.apply_create(fake, document, **{**dict(reviewed_plan=document["plan_digest"], accept_resolved_versions=True), **change})
    assert len(fake.calls) == before


def test_edited_plan_and_bad_inputs_are_refused():
    fake = Fake()
    document = plan(fake)
    document["contexts"][0]["links"] = []
    before = len(fake.calls)
    with pytest.raises(ValueError):
        authoring.apply_create(fake, document, reviewed_plan=document["plan_digest"], accept_resolved_versions=True)
    assert len(fake.calls) == before
    with pytest.raises(ValueError):
        plan(Fake(), pins={"parent-9": {"leaf-0": 7}})
    with pytest.raises(ValueError):
        plan(Fake(), pins={"parent-1": {"leaf-9": 7}})
    with pytest.raises(ValueError):
        authoring.plan_create(Fake(), NAMES, description=" ", root="x")


def test_cli_parses_pins_and_hides_nothing_the_operator_must_review(tmp_path, monkeypatch, capsys):
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
    monkeypatch.setattr(authoring, "Client", Transport)
    out = tmp_path / "plan.json"
    assert authoring.main(["plan-create", *NAMES, "--description", "shared", "--root", "# root", "--pin", "parent-1:leaf-0=7", "--out", str(out)]) == 0
    shown = json.loads(capsys.readouterr().out)
    assert shown["plan_digest"] == json.loads(out.read_text())["plan_digest"]
    assert shown["contexts"][1]["exceptions"] == [{"skill": "leaf-0", "pin": 7}]
    assert (out.stat().st_mode & 0o777) == 0o600
    assert authoring.main(["apply-create", "--plan", str(out), "--reviewed-plan", shown["plan_digest"]]) == 2
    with pytest.raises(ValueError):
        authoring._parse_pins(["bad"])
