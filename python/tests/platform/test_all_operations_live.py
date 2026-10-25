"""Every catalog operation, called against a real backend (FI_BASE_URL). No mocks.

The client is strict (`strict_responses=True`), so a response that does not match the
generated models fails the test. A few operations cannot succeed on every install
(a plan-gated feature, a background worker that has not finished, an id that only
exists once traces are indexed); those accept the typed error the backend sends, and
`test_every_operation_was_called` (last in this file) prints what each one returned.
"""

from __future__ import annotations

import time
import uuid
import warnings
from pathlib import Path

import fi.platform as fi
import pytest
import yaml
from fi.platform._transport import Operation

CATALOG = Path(__file__).resolve().parents[3] / "sdkgen" / "catalog" / "operations.yaml"

CODE_EVAL = "def evaluate(input, **kwargs):\n    return {'result': True, 'reason': 'ok'}\n"


def _name(prefix: str) -> str:
    return f"sdk-{prefix}-{uuid.uuid4().hex[:8]}"


def raw(client, method: str, path: str, body=None):
    """Setup calls for endpoints that are not in the catalog (yet)."""
    op = Operation(id="raw", method=method, path=path, unwrap="result", pagination=None)
    return client._transport.request(op, body=body)


def allow(fn, *statuses: int):
    """Call fn; return None instead of raising for the listed HTTP statuses."""
    try:
        return fn()
    except fi.APIError as exc:
        if exc.status_code in statuses:
            return None
        raise


@pytest.fixture
def dataset(client):
    ds = client.datasets.create(new_dataset_name=_name("ds"))
    columns = client.datasets.columns.add(
        ds.dataset_id, new_columns_data=[{"name": "question", "data_type": "text"}, {"name": "answer", "data_type": "text"}]
    ).data
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", fi.BetaWarning)
        client.datasets.rows.add(
            ds.dataset_id,
            rows=[{"cells": [{"column_name": "question", "value": f"{i}+{i}?"}, {"column_name": "answer", "value": str(2 * i)}]} for i in range(10)],
        )
    yield ds, columns
    allow(lambda: client.datasets.delete(dataset_ids=[ds.dataset_id]), 400, 404)


@pytest.fixture
def code_template(client):
    return client.evals.templates.create(
        name=_name("tpl").replace("-", "_"), eval_type="code", code_language="python", code=CODE_EVAL, output_type="pass_fail"
    )


@pytest.fixture
def project(client):
    """An observe project with two spans in one session, sent through span ingestion."""
    name = _name("proj")
    now = time.time_ns()
    spans = [
        {
            "project_name": name, "project_type": "observe", "trace_id": uuid.uuid4().hex, "span_id": uuid.uuid4().hex[:16],
            "name": f"chat-{i}", "start_time": now - 2_000_000_000, "end_time": now - 1_000_000_000, "latency": 1000, "status": "OK",
            "attributes": {"gen_ai.span.kind": "LLM", "input.value": "What is 2+2?", "output.value": "4", "session.id": "sdk-session"},
        }
        for i in range(2)
    ]
    # One span first: the backend creates a new project from parallel threads, so a first
    # batch of several spans can race on the project's unique constraint (backend bug).
    ids = []
    for span in spans:
        ids += raw(client, "POST", "/tracer/observation-span/create_otel_span/", body=[span])["ids"]
    project_id = client.projects.list(name=name)["projects"][0]["id"]
    return project_id, spans, ids


# --------------------------------------------------------------------------- #


def test_context(client):
    me = client.account.whoami()
    assert me.email
    workspaces = client.workspaces.list()
    assert workspaces.workspaces
    assert client.workspaces.get(workspaces.workspaces[0].id).workspaces


