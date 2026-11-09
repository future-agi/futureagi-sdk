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

CATALOG = Path(__file__).resolve().parents[3] / "sdkgen" / "catalog" / "operations.yaml"

CODE_EVAL = "def evaluate(input, **kwargs):\n    return {'result': True, 'reason': 'ok'}\n"


def _name(prefix: str) -> str:
    return f"sdk-{prefix}-{uuid.uuid4().hex[:8]}"


def allow(fn, *statuses: int):
    """Call fn; return None instead of raising for the listed HTTP statuses."""
    try:
        return fn()
    except fi.APIError as exc:
        if exc.status_code in statuses:
            return None
        raise


def wait_until(predicate, timeout: float = 20.0, every: float = 0.25) -> bool:
    """Poll a backend state change made by a background worker."""
    deadline = time.monotonic() + timeout
    while not predicate():
        if time.monotonic() > deadline:
            return False
        time.sleep(every)
    return True


def eventually(fn, *statuses: int, timeout: float = 20.0):
    """Retry fn while it fails with one of the statuses (backend background work); None if it never succeeds."""
    deadline = time.monotonic() + timeout
    while True:
        try:
            return fn()
        except fi.APIError as exc:
            if exc.status_code not in statuses:
                raise
            if time.monotonic() > deadline:
                return None
            time.sleep(0.5)


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
def prompt(client):
    created = client.prompts.create(name=_name("prompt"), description="sdk test")
    yield created
    allow(lambda: client.prompts.delete(created.id), 400, 404)


@pytest.fixture
def text_label(client):
    label = client.annotations.labels.create(
        name=_name("label"), type="text", settings={"placeholder": "notes", "max_length": 200, "min_length": 0}
    )
    yield label
    allow(lambda: client.annotations.labels.delete(label.id), 400, 404)


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
    # One span per call: the backend creates a new project from parallel threads, so a first
    # batch of several spans can race on the project's unique constraint (backend bug).
    ids = []
    for span in spans:
        ids += client.spans.ingest([span])["ids"]  # hand-written in fi/platform/resources/spans.py
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

    assert ds.dataset_id in [d.dataset_id for d in client.datasets.list_names().datasets]
    client.datasets.evals.stats(ds.dataset_id)


def test_datasets_from_file_and_huggingface(client):
    csv = ("qa.csv", b"question,answer\n1+1?,2\n2+2?,4\n")
    started = client.datasets.create_from_file(file=csv, new_dataset_name=_name("csv"), model_type="GenerativeLLM")
    try:
        assert started.dataset_id
        # Rows are loaded by a background worker; the table exists right away.
        assert client.datasets.get(started.dataset_id).column_config is not None
    finally:
        allow(lambda: client.datasets.delete(dataset_ids=[started.dataset_id]), 400, 404)
    # Needs outbound access to huggingface.co; a self-hosted install may not have it.
    hf = allow(lambda: client.datasets.create_from_huggingface(
        name=_name("hf"), huggingface_dataset_name="rajpurkar/squad", huggingface_dataset_split="validation", num_rows=5), 400, 500, 502, 503)
    if hf:
        allow(lambda: client.datasets.delete(dataset_ids=[hf.dataset_id]), 400, 404)


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


def test_prompts_lifecycle(client, prompt):
    assert client.prompts.get(prompt.id).name == prompt.name
    assert client.prompts.update(prompt.id, description="updated").description == "updated"
    assert [p.id for p in client.prompts.list(search=prompt.name)] == [prompt.id]
    assert client.prompts.versions.list(prompt.id).to_list()[0]["template_version"] == "v1"
    config = [{"messages": [{"role": "user", "content": [{"type": "text", "text": "Say hi"}]}], "configuration": {"model": "gpt-4o-mini"}}]
    receipt = client.prompts.run(prompt.id, version="v1", is_run="prompt", prompt_config=config)
    assert receipt.template_id == prompt.id
    assert client.prompts.run_status(prompt.id, template_version="v1").status


PROMPT_CONFIG = [{"messages": [{"role": "user", "content": [{"type": "text", "text": "Say hi to {{name}}"}]}],
                  "configuration": {"model": "gpt-4o-mini", "temperature": 0.5, "max_tokens": 64}, "placeholders": []}]


