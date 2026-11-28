"""Every catalog operation, called against a real backend (FI_BASE_URL). No mocks.

The client is strict (`strict_responses=True`), so a response that does not match the
generated models fails the test. A few operations cannot succeed on every install
(a plan-gated feature, a background worker that has not finished, an id that only
exists once traces are indexed); those accept the typed error the backend sends, and
`test_every_operation_was_called` (last in this file) prints what each one returned.
"""

from __future__ import annotations

import asyncio
import decimal
import json
import os
import re
import time
import unicodedata
import uuid
import warnings
from datetime import datetime, timedelta, timezone
from ipaddress import ip_address
from pathlib import Path
from urllib.parse import urlsplit

import fi.platform as fi
import httpx
import pytest
import yaml

CATALOG = Path(__file__).resolve().parents[3] / "sdkgen" / "catalog" / "operations.yaml"
SQL_TOTAL_TIMEOUT = 150.0
SQL_CLEANUP_TIMEOUT = 10.0
TERMINAL_SQL_STATES = {"succeeded", "failed", "cancelled"}

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


# run_debug_failures refuses a run it cannot diagnose with 409 and one of these eligibility codes
# (debug_failures_refusal, product tracer/services/simulation_investigation.py:159-189).
DEBUG_FAILURES_INELIGIBLE = {
    "execution_not_completed",
    "execution_calls_unfinished",
    "investigation_too_few_calls",
    "investigation_nothing_failed",
}


def refused_with(fn, http_status: int, **body) -> fi.APIError:
    """Call fn, which must fail with exactly `http_status` and a JSON body whose listed fields equal `body`.

    Unlike allow(), this proves which view answered: a route the backend lacks gets Django's own
    404 page, never the view's error body."""
    with pytest.raises(fi.APIError) as caught:
        fn()
    error = caught.value
    assert error.status_code == http_status, (error.status_code, error.body)
    assert isinstance(error.body, dict), error.body
    assert {key: error.body.get(key) for key in body} == body, error.body
    return error


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


def _poll_sql_result(get_result, job_id, project_id, *, clock=time.monotonic, sleep=time.sleep):
    # The backend allows 90s queued, then 45s from execution start; allow 15s for transport.
    deadline = clock() + SQL_TOTAL_TIMEOUT
    state = "not polled"
    while (remaining := deadline - clock()) > 0:
        page = get_result(job_id, project_id=project_id, offset=0, limit=1,
                          options=fi.RequestOptions(timeout=remaining, max_retries=0))
        assert page.id == job_id and page.project_id == project_id
        state = page.state
        remaining = deadline - clock()
        if remaining <= 0:
            break
        if state in TERMINAL_SQL_STATES:
            return page
        sleep(min(0.5, remaining))
    raise AssertionError(f"SQL job {job_id} did not finish in 150s: {state}")


def _sql_request_options(deadline, *, clock=time.monotonic):
    remaining = deadline - clock()
    if remaining <= 0:
        raise AssertionError("SQL request deadline exceeded")
    return fi.RequestOptions(timeout=remaining, max_retries=0)


async def _poll_sql_result_async(
    client,
    job_id,
    project_id,
    *,
    clock=time.monotonic,
    sleep=asyncio.sleep,
    deadline=None,
):
    deadline = clock() + SQL_TOTAL_TIMEOUT if deadline is None else deadline
    state = "not polled"
    while (remaining := deadline - clock()) > 0:
        page = await client.sql.get_result(
            job_id,
            project_id=project_id,
            offset=0,
            limit=1,
            options=fi.RequestOptions(timeout=remaining, max_retries=0),
        )
        assert page.id == job_id and page.project_id == project_id
        state = page.state
        remaining = deadline - clock()
        if remaining <= 0:
            break
        if state in TERMINAL_SQL_STATES:
            return page
        await sleep(min(0.5, remaining))
    raise AssertionError(f"SQL async job {job_id} did not finish in 150s: {state}")