def test_datasets_full_lifecycle(client, dataset, code_template):
    ds, (question, answer) = dataset
    assert client.datasets.columns.add_static(ds.dataset_id, new_column_name="notes", column_type="text")
    assert ds.dataset_id in [d.id for d in client.datasets.list(search_text=ds.dataset_name)]
    table = client.datasets.get(ds.dataset_id)
    assert len(table.table) == 10
    row = table.table[0].row_id

    assert client.datasets.columns.rename(ds.dataset_id, answer.id, new_column_name="expected")
    assert client.datasets.cells.update(ds.dataset_id, row_id=row, column_id=answer.id, new_value="changed")

    client.datasets.evals.add(ds.dataset_id, name="code_check", template_id=code_template.id, config={"mapping": {"input": "question"}}, run=False)
    evals = client.datasets.evals.list(ds.dataset_id, eval_type="user").evals
    assert [e["name"] for e in evals] == ["code_check"]
    assert client.datasets.evals.run(ds.dataset_id, user_eval_ids=[evals[0]["id"]])

    prompt_config = {"model": "gpt-4o-mini", "messages": [{"role": "user", "content": "{{question}}"}]}
    assert client.datasets.prompts.add(dataset_id=ds.dataset_id, name="answer_llm", config=prompt_config)
    stats = client.datasets.prompts.stats(ds.dataset_id)
    assert [p.name for p in stats.prompts] == ["answer_llm"]
    column = next(c for c in client.datasets.get(ds.dataset_id).column_config if c.name == "answer_llm")
    assert client.datasets.prompts.update(dataset_id=ds.dataset_id, column_id=column.id, name="answer_llm2", config=prompt_config)
    # Queues an LLM call; succeeds whether or not a provider key is configured.
    allow(lambda: client.datasets.prompts.run(run_prompt_ids=[stats.prompts[0].id], selected_all_rows=True), 400)


def test_eval_templates_and_groups(client, code_template):
    page = client.evals.templates.list(page_size=5, owner_filter="system")
    assert page.items and page.total
    detail = client.evals.templates.get(code_template.id)
    assert detail.id == code_template.id
    assert client.evals.templates.update(code_template.id, description="updated by sdk test").updated
    assert client.evals.templates.get(code_template.id).description == "updated by sdk test"

    groups = client.evals.groups.list()
    assert "data" in groups
    group_id = groups["data"][0]["id"] if groups["data"] else str(uuid.uuid4())
    allow(lambda: client.evals.groups.get(group_id), 400, 404)
    # Runs the template for real; needs a model provider on the backend for most templates.
    allow(lambda: client.evals.test(name=code_template.name, output_type="Pass/Fail", template_id=code_template.id, template_type="Futureagi",
                                    config={"mapping": {"input": "input"}}, mapping={"input": "hello"}), 400)


def test_prompts_lifecycle(client):
    prompt = client.prompts.create(name=_name("prompt"), description="sdk test")
    assert client.prompts.get(prompt.id).name == prompt.name
    assert client.prompts.update(prompt.id, description="updated").description == "updated"
    assert [p.id for p in client.prompts.list(search=prompt.name)] == [prompt.id]
    assert client.prompts.versions.list(prompt.id).to_list()[0]["template_version"] == "v1"
    config = [{"messages": [{"role": "user", "content": [{"type": "text", "text": "Say hi"}]}], "configuration": {"model": "gpt-4o-mini"}}]
    receipt = client.prompts.run(prompt.id, version="v1", is_run="prompt", prompt_config=config)
    assert receipt.template_id == prompt.id
    assert client.prompts.run_status(prompt.id, template_version="v1").status


def test_observability(client, project, code_template):
    project_id, spans, span_ids = project
    assert client.projects.get(project_id).id == project_id
    # Lists are served from ClickHouse, which fills asynchronously after ingestion.
    traces = client.traces.list(project_id=project_id)
    spans_page = client.spans.list(project_id=project_id)
    sessions = client.sessions.list(project_id=project_id)
    assert traces.metadata is not None and spans_page.metadata is not None and sessions.metadata is not None
    trace_id = str(uuid.UUID(spans[0]["trace_id"]))
    allow(lambda: client.traces.get(trace_id, project_id=project_id), 400)
    allow(lambda: client.spans.get(span_ids[0], project_id=project_id), 400)
    allow(lambda: client.sessions.get(str(uuid.uuid4())), 400, 404)
    assert client.traces.error_analysis(trace_id).analysis_exists is False

    props = client.traces.properties.list(workflow="observability")
    assert props.metrics

    config = client.evals.configs.create(eval_template=code_template.id, project=project_id, name=_name("cfg"), mapping={"input": "input"})
    assert config.id in [c.id for c in client.evals.configs.list()]
    task = client.evals.tasks.create(project=project_id, name=_name("task"), sampling_rate=100, run_type="historical", evals=[config.id], spans_limit=10)
    assert [row.id for row in client.evals.tasks.list(project_id=project_id).table] == [task.id]
    assert client.evals.tasks.get(task.id).project == project_id
    # The task's status moves on in a background worker, so only the first pause is certain.
    assert client.evals.tasks.pause(eval_task_id=task.id).message
    allow(lambda: client.evals.tasks.resume(eval_task_id=task.id), 400)
    allow(lambda: client.evals.tasks.pause(eval_task_id=task.id), 400)  # updates need a paused task
    allow(lambda: client.evals.tasks.update(eval_task_id=task.id, edit_type="fresh_run", name="renamed"), 400)

    assert client.alerts.rules.list().column_config
    client.alerts.logs.list().first_page()
    allow(lambda: client.error_clusters.list(), 402)  # plan-gated
    allow(lambda: client.error_clusters.get(str(uuid.uuid4())), 400, 402, 404)


