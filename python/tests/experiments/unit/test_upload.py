"""A5: uploaded runs against the contract stand-in (``contract_server.py``; read its PROVENANCE:
derived from the backend code and the SDK's OpenAPI spec, NOT recorded from a server).

No network, no model: every request goes to an httpx.MockTransport.
"""

import json

import pytest

from fi import experiments
from fi.experiments import _upload
from fi.experiments._journal import load as load_journal
from fi.experiments._upload import UploadConflictError, UploadStalledError, bounded, project_item
from tests.experiments.unit.contract_server import ContractServer, client_for

ROWS = [
    {"question": "where is order 1?", "expected": "shipped"},
    {"question": "where is order 2?", "expected": "lost"},
    {"question": "where is order 3?", "expected": "shipped"},
]


NAMED = experiments.dataset(ROWS, name="support-rows")  # inline rows on an uploaded run need a name


def task(row):
    return "shipped"


def correct(output, expected) -> bool:
    return output == expected


def _run(server, dataset=NAMED, evaluators=(correct,), **kw):
    kw.setdefault("trace", False)
    kw.setdefault("progress", False)
    if isinstance(dataset, list):  # inline rows on an uploaded run need a name
        dataset = experiments.dataset(dataset, name=kw.pop("dataset_name", "support-rows"))
    return experiments.run(dataset, kw.pop("task", task), list(evaluators), client=client_for(server), **kw)


def test_local_rows_upload_end_to_end():
    server = ContractServer()
    result = _run(server)
    assert result.status == "completed"
    [ds] = server.datasets.values()
    assert ds["name"] == "support-rows" and len(ds["versions"]) == 1
    [run] = server.runs.values()
    assert len(run["body"]["expected_items"]) == 3 and len(run["items"]) == 3
    [metric_id] = run["body"]["evaluator_metric_ids"]
    assert server.metrics[metric_id]["kind"] == "external"
    values = sorted(ref["value"] for it in run["items"].values() for ref in it["score_refs"])
    assert values == [0.0, 1.0, 1.0]
    assert result.dataset_version_id == ds["versions"][0]["id"]
    journal = load_journal(result.run_id)
    assert all(rec.acked for rec in journal.records.values())
    assert journal.plan["upload_session"]["create_body"] == run["body"]


def test_unchanged_rows_reuse_the_version_and_a_changed_row_snapshots_with_its_parent():
    server = ContractServer()
    first = _run(server)
    second = _run(server)
    [ds] = server.datasets.values()
    assert len(ds["versions"]) == 1 and first.dataset_version_id == second.dataset_version_id
    rows = [dict(r, id=f"T{i}") for i, r in enumerate(ROWS)]
    a = _run(server, dataset=rows, dataset_name="support-ids")
    rows[1]["expected"] = "found"
    b = _run(server, dataset=rows, dataset_name="support-ids")
    versions = [d for d in server.datasets.values() if len(d["versions"]) == 2][0]["versions"]
    assert versions[1]["parent_version"] == versions[0]["id"] == a.dataset_version_id
    assert b.dataset_version_id == versions[1]["id"]
    ids_a = {i.example_id for i in a.items}
    ids_b = {i.example_id for i in b.items}
    assert ids_a == ids_b  # rows keep their example ids across versions (external_id inheritance)


def test_server_dataset_by_name_snapshots_its_data_columns_only(capsys):
    server = ContractServer()
    server.add_dataset("Support tickets", ROWS)
    seen = []

    def spy(row):
        seen.append(dict(row.inputs))
        return "shipped"

    result = _run(server, dataset="Support tickets", task=spy, progress=True)
    assert result.status == "completed"
    assert all(set(s) == {"question"} for s in seen)  # the evaluation column is not an input
    items = server.datasets[result.dataset_id]["versions"][0]["items"]
    assert all(it["legacy_row"] for it in items)
    err = capsys.readouterr().err
    assert "snapshotted version" in err
    assert "Upload   3 items stored in 1 batch(es)" in err and "is completed on the server" in err


