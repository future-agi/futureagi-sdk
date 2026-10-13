"""Lifecycle transport tests using actual backend response fixtures."""

import json
from pathlib import Path

import httpx
import pytest
from jsonschema import ValidationError

from fi import FutureAGIClient
from fi.futureagi_client import FutureAGIAPIError
from fi.generated.openapi_client.models.dataset_version_create import (
    DatasetVersionCreate,
)
from fi.generated.openapi_client.models.external_run_create_request import (
    ExternalRunCreateRequest,
)
from fi.generated.openapi_client.models.external_run_results_request import (
    ExternalRunResultsRequest,
)
from fi.generated.openapi_client.models.run_comparison_request import (
    RunComparisonRequest,
)
from fi.generated.openapi_client.models.release_gate_report import ReleaseGateReport

FIXTURES = Path(__file__).parents[2] / "tests/fixtures/dataset-experiments"
DATASET = "00000000-0000-4000-8000-000000000001"
VERSION = "00000000-0000-4000-8000-000000000002"
RUN = "00000000-0000-4000-8000-000000000003"
EXAMPLE = "00000000-0000-4000-8000-000000000004"


def fixture(name):
    payload = json.loads((FIXTURES / name).read_text())

    # Generated Python models expose datetimes and serialize UTC as +00:00.
    # Normalize only the API's datetime fields, never arbitrary input/output.
    def timestamps(value):
        if isinstance(value, list):
            return [timestamps(item) for item in value]
        if isinstance(value, dict):
            return {
                key: item.replace("Z", "+00:00")
                if key in {"created_at", "updated_at", "started_at", "completed_at"}
                and isinstance(item, str)
                and item.endswith("Z")
                else timestamps(item)
                for key, item in value.items()
            }
        return value

    return timestamps(payload)


def client_for(handler):
    client = FutureAGIClient(
        api_key="local-api", secret_key="local-secret", base_url="http://api.test"
    )
    client.generated_client.set_httpx_client(
        httpx.Client(
            base_url="http://api.test",
            headers={"X-Api-Key": "local-api", "X-Secret-Key": "local-secret"},
            transport=httpx.MockTransport(handler),
        )
    )
    return client


def plain(value):
    return value.to_dict() if hasattr(value, "to_dict") else value


@pytest.mark.parametrize("value", [False, 0, "text", ["text", None], {"nested": None}])
def test_snapshot_201_preserves_open_json_and_is_one_attempt(value):
    calls = []
    body = {
        "items": [
            {"input": value, "expected": None, "metadata": {"nested": [None, False, 0]}}
        ]
    }
    response = fixture("dataset-snapshot-created.json")

    def handler(request):
        calls.append(request)
        assert request.method == "POST"
        assert request.url.path == f"/model-hub/datasets/{DATASET}/versions/"
        assert request.headers["X-Api-Key"] == "local-api"
        assert request.headers["X-Secret-Key"] == "local-secret"
        assert json.loads(request.content) == body
        return httpx.Response(201, json=response)

    with client_for(handler) as client:
        assert (
            plain(
                client.datasets.versions.create(
                    DATASET, DatasetVersionCreate.from_dict(body)
                )
            )
            == response
        )
    assert len(calls) == 1


def test_version_reads_forward_pagination_and_preserve_scalar_null_items():
    requests = []
    responses = [
        fixture("dataset-version-list.json"),
        fixture("dataset-version-detail.json"),
    ]

    def handler(request):
        index = len(requests)
        requests.append(request)
        assert request.method == "GET"
        assert dict(request.url.params) == {"limit": "2", "offset": "3"}
        expected_path = f"/model-hub/datasets/{DATASET}/versions/" + (
            f"{VERSION}/" if index else ""
        )
        assert request.url.path == expected_path
        return httpx.Response(200, json=responses[index])

    with client_for(handler) as client:
        assert (
            plain(client.datasets.versions.list(DATASET, limit=2, offset=3))
            == responses[0]
        )
        assert (
            plain(client.datasets.versions.get(DATASET, VERSION, limit=2, offset=3))
            == responses[1]
        )
    assert len(requests) == 2


