"""Legacy evaluator logs contain operational context, never evaluated content."""
import logging
import sys
from concurrent.futures import TimeoutError
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from fi.evals.core import cloud_registry
from fi.evals.evaluator import Evaluator
from fi.evals.otel import enrichment as span_enrichment
from fi.evals.types import BatchRunResult, EvalResult


INPUT_SENTINEL = "synthetic-private-prompt-4d36"
OUTPUT_SENTINEL = "synthetic-private-output-3f91"
ERROR_SENTINEL = "synthetic-private-error-6b28"
ERROR_MESSAGE = f"{ERROR_SENTINEL}: {INPUT_SENTINEL} / {OUTPUT_SENTINEL}"


@pytest.fixture
def inputs():
    return {
        "input": {"prompt": INPUT_SENTINEL},
        "output": [{"answer": OUTPUT_SENTINEL}],
    }


@pytest.fixture
def evaluator(monkeypatch, caplog):
    # Exercise the real evaluator methods without creating an HTTP session.
    client = object.__new__(Evaluator)
    client._base_url = "http://127.0.0.1:9"
    client._fi_api_key = "test-key"
    client._fi_secret_key = "test-secret"
    client._default_timeout = 13
    client._max_workers = 1
    client.request = Mock(return_value=BatchRunResult(eval_results=[
        EvalResult(name="toxicity", output=OUTPUT_SENTINEL, reason=INPUT_SENTINEL),
    ]))
    # All optional integrations are synthetic, including their import paths.
    integrations = SimpleNamespace(
        mapping=Mock(side_effect=lambda name, inputs, **kwargs: inputs),
        enrichment=SimpleNamespace(
            is_auto_enrichment_enabled=Mock(return_value=False),
            enrich_span_with_batch_result=Mock(return_value=0),
        ),
    )
    monkeypatch.setitem(sys.modules, "fi.evals.core.cloud_registry", SimpleNamespace(
        map_inputs_to_backend=integrations.mapping,
    ))
    monkeypatch.setitem(sys.modules, "fi.evals.otel.enrichment", integrations.enrichment)
    monkeypatch.setitem(sys.modules, "fi.evals.otel_utils", SimpleNamespace(
        _get_current_otel_span=Mock(return_value=None),
    ))
    caplog.set_level(logging.DEBUG)
    return client, integrations


def assert_private_logs(caplog, expected, evaluation=True):
    assert expected in caplog.text
    if evaluation:
        assert "toxicity" in caplog.text
    for sentinel in (INPUT_SENTINEL, OUTPUT_SENTINEL, ERROR_SENTINEL):
        assert sentinel not in caplog.text
        assert all(sentinel not in str(record.args) for record in caplog.records)
    assert all(record.exc_info is None for record in caplog.records)
    assert all(record.exc_text is None for record in caplog.records)


@pytest.mark.parametrize("timeout,effective_timeout", [(None, 13), (0, 13), (3, 3)])
@pytest.mark.parametrize("error_type", [TimeoutError, RuntimeError])
def test_request_failure_logs_no_inputs_or_exception_text(
    evaluator, inputs, caplog, timeout, effective_timeout, error_type,
):
    client, _ = evaluator
    # A completed request raises deterministically; this does not establish a
    # wall-clock deadline or cancellation contract for the thread executor.
    client.request.side_effect = error_type(ERROR_MESSAGE)

    result = client.evaluate("toxicity", inputs, timeout=timeout, skip_input_mapping=True)

    client.request.assert_called_once()
    config = client.request.call_args.kwargs["config"]
    assert config.timeout == effective_timeout
    assert INPUT_SENTINEL in config.json["inputs"]["input"]
    assert OUTPUT_SENTINEL in config.json["inputs"]["output"]
    assert len(result.eval_results) == 1
    failure = result.eval_results[0]
    assert failure.name == "toxicity"
    assert failure.output is None
    assert failure.runtime == 0
    if error_type is TimeoutError:
        assert failure.reason == f"Evaluation timed out after {effective_timeout}s"
        assert_private_logs(caplog, f"timed out after {effective_timeout}s")
    else:
        # Caller-visible reasons retain the original exception text.
        assert failure.reason == ERROR_MESSAGE
        assert_private_logs(caplog, "Evaluation toxicity failed")
    assert f"error type: {error_type.__name__}" in caplog.text
    assert "Failed to evaluate 1 inputs out of 2 total inputs" in caplog.text