def _cancel_sql_job_bounded(client, job_id, project_id, *, timeout=SQL_CLEANUP_TIMEOUT,
                            clock=time.monotonic, sleep=time.sleep):
    deadline = clock() + timeout
    state = "unknown"
    while (remaining := deadline - clock()) > 0:
        result = client.sql.cancel(
            job_id,
            project_id=project_id,
            options=fi.RequestOptions(timeout=remaining, max_retries=0),
        )
        state = result.state
        if state in TERMINAL_SQL_STATES:
            return result
        remaining = deadline - clock()
        if remaining <= 0:
            break
        sleep(min(0.5, remaining))
    raise AssertionError(f"SQL job {job_id} remained {state} after bounded cleanup")


async def _cancel_sql_job_bounded_async(
    client,
    job_id,
    project_id,
    *,
    timeout=SQL_CLEANUP_TIMEOUT,
    clock=time.monotonic,
    sleep=asyncio.sleep,
):
    deadline = clock() + timeout
    state = "unknown"
    while (remaining := deadline - clock()) > 0:
        result = await client.sql.cancel(
            job_id,
            project_id=project_id,
            options=_sql_request_options(deadline, clock=clock),
        )
        state = result.state
        if state in TERMINAL_SQL_STATES:
            return result
        remaining = deadline - clock()
        if remaining <= 0:
            break
        await sleep(min(0.5, remaining))
    raise AssertionError(f"SQL async job {job_id} remained {state} after bounded cleanup")


def _run_with_cleanup_preserving_primary(work, cleanup):
    """Run cleanup without replacing a failure from the operation under test."""
    primary = cleanup_error = None
    result = None
    try:
        result = work()
    except BaseException as exc:
        primary = exc
    try:
        cleanup()
    except BaseException as exc:
        cleanup_error = exc
    if primary is not None:
        if cleanup_error is not None:
            warnings.warn(
                "SQL cleanup failed after the primary failure "
                f"({type(cleanup_error).__name__})",
                RuntimeWarning,
                stacklevel=2,
            )
        raise primary.with_traceback(primary.__traceback__)
    if cleanup_error is not None:
        raise cleanup_error.with_traceback(cleanup_error.__traceback__)
    return result


async def _async_wait_until(predicate, deadline: float, every: float = 0.25) -> bool:
    """Poll an async backend state change without exceeding the caller's deadline."""
    while (remaining := deadline - time.monotonic()) > 0:
        if await predicate():
            return True
        await asyncio.sleep(min(every, remaining))
    return False


async def _run_async_with_cleanup_preserving_primary(work, cleanup):
    """Run async cleanup without replacing a failure from the operation under test."""
    primary = cleanup_error = None
    result = None
    try:
        result = await work()
    except BaseException as exc:
        primary = exc
    try:
        await cleanup()
    except BaseException as exc:
        cleanup_error = exc
    if primary is not None:
        if cleanup_error is not None:
            warnings.warn(
                "SQL cleanup failed after the primary failure "
                f"({type(cleanup_error).__name__})",
                RuntimeWarning,
                stacklevel=2,
            )
        raise primary.with_traceback(primary.__traceback__)
    if cleanup_error is not None:
        raise cleanup_error.with_traceback(cleanup_error.__traceback__)
    return result


def _sql_collector_url(raw, collector_port):
    """Only the standalone API origin may select a credentialed collector on the same loopback host."""
    __tracebackhide__ = True  # pytest must not display a rejected URL containing userinfo
    try:
        base = urlsplit(raw)
        host = base.hostname or ""
        if host != "localhost":
            address = ip_address(host)  # literal only; never resolve a configured hostname
            if not address.is_loopback or "%" in host:
                raise ValueError
            if address.version == 6:
                host = f"[{host}]"
        # Compare the whole input, not just .hostname: reject userinfo, paths,
        # malformed authorities and characters that URL parsers would discard.
        origin = f"{base.scheme}://{host}" + (f":{base.port}" if base.port is not None else "")
        if base.scheme not in {"http", "https"} or base.port == 0 or raw.lower() not in (origin, origin + "/"):
            raise ValueError
    except ValueError:
        raise ValueError("SQL fixture requires an HTTP(S) loopback API origin") from None
    if not re.fullmatch(r"[1-9][0-9]{0,4}", collector_port) or int(collector_port) > 65535:
        raise ValueError("SQL fixture requires a valid collector port")
    return f"{base.scheme}://{host}:{collector_port}/v1/traces"