def test_prompt_drafts_commits_and_labels(client):
    """The fi.prompt module's flow: draft -> commit -> label -> fetch by name/label."""
    name = _name("draft")
    template = client.prompts.create_draft(name=name, prompt_config=PROMPT_CONFIG, variable_names={"name": "world"}, placeholders={})
    try:
        assert template.id and template.name == name
        committed = client.prompts.commit(template.id, version_name="v1", message="initial", set_default=True)
        assert "v1" in committed  # the server answers with a message string
        client.prompts.add_draft(template.id, new_prompts=[{"prompt_config": PROMPT_CONFIG, "variable_names": {"name": "world"}, "evaluation_configs": [], "metadata": {}, "placeholders": {}}])
        versions = client.prompts.versions.list(template.id).to_list()
        assert len(versions) >= 2
        v1 = next(v for v in versions if v["template_version"] == "v1")

        by_name = client.prompts.get_by_name(name=name)
        assert by_name["id"] == template.id
        client.prompts.history(template_id=template.id).first_page()

        label_name = _name("lbl")
        label = client.prompts.labels.create(name=label_name, type="custom")
        try:
            assert label.id in [lbl.id for lbl in client.prompts.labels.list()]
            client.prompts.labels.assign(template.id, label.id, version="v1")
            assert client.prompts.labels.for_template(template_id=template.id)
            assert client.prompts.labels.get_template(name=name, label=label_name)["id"] == template.id
            client.prompts.labels.set_default(template_name=name, version="v1")
            client.prompts.labels.remove(label_id=label.id, version_id=v1["id"])
        finally:
            allow(lambda: client.request("DELETE", f"/model-hub/prompt-labels/{label.id}/"), 400, 404)  # not in the catalog

        # Both call an LLM on the backend, which a self-hosted install may have no provider for.
        allow(lambda: client.prompts.generate(statement="Summarise a support ticket in one line."), 400, 402, 500)
        allow(lambda: client.prompts.improve(existing_prompt="Summarise this.", improvement_requirements="Be specific."), 400, 402, 500)
    finally:
        client.prompts.delete(template.id)
    with pytest.raises((fi.NotFoundError, fi.BadRequestError)):
        client.prompts.get(template.id)


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
    # A background worker moves the task from 'pending' to 'running', and only a running task can
    # be paused; after that its status keeps moving, so the later transitions may be refused.
    paused = eventually(lambda: client.evals.tasks.pause(eval_task_id=task.id), 400)
    assert paused is None or paused.message
    allow(lambda: client.evals.tasks.resume(eval_task_id=task.id), 400)
    allow(lambda: client.evals.tasks.pause(eval_task_id=task.id), 400)  # updates need a paused task
    allow(lambda: client.evals.tasks.update(eval_task_id=task.id, edit_type="fresh_run", name="renamed"), 400)

    assert client.alerts.rules.list().column_config
    client.alerts.logs.list().first_page()
    allow(lambda: client.error_clusters.list(), 402)  # plan-gated
    allow(lambda: client.error_clusters.get(str(uuid.uuid4())), 400, 402, 404)


def test_error_cluster_missing_tabs(client):
    """Both catalogued tabs must preserve the missing-issue/plan-gate errors.

    A fresh workspace has no scanner-produced issue. Exercise these read-only
    operations explicitly rather than silently dropping them from completeness.
    This is negative-path coverage, not evidence of a successful issue read.
    """
    missing = str(uuid.uuid4())
    for read in (client.error_clusters.overview, client.error_clusters.traces):
        with pytest.raises((fi.NotFoundError, fi.PaymentRequiredError)):
            read(missing)


def test_annotation_labels(client, text_label, project):
    assert client.annotations.labels.get(text_label.id).name == text_label.name
    assert text_label.id in [lbl.id for lbl in client.annotations.labels.list(search=text_label.name)]
    # Annotates spans by id; spans are visible to this endpoint once ClickHouse has indexed them.
    _, _, span_ids = project
    records = [{"observation_span_id": span_ids[0], "annotations": [{"annotation_label_id": text_label.id, "value": "fine"}], "notes": [{"text": "sdk"}]}]
    allow(lambda: client.annotations.bulk_create(records=records), 400, 404)


