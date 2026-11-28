"""Recorded judge metadata can be public without changing the replay contract."""
from copy import deepcopy
from hashlib import sha256

from tests.experiments.unit.fixtures.public_metadata import public_fixture


def test_projection_keeps_replay_data_and_does_not_mutate_its_input():
    original = {
        "provenance": {
            "e2e_sha": "private-source", "sdk_sha": "private-source",
            "suite_run_id": "private-run", "row": "private-case",
            "status": "GREEN", "criteria": "Is it correct?", "failed_checks": [],
        },
        "records": [{"response": {"system_fingerprint": "provider-example", "choices": [{"text": "yes"}]},
                     "system": "Judge the answer", "user": "answer", "status": 200, "must_pass": True}],
    }
    snapshot = deepcopy(original)
    projected = public_fixture(original)
    assert original == snapshot
    assert projected["provenance"] == {
        "record": "judge-paraphrase-and-criteria-regressions",
        "status": "GREEN", "criteria": "Is it correct?", "failed_checks": [],
    }
    expected = deepcopy(original["records"])
    expected[0]["response"]["system_fingerprint"] = "sha256:" + sha256(b"provider-example").hexdigest()
    assert projected["records"] == expected
    assert public_fixture(projected) == projected


def test_distinct_provider_fingerprints_remain_distinguishable():
    result = public_fixture({"records": [{"system_fingerprint": value} for value in ("first", "second", "first")]})
    first, second, repeated = result["records"]
    assert first == repeated and first != second