def test_mapping_failure_logs_only_exception_type(evaluator, inputs, caplog):
    client, integrations = evaluator
    integrations.mapping.side_effect = ValueError(ERROR_MESSAGE)

    result = client.evaluate("toxicity", inputs)

    integrations.mapping.assert_called_once()
    client.request.assert_called_once()
    assert result.eval_results == client.request.return_value.eval_results
    config = client.request.call_args.kwargs["config"]
    assert INPUT_SENTINEL in config.json["inputs"]["input"]
    assert OUTPUT_SENTINEL in config.json["inputs"]["output"]
    assert_private_logs(caplog, "Dynamic input mapping skipped")
    assert "error type: ValueError" in caplog.text


def test_enrichment_failure_logs_no_result_or_exception_text(evaluator, inputs, caplog):
    client, integrations = evaluator
    integrations.enrichment.is_auto_enrichment_enabled.return_value = True
    enrich = integrations.enrichment.enrich_span_with_batch_result
    enrich.side_effect = ValueError(ERROR_MESSAGE)

    result = client.evaluate("toxicity", inputs, skip_input_mapping=True)

    enrich.assert_called_once_with(result)
    assert result.eval_results == client.request.return_value.eval_results
    assert result.eval_results[0].output == OUTPUT_SENTINEL
    assert result.eval_results[0].reason == INPUT_SENTINEL
    assert_private_logs(caplog, "Failed to enrich span for evaluation toxicity")
    assert "error type: ValueError" in caplog.text


def test_trace_import_error_omits_exception_traceback(evaluator, inputs, caplog, monkeypatch):
    client, _ = evaluator
    get_current_span = Mock(side_effect=ImportError(ERROR_MESSAGE))
    monkeypatch.setitem(sys.modules, "opentelemetry", SimpleNamespace(
        trace=SimpleNamespace(get_current_span=get_current_span),
    ))

    result = client.evaluate(
        "toxicity", inputs, trace_eval=True, custom_eval_name="privacy-test",
        skip_input_mapping=True,
    )

    assert result is None
    get_current_span.assert_called_once()
    client.request.assert_not_called()
    assert_private_logs(caplog, "Future AGI SDK not found")
    assert "error type: ImportError" in caplog.text


def configure(client, inputs):
    return client.evaluate(
        "toxicity", inputs, platform="test-platform", custom_eval_name="privacy-test",
        span_id="synthetic-span", trace_id="synthetic-trace",
    )


def test_configuration_warning_omits_response_body(evaluator, inputs, caplog):
    client, _ = evaluator
    body = {"error": ERROR_MESSAGE}
    response = SimpleNamespace(status_code=422, text=ERROR_MESSAGE, json=Mock(return_value=body))
    client.request.return_value = response

    result = configure(client, inputs)

    assert result is body
    response.json.assert_called_once()
    client.request.assert_called_once()
    config = client.request.call_args.kwargs["config"]
    assert config.json["eval_config"]["inputs"] == inputs
    assert config.timeout == client._default_timeout
    assert_private_logs(caplog, "Received non-200 status code from backend: 422")


def test_configuration_import_error_omits_exception_traceback(evaluator, inputs, caplog):
    client, _ = evaluator
    client.request.side_effect = ImportError(ERROR_MESSAGE)

    assert configure(client, inputs) is None

    client.request.assert_called_once()
    assert_private_logs(caplog, "Future AGI SDK not found")
    assert "error type: ImportError" in caplog.text


def test_configuration_other_errors_still_reach_caller(evaluator, inputs, caplog):
    client, _ = evaluator
    error = RuntimeError(ERROR_MESSAGE)
    client.request.side_effect = error

    with pytest.raises(RuntimeError) as raised:
        configure(client, inputs)

    assert raised.value is error
    assert str(raised.value) == ERROR_MESSAGE
    client.request.assert_called_once()
    assert caplog.records == []


def test_registry_failure_inside_evaluate_omits_exception_text(
    evaluator, inputs, caplog, monkeypatch,
):
    client, _ = evaluator
    session = SimpleNamespace(registry_cache={}, get=Mock(side_effect=ValueError(ERROR_MESSAGE)))
    client._registry_session = session
    monkeypatch.setitem(sys.modules, "fi.evals.core.cloud_registry", cloud_registry)

    result = client.evaluate("toxicity", inputs)

    session.get.assert_called_once()
    assert result.eval_results == client.request.return_value.eval_results
    assert INPUT_SENTINEL in client.request.call_args.kwargs["config"].json["inputs"]["input"]
    assert_private_logs(caplog, "Failed to load cloud eval registry", evaluation=False)
    assert "error type: ValueError" in caplog.text


