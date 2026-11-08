"""Remaining catalog operations; coverage is checked across both live modules."""

from __future__ import annotations

import uuid
import warnings

import fi.platform as fi
import pytest

from .test_all_operations_live import (
    _name,
    allow,
    wait_until,
)


def test_experiments_and_optimizations(client, dataset, code_template, prompt):
    ds, (question, _) = dataset
    client.prompts.get(prompt.id)  # materializes the v1 draft
    client.prompts.commit(prompt.id, version_name="v1", message="init", set_default=True)
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


def test_agents_and_simulation(client, request):
    agent = client.agents.create(agent_name=_name("agent"), agent_type="text", commit_message="v1", provider="custom", model="gpt-4o-mini")
    agent_id = agent.agent.id
    assert client.agents.get(agent_id).agent_name == agent.agent.agent_name
    assert client.agents.update(agent_id, description="updated").agent.description == "updated"
    assert client.agents.versions.create(agent_id, commit_message="v2").version.version_number == 2
    assert agent_id in [a.id for a in client.agents.list(search=agent.agent.agent_name)]

    ds = client.datasets.create(new_dataset_name=_name("scenario-src"))
    request.addfinalizer(lambda: allow(lambda: client.datasets.delete(dataset_ids=[ds.dataset_id]), 400, 404))
    request.addfinalizer(lambda: allow(lambda: client.request("DELETE", f"/simulate/agent-definitions/{agent_id}/delete/"), 400, 404))
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
    if sessions:  # sessions exist once traffic with x-agentcc-session-id has gone through the gateway
        assert isinstance(client.gateway.sessions.requests(session_id), list)
    else:
        allow(lambda: client.gateway.sessions.requests(session_id), 400, 404)
    overview = client.gateway.analytics()
    assert "total_requests" in overview


def test_knowledge_bases_lifecycle(client):
    """One store: the id a create returns is the one get, list, update and delete work with."""
    kb = client.knowledge_bases.create(name=_name("kb"), chunk_size=256)
    try:
        assert kb.id and kb.embedding_model and kb.chunk_size == 256
        assert client.knowledge_bases.get(kb.id).name == kb.name
        assert kb.id in [k.id for k in client.knowledge_bases.list(search=kb.name)]
        assert client.knowledge_bases.update(kb.id, name=kb.name + "-u").name == kb.name + "-u"
        assert client.knowledge_bases.get(kb.id).name == kb.name + "-u"
    finally:
        client.knowledge_bases.delete(kb.id)
    with pytest.raises(fi.NotFoundError):
        client.knowledge_bases.get(kb.id)


def test_file_knowledge_bases_and_usage(client):
    """The file store (the app's Knowledge Base page): create with uploads, update, files, delete."""
    created = client.file_knowledge_bases.create(name=_name("kb"), files=[("notes.txt", b"The SDK uploads files as multipart form data.\n")])
    kb_id = created.kb_id
    try:
        assert kb_id and created.file_ids
        assert kb_id in [kb.id for kb in client.file_knowledge_bases.list_names().table_data]
        assert kb_id in [row.id for row in client.file_knowledge_bases.list().table_data]
        # Backend: an update that adds files is refused (400) while an earlier upload is still
        # being processed, and the refused update stores its file anyway. Wait for the worker.
        def processed() -> bool:
            return all(f.status != "Processing" for f in client.file_knowledge_bases.files.list(kb_id=kb_id).table_data)

        assert wait_until(processed)
        updated = client.file_knowledge_bases.update(kb_id=kb_id, name=created.kb_name + "-u", files=[("more.txt", b"A second file.\n")])
        assert updated.name.endswith("-u")
        files = client.file_knowledge_bases.files.list(kb_id=kb_id)
        assert files.total_rows == 2
        assert wait_until(processed)  # a file being processed is not deleted
        assert client.file_knowledge_bases.files.delete(kb_id=kb_id, file_ids=[files.table_data[0].id])
        assert wait_until(lambda: client.file_knowledge_bases.files.list(kb_id=kb_id).total_rows == 1)
    finally:
        client.file_knowledge_bases.delete(kb_ids=[kb_id])
    allow(lambda: client.usage.overview(), 404)  # not served by self-hosted installs


def test_models_and_provider_keys(client):
    models = client.models.list()
    assert models.results is not None
    client.provider_keys.list().first_page()


def test_dashboards_lifecycle(client):
    metric = next(m for m in client.dashboards.metrics.list(workflow="observability").metrics if m.role == "metric")
    query = {"time_range": {"preset": "7D"}, "metrics": [{"name": metric.name, "type": metric.category, "aggregation": "avg"}]}
    assert client.dashboards.query(**query).metrics[0].name == metric.name

    dashboard = client.dashboards.create(name=_name("dash"))
    try:
        assert dashboard.id in [d.id for d in client.dashboards.list()]
        assert client.dashboards.get(dashboard.id).name == dashboard.name
        assert client.dashboards.update(dashboard.id, name=dashboard.name + "-u").name.endswith("-u")
        partial = client.dashboards.update(dashboard.id, description="description only")  # a PATCH is partial
        assert partial.description == "description only" and partial.name == dashboard.name + "-u"
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
