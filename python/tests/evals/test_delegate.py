"""``client.evals.evaluate(...)`` is ``Evaluator(...).evaluate(...)`` with the client's keys and base URL;
and two evaluators with different keys never send each other's."""

from __future__ import annotations

import pytest

from fi import FutureAGIClient
from fi.evals import Evaluator
from fi.evals.types import BatchRunResult
from tests.evals import _mock_http


def _client(**kwargs) -> FutureAGIClient:
    return FutureAGIClient(api_key="key-B", secret_key="secret-B", base_url="http://127.0.0.1:9", **kwargs)


def test_the_delegate_sends_the_client_keys_and_returns_the_evaluator_result(backend) -> None:
    result = _client().evals.evaluate(eval_templates="toxicity", inputs={"output": "hi"}, model_name="turing_flash")
    assert isinstance(result, BatchRunResult)
    assert result.eval_results[0].output == "Passed" and result.eval_results[0].model == "turing_flash"
    assert {(c["x_api_key"], c["x_secret_key"], c["host"]) for c in backend.calls} == {("key-B", "secret-B", "127.0.0.1:9")}


def test_the_delegate_sends_what_evaluator_sends(backend) -> None:
    _client().evals.evaluate("groundedness", {"output": "Paris.", "context": "Paris is in France.", "input": "?"})
    via_client = [{k: v for k, v in c.items() if k not in ("x_api_key", "x_secret_key")} for c in backend.calls]
    backend.calls.clear()
    _mock_http.reset_caches()
    Evaluator().evaluate("groundedness", {"output": "Paris.", "context": "Paris is in France.", "input": "?"})
    direct = [{k: v for k, v in c.items() if k not in ("x_api_key", "x_secret_key")} for c in backend.calls]
    assert via_client == direct and len(direct) == 2


def test_one_evaluator_is_kept_per_client(backend) -> None:
    client = _client()
    client.evals.evaluate("toxicity", {"output": "a"})
    first = client.evals._delegate.evaluator()
    client.evals.evaluate("toxicity", {"output": "b"})
    assert client.evals._delegate.evaluator() is first


def test_with_options_copy_has_its_own_delegate_with_the_same_keys(backend) -> None:
    clone = _client().with_options(timeout=5)
    clone.evals.evaluate("toxicity", {"output": "a"})
    assert {c["x_api_key"] for c in backend.calls} == {"key-B"}


def test_no_keys_raise_before_any_request(backend, monkeypatch) -> None:
    from fi._credentials import MissingAuthError

    monkeypatch.delenv("FI_API_KEY")
    monkeypatch.delenv("FI_SECRET_KEY")
    with pytest.raises(MissingAuthError):
        FutureAGIClient(base_url="http://127.0.0.1:9").evals.evaluate("toxicity", {"output": "a"})
    assert backend.calls == []


def test_two_evaluators_with_different_keys_each_send_their_own(backend) -> None:
    """The keys are per instance. (In ai-evaluation 1.1.0 they were class attributes, so the
    registry lookup of the first evaluator went out with the keys of the last one built.)"""
    first = Evaluator(fi_api_key="key-1", fi_secret_key="secret-1", fi_base_url="http://127.0.0.1:9")
    Evaluator(fi_api_key="key-2", fi_secret_key="secret-2", fi_base_url="http://localhost:9")
    first.evaluate("toxicity", {"output": "x"})
    assert {(c["x_api_key"], c["x_secret_key"], c["host"]) for c in backend.calls} == {("key-1", "secret-1", "127.0.0.1:9")}
    assert len(backend.calls) == 2


def test_two_platform_clients_do_not_share_keys(backend) -> None:
    a = FutureAGIClient(api_key="key-1", secret_key="secret-1", base_url="http://127.0.0.1:9")
    b = FutureAGIClient(api_key="key-2", secret_key="secret-2", base_url="http://localhost:9")
    a.evals.evaluate("toxicity", {"output": "x"})
    b.evals.evaluate("toxicity", {"output": "x"})
    a.evals.evaluate("tone", {"output": "x"})
    by_host = {}
    for call in backend.calls:
        by_host.setdefault(call["host"], set()).add((call["x_api_key"], call["x_secret_key"]))
    assert by_host == {"127.0.0.1:9": {("key-1", "secret-1")}, "localhost:9": {("key-2", "secret-2")}}