def _clean_sql_otlp_receipt(body):
    """The released e2e/lib/otlp.ts accepts an empty body or a receipt with no losses or warnings."""
    def invalid_constant(_):  # Python accepts NaN/Infinity by default; JSON.parse does not.
        raise ValueError

    def unique_object(pairs):
        obj = dict(pairs)
        if len(obj) != len(pairs):
            raise ValueError
        return obj

    try:
        text = body.decode("utf-8")
        # String.trim() treats Unicode separators and BOM as whitespace, not arbitrary controls.
        if all(ch in "\t\n\v\f\r\ufeff" or unicodedata.category(ch).startswith("Z") for ch in text):
            return True
        receipt = json.loads(text, object_pairs_hook=unique_object, parse_int=decimal.Decimal,
                             parse_float=decimal.Decimal, parse_constant=invalid_constant)
    except (ValueError, RecursionError, decimal.InvalidOperation):
        return False

    counts = {"rejectedSpans", "rejected_spans"}
    messages = {"errorMessage", "error_message"}
    if not isinstance(receipt, dict) or receipt.keys() - {"partialSuccess", "partial_success"}:
        return False
    for partial in receipt.values():  # both aliases may be present
        if not isinstance(partial, dict) or partial.keys() - (counts | messages):
            return False
        for key, value in partial.items():
            if key in counts:
                zero = isinstance(value, decimal.Decimal) and value.is_zero()
                if not zero and not (isinstance(value, str) and re.fullmatch(r"0+", value)):
                    return False
            elif value != "":
                return False
    return True


def _seed_sql_spans(url, name):
    """Keep the collector exchange out of subsequent project-discovery tracebacks."""
    __tracebackhide__ = True
    trace_id, session_id = uuid.uuid4().hex, str(uuid.uuid4())
    start = time.time_ns() - 1_000_000_000

    def attr(key, value):
        return {"key": key, "value": {"stringValue": value}}

    spans = [
        {"traceId": trace_id, "spanId": uuid.uuid4().hex[:16], "name": f"sql-{role}", "kind": 1,
         "startTimeUnixNano": str(start), "endTimeUnixNano": str(start + 50_000_000), "status": {"code": 1},
         "attributes": [attr("fi.span.kind", "llm"), attr("session.id", session_id)]}
        for role in ("root", "child")
    ]
    spans[1]["parentSpanId"] = spans[0]["spanId"]
    resource = {"attributes": [attr("project_name", name), attr("project_type", "observe"), attr("service.name", name)]}
    payload = {"resourceSpans": [{"resource": resource, "scopeSpans": [{"scope": {"name": "sdk-e2e"}, "spans": spans}]}]}

    with httpx.Client(trust_env=False, follow_redirects=False, timeout=30) as http:
        headers = {"X-Api-Key": os.environ["FI_API_KEY"], "X-Secret-Key": os.environ["FI_SECRET_KEY"]}
        try:
            reply = http.post(url, json=payload, headers=headers)
        except httpx.RequestError:
            reply = None
        if reply is None:  # Don't chain a transport exception into pytest's report.
            pytest.fail("SQL fixture collector request failed", pytrace=False)
        if not reply.is_success:
            pytest.fail(f"SQL fixture collector returned HTTP {reply.status_code}", pytrace=False)
        if not _clean_sql_otlp_receipt(reply.content):
            pytest.fail("SQL fixture collector returned an invalid or partial OTLP receipt", pytrace=False)
    return spans


