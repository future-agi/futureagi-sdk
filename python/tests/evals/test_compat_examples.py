"""The published examples send the same requests and return the same results as on ai-evaluation 1.1.0.

Each example in ``_examples.py`` runs against the fake eval API in ``_mock_http.py``. The golden file
holds what ai-evaluation 1.1.0 sent and returned for the same example under the same fake; here the
port must match it exactly, except for the few examples listed in ``INTENDED_DIFFERENCES``, whose
difference is checked precisely below and listed for the docs.
"""

from __future__ import annotations

import pytest

from tests.evals import _examples, _mock_http
from tests.evals._golden import golden


def _run(name: str, monkeypatch: pytest.MonkeyPatch) -> dict:
    env, overrides = _examples.SPECIAL.get(name, ({}, {}))
    for key, value in env.items():
        if value is None:
            monkeypatch.delenv(key, raising=False)
        else:
            monkeypatch.setenv(key, value)
    _mock_http.reset_caches()
    return _mock_http.run_example(_examples.EXAMPLES[name], _mock_http.FakeBackend(overrides))


def test_the_golden_file_covers_every_example() -> None:
    assert sorted(golden()["examples"]) == sorted(_examples.names())


@pytest.mark.parametrize("name", [n for n in _examples.names() if n not in _examples.INTENDED_DIFFERENCES])
def test_example_matches_ai_evaluation_1_1_0(name: str, monkeypatch: pytest.MonkeyPatch) -> None:
    got = _run(name, monkeypatch)
    want = golden()["examples"][name]
    assert got["requests"] == want["requests"], "the requests differ from 1.1.0"
    assert {k: v for k, v in got.items() if k != "requests"} == {k: v for k, v in want.items() if k != "requests"}


def _without_reasons(result: dict) -> dict:
    return dict(result, eval_results=[dict(r, reason=None) for r in result["eval_results"]])


def test_an_http_error_status_is_sent_once_not_three_times(monkeypatch: pytest.MonkeyPatch) -> None:
    """ai-evaluation re-sent a request whose response was an HTTP error (its retry loop also caught
    the error the response handler raised): three POSTs a second apart. Here only transport
    failures are retried, so the request goes once; the result is the same apart from its reason."""
    name = "error_server_rejects_keys"
    got, want = _run(name, monkeypatch), golden()["examples"][name]
    assert len(want["requests"]) == 3 and all(r == want["requests"][0] for r in want["requests"])
    assert got["requests"] == want["requests"][:1]
    assert _without_reasons(got["result"]) == _without_reasons(want["result"])


def test_a_403_reason_leads_with_the_server_sentence_then_the_key_hint(monkeypatch: pytest.MonkeyPatch) -> None:
    """ai-evaluation answered every 403 with one fixed sentence about the keys, whatever the server
    said. Here the reason is the server's sentence and the status, then the same hint about the keys."""
    name = "error_server_rejects_keys"
    got, want = _run(name, monkeypatch), golden()["examples"][name]
    assert [r["reason"] for r in want["result"]["eval_results"]] == [
        "Invalid FI Client Authentication, please check your API key and secret key."]
    assert [r["reason"] for r in got["result"]["eval_results"]] == [
        "Authentication credentials were not provided. (HTTP 403) Check your API key and secret key."]


def test_missing_keys_raise_the_same_error_class(monkeypatch: pytest.MonkeyPatch) -> None:
    """Both raise ``MissingAuthError`` before any request. The message here also names
    ``futureagi-py login``, the third way this package reads keys."""
    name = "error_missing_keys"
    got, want = _run(name, monkeypatch), golden()["examples"][name]
    assert want["raised"] == got["raised"] == "MissingAuthError"
    assert got["requests"] == want["requests"] == []
    assert "FI_API_KEY" in got["message"] and "FI_SECRET_KEY" in got["message"]
