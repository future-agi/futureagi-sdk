"""Run a deterministic external workflow through the draft generated SDK.

Set FI_API_KEY, FI_SECRET_KEY, FI_BASE_URL, DATASET_ID and METRIC_ID. The metric
must describe the local exact-match rule used here. Each invocation creates a
new snapshot and two runs. No model, hosted evaluator or trace exporter runs.
"""

import argparse
import json
import os
from pathlib import Path
from uuid import UUID, uuid4

from fi import FutureAGIClient
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


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--release-gate", action="store_true")
    args = parser.parse_args()
    dataset_id = str(UUID(os.environ["DATASET_ID"]))
    metric_id = str(UUID(os.environ["METRIC_ID"]))
    with FutureAGIClient() as client:
        version = client.datasets.versions.create(
            dataset_id,
            DatasetVersionCreate.from_dict(
                {
                    "description": "SDK external workflow example",
                    "items": [
                        {
                            "external_id": "shipping",
                            "input": {"topic": "shipping"},
                            "expected": 5,
                        },
                        {
                            "external_id": "returns",
                            "input": {"topic": "returns"},
                            "expected": 30,
                        },
                    ],
                }
            ),
        ).result
        cases = [
            item.to_dict()
            for item in client.datasets.versions.get(
                dataset_id, str(version.id)
            ).result.items
        ]
        assert len(cases) == 2
        assert client.datasets.versions.list(dataset_id, limit=1).result.versions
        runs = {}
        for label, policy in [
            ("baseline", {"shipping": 5, "returns": 14}),
            ("candidate", {"shipping": 3, "returns": 30}),
        ]:
            create_body = ExternalRunCreateRequest.from_dict(
                {
                    "run_id": str(uuid4()),
                    "dataset_version_id": str(version.id),
                    "expected_items": [
                        {"example_id": case["example_id"], "trial_number": 1}
                        for case in cases
                    ],
                    "evaluator_metric_ids": [metric_id],
                    "model_config": policy,
                    "metadata": {"name": label, "task_revision": "sdk-example-v1"},
                }
            )
            run = client.experiment_runs.create(create_body).result
            assert client.experiment_runs.create(create_body).result.id == run.id
            binding = next(
                value
                for value in run.evaluator_bindings
                if str(value.metric_id) == metric_id
            )
            results = []
            for case in cases:
                # Replace this caller-owned task with your agent or tool loop.
                document = {"days": policy[case["input"]["topic"]]}
                output = int(document["days"])
                results.append(
                    {
                        "example_id": case["example_id"],
                        "trial_number": 1,
                        "receipt_key": str(uuid4()),
                        "status": "completed",
                        "output": output,
                        "score_refs": [
                            {
                                "metric_id": metric_id,
                                "evaluator_version_id": str(
                                    binding.evaluator_version_id
                                ),
                                "status": "assessed",
                                "value": int(output == case["expected"]),
                            }
                        ],
                    }
                )
            upload = ExternalRunResultsRequest.from_dict({"items": results})
            first = client.experiment_runs.ingest_results(str(run.id), upload)
            replay = client.experiment_runs.ingest_results(str(run.id), upload)
            assert first.to_dict() == replay.to_dict()
            runs[label] = str(run.id)
        response = client.experiment_runs.compare(
            RunComparisonRequest.from_dict(
                {
                    "baseline_run_id": runs["baseline"],
                    "candidate_run_id": runs["candidate"],
                    "metric_id": metric_id,
                    "passing_score": 1,
                    **(
                        {"release_gate": {"max_regressions": 0}}
                        if args.release_gate
                        else {}
                    ),
                }
            )
        )
        payload = response.to_dict()
        summary = payload["result"]["comparison"]
        assert (
            summary["baseline"]["score_average"]
            == summary["candidate"]["score_average"]
            == 0.5
        )
        assert (
            summary["status_counts"]["regressed"]
            == summary["status_counts"]["improved"]
            == 1
        )
        Path("sdk-comparison.json").write_text(json.dumps(payload, indent=2) + "\n")
        print("Python SDK: equal means 0.5; improved=1, regressed=1; replay unchanged")
        # The application decides its CI exit after retaining the server report.
        if args.release_gate:
            verdict = payload["result"]["release_gate"]["verdict"]
            print(f"Release gate: {verdict}")
            raise SystemExit(0 if verdict == "pass" else 1)


if __name__ == "__main__":
    main()