def test_annotation_queue_workflow(client, dataset):
    ds, _ = dataset
    row = client.datasets.get(ds.dataset_id).table[0].row_id
    label = raw(client, "POST", "/model-hub/annotations-labels/", body={"name": _name("label"), "type": "text", "settings": {"placeholder": "notes", "max_length": 200, "min_length": 0}})
    queue = raw(client, "POST", "/model-hub/annotation-queues/", body={"name": _name("queue"), "label_ids": [label["id"]], "dataset": ds.dataset_id})
    raw(client, "POST", f"/model-hub/annotation-queues/{queue['id']}/items/add-items/", body={"items": [{"source_type": "dataset_row", "source_id": row}]})
    raw(client, "POST", f"/model-hub/annotation-queues/{queue['id']}/update-status/", body={"status": "active"})

    assert [q.id for q in client.annotation_queues.list(search=queue["name"])] == [queue["id"]]
    assert client.annotation_queues.get(queue["id"]).status == "active"
    items = client.annotation_queues.items.list(queue["id"]).to_list()
    assert len(items) == 1
    detail = client.annotation_queues.items.annotate_detail(queue["id"], items[0].id)
    assert detail.item["id"] == items[0].id
    assert client.annotation_queues.items.submit(queue["id"], items[0].id, annotations=[{"label_id": label["id"], "value": "looks right"}]).submitted == 1
    assert client.annotation_queues.items.complete(queue["id"], items[0].id).completed_item_id == items[0].id


def test_experiments_and_optimizations(client, dataset, code_template):
    ds, (question, _) = dataset
    prompt = client.prompts.create(name=_name("prompt"))
    client.prompts.get(prompt.id)  # materializes the v1 draft
    raw(client, "POST", f"/model-hub/prompt-templates/{prompt.id}/commit/", body={"version_name": "v1", "message": "init", "set_default": True})
    version = client.prompts.versions.list(prompt.id).to_list()[0]["id"]

    message = client.experiments.create(
        name=_name("exp"), dataset_id=ds.dataset_id, column_id=question.id,
        prompt_config=[{"name": "p1", "prompt_id": prompt.id, "prompt_version": version, "model": "gpt-4o-mini", "messages": [{"role": "user", "content": "{{question}}"}]}],
        user_eval_metrics=[{"template_id": code_template.id, "name": "code_check", "config": {"mapping": {"input": "question"}}}],
    )
    assert "experiment_id=" in message
    experiments = client.experiments.list(dataset_id=ds.dataset_id).to_list()
    assert len(experiments) == 1
    assert client.experiments.get(experiments[0].id).dataset_id == ds.dataset_id

    run = client.optimizations.create(name=_name("opt"), column_id=question.id, optimizer_algorithm="random_search")
    assert client.optimizations.get(run.id).optimiser_name == run.name
    assert run.id in [r["id"] for r in client.optimizations.list()]