def test_version_pin_reads_that_version_and_creates_nothing():
    server = ContractServer()
    first = _run(server, dataset=NAMED)
    posts = server.count("POST", r"/model-hub/datasets/.*/versions/")
    pinned = _run(server, dataset=first.dataset_id, version=first.dataset_version_id)
    assert server.count("POST", r"/model-hub/datasets/.*/versions/") == posts
    assert {i.example_id for i in pinned.items} == {i.example_id for i in first.items}


def test_unknown_dataset_name_is_one_clear_error():
    server = ContractServer()
    with pytest.raises(experiments.errors.DatasetNotFoundError):
        _run(server, dataset="Nope")


def test_ingest_retries_through_503s_without_duplicates(monkeypatch):
    monkeypatch.setattr(_upload, "BACKOFF_S", (0.01,))
    server = ContractServer()
    server.fail_ingest = [503, 502]
    result = _run(server)
    [run] = server.runs.values()
    assert result.status == "completed" and len(run["items"]) == 3
    assert result.metadata["upload"]["retries"] == 2


def test_stalled_upload_then_resume_resends_only_unacked(monkeypatch):
    monkeypatch.setattr(_upload, "BACKOFF_S", (0.01,))
    monkeypatch.setattr(_upload, "GIVE_UP_S", 0.0)
    server = ContractServer()
    server.fail_ingest = [503]
    with pytest.raises(UploadStalledError) as info:
        _run(server)
    assert info.value.exit_code == 3
    [run_id] = server.runs
    assert server.runs[run_id]["items"] == {}
    calls = []
    result = _run(server, task=lambda row: calls.append(row) or "shipped", resume=run_id)
    assert calls == []  # every trial was already journaled: nothing re-runs
    assert len(server.runs[run_id]["items"]) == 3 and result.status == "completed"
    assert server.count("POST", r"/model-hub/experiment-runs/") == 2  # the create was replayed, same body


def test_conflicting_result_stops_the_run_with_exit_3(monkeypatch):
    server = ContractServer()
    first = _run(server)
    journal_path = load_journal(first.run_id)
    # the server already holds these identities; a different payload under the same run is a 409
    run = server.runs[first.run_id]
    some = next(iter(run["items"].values()))
    some["_payload"] = {**some["_payload"], "output": "edited"}
    from fi.experiments._upload import Uploader
    from fi.experiments.evaluators.binding import bindings_from_plan

    bindings = bindings_from_plan(journal_path.plan["upload_session"]["bindings"])
    import asyncio

    async def go():
        up = Uploader(client_for(server), first.run_id, bindings, on_ack=lambda r: None)
        up.start()
        for rec in journal_path.records.values():
            up.submit(rec.receipt_key, rec.item_bytes)
        await up.close()

    with pytest.raises(UploadConflictError) as info:
        asyncio.run(go())
    assert info.value.exit_code == 3


def test_experiment_id_and_metadata_reach_the_create_body():
    server = ContractServer()
    _run(server, experiment="7d8b1d7e-6a3c-4f4f-9c0e-6e2b0d6b1a11", name="r1", metadata={"api_key": "sk-123456789"})
    [run] = server.runs.values()
    body = run["body"]
    assert body["experiment_id"] == "7d8b1d7e-6a3c-4f4f-9c0e-6e2b0d6b1a11"
    assert body["metadata"]["name"] == "r1" and body["metadata"]["api_key"] == "[redacted]"


def test_experiment_without_upload_is_refused():
    with pytest.raises(experiments.errors.UsageError):
        experiments.run(NAMED, task, experiment="x", upload=False, trace=False, progress=False)


def test_no_keys_names_upload_false(monkeypatch):
    with pytest.raises(Exception) as info:
        experiments.run(NAMED, task, trace=False, progress=False)
    assert "upload=False" in str(info.value)