def test_annotation_queue_workflow(client, dataset, text_label):
    ds, _ = dataset
    rows = [r.row_id for r in client.datasets.get(ds.dataset_id).table[:3]]
    me = client.account.whoami()
    queue = client.annotation_queues.create(name=_name("queue"), label_ids=[text_label.id], extra_body={"dataset": ds.dataset_id})
    exported_dataset = None
    try:
        assert client.annotation_queues.update(queue.id, description="updated").description == "updated"
        added = client.annotation_queues.items.add(queue.id, items=[{"source_type": "dataset_row", "source_id": r} for r in rows])
        assert added.added == 3
        assert client.annotation_queues.update_status(queue.id, status="active").status == "active"

        assert [q.id for q in client.annotation_queues.list(search=queue.name)] == [queue.id]
        assert client.annotation_queues.get(queue.id).status == "active"
        items = client.annotation_queues.items.list(queue.id).to_list()
        assert len(items) == 3
        first, second, third = (item.id for item in items)

        allow(lambda: client.annotation_queues.items.assign(queue.id, item_ids=[first, second], user_ids=[me.id]), 400)
        detail = client.annotation_queues.items.annotate_detail(queue.id, first)
        assert detail.item["id"] == first
        assert client.annotation_queues.items.submit(queue.id, first, annotations=[{"label_id": text_label.id, "value": "looks right"}]).submitted == 1
        assert client.annotation_queues.items.list_annotations(queue.id, first)
        assert client.annotation_queues.items.complete(queue.id, first).completed_item_id == first
        client.annotation_queues.items.skip(queue.id, second)
        allow(lambda: client.annotation_queues.items.import_annotations(queue.id, third, annotations=[{"label_id": text_label.id, "value": "imported"}]), 400)
        assert client.annotation_queues.items.remove(queue.id, item_ids=[third]).removed == 1

        progress = client.annotation_queues.progress(queue.id)
        assert progress.total == 2 and progress.completed == 1
        client.annotation_queues.analytics(queue.id)
        client.annotation_queues.agreement(queue.id)
        assert isinstance(client.annotation_queues.export(queue.id), list)
        exported = client.annotation_queues.export_to_dataset(queue.id, dataset_name=_name("export"))
        exported_dataset = exported.dataset_id

        extra = client.annotations.labels.create(name=_name("extra"), type="text", settings={"placeholder": "x", "max_length": 50, "min_length": 0})
        try:
            assert client.annotation_queues.add_label(queue.id, label_id=extra.id).created
            assert client.annotation_queues.remove_label(queue.id, label_id=extra.id).removed
        finally:
            allow(lambda: client.annotations.labels.delete(extra.id), 400, 404)

        # Scores: the unified annotation store behind queues and span annotations.
        score = client.scores.create(source_type="dataset_row", source_id=rows[1], label_id=text_label.id, value="direct")
        assert score.label_id == text_label.id and score.value == "direct"  # any JSON value, a string here
        bulk = client.scores.create_bulk(source_type="dataset_row", source_id=rows[1], scores=[{"label_id": text_label.id, "value": "bulk"}])
        assert bulk.scores and not bulk.errors
        assert len(client.scores.list_for_source(source_type="dataset_row", source_id=rows[1])) >= 1
    finally:
        allow(lambda: client.annotation_queues.delete(queue.id), 400, 404)
        if exported_dataset:
            allow(lambda: client.datasets.delete(dataset_ids=[exported_dataset]), 400, 404)


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


def _publish_context_fixture(client, name, files):
    """Author a real context through HTTP; authoring is not yet catalogued."""
    base = "/model-hub/skills/contexts/"
    options = fi.RequestOptions(headers={"Idempotency-Key": str(uuid.uuid4())})
    created = client.request("POST", base, body={
        "name": name, "description": "SDK live consumption fixture", "tags": [], "files": files,
    }, options=options)
    root = base + created["context_id"] + "/draft/"
    draft = client.request("GET", root)
    review = client.request("POST", root + "head-review/", body={"revision": draft["revision"]})
    acknowledgment = {
        "revision": draft["revision"], "expected_digest": draft["digest"],
        "expected_head_version": review["expected_head_version"],
        "review_fingerprint": review["review_fingerprint"],
    }
    accepted = client.request("POST", root + "acknowledge-head/", body=acknowledgment)
    published = client.request("POST", root + "publish/", body={
        **acknowledgment, "revision": accepted["revision"], "base_version": draft["base_version"],
        "review_fingerprint": accepted["review_fingerprint"],
        "note": "SDK live lifecycle", "acknowledge_warnings": True,
    }, options=fi.RequestOptions(headers={"Idempotency-Key": str(uuid.uuid4())}))
    return created["context_id"], published["version"]


