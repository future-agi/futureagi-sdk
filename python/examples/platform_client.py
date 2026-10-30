"""A tour of `fi.Client`: one client for the whole Future AGI platform.

    export FI_API_KEY=... FI_SECRET_KEY=...    # FI_BASE_URL defaults to https://api.futureagi.com
    python examples/platform_client.py

Most of it only reads. It creates one dataset and one dashboard and deletes both at the end.
"""

from __future__ import annotations

import uuid
import warnings

from fi import Client
from fi.platform import APIError, BetaWarning, PaymentRequiredError

warnings.simplefilter("ignore", BetaWarning)  # datasets.rows.add is beta


def section(title: str) -> None:
    print(f"\n== {title}")


with Client() as client:
    section("Who am I")
    me = client.account.whoami()
    print(f"{me.name} <{me.email}>")
    for ws in client.workspaces.list().workspaces:
        print(f"workspace: {ws.name} ({ws.member_count} members)")

    section("Datasets: create, fill, read, delete")
    ds = client.datasets.create(new_dataset_name=f"sdk-example-{uuid.uuid4().hex[:6]}")
    try:
        client.datasets.columns.add(
            ds.dataset_id,
            new_columns_data=[{"name": "question", "data_type": "text"}, {"name": "answer", "data_type": "text"}],
        )
        client.datasets.rows.add(
            ds.dataset_id,
            rows=[
                {"cells": [{"column_name": "question", "value": "What is 2+2?"}, {"column_name": "answer", "value": "4"}]},
                {"cells": [{"column_name": "question", "value": "Capital of France?"}, {"column_name": "answer", "value": "Paris"}]},
            ],
        )
        table = client.datasets.get(ds.dataset_id)
        names = {c.id: c.name for c in table.column_config}
        for row in table.table:
            cells = {names[k]: v["cell_value"] for k, v in row.model_extra.items() if k in names}
            print(f"row {row.order}: {cells}")
    finally:
        client.datasets.delete(dataset_ids=[ds.dataset_id])
        print(f"deleted {ds.dataset_name}")

    print("first datasets in the workspace:", [d.name for d in client.datasets.list().to_list(limit=5)])

    section("Prompts")
    for prompt in client.prompts.list().to_list(limit=5):
        print(f"prompt: {prompt.name}")

    section("Evaluations")
    templates = client.evals.templates.list(page_size=5, owner_filter="system")
    print(f"{templates.total} system eval templates, e.g. {[t.name for t in templates.items]}")

    section("Tracing")
    projects = client.projects.list(page_size=5)["projects"]
    for project in projects:
        print(f"project: {project['name']} ({project.get('trace_count', '?')} traces)")
    if projects:
        traces = client.traces.list(project_id=projects[0]["id"], page_size=3)
        print(f"traces in {projects[0]['name']}: {traces.metadata.total_rows}")

    section("Annotations, experiments, simulation")
    print("annotation queues:", [q.name for q in client.annotation_queues.list().to_list(limit=5)])
    print("experiments:", [e.name for e in client.experiments.list().to_list(limit=5)])
    print("agents:", [a.agent_name for a in client.agents.list().to_list(limit=5)])

    section("Gateway (management API; chat calls go through fi.gateway)")
    for gw in client.gateway.list():
        print(f"gateway: {gw.name} -> {gw.base_url}")
    overview = client.gateway.analytics()
    print(f"requests in the last 24h: {overview['total_requests']['value']}")

    section("Dashboards: create, query, delete")
    metric = next(m for m in client.dashboards.metrics.list(workflow="observability").metrics if m.role == "metric")
    query = {"time_range": {"preset": "7D"}, "metrics": [{"name": metric.name, "type": metric.category, "aggregation": "avg"}]}
    dashboard = client.dashboards.create(name=f"sdk-example-{uuid.uuid4().hex[:6]}")
    try:
        widget = client.dashboards.widgets.create(dashboard.id, name=metric.display_name or metric.name, query_config=query)
        series = client.dashboards.widgets.query(dashboard.id, widget.id).metrics[0].series[0]
        print(f"{metric.name}: {len(series.data)} daily points")
    finally:
        client.dashboards.delete(dashboard.id)
        print(f"deleted dashboard {dashboard.name}")

    section("Typed errors")
    try:
        client.error_clusters.list()
        print("error feed is enabled on this plan")
    except PaymentRequiredError as exc:
        print(f"error feed: {exc}")
    try:
        client.datasets.get(str(uuid.uuid4()))
    except APIError as exc:
        print(f"unknown dataset -> {type(exc).__name__} {exc.status_code} ({exc.type})")