def test_template_metric_is_created_once_and_found_by_name_after():
    from tests.experiments.unit.test_hosted_mapping import FIXTURE

    server = ContractServer()
    original = server.__call__

    def handler(request):
        if request.url.path == "/sdk/api/v1/get-evals/":
            import httpx

            return httpx.Response(200, json=FIXTURE["response"])
        if request.url.path == "/sdk/api/v1/new-eval/":
            import httpx

            return httpx.Response(200, json={"result": [{"evaluations": [{"output": "Passed", "reason": "ok"}]}]})
        return original(request)

    from fi.futureagi_client import FutureAGIClient
    import httpx

    def client():
        c = FutureAGIClient(api_key="k-test-1234", secret_key="s-test-1234", base_url="http://srv.test")
        c.generated_client.get_httpx_client()._transport = httpx.MockTransport(handler)
        return c

    for _ in range(2):
        experiments.run(NAMED, task, ["is_json"], client=client(), trace=False, progress=False)
    assert server.count("POST", r"/model-hub/develops/.*/add_user_eval/") == 1
    run_bodies = [r["body"] for r in server.runs.values()]
    assert run_bodies[0]["evaluator_metric_ids"] == run_bodies[1]["evaluator_metric_ids"]


def test_projection_truncates_large_values_and_keeps_the_journal_whole():
    big = "x" * 300_000
    item = {"example_id": "e", "trial_number": 1, "status": "completed", "output": big, "scores": {}}
    data = json.dumps(item).encode()
    out = project_item(data, "r", {})
    assert out["output"]["fi_truncated"] is True and out["output"]["bytes"] > 262_144
    assert len(json.dumps(out["output"]).encode()) < 262_144
    assert bounded("small") == "small"
    assert project_item(data, "r", {}) == out  # deterministic: a replay sends identical bytes


def test_score_refs_map_status_and_bool_scores():
    from fi.experiments._upload import score_ref

    assert score_ref({"status": "skipped"}, "m", "v")["status"] == "not_assessed"
    assert score_ref({"value": None, "passed": True}, "m", "v")["value"] == 1.0
    assert score_ref({"status": "error", "value": 0.4}, "m", "v")["value"] is None


def test_srv3_wrappers_send_the_documented_routes():
    server = ContractServer()
    first = _run(server)
    client = client_for(server)
    header = client.experiment_runs.get(first.run_id)["result"]
    assert header["plan_size"] == 3 and header["item_counts"]["completed"] == 3
    page = client.experiment_runs.list_items(first.run_id, status="completed", limit=2)["result"]
    assert len(page["items"]) == 2 and page["has_more"] is True
    method, path, _ = server.requests[-1]
    assert path.endswith(f"/experiment-runs/{first.run_id}/items/")


def test_uploaded_spans_are_scrubbed_and_carry_the_run(monkeypatch):
    """trace=True with upload: the run's provider exports through ScrubbingExporter (an in-memory
    exporter stands in for traceAI's OTLP exporter, so nothing leaves the process)."""
    pytest.importorskip("opentelemetry.sdk")  # absent on Python 3.14 until TA-1
    from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

    from fi.experiments._tracing.export import exporter_factory
    from fi.experiments._upload_session import UploadSession

    mem = InMemorySpanExporter()

    def factory(self, **kw):
        creds = self.client.auth
        return exporter_factory(base_url=self.base_url, api_key=creds.api_key, secret_key=creds.secret_key,
                                inner=mem, **kw)

    monkeypatch.setattr(UploadSession, "exporter_factory", factory)
    monkeypatch.setenv("OPENAI_API_KEY", "sk-supersecret-123456")

    def leaky(row, ctx):
        ctx.span.set_attribute("note", "key is sk-supersecret-123456")
        ctx.span.set_attribute("http.request.header.authorization", "Bearer abc")
        ctx.span.set_attribute("gen_ai.usage.input_tokens", 12)
        return "shipped"

    server = ContractServer()
    result = _run(server, task=leaky, trace=True, instrument=False)
    roots = [s for s in mem.get_finished_spans() if s.name == "experiment.trial"]
    assert len(roots) == 3
    assert {s.attributes["fi.experiment.run_id"] for s in roots} == {result.run_id}
    assert {s.attributes["fi.dataset.version_id"] for s in roots} == {result.dataset_version_id}
    dumped = json.dumps([dict(s.attributes) for s in mem.get_finished_spans()], default=str)
    assert "sk-supersecret" not in dumped
    assert roots[0].attributes["http.request.header.authorization"] == "[redacted]"
    assert roots[0].attributes["gen_ai.usage.input_tokens"] == 12
    assert roots[0].resource.attributes["project_version_id"] == result.run_id
    traced = {it["trace_id"] for it in server.runs[result.run_id]["items"].values()}
    assert traced == {format(s.context.trace_id, "032x") for s in roots}


