"""Offline regressions for cloud evaluation results and request configuration."""
from concurrent.futures import TimeoutError
from unittest.mock import Mock

import pytest
from requests import ConnectionError, HTTPError

from fi.evals import evaluate
from fi.evals.core import cloud_registry
from fi.evals.core.engines import TuringEngine
from fi.evals.evaluator import Evaluator
from fi.evals.types import BatchRunResult, EvalResult
from tests.core import _egress


@pytest.fixture(autouse=True)
def no_egress(monkeypatch, tmp_path):
    _egress.install(monkeypatch, tmp_path)
    yield
    _egress.assert_no_attempts()


@pytest.fixture
def evaluator(monkeypatch):
    # Keep the real public entrypoint, engine, and legacy evaluate method. Only
    # registry lookup and the request boundary are replaced with offline fakes.
    client = object.__new__(Evaluator)
    client._base_url = "http://127.0.0.1:9"
    client._fi_api_key = "test-key"
    client._fi_secret_key = "test-secret"
    client._default_timeout = 13
    client._max_workers = 1
    client.request = Mock(return_value=BatchRunResult(eval_results=[
        EvalResult(name="tone", output="Passed", reason="Evaluation completed"),
    ]))
    monkeypatch.setattr(TuringEngine, "_get_evaluator", lambda self: client)
    monkeypatch.setattr(
        cloud_registry, "map_inputs_to_backend",
        lambda name, inputs, **kwargs: inputs,
    )
    return client


def cloud_evaluate(name="tone", **kwargs):
    return evaluate(
        name, engine="turing", model="turing_flash", output="hello",
        fi_api_key="test-key", fi_secret_key="test-secret",
        fi_base_url="http://127.0.0.1:9", **kwargs,
    )


@pytest.mark.parametrize("error,expected_error", [
    (HTTPError("429 Too Many Requests"), "429 Too Many Requests"),
    (ConnectionError("Connection interrupted"), "Connection interrupted"),
    (ValueError("Invalid response body"), "Invalid response body"),
    (TimeoutError("Request timed out"), "Evaluation timed out after 13s"),
])
@pytest.mark.parametrize("batched", [False, True], ids=["single", "batch"])
def test_cloud_request_failure_has_failed_status(evaluator, error, expected_error, batched):
    evaluator.request.side_effect = error

    result = cloud_evaluate(["tone"] if batched else "tone")
    evaluator.request.assert_called_once()
    if batched:
        assert result.success_rate == 0.0
        result = result.results[0]
    assert result.status == "failed"
    assert result.error == expected_error
    assert result.reason == expected_error
    assert result.score is None
    assert result.passed is None
    assert result.latency_ms >= 0


@pytest.mark.parametrize("output,score", [("Passed", 1.0), ("Failed", 0.0), (0, 0.0), (False, 0.0)])
def test_cloud_completed_negative_score_is_not_a_request_failure(evaluator, output, score):
    evaluator.request.return_value = BatchRunResult(eval_results=[
        EvalResult(name="tone", output=output, reason="Evaluation completed", eval_id="eval-1"),
    ])

    batch = cloud_evaluate(["tone"])

    assert batch.success_rate == 1.0
    result = batch.results[0]
    assert result.status == "completed"
    assert result.error is None
    assert result.score == score
    assert result.reason == "Evaluation completed"
    assert result.metadata["eval_id"] == "eval-1"


def test_cloud_mixed_batch_counts_only_completed_requests(evaluator):
    evaluator.request.side_effect = [
        HTTPError("503 Service Unavailable"),
        BatchRunResult(eval_results=[EvalResult(name="toxicity", output="Failed")]),
    ]

    batch = cloud_evaluate(["tone", "toxicity"])

    assert evaluator.request.call_count == 2
    assert batch.success_rate == 0.5
    assert [result.status for result in batch] == ["failed", "completed"]
    assert batch.results[1].score == 0.0


@pytest.mark.parametrize("config", [
    {"run_config": {"max_steps": 1}},
    {"knowledge_base_id": "kb-test", "choice_scores": {"yes": 1, "no": 0}},
])
@pytest.mark.parametrize("name", ["tone", ["tone", "toxicity"]], ids=["single", "batch"])
def test_cloud_config_reaches_each_request(evaluator, config, name):
    from copy import deepcopy

    original = deepcopy(config)

    result = cloud_evaluate(name, config=config)

    assert result is not None
    assert config == original
    assert evaluator.request.call_count == (len(name) if isinstance(name, list) else 1)
    for call in evaluator.request.call_args_list:
        payload = call.kwargs["config"].json
        assert payload.get("config") == {"params": original}
        assert payload["inputs"] == {"output": "hello"}
        assert payload["model"] == "turing_flash"


@pytest.mark.parametrize("config", [None, {}])
def test_cloud_config_defaults_keep_existing_payload(evaluator, config):
    result = cloud_evaluate(config=config)

    assert result.status == "completed"
    evaluator.request.assert_called_once()
    assert "config" not in evaluator.request.call_args.kwargs["config"].json


def async_response(execution_ids):
    response = Mock()
    response.json.return_value = {
        "status": True,
        "result": [{"evaluations": [
            {"name": "tone", "output_type": "Pass/Fail", "eval_id": execution_id}
            for execution_id in execution_ids
        ]}],
    }
    return response


def test_async_submit_rejects_batch_before_scheduling(evaluator):
    # A single Execution cannot track this response's two independent jobs.
    # Reject batched inputs before scheduling until a batch API is supported.
    evaluator.request.return_value = async_response(["exec-1", "exec-2"])

    with pytest.raises(ValueError, match="batch|single|list"):
        evaluator.submit(
            "tone", {"output": ["hello", "goodbye"]}, model_name="turing_flash",
        )

    evaluator.request.assert_not_called()


def test_async_submit_single_input_keeps_waitable_handle(evaluator):
    completed = Mock()
    completed.json.return_value = {
        "status": True,
        "result": {
            "eval_status": "completed",
            "result": {"name": "tone", "output": "Passed", "eval_id": "exec-1"},
        },
    }
    evaluator.request.side_effect = [async_response(["exec-1"]), completed]

    handle = evaluator.submit("tone", {"output": "hello"}, model_name="turing_flash")

    assert handle.id == "exec-1"
    assert handle.status == "pending"
    assert handle.wait(poll_interval=0, timeout=1) is handle
    assert handle.status == "completed"
    assert handle.result.eval_id == "exec-1"
    assert evaluator.request.call_count == 2
    submission, refresh = evaluator.request.call_args_list
    assert submission.kwargs["config"].json["is_async"] is True
    assert refresh.kwargs["config"].params == {"eval_id": "exec-1"}