def _discover_sql_project(client, name):
    def matching_projects():
        try:
            return [p["id"] for p in client.projects.list(name=name)["projects"] if p["name"] == name]
        except fi.FutureAGIError:
            pass  # The SDK error may include a response body; fail outside its exception handler.
        pytest.fail("SQL fixture project lookup failed", pytrace=False)

    assert wait_until(lambda: len(matching_projects()) == 1, timeout=60), "collector project was not created"
    project_id, = matching_projects()
    return project_id


@pytest.fixture
def sql_project(client):
    """Seed ClickHouse via the released standalone collector, as in OBS-E2E-061."""
    __tracebackhide__ = True  # Keep the span payload out of a discovery failure's locals, too.
    url = _sql_collector_url(os.environ["FI_BASE_URL"], os.environ.get("FI_COLLECTOR_OTLP_HTTP_PORT", "24318"))
    name = f"sdk-sql-{uuid.uuid4().hex}"
    spans = _seed_sql_spans(url, name)
    return _discover_sql_project(client, name), name, spans


def test_sql_job_on_synthetic_spans(client, sql_project):
    """Exercise default reuse omission, multiple result pages, and cancellation cleanup."""
    project_id, project_name, spans = sql_project
    assert client.projects.get(project_id).name == project_name
    assert client.sql.get_catalog(project_id=project_id).max_window_days >= 1
    # The ClickHouse list and the SQL scan must see the fixture after async ingestion.
    assert wait_until(lambda: len(client.spans.list(project_id=project_id).table) == len(spans))
    start = datetime.fromtimestamp(int(spans[0]["startTimeUnixNano"]) / 1e9, tz=timezone.utc) - timedelta(minutes=1)
    job = client.sql.run(
        project_id=project_id,
        sql="SELECT name FROM spans ORDER BY name",
        start=start.isoformat(),
        end=datetime.now(timezone.utc).isoformat(),
    )
    assert job.id and job.project_id == project_id
    final = None

    def read_pages():
        nonlocal final
        first = _poll_sql_result(client.sql.get_result, job.id, project_id)
        assert first.state == "succeeded", first.error
        assert first.result.rows and len(first.result.rows) == 1
        assert first.result.has_more is True
        assert first.result.next_offset is not None
        second = client.sql.get_result(
            job.id, project_id=project_id, offset=first.result.next_offset, limit=1
        )
        assert second.state == "succeeded", second.error
        assert second.result.rows and len(second.result.rows) == 1
        assert second.result.has_more is False
        assert {row[0] for row in first.result.rows + second.result.rows} == {f"sql-{role}" for role in ("root", "child")}

    def cleanup():
        nonlocal final
        # Cancelling an already completed job returns its unchanged terminal snapshot.
        final = _cancel_sql_job_bounded(client, job.id, project_id)
        assert final.id == job.id and final.project_id == project_id
        assert final.state == "succeeded"

    _run_with_cleanup_preserving_primary(read_pages, cleanup)

    # A tiny fixture often completes before the cancellation request reaches the API. Do not
    # call that a cancellation proof; the explicit pending path keeps the gate honest.
    active_job = None
    active_job_id = None
    active_state = None

    def active_work():
        nonlocal active_job, active_job_id, active_state
        active_job = client.sql.run(
            project_id=project_id,
            sql="SELECT name FROM spans ORDER BY name",
            start=start.isoformat(),
            end=datetime.now(timezone.utc).isoformat(),
            reuse=False,
            options=fi.RequestOptions(timeout=SQL_TOTAL_TIMEOUT, max_retries=0),
        )
        active_job_id = active_job.id
        active_state = active_job.state
        assert active_job_id and active_job.project_id == project_id
        if active_state in TERMINAL_SQL_STATES:
            pytest.skip(f"pending active SQL cancellation: fixture job was already {active_state}")
        cancelled = client.sql.cancel(
            active_job_id,
            project_id=project_id,
            options=fi.RequestOptions(timeout=SQL_CLEANUP_TIMEOUT, max_retries=0),
        )
        active_state = cancelled.state
        if active_state != "cancelled":
            pytest.skip(f"pending active SQL cancellation: job reached {active_state} before cancel")
        assert cancelled.id == active_job_id and cancelled.project_id == project_id

    def active_cleanup():
        nonlocal active_state
        if active_state in TERMINAL_SQL_STATES:
            return
        if not active_job_id:
            raise AssertionError("owned active SQL job did not return an id")
        final = _cancel_sql_job_bounded(client, active_job_id, project_id)
        active_state = final.state
        assert active_state in TERMINAL_SQL_STATES

    _run_with_cleanup_preserving_primary(active_work, active_cleanup)