def test_collector_endpoint_is_the_run_server():
    pytest.importorskip("opentelemetry.sdk")  # the export module needs it (absent on 3.14, TA-1)
    from fi.experiments._tracing.export import collector_endpoint

    assert collector_endpoint("http://127.0.0.1:18000/") == "http://127.0.0.1:18000/tracer/v1/traces"


# ---- log_results / futureagi-py upload FILE --------------------------------------------------------


def test_log_results_stores_exactly_the_recorded_identities(tmp_path):
    server = ContractServer()
    rows = [dict(r, id=f"T{i}") for i, r in enumerate(ROWS)]
    results = [
        {"id": "T0", "output": "shipped", "latency_ms": 12.5, "cost_usd": 0.001, "scores": {"human": True}},
        {"id": "T2", "trial": 2, "output": "lost", "scores": {"human": {"value": 0.0, "explanation": "wrong"}}},
        {"number": 2, "error": {"type": "Timeout", "message": "took too long"}},
    ]
    result = experiments.log_results(experiments.dataset(rows, name="support-rows"), results, [correct],
                                     client=client_for(server), progress=False)
    [run] = server.runs.values()
    idents = sorted((e["example_id"], e["trial_number"]) for e in run["body"]["expected_items"])
    assert len(idents) == 3 and result.status == "completed"
    stored = {(i["example_id"], i["trial_number"]): i for i in run["items"].values()}
    by_status = sorted(i["status"] for i in stored.values())
    assert by_status == ["completed", "completed", "failed"]
    failed = next(i for i in stored.values() if i["status"] == "failed")
    assert failed["error"]["type"] == "Timeout"
    first = next(i for i in stored.values() if i["latency_ms"] == 12.5)
    assert first["cost"] == 0.001
    names = {server.metrics[m]["name"] for m in run["body"]["evaluator_metric_ids"]}
    assert names == {"correct", "human"}


def test_log_results_names_unknown_rows():
    server = ContractServer()
    with pytest.raises(experiments.errors.UsageError, match="rows the dataset does not have"):
        experiments.log_results(NAMED, [{"number": 9, "output": "x"}], client=client_for(server), progress=False)


def test_upload_command_reads_a_results_file(tmp_path, monkeypatch):
    import argparse

    from fi.experiments._cli import upload as upload_cli

    server = ContractServer()
    rows_path = tmp_path / "support.jsonl"
    rows_path.write_text("\n".join(json.dumps(dict(r, id=f"T{i}")) for i, r in enumerate(ROWS)))
    res_path = tmp_path / "results.jsonl"
    res_path.write_text(json.dumps({"id": "T1", "output": "lost"}) + "\n")
    import fi.experiments._log_results as lr

    real = lr.log_results
    monkeypatch.setattr(lr, "log_results", lambda *a, **k: real(*a, client=client_for(server), **k))
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers()
    upload_cli.register_upload(sub, "x")
    args = parser.parse_args(["upload", str(res_path), "--dataset", str(rows_path), "--dataset-name", "support", "--json",
                              "--no-env-file"])
    assert args.func(args) == 0
    [run] = server.runs.values()
    assert len(run["items"]) == 1
    [ds] = server.datasets.values()
    assert ds["name"] == "support"


def test_failed_rows_come_from_the_server_when_this_machine_has_no_journal(tmp_path, monkeypatch):
    server = ContractServer()

    def flaky(row):
        if "2" in row["question"]:
            raise RuntimeError("tool returned 500")
        return "shipped"

    first = _run(server, task=flaky)
    monkeypatch.setenv("FI_RUN_DIR", str(tmp_path / "another-machine"))
    seen = []
    retry = _run(server, task=lambda row: seen.append(row["question"]) or "shipped",
                 rows=experiments.failed(first.run_id))
    assert seen == ["where is order 2?"]
    assert server.count("GET", rf"/model-hub/experiment-runs/{first.run_id}/") == 1
    assert len(retry.items) == 1