def test_skills_catalog_lifecycle(client):
    name = _name("skill")
    text = f"---\nname: {name}\ndescription: Use for SDK lifecycle validation.\n---\nRead the approved policy.\n"
    published = client.skills.publish(
        files=[{"path": "SKILL.md", "content": text}], labels=[], tags=["sdk-live"], acknowledge_warnings=True,
    )
    skill_id, version = published.skill.id, published.version
    assert skill_id in [item.id for item in client.skills.list(search=name)]
    assert client.skills.update_tags(skill_id, tags=["sdk-updated"]).tags == ["sdk-updated"]
    label = client.skills.set_label(
        skill_id, "sdk-live", version=version["number"], expected_release_revision=published.release_revision,
    )
    assert label.version_id == version["id"]
    resolved = client.skills.resolve(name=name, label="sdk-live")
    assert (resolved.skill_id, resolved.version_id, resolved.digest) == (skill_id, version["id"], version["digest"])
    assert client.skills.read_file(skill_id, resolved.version, path="SKILL.md").text == text


@pytest.mark.parametrize("kind", ["skill", "agent_context"])
def test_scoped_consumption_lifecycle(client, kind):
    """Real issuance, paged immutable reads, label movement, and revocation.

    No mocked transport or blanket error allowance: a missing facade fails this
    suite, rather than letting the completeness check report false coverage.
    """
    import asyncio
    import hashlib
    import os
    from datetime import datetime, timedelta, timezone

    from fi.context import AsyncContextClient, ContextClient
    from fi.skills import AsyncSkillsClient, SkillsClient

    name = _name("consume")
    entrypoint = "SKILL.md" if kind == "skill" else "AGENTS.md"
    text = "Read the approved café policy before responding.\n"
    if kind == "skill":
        text = f"---\nname: {name}\ndescription: Use for SDK consumption validation.\n---\n" + text
    files = [
        {"path": entrypoint, "content": text},
        {"path": "references/policy.md", "content": "Approved policy.\n"},
        # Exceed both default page and chunk sizes: the public snapshot clients
        # must continue the original lease, not merely read the resolve page.
        *[{"path": f"references/part-{i:02d}.md", "content": f"Policy part {i}.\n"} for i in range(26)],
        {"path": "references/unicode.md", "content": "雪𠜎 café\n" * 6000},
    ]
    if kind == "skill":
        published = client.skills.publish(files=files, labels=["sdk-live"], acknowledge_warnings=True)
        resource_id, version = published.skill.id, published.version
    else:
        resource_id, version = _publish_context_fixture(client, name, files)
    issue_args = {
        "purpose": "consume",
        "grants": [{"kind": kind, "resource_id": resource_id,
                    "labels": ["sdk-live"] if kind == "skill" else [], "version_ids": [version["id"]]}],
        "binding_ids": [],
        "expires_at": (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat(),
        "idempotency_key": str(uuid.uuid4()),
    }
    issued = client.context_credentials.issue(**issue_args)
    revoked = False
    try:
        assert issued.secret_available and issued.secret
        replay = client.context_credentials.issue(**issue_args)
        assert replay.id == issued.id and replay.secret is None and not replay.secret_available
        metadata = next(item for item in client.context_credentials.list(page_size=1) if item.id == issued.id)
        assert metadata.purpose == "consume" and metadata.grants[0].resource_id == resource_id
        assert "secret" not in metadata.model_dump()
        with fi.Client(base_url=os.environ["FI_BASE_URL"], auth=fi.ContextAuth(issued.secret),
                       strict_responses=True, max_retries=0) as scoped:
            resource = scoped.skill_consumption if kind == "skill" else scoped.contexts
            resolved = resource.resolve(name=name, **({"label": "sdk-live"} if kind == "skill" else {"version": version["number"]}))
            assert (resolved.resource_id, resolved.version_id, resolved.digest) == (resource_id, version["id"], version["digest"])
            assert resolved.resolution_id and resolved.resolution_expires_at
            snapshots = SkillsClient(scoped) if kind == "skill" else ContextClient(scoped)
            snapshot = snapshots.resolve(name, version=version["number"])
            assert snapshot.identity.version_id == resolved.version_id
            if kind == "skill":
                newer = client.skills.publish(
                    files=[{**files[0], "content": text + "New policy revision.\n"}, files[1]],
                    labels=[], acknowledge_warnings=True,
                )
                client.skills.set_label(resource_id, "sdk-live", version=newer.version["number"],
                                        expected_release_revision=newer.release_revision)
                assert resource.resolve(name=name, label="sdk-live").version_id == newer.version["id"]
            # Continuation uses the original lease and version, never re-resolves a label.
            seen = []
            offset = 0
            while True:
                page = resource.manifest(resource_id, resolved.version, resolution_id=resolved.resolution_id,
                                         file_offset=offset, file_limit=1)
                assert (page.version_id, page.digest, page.resolution_id) == (resolved.version_id, resolved.digest, resolved.resolution_id)
                seen.extend(page.files)
                if page.next_file_offset is None:
                    break
                assert offset < page.next_file_offset < page.file_count
                offset = page.next_file_offset
            assert len(seen) == resolved.file_count
            assert len({file.path for file in seen}) == len(seen)
            chunks, offset = [], 0
            while True:
                chunk = resource.read_file(resource_id, resolved.version, path=entrypoint,
                                           resolution_id=resolved.resolution_id, offset=offset, max_bytes=16)
                assert (chunk.version_id, chunk.digest) == (resolved.version_id, resolved.digest)
                chunks.append(chunk.text)
                if chunk.eof:
                    break
                assert offset < chunk.next_offset <= len(text)
                offset = chunk.next_offset
            assert "".join(chunks) == text
            entry = next(file for file in seen if file.path == entrypoint)
            assert entry.sha256 == hashlib.sha256(text.encode()).hexdigest()
            assert entry.size_bytes == len(text.encode())
            access = resource.check_access(resource_id, resolved.version, resolution_id=resolved.resolution_id)
            assert access.allowed and access.version_id == resolved.version_id and access.digest == resolved.digest
            verified = snapshot.read_all()
            expected_files = {item["path"]: item["content"] for item in files}
            assert {path: verified.files[path] for path in expected_files} == expected_files
            assert len(verified.files) == resolved.file_count
            snapshots.check_access(snapshot.identity, snapshot.manifest.lease)

            async def verify_async_snapshot():
                async with fi.AsyncClient(base_url=os.environ["FI_BASE_URL"], auth=fi.ContextAuth(issued.secret),
                                          strict_responses=True, max_retries=0) as async_scoped:
                    async_snapshots = AsyncSkillsClient(async_scoped) if kind == "skill" else AsyncContextClient(async_scoped)
                    async_snapshot = await async_snapshots.resolve(name, version=version["number"])
                    async_verified = await async_snapshot.read_all()
                    assert async_snapshot.identity == snapshot.identity
                    assert dict(async_verified.files) == dict(verified.files)
                    await async_snapshots.check_access(async_snapshot.identity, async_snapshot.manifest.lease)

            asyncio.run(verify_async_snapshot())
            # Consumption credentials cannot enumerate the broader library.
            with pytest.raises(fi.APIError) as denied:
                scoped.skills.list().first_page()
            assert denied.value.status_code in (401, 403)
            client.context_credentials.revoke(issued.id)
            revoked = True
            for continuation in (
                lambda: resource.resolve(name=name, version=resolved.version),
                lambda: resource.manifest(resource_id, resolved.version, resolution_id=resolved.resolution_id),
                lambda: resource.read_file(resource_id, resolved.version, path=entrypoint, resolution_id=resolved.resolution_id),
                lambda: resource.check_access(resource_id, resolved.version, resolution_id=resolved.resolution_id),
                lambda: snapshot.read_file(entrypoint),
                lambda: snapshots.check_access(snapshot.identity, snapshot.manifest.lease),
            ):
                with pytest.raises(fi.APIError) as revoked_error:
                    continuation()
                assert revoked_error.value.status_code in (401, 403)
    finally:
        if not revoked:
            client.context_credentials.revoke(issued.id)


def test_context_catalog_operations_succeeded(client, record_calls):
    """The new lifecycle slice requires success, not just recorded HTTP errors."""
    prefixes = ("contexts.", "skill_consumption.", "context_credentials.", "skills.")
    operations = [entry["id"] for entry in yaml.safe_load(CATALOG.read_text())["operations"]
                  if entry["id"].startswith(prefixes) and entry["surfaces"].get("sdk") is not False]
    missing = [operation for operation in operations if "ok" not in record_calls.get(operation, [])]
    assert not missing, f"context/skill operations without a successful real-backend call: {missing}"


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