def test_sql_job_async_on_synthetic_spans(sql_project):
    """Exercise the real AsyncClient against the same owned fixture used by the sync path."""
    project_id, _, spans = sql_project

    async def run():
        deadline = time.monotonic() + SQL_TOTAL_TIMEOUT
        async with fi.AsyncClient(
            api_key=os.environ["FI_API_KEY"],
            secret_key=os.environ["FI_SECRET_KEY"],
            base_url=os.environ["FI_BASE_URL"],
            strict_responses=True,
        ) as client:
            job = None
            known_state = None

            async def work():
                nonlocal job, known_state
                async def spans_ready():
                    page = await client.spans.list(
                        project_id=project_id,
                        options=_sql_request_options(deadline),
                    )
                    return len(page.table) == len(spans)

                assert await _async_wait_until(spans_ready, deadline), "async fixture spans were not indexed"
                catalog = await client.sql.get_catalog(
                    project_id=project_id,
                    options=_sql_request_options(deadline),
                )
                assert catalog.max_window_days >= 1
                start = datetime.fromtimestamp(
                    int(spans[0]["startTimeUnixNano"]) / 1e9, tz=timezone.utc
                ) - timedelta(minutes=1)
                job = await client.sql.run(
                    project_id=project_id,
                    sql="SELECT count() AS n FROM spans",
                    start=start.isoformat(),
                    end=datetime.now(timezone.utc).isoformat(),
                    options=_sql_request_options(deadline),
                )
                known_state = job.state
                assert job.id and job.project_id == project_id
                page = await _poll_sql_result_async(
                    client, job.id, project_id, deadline=deadline
                )
                known_state = page.state
                assert page.state == "succeeded", page.error
                assert page.result.rows == [[len(spans)]]

            async def cleanup():
                if job is None:
                    return
                if not job.id:
                    raise AssertionError("owned async SQL job did not return an id")
                final = await _cancel_sql_job_bounded_async(
                    client, job.id, project_id
                )
                assert final.id == job.id and final.project_id == project_id
                if known_state == "succeeded":
                    assert final.state == "succeeded"

            await _run_async_with_cleanup_preserving_primary(work, cleanup)

    asyncio.run(run())


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
    # Added in backend v1.58.0 (MCP tools get_error_cluster_overview / list_error_cluster_traces).
    allow(lambda: client.error_clusters.overview(str(uuid.uuid4()), rep_limit=1), 400, 402, 404)
    allow(lambda: client.error_clusters.list_traces(str(uuid.uuid4()), limit=5), 400, 402, 404)


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
    versions = client.agents.versions.list(agent_id).to_list()
    assert sorted(v["version_number"] for v in versions) == [1, 2]
    assert client.agents.versions.get(agent_id, versions[0]["id"])["id"] == versions[0]["id"]
    # A version made from settings has no stored agent document.
    allow(lambda: client.agents.versions.get_definition(agent_id, versions[0]["id"]), 404)
    assert client.agents.runs.list(agent_id).results == []

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
    executions = client.simulation.tests.list_executions(test.id).to_list()
    assert not execution or execution.execution_id in [e.id for e in executions]
    # Empty lists are refused before anything is created (no judge credits).
    allow(lambda: client.simulation.tests.add_eval_configs(test.id, evaluations_config=[]), 400)
    allow(lambda: client.simulation.executions.list_calls(execution_id).first_page(), 404)
    # Debug failures (MCP get_debug_failures / run_debug_failures). Product 2aa9ca3,
    # simulate/views/debug_analysis.py: a run never analysed reads not_requested. Start answers
    # 202 (pending while its jobs wait for the Error Feed worker, which a standalone stack does not
    # run) only for a finished run with at least 15 connected calls and a failing call; any other
    # run is refused with 409 and one of the eligibility codes in
    # tracer/services/simulation_investigation.py:159-189. An unknown run is a 404 in the product's
    # error envelope {status: false, ...}, where a missing route would get Django's 404 page.
    insights = client.simulation.executions.insights
    if execution:
        state = insights.get(execution_id)
        assert (state.test_execution_id, state.status) == (execution_id, "not_requested")
        try:
            started = insights.start(execution_id)
        except fi.ConflictError as conflict:
            assert conflict.code in DEBUG_FAILURES_INELIGIBLE, conflict.body
            print(f"run_debug_failures refused: {conflict.code}")
        else:
            assert started.status == "pending" and insights.get(execution_id).status == "pending"
            print("run_debug_failures accepted: pending")
    else:
        refused_with(lambda: insights.get(execution_id), 404, status=False)
        refused_with(lambda: insights.start(execution_id), 404, status=False)
    allow(lambda: client.simulation.executions.rerun_calls(execution_id, rerun_type="eval_only", call_execution_ids=[str(uuid.uuid4())]), 400, 404)
    allow(lambda: client.simulation.calls.get(str(uuid.uuid4())), 404)