def test_agents_and_simulation(client):
    agent = client.agents.create(agent_name=_name("agent"), agent_type="text", commit_message="v1", provider="custom", model="gpt-4o-mini")
    agent_id = agent.agent.id
    assert client.agents.get(agent_id).agent_name == agent.agent.agent_name
    assert client.agents.update(agent_id, description="updated").agent.description == "updated"
    assert client.agents.versions.create(agent_id, commit_message="v2").version.version_number == 2
    assert agent_id in [a.id for a in client.agents.list(search=agent.agent.agent_name)]

    ds = client.datasets.create(new_dataset_name=_name("scenario-src"))
    client.datasets.columns.add(ds.dataset_id, new_columns_data=[{"name": "situation", "data_type": "text"}])
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", fi.BetaWarning)
        client.datasets.rows.add(ds.dataset_id, rows=[{"cells": [{"column_name": "situation", "value": f"Refund request #{i}"}]} for i in range(10)])
    client.simulation.scenarios.create(name=_name("scenario"), kind="dataset", dataset_id=ds.dataset_id, agent_definition_id=agent_id, source_type="agent_definition")
    scenarios = client.simulation.scenarios.list(agent_definition_id=agent_id).to_list()
    assert len(scenarios) == 1
    assert client.simulation.scenarios.get(scenarios[0].id).id == scenarios[0].id
    assert client.simulation.scenarios.update(scenarios[0].id, description="updated").scenario.description == "updated"

    test = client.simulation.tests.create(name=_name("simtest"), agent_definition_id=agent_id, scenario_ids=[scenarios[0].id])
    assert client.simulation.tests.get(test.id).name == test.name
    assert test.id in [t.id for t in client.simulation.tests.list(search=test.name)]
    # Runs only once scenario generation (a background job) has finished.
    execution = allow(lambda: client.simulation.tests.run(test.id), 400)
    execution_id = execution.execution_id if execution else str(uuid.uuid4())
    client.simulation.executions.list().first_page()
    # Backend bug: an unknown execution id returns 500 instead of 404.
    allow(lambda: client.simulation.executions.get(execution_id).first_page(), 404, 500)
    allow(lambda: client.simulation.executions.analytics(execution_id), 404, 500)


def test_gateway_management(client):
    gateways = client.gateway.list()
    assert gateways and gateways[0].id
    client.gateway.config(gateways[0].id)
    client.gateway.request_logs.list().first_page()
    assert "rules" in client.gateway.guardrail_rules.list()
    sessions = client.gateway.sessions.list().to_list(limit=1)
    session_id = sessions[0].id if sessions else str(uuid.uuid4())
    allow(lambda: client.gateway.sessions.requests(session_id), 400, 404)
    overview = client.gateway.analytics()
    assert "total_requests" in overview


def test_knowledge_bases_and_usage(client):
    kbs = client.knowledge_bases.list()
    kb_id = kbs.results[0]["id"] if kbs.results else str(uuid.uuid4())
    allow(lambda: client.knowledge_bases.get(kb_id), 404)
    allow(lambda: client.usage.overview(), 404)  # not served by self-hosted installs


def test_dashboards_lifecycle(client):
    metric = next(m for m in client.dashboards.metrics.list(workflow="observability").metrics if m.role == "metric")
    query = {"time_range": {"preset": "7D"}, "metrics": [{"name": metric.name, "type": metric.category, "aggregation": "avg"}]}
    assert client.dashboards.query(**query).metrics[0].name == metric.name

    dashboard = client.dashboards.create(name=_name("dash"))
    try:
        assert dashboard.id in [d.id for d in client.dashboards.list()]
        assert client.dashboards.get(dashboard.id).name == dashboard.name
        assert client.dashboards.update(dashboard.id, name=dashboard.name + "-u").name.endswith("-u")
        widget = client.dashboards.widgets.create(dashboard.id, name="w1", query_config=query)
        assert [w.id for w in client.dashboards.widgets.list(dashboard.id)] == [widget.id]
        assert client.dashboards.widgets.get(dashboard.id, widget.id).name == "w1"
        assert client.dashboards.widgets.update(dashboard.id, widget.id, name="w2").name == "w2"
        assert client.dashboards.widgets.query(dashboard.id, widget.id).metrics
        client.dashboards.filter_values(metric_name="model", metric_type="system_metric", source="spans")
    finally:
        client.dashboards.delete(dashboard.id)
    with pytest.raises((fi.NotFoundError, fi.BadRequestError)):  # backend answers 400, not 404
        client.dashboards.get(dashboard.id)


# --------------------------------------------------------------------------- #


def test_every_operation_was_called(client, record_calls):
    """Runs last: every SDK operation in the catalog was exercised by a test above."""
    if not record_calls:
        pytest.skip("run the whole module to check coverage")
    ops = [e["id"] for e in yaml.safe_load(CATALOG.read_text())["operations"] if e["surfaces"].get("sdk") is not False]
    for op_id in ops:
        outcomes = record_calls.get(op_id, [])
        print(f"{op_id:44} {'ok' if 'ok' in outcomes else ','.join(sorted(set(outcomes))) or 'NOT CALLED'}")
    missing = [op for op in ops if op not in record_calls]
    assert not missing, f"operations no test called: {missing}"
