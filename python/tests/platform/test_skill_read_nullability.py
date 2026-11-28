"""Exercise the real strict decode path: null is a value, not an absent key."""

import copy

import httpx
import pytest
from fi.platform import Client, ResponseValidationError, models

UID = "00000000-0000-4000-8000-000000000001"
NOW = "2026-01-01T00:00:00Z"
PERMISSIONS = dict.fromkeys(("can_publish", "can_promote", "can_manage_protection", "can_quarantine", "can_issue_credentials"), False)
STATE = {"latest_version": None, "labels": [], "release_revision": 1, "security_revision": 1, "protected_label_names": []}
DETAIL = {
    "own_draft": None, "latest": None,
    "release_state": {**STATE, "permissions": PERMISSIONS},
    "context": {**STATE, "id": UID, "kind": "agent_context", "name": "example", "description": "fixture", "tags": [],
                "metadata_revision": 1, "has_draft": False, "updated_at": NOW, "updated_by": None},
}
LOADS = {"fetch": None, "load": None}


def read(data, op, *, strict=True):
    def reply(_request):
        return httpx.Response(200, json={"status": True, "result": data})

    with httpx.Client(transport=httpx.MockTransport(reply)) as http:
        with Client(base_url="http://fixture.test", api_key="test", secret_key="test", http_client=http,
                    max_retries=0, strict_responses=strict) as client:
            if op == "detail":
                return client.contexts.get(UID)
            return client.skills.latest_load(resource_id=UID, kind="skill", since=NOW)


@pytest.mark.parametrize("op,valid,fields", [("detail", DETAIL, ("own_draft", "latest")), ("loads", LOADS, ("load", "fetch"))])
def test_required_key_is_independent_of_nullable_value(op, valid, fields):
    result = read(valid, op)
    for field in fields:
        assert field in result.__required__ and getattr(result, field) is None
        rest = {k: v for k, v in valid.items() if k != field}
        with pytest.raises(ResponseValidationError):
            read(rest, op)
        for wrong in ([], {}, "not an object", False):
            with pytest.raises(ResponseValidationError):
                read({**valid, field: wrong}, op)
        assert getattr(read(rest, op, strict=False), field) is None
    with pytest.raises(ResponseValidationError):
        read(None, op)


def test_populated_references_are_typed_and_nested_keys_are_checked():
    draft = {"base_version": None, "revision": 1}
    fetch = {"sdk_version": None, "tracing_mode": None, "can_record": False, "client": ""}
    assert isinstance(read({**DETAIL, "own_draft": draft}, "detail").own_draft, models.SkillsContextOwnDraft)
    assert isinstance(read({**LOADS, "fetch": fetch}, "loads").fetch, models.LatestFetch)
    with pytest.raises(ResponseValidationError):
        read({**DETAIL, "own_draft": {"revision": 1}}, "detail")
    with pytest.raises(ResponseValidationError):
        read({**LOADS, "fetch": {**fetch, "can_record": "false"}}, "loads")
    with pytest.raises(ResponseValidationError):
        read({**DETAIL, "release_state": None}, "detail")
    invalid = copy.deepcopy(DETAIL)
    del invalid["context"]["updated_by"]
    with pytest.raises(ResponseValidationError):
        read(invalid, "detail")