def test_simulation_personas(client, request):
    """Workspace personas: the whole write path, cleaned up through client.request (the SDK
    deliberately exposes no delete)."""
    name = _name("persona")
    persona = client.simulation.personas.create(name=name, description="A patient caller")
    request.addfinalizer(lambda: allow(lambda: client.request("DELETE", f"/simulate/api/personas/{persona.id}/"), 404))
    assert persona.persona_type == "workspace"
    assert client.simulation.personas.get(persona.id).name == name
    assert client.simulation.personas.update(persona.id, name=name, description="updated").description == "updated"
    copy = client.simulation.personas.duplicate(persona.id, name=f"{name}-copy")
    request.addfinalizer(lambda: allow(lambda: client.request("DELETE", f"/simulate/api/personas/{copy.id}/"), 404))
    assert copy.id != persona.id and copy.description == "updated"
    assert {name, f"{name}-copy"} <= {p["name"] for p in client.simulation.personas.list(search=name)}


def test_simulation_environments_and_jobs(client):
    """The environment-era surface (the CLI's `fi sim`). Building an environment runs a builder
    agent and spends credits, so a fresh stack has none: every per-environment call is made
    against an id that does not exist, which still proves the route, the method, the body and
    the typed error. Builder writes get invalid bodies that the server refuses before creating
    anything."""
    assert isinstance(client.simulation.environments.list().first_page().items, list)
    env, other = str(uuid.uuid4()), str(uuid.uuid4())
    environments = client.simulation.environments
    for call in (
        lambda: environments.get(env),
        lambda: environments.rename(env, name="renamed"),
        lambda: environments.run_plan(env),
        lambda: environments.run(env, scenario_ids=["1"]),
        lambda: environments.versions.list(env),
        lambda: environments.versions.suite_members(env, other),
        lambda: environments.versions.create_agent(env, prompt="You are a support agent."),
        lambda: environments.versions.retry_agent(env, other),
        lambda: environments.versions.set_default(env, "agent", other, expected_default_id=None),
        lambda: environments.versions.diff(env, "agent", other),
        lambda: environments.drafts.list(env),
        lambda: environments.drafts.save(env, drafts=[{"piece": "suite", "expected_parent_id": None}], idempotency_key="sdk-live"),
        lambda: environments.nudges.list(env),
        lambda: environments.nudges.answer(env, other, answer="no"),
        lambda: environments.nudges.stop(env, other),
        lambda: environments.evaluations.available(env),
        lambda: environments.evaluations.add(env, name="task_completion"),
        lambda: environments.evaluations.update(env, other, model="turing_large"),
        lambda: environments.evaluations.set_tool_call(env, enable_tool_evaluation=True),
        lambda: environments.runs.add_evaluation(env, other, name="task_completion"),
        lambda: environments.runs.regrade(env, other, eval_config_ids=[other]),
    ):
        with pytest.raises(fi.NotFoundError):
            call()

    jobs = client.simulation.jobs
    for call in (
        lambda: jobs.get(env),
        lambda: jobs.send_message(env, content="Docker", client_request_id="sdk-live"),
        lambda: jobs.adjust(env, instruction="Add a refund scenario."),
        lambda: jobs.extend(env, count=1),
        lambda: jobs.cancel(env),
        lambda: jobs.scenarios.list(env),
    ):
        with pytest.raises(fi.NotFoundError):
            call()
    for call in (
        lambda: jobs.create(agent={}, artifacts={}),  # connector and level are required
        lambda: jobs.preflight(agent={}, artifacts={}),
        lambda: jobs.set_secret_values(environment_id=env, environment_values={}),
        lambda: jobs.scenarios.amend(env, changes=[]),
    ):
        with pytest.raises(fi.BadRequestError):
            call()
    # Actors, scenario checks and lifecycle, readiness and a trial's workers, against ids that do not exist. A backend
    # release without these routes answers 404 too, which still proves the method, path and body the SDK sends.
    refused = (400, 404, 405, 409, 422)
    for call in (
        lambda: environments.actors.list(env),
        lambda: environments.actors.get(env, "caller"),
        lambda: environments.actors.validate(env, op="delete", actor_id="caller"),
        lambda: environments.actors.create(env, actor={"name": "Dispatcher"}, new_id="dispatcher"),
        lambda: environments.actors.update(env, "caller", changes={"goal": "Book a ride"}),
        lambda: environments.actors.delete(env, "caller", expected_revision=1),
        lambda: environments.actors.set_limits(env, limits={"per_scenario": 2}, expected_revision=1),
        lambda: environments.actors.accept_unresolved(env, policy="keep", expected_revision=1),
        lambda: environments.versions.source_changes(env, other),
        lambda: environments.scenarios.validate(env, keys=["refund-flow"]),
        lambda: environments.scenarios.validation_status(env, job_id=other),
        lambda: environments.scenarios.running_validation(env),
        lambda: environments.scenarios.archive(env, "refund-flow", reason="duplicate"),
        lambda: environments.scenarios.restore(env, "refund-flow"),
        lambda: environments.scenarios.records(env, "refund-flow", table="bookings"),
        lambda: environments.scenarios.revisions(env, "refund-flow"),
        lambda: environments.drafts.review(env),
        lambda: environments.drafts.validate(env, expected_revisions={"environment": 0}, expected_review_digest="sdk-live"),
        lambda: environments.readiness.get(env),
        lambda: environments.readiness.get_for_scenarios(env, scenario_ids=["refund-flow"]),
        lambda: environments.readiness.cases(env, bucket="blocked"),
        lambda: environments.readiness.recheck(env),
        lambda: environments.readiness.history(env),
        lambda: client.simulation.calls.workers(other),
    ):
        allow(call, *refused)
    staged = jobs.upload_sources(files=[("agent/main.py", b"print('hi')\n"), ("README.md", b"# agent\n")], paths=["agent/main.py", "README.md"], name=_name("source"))
    assert staged.source_id and staged.file_count == 2  # both repeated form fields arrived
    # Only a GOOGLE_APPLICATION_CREDENTIALS service-account JSON is accepted today.
    with pytest.raises(fi.APIError) as refused:
        jobs.upload_secret_file(file=("creds.json", b"{}"), environment_name="NOT_A_SUPPORTED_NAME")
    assert refused.value.status_code in (400, 422)