@pytest.fixture
def real_enrichment(evaluator, monkeypatch):
    client, _ = evaluator
    span = Mock()
    monkeypatch.setitem(sys.modules, "fi.evals.otel.enrichment", span_enrichment)
    monkeypatch.setattr(span_enrichment, "OTEL_AVAILABLE", True)
    monkeypatch.setattr(span_enrichment, "_auto_enrichment_enabled", True)
    monkeypatch.setattr(span_enrichment, "get_current_span", Mock(return_value=span))
    return client, span


@pytest.mark.parametrize("score", [OUTPUT_SENTINEL, 0.314159])
def test_real_auto_enrichment_never_logs_evaluation_output(real_enrichment, inputs, caplog, score):
    client, span = real_enrichment
    client.request.return_value = BatchRunResult(eval_results=[
        EvalResult(name="toxicity", output=score, reason=INPUT_SENTINEL),
    ])

    result = client.evaluate("toxicity", inputs, skip_input_mapping=True)

    assert result.eval_results == client.request.return_value.eval_results
    if isinstance(score, str):
        span.set_attribute.assert_not_called()
        assert_private_logs(caplog, "Cannot normalize score string to float")
    else:
        span.set_attribute.assert_any_call(span_enrichment.EvaluationAttributes.SCORE_VALUE, score)
        span.set_attribute.assert_any_call(span_enrichment.EvaluationAttributes.EXPLANATION, INPUT_SENTINEL)
        assert_private_logs(caplog, "Enriched span with evaluation toxicity")
        assert str(score) not in caplog.text


def test_real_auto_enrichment_failure_omits_exception_text(real_enrichment, inputs, caplog):
    client, span = real_enrichment
    client.request.return_value = BatchRunResult(eval_results=[
        EvalResult(name="toxicity", output=0.5, reason=INPUT_SENTINEL),
    ])
    span.set_attribute.side_effect = ValueError(ERROR_MESSAGE)

    result = client.evaluate("toxicity", inputs, skip_input_mapping=True)

    assert result.eval_results == client.request.return_value.eval_results
    assert_private_logs(caplog, "Failed to enrich span with evaluation toxicity")
    assert "error type: ValueError" in caplog.text


@pytest.mark.parametrize("operation", [
    "current_span", "eval_result", "batch_result", "create_span", "context_enter", "context_exit",
])
def test_enrichment_sibling_failures_omit_exception_text(operation, caplog, monkeypatch):
    caplog.set_level(logging.DEBUG)
    monkeypatch.setattr(span_enrichment, "OTEL_AVAILABLE", True)
    monkeypatch.setattr(span_enrichment, "_auto_enrichment_enabled", True)
    monkeypatch.setattr(span_enrichment, "trace", SimpleNamespace(
        get_current_span=Mock(side_effect=ValueError(ERROR_MESSAGE)),
        get_tracer=Mock(side_effect=ValueError(ERROR_MESSAGE)),
    ), raising=False)
    noop_context = object()
    monkeypatch.setitem(sys.modules, "fi.evals.otel.tracer", SimpleNamespace(
        _NoOpContextManager=lambda: noop_context,
    ))

    if operation == "current_span":
        assert span_enrichment.get_current_span() is None
        message = "Failed to get current span"
    elif operation == "eval_result":
        result = SimpleNamespace(name="toxicity", output=0.5, reason=INPUT_SENTINEL, runtime=ERROR_MESSAGE)
        assert span_enrichment.enrich_span_with_eval_result(result) is False
        message = "Failed to enrich span with EvalResult"
    elif operation == "batch_result":
        class BrokenResults:
            def __iter__(self):
                raise ValueError(ERROR_MESSAGE)

        assert span_enrichment.enrich_span_with_batch_result(
            SimpleNamespace(eval_results=BrokenResults()),
        ) == 0
        message = "Failed to enrich span with BatchRunResult"
    elif operation == "create_span":
        assert span_enrichment.create_evaluation_span("toxicity") is noop_context
        message = "Failed to create evaluation span"
    elif operation == "context_enter":
        context = span_enrichment.EvaluationSpanContext("toxicity")
        assert context.__enter__() is context
        assert context.__exit__(None, None, None) is False
        message = "Failed to create evaluation span"
    else:
        context = span_enrichment.EvaluationSpanContext("toxicity", create_child_span=False)
        context.__enter__()
        context._span = Mock()
        context._span.set_status.side_effect = ValueError(ERROR_MESSAGE)
        monkeypatch.setattr(span_enrichment, "Status", lambda code: code, raising=False)
        monkeypatch.setattr(span_enrichment, "StatusCode", SimpleNamespace(OK="ok"), raising=False)
        assert context.__exit__(None, None, None) is False
        message = "Error closing evaluation span"

    assert_private_logs(caplog, message, evaluation=False)
    assert "error type: ValueError" in caplog.text