@pytest.mark.parametrize(
    "comparison_fixture",
    ["run-comparison-missing.json", "run-comparison-assessed.json"],
)
def test_external_run_result_and_comparison_use_generated_wire_contract(
    comparison_fixture,
):
    create = {
        "run_id": RUN,
        "dataset_version_id": VERSION,
        "expected_items": [{"example_id": EXAMPLE, "trial_number": 1}],
        "model_config": {"scalar": False, "array": [1, None]},
        "metadata": {},
    }
    upload = {
        "items": [
            {
                "example_id": EXAMPLE,
                "trial_number": 1,
                "receipt_key": "delivery-one",
                "status": "completed",
                "output": [False, 0, None],
                "error": None,
                "trace_id": None,
                "root_span_id": None,
                "score_refs": [],
            }
        ]
    }
    compare = {
        "baseline_run_id": RUN,
        "candidate_run_id": VERSION,
        "metric_id": EXAMPLE,
        "passing_score": None,
    }
    expected = [
        ("/model-hub/experiment-runs/", create, fixture("external-run-created.json")),
        (
            f"/model-hub/experiment-runs/{RUN}/results/",
            upload,
            fixture("external-run-results.json"),
        ),
        (
            "/model-hub/experiment-runs/compare/",
            compare,
            fixture(comparison_fixture),
        ),
    ]
    calls = []

    def handler(request):
        path, body, response = expected[len(calls)]
        calls.append(request)
        assert request.method == "POST" and request.url.path == path
        assert json.loads(request.content) == body
        return httpx.Response(200, json=response)

    with client_for(handler) as client:
        assert (
            plain(
                client.experiment_runs.create(
                    ExternalRunCreateRequest.from_dict(create)
                )
            )
            == expected[0][2]
        )
        assert (
            plain(
                client.experiment_runs.ingest_results(
                    RUN, ExternalRunResultsRequest.from_dict(upload)
                )
            )
            == expected[1][2]
        )
        assert (
            plain(
                client.experiment_runs.compare(RunComparisonRequest.from_dict(compare))
            )
            == expected[2][2]
        )
    assert len(calls) == 3


@pytest.mark.parametrize("name", ["allowance", "critical"])
def test_compare_returns_gate_report_without_making_ci_decision(name):
    response = fixture(f"run-comparison-gate-{name}.json")
    compare = {
        "baseline_run_id": response["result"]["baseline_run_id"],
        "candidate_run_id": response["result"]["candidate_run_id"],
        "metric_id": response["result"]["metric_id"],
        "passing_score": 1,
        "release_gate": response["result"]["release_gate"]["policy"],
    }
    calls = []

    def handler(request):
        calls.append(request)
        assert request.method == "POST"
        assert request.url.path == "/model-hub/experiment-runs/compare/"
        assert json.loads(request.content) == compare
        return httpx.Response(200, json=response)

    with client_for(handler) as client:
        parsed = client.experiment_runs.compare(RunComparisonRequest.from_dict(compare))
        assert parsed.to_dict() == response
        assert parsed.result.release_gate.verdict.value == (
            "pass" if name == "allowance" else "fail"
        )
    assert len(calls) == 1


@pytest.mark.parametrize(
    "policy",
    [
        None,
        [],
        {"max_regressions": True},
        {"max_regressions": 1.0},
        {"max_regressions": -1},
        {"max_regressions": None},
        {"max_regresions": 10},
        {"critical_cases": None},
        {"critical_cases": [{"example_id": EXAMPLE, "trial_number": 0}]},
        {"critical_cases": [{"example_id": EXAMPLE, "trial_number": 2147483648}]},
        {"critical_cases": [{"example_id": EXAMPLE, "trial_number": True}]},
        {"critical_cases": [{"example_id": EXAMPLE, "trial_number": 1, "typo": 1}]},
    ],
)
def test_invalid_gate_cannot_be_silently_weakened_before_transport(policy):
    calls = []
    with client_for(lambda request: calls.append(request)) as client:
        with pytest.raises((ValidationError, TypeError)):
            client.experiment_runs.compare(
                RunComparisonRequest.from_dict(
                    {
                        "baseline_run_id": RUN,
                        "candidate_run_id": VERSION,
                        "metric_id": EXAMPLE,
                        "release_gate": policy,
                    }
                )
            )
    assert calls == []


def test_gate_model_defaults_nulls_and_forward_compatible_report_fields():
    from fi.generated.openapi_client.models.release_gate_policy import ReleaseGatePolicy

    assert ReleaseGatePolicy.from_dict({}).to_dict() == {}
    assert ReleaseGatePolicy().to_dict() == {"max_regressions": 0}
    with pytest.raises(ValidationError):
        ReleaseGatePolicy(max_regressions=True).to_dict()
    payload = {
        "verdict": "fail",
        "expected_count": 0,
        "comparable_count": 0,
        "regression_count": 0,
        "policy": {},
        "passing_score": None,
        "higher_is_better": True,
        "blockers": [
            {
                "example_id": None,
                "trial_number": None,
                "reason": "empty_plan",
                "new_detail": 0,
            }
        ],
        "new_report_field": {"nested": [None, False]},
    }
    assert ReleaseGateReport.from_dict(payload).to_dict() == payload


@pytest.mark.parametrize("failure", ["timeout", "invalid-json", "conflict"])
def test_snapshot_never_retries_ambiguous_response_or_conflict(failure):
    calls = []

    def handler(request):
        calls.append(request)
        if failure == "timeout":
            raise httpx.ReadTimeout("response lost", request=request)
        if failure == "invalid-json":
            return httpx.Response(201, content=b"not-json")
        return httpx.Response(409, json={"status": False, "message": "conflict"})

    exception = {
        "timeout": httpx.ReadTimeout,
        "invalid-json": ValueError,
        "conflict": FutureAGIAPIError,
    }[failure]
    with client_for(handler) as client, pytest.raises(exception):
        client.datasets.versions.create(
            DATASET, DatasetVersionCreate.from_dict({"items": []})
        )
    assert len(calls) == 1