def test_evidence_imports_and_epochs(client):
    """Evidence imports and Epoch (the product's MCP group `epoch`), against the views of product
    2dcb8dc. A fresh standalone stack has no environment: the product makes one only through a
    builder build, which needs the simulation runner and a sandbox that the stack does not start
    (product e2e/lib/environment-seed.ts seeds one through internal services instead). So it has no
    environment run to launch an Epoch from, and no Epoch or candidate either. Every call names
    ids that do not exist and asserts the refusal body of the view that answers it:

    - evidence imports: HarnessEnvironmentViewSet._not_found, 404 {"detail": "Environment not
      found"} (simulate/views/harness_environment.py:329-333; create 921, list 985, get 1005,
      discard 1022, draft 1048 and add 1084, the last two after require_versioning, which the
      standalone overlay enables with HARNESS_VERSIONING_ENABLED);
    - Epochs and candidates: agent_fix._not_found, 404 {"error": "not_found", "message": "Not
      found"} (simulate/views/agent_fix.py:96-99, HostedHarnessError.as_dict in
      simulate/services/hosted_harness.py:115-121; list 154, launch_options 183, launch 202,
      get 226, retry 239, stop 254, make_default 283, open_pull_request 306, patch 332). These
      views first check the fix_my_agent entitlement (AgentFixRunViewSet.initial, 112-116; a
      denial is a 402 entitlement_error from accounts/authentication.py custom_exception_handler),
      so this body also shows the entitlement allowed. It is on a self-hosted stack:
      fix_my_agent requires a licence but is not oss_locked (tfc/capabilities/registry.py:195-201),
      and self-hosted allows every such feature (tfc/capabilities/service.py:156-161), unlike
      instant_eval and insights, which are oss_locked;
    - a coding agent's brief and attempt verdict (product 2aa9ca3): the same 404 body, but from
      AgentFixRunViewSet.initial before the entitlement check, because the stack leaves
      AGENT_FIX_OUTSIDE_ATTEMPTS_ENABLED off (simulate/views/agent_fix.py:143-148,
      tfc/settings/settings.py:1166-1170). Their 404 says nothing about the entitlement.

    Request bodies are valid, so the serializer passes and the view itself refuses."""
    env, import_id, run, candidate = (str(uuid.uuid4()) for _ in range(4))
    imports = client.simulation.environments.evidence_imports
    transcript = [{"name": "refund.txt", "format": "text", "text": "User: I want a refund.\nAgent: Done."}]
    expected_drafts = {"environment": {"id": None, "revision": 0}, "suite": {"id": None, "revision": 0}}
    for call in (
        lambda: imports.list(env),
        lambda: imports.create(env, source_kind="transcript", transcripts=transcript),
        lambda: imports.get(env, import_id),
        lambda: imports.draft(env, import_id, case_ids=[candidate]),
        lambda: imports.add_cases(env, import_id, case_ids=[candidate], expected_drafts=expected_drafts, idempotency_key=_name("add")),
        lambda: imports.discard(env, import_id),
    ):
        refused_with(call, 404, detail="Environment not found")

    epochs = client.simulation.epochs
    for call in (
        lambda: epochs.list(environment_id=env, limit=1).first_page(),
        lambda: epochs.launch_options(source_run_id=run),
        lambda: epochs.coding_agent_brief(source_run_id=run),
        lambda: epochs.attempt_verdict(run),
        lambda: epochs.launch(source_run_id=run, target_scenario_keys=["scenario-1"], surfaces=["prompt"], budget_credits=1),
        lambda: epochs.get(run),
        lambda: epochs.stop(run),
        lambda: epochs.retry(run),
        lambda: epochs.candidates.patch(run, candidate),
        lambda: epochs.candidates.make_default(run, candidate),
        lambda: epochs.candidates.open_pull_request(run, candidate),
    ):
        refused_with(call, 404, error="not_found", message="Not found")
    # Shipping a candidate its checks refused is a person's decision, made in Future AGI: an
    # override_reason sent with an API key is refused before the candidate is looked up
    # (AgentFixRunViewSet._override_reason, simulate/views/agent_fix.py:403-414 at 2aa9ca3).
    for call in (
        lambda: epochs.candidates.make_default(run, candidate, override_reason="sdk live test"),
        lambda: epochs.candidates.open_pull_request(run, candidate, override_reason="sdk live test"),
    ):
        refused_with(call, 403, error="fix_override_needs_person")


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