def test_a_server_without_srv3_or_srv5_says_which_feature_is_missing(monkeypatch):
    import httpx

    server = ContractServer()
    first = _run(server)

    def old_server(request):  # the published image: no SRV-3 / SRV-5 routes, the web server's own 404
        if "external-metrics" in request.url.path or request.url.path.endswith(f"/experiment-runs/{first.run_id}/"):
            return httpx.Response(404, text="<h1>Not Found</h1>", headers={"content-type": "text/html"})
        return server(request)

    from fi.futureagi_client import FutureAGIClient

    c = FutureAGIClient(api_key="k-test-1234", secret_key="s-test-1234", base_url="http://srv.test")
    c.generated_client.get_httpx_client()._transport = httpx.MockTransport(old_server)
    with pytest.raises(experiments.errors.NotSupportedByServerError, match="SRV-5"):
        experiments.run(NAMED, task, [correct], client=c, trace=False, progress=False)
    monkeypatch.setenv("FI_RUN_DIR", "/nonexistent-run-dir-for-test")
    with pytest.raises(experiments.errors.NotSupportedByServerError, match="SRV-3"):
        experiments.run(NAMED, task, client=c, rows=experiments.failed(first.run_id), trace=False, progress=False)


def test_a_bad_task_is_refused_before_any_request():
    server = ContractServer()
    with pytest.raises(experiments.errors.UsageError):
        _run(server, task=lambda row, ctx, extra: 1)
    assert server.requests == []


def test_an_fi_datasets_dataset_object_is_used_by_its_id():
    server = ContractServer()
    did = server.add_dataset("Support tickets", ROWS)

    class Config:
        id = did
        name = "Support tickets"

    class Dataset:  # the shape of fi.datasets.Dataset: a dataset_config with id and name
        dataset_config = Config()

    result = _run(server, dataset=Dataset())
    assert result.dataset_id == did and server.count("GET", r"/model-hub/develops/get-datasets-names/") == 0


def test_two_datasets_with_one_name_is_ambiguous():
    server = ContractServer()
    server.add_dataset("Twins", ROWS)
    server.add_dataset("Twins", ROWS)
    with pytest.raises(experiments.errors.AmbiguousDatasetError):
        _run(server, dataset="Twins")


def test_batches_hold_at_most_100_items_and_2_mib():
    import asyncio
    import uuid

    from fi.experiments._upload import BATCH_MAX_BYTES, Uploader

    def item(i, size):
        data = json.dumps({"example_id": f"00000000-0000-4000-8000-{i:012d}", "trial_number": 1,
                           "status": "completed", "output": "x" * size, "scores": {}}).encode()
        return f"r{i}", data

    async def go(items):
        """Every item through a real Uploader and the platform client to a run the stand-in holds; the batches sent."""
        server = ContractServer()
        run_id = str(uuid.uuid4())
        plan = [{"example_id": json.loads(data)["example_id"], "trial_number": 1} for _, data in items]
        body = {"run_id": run_id, "dataset_version_id": str(uuid.uuid4()), "expected_items": plan,
                "evaluator_metric_ids": [], "model_config": {}, "metadata": {}}
        server.runs[run_id] = {"body": body, "items": {}}
        up = Uploader(client_for(server), run_id, {}, on_ack=lambda r: None)
        up.start()
        for receipt, data in items:
            up.submit(receipt, data)
        stats = await up.close()
        return stats, [body["items"] for method, _, body in server.requests if method == "POST"]

    stats, sent = asyncio.run(go([item(i, 10) for i in range(250)]))
    assert stats.acked == 250 and max(len(b) for b in sent) <= 100
    _, sent = asyncio.run(go([item(i, 200_000) for i in range(30)]))  # each ~200 KB: about 10 per batch
    assert all(len(json.dumps({"items": b}).encode()) <= BATCH_MAX_BYTES + 4096 for b in sent) and len(sent) >= 3
