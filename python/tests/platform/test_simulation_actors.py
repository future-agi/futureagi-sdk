"""client.simulation.environments.actors, against an in-process httpx MockTransport (no backend)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import fi.platform as fp
import httpx
import pytest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from tests.platform.test_generator import CONTRACT, _with  # noqa: E402

from sdkgen import generator as generate  # noqa: E402

BASE = "http://backend.test"
ENV = "11111111-1111-4111-8111-11111111111a"
ACTORS = {"status": True, "result": {"actors": [], "limits": {}, "revision": 3}}


def _client(sent: list[httpx.Request], result: dict) -> fp.Client:
    def handler(request: httpx.Request) -> httpx.Response:
        sent.append(request)
        return httpx.Response(200, json=result)

    http = httpx.Client(transport=httpx.MockTransport(handler))
    return fp.Client(api_key="k", secret_key="s", base_url=BASE, http_client=http)


def test_list_and_get_read_the_environments_actors():
    sent: list[httpx.Request] = []
    client = _client(sent, ACTORS)

    client.simulation.environments.actors.list(ENV)
    client.simulation.environments.actors.get(ENV, "caller", scenario_key="refund-flow")

    assert [(r.method, r.url.path) for r in sent] == [
        ("GET", f"/simulate/api/harness-environments/{ENV}/actors/"),
        ("GET", f"/simulate/api/harness-environments/{ENV}/actors/caller/"),
    ]
    assert sent[1].url.params["scenario_key"] == "refund-flow"


def test_create_sends_new_id_as_the_actors_id_and_keeps_the_environment_in_the_path():
    sent: list[httpx.Request] = []
    client = _client(sent, ACTORS)

    client.simulation.environments.actors.create(
        ENV, actor={"name": "Dispatcher"}, new_id="dispatcher", expected_revision=3
    )

    assert sent[0].method == "POST"
    assert sent[0].url.path == f"/simulate/api/harness-environments/{ENV}/actors/"
    assert json.loads(sent[0].content) == {
        "actor": {"name": "Dispatcher"},
        "id": "dispatcher",
        "expected_revision": 3,
    }


def test_update_replaces_one_actor_with_changes():
    sent: list[httpx.Request] = []
    client = _client(sent, ACTORS)

    client.simulation.environments.actors.update(
        ENV, "caller", changes={"goal": "Book a ride"}
    )

    assert (sent[0].method, sent[0].url.path) == (
        "PUT",
        f"/simulate/api/harness-environments/{ENV}/actors/caller/",
    )
    assert json.loads(sent[0].content) == {"changes": {"goal": "Book a ride"}}


def test_validate_writes_nothing_and_names_the_op():
    sent: list[httpx.Request] = []
    client = _client(
        sent,
        {"status": True, "result": {"problems": [], "unconfirmed_shared_actions": []}},
    )

    client.simulation.environments.actors.validate(ENV, op="delete", actor_id="caller")

    assert (sent[0].method, sent[0].url.path) == (
        "POST",
        f"/simulate/api/harness-environments/{ENV}/actor-validation/",
    )
    assert json.loads(sent[0].content) == {"op": "delete", "actor_id": "caller"}


def test_two_parameters_with_one_argument_name_fail_the_build():
    """Without the rename, the body `id` and the path `id` would be one Python argument twice."""
    catalog = _with("simulation.environments.actors.create")
    entry = next(
        e
        for e in catalog["operations"]
        if e["id"] == "simulation.environments.actors.create"
    )
    entry.pop("contract_fix")

    with pytest.raises(
        generate.CatalogError, match=r"two parameters become the argument \['id'\]"
    ):
        generate.load(CONTRACT, catalog)


def test_delete_limits_and_accept_unresolved():
    sent: list[httpx.Request] = []
    client = _client(sent, ACTORS)

    client.simulation.environments.actors.delete(ENV, "coworker", expected_revision=3)
    client.simulation.environments.actors.set_limits(ENV, limits={"max_active": 2, "actor_seconds_per_call": None})
    client.simulation.environments.actors.accept_unresolved(ENV, policy="refunds over 500 need a manager", expected_revision=4)

    assert [(r.method, r.url.path) for r in sent] == [
        ("DELETE", f"/simulate/api/harness-environments/{ENV}/actors/coworker/"),
        ("PUT", f"/simulate/api/harness-environments/{ENV}/actor-limits/"),
        ("POST", f"/simulate/api/harness-environments/{ENV}/actor-unresolved/accept/"),
    ]
    assert sent[0].url.params["expected_revision"] == "3"
    assert json.loads(sent[1].content) == {"limits": {"max_active": 2, "actor_seconds_per_call": None}}
    assert json.loads(sent[2].content) == {"policy": "refunds over 500 need a manager", "expected_revision": 4}


def test_an_environment_refusal_carries_its_code():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(404, json={"error": "unresolved_not_found", "message": "that point is no longer waiting", "retryable": False})

    http = httpx.Client(transport=httpx.MockTransport(handler))
    client = fp.Client(api_key="k", secret_key="s", base_url=BASE, http_client=http)

    with pytest.raises(fp.NotFoundError) as refused:
        client.simulation.environments.actors.accept_unresolved(ENV, policy="gone")

    assert refused.value.code == "unresolved_not_found"


def test_a_run_sends_its_seed():
    sent: list[httpx.Request] = []
    client = _client(sent, {"status": True, "result": {"job_id": "j1"}})

    client.simulation.environments.run(ENV, scenario_ids=["refund-flow"], trials=1, seed="7")

    assert (sent[0].method, sent[0].url.path) == ("POST", f"/simulate/api/harness-environments/{ENV}/run/")
    assert json.loads(sent[0].content) == {"scenario_ids": ["refund-flow"], "trials": 1, "seed": "7"}


def test_a_run_sends_an_idempotency_key_given_or_new():
    sent: list[httpx.Request] = []
    client = _client(sent, {"status": True, "result": {"job_id": "j1"}})

    client.simulation.environments.run(ENV, scenario_ids=["refund-flow"], idempotency_key="run-1")
    client.simulation.environments.run(ENV, scenario_ids=["refund-flow"])
    client.simulation.environments.run(ENV, scenario_ids=["refund-flow"])

    keys = [request.headers.get("idempotency-key") for request in sent]
    assert keys[0] == "run-1"
    assert keys[1] and keys[2] and keys[1] != keys[2]


@pytest.mark.parametrize(
    ("body", "code"), [({"code": 7}, None), ({"code": 7, "error": "keys_invalid"}, "keys_invalid")]
)
def test_an_error_code_that_is_not_a_string_is_read_as_typescript_reads_it(body, code):
    response = httpx.Response(400, json=body, request=httpx.Request("GET", "https://x"))

    assert fp.APIError("refused", response=response, body=body).code == code



@pytest.mark.parametrize("actor_id", ["", "  "])
def test_an_empty_path_value_is_refused_before_any_request(actor_id):
    sent: list[httpx.Request] = []
    client = _client(sent, {"status": True, "result": {}})

    with pytest.raises(ValueError, match="actor_id is empty|id is empty"):
        client.simulation.environments.actors.get(ENV, actor_id)
    assert sent == []
