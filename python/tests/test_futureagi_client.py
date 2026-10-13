import json

import httpx

from fi import FutureAGIClient


def _client_with_transport(handler):
    client = FutureAGIClient(
        api_key="api-key",
        secret_key="secret-key",
        base_url="http://api.test",
    )
    client.generated_client.set_httpx_client(
        httpx.Client(
            base_url="http://api.test",
            headers={
                "X-Api-Key": "api-key",
                "X-Secret-Key": "secret-key",
            },
            transport=httpx.MockTransport(handler),
        )
    )
    return client


def test_futureagi_client_sends_auth_headers_and_query_params():
    requests = []

    def handler(request):
        requests.append(request)
        assert request.headers["X-Api-Key"] == "api-key"
        assert request.headers["X-Secret-Key"] == "secret-key"
        assert request.url.path == "/model-hub/annotation-queues/"
        assert request.url.params["limit"] == "10"
        return httpx.Response(200, json={"count": 0, "results": []})

    client = _client_with_transport(handler)

    assert client.annotation_queues.list(limit=10) == {
        "count": 0,
        "results": [],
    }
    assert len(requests) == 1


def test_futureagi_client_wraps_discussion_comments():
    requests = []

    def handler(request):
        requests.append(request)
        assert request.method == "POST"
        assert request.url.path == (
            "/model-hub/annotation-queues/q1/items/"
            "11111111-1111-1111-1111-111111111111/discussion/"
        )
        assert json.loads(request.content) == {
            "comment": "@reviewer please check this item",
            "mentioned_user_ids": ["u1"],
        }
        return httpx.Response(
            200,
            json={
                "status": True,
                "result": {"review_comments": [], "review_threads": []},
            },
        )

    client = _client_with_transport(handler)

    client.annotation_queues.discussion.comment(
        "q1",
        "11111111-1111-1111-1111-111111111111",
        {
            "comment": "@reviewer please check this item",
            "mentioned_user_ids": ["u1"],
        },
    )
    assert len(requests) == 1


def test_futureagi_client_wraps_common_public_sdk_paths():
    requests = []
    expected = [
        ("GET", "/model-hub/develops/dataset-1/get-dataset-table/"),
        ("GET", "/model-hub/experiments/v2/experiment-1/rows/"),
        ("GET", "/simulate/run-tests/run-test-1/status/"),
        ("GET", "/tracer/trace/list_voice_calls/"),
        ("GET", "/accounts/user-info/"),
        ("GET", "/tracer/user-alert-logs/alert-1/list/"),
    ]

    def handler(request):
        requests.append(request)
        method, path = expected.pop(0)
        assert request.method == method
        assert request.url.path == path
        return httpx.Response(200, json={"ok": True})

    client = _client_with_transport(handler)

    client.datasets.get_table("dataset-1", limit=5)
    client.experiments.rows("experiment-1", page=1)
    client.simulations.run_tests.status("run-test-1")
    client.tracing.voice_calls(project_id="project-1")
    client.users.current()
    client.alerts.logs_for_alert("alert-1")

    assert len(requests) == 6
    assert expected == []


def test_futureagi_client_wraps_eval_and_simulation_eval_paths():
    requests = []
    expected = [
        ("POST", "/model-hub/eval-templates/list/"),
        ("POST", "/model-hub/eval-templates/create-v2/"),
        ("GET", "/model-hub/eval-templates/eval-template-1/detail/"),
        ("PUT", "/model-hub/eval-templates/eval-template-1/update/"),
        ("GET", "/model-hub/eval-templates/eval-template-1/versions/"),
        ("POST", "/sdk/api/v1/new-eval/"),
        ("GET", "/sdk/api/v1/new-eval/"),
        ("POST", "/simulate/run-tests/run-test-1/eval-configs/"),
        (
            "GET",
            "/simulate/run-tests/run-test-1/eval-configs/eval-config-1/get-structure/",
        ),
        ("GET", "/simulate/run-tests/run-test-1/eval-summary/"),
        ("POST", "/simulate/run-tests/run-test-1/run-new-evals/"),
    ]

    def handler(request):
        requests.append(request)
        method, path = expected.pop(0)
        assert request.method == method
        assert request.url.path == path
        return httpx.Response(200, json={"ok": True})

    client = _client_with_transport(handler)

    client.evals.list_templates({"filters": {}})
    client.evals.create_template({"name": "Faithfulness"})
    client.evals.get_template("eval-template-1")
    client.evals.update_template("eval-template-1", {"name": "Faithfulness v2"})
    client.evals.template_versions("eval-template-1")
    client.evals.run_v2({"eval_id": "run-1", "data": []})
    client.evals.get_run_v2("11111111-1111-1111-1111-111111111111")
    client.simulations.run_tests.add_eval_configs(
        "run-test-1", {"eval_configs": [{"eval_id": "eval-template-1"}]}
    )
    client.simulations.run_tests.eval_config_structure("run-test-1", "eval-config-1")
    client.simulations.run_tests.eval_summary("run-test-1", test_execution_id="te-1")
    client.simulations.run_tests.run_new_evals(
        "run-test-1", {"test_execution_ids": ["te-1"], "eval_config_ids": ["cfg-1"]}
    )

    assert len(requests) == 11
    assert expected == []
