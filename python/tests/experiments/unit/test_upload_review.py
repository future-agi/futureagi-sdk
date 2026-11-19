"""L-SDK wave-1 review fixes (reports/L-SDK-w1-review.md M1, M2, M4, M5 and the should-fix items),
against the contract stand-in (``contract_server.py``: derived from the backend code @ the recorded revision,
NOT recorded). Each stand-in rule a test leans on is copied from the backend, not from the SDK.

No network, no model: every request goes to an httpx.MockTransport.
"""

import json
import shlex
import sys

import httpx
import pytest

from fi import experiments
from fi.experiments import _upload
from fi.experiments._journal import load as load_journal
from fi.experiments._server_dataset import DatasetChangedError, item_content_hash
from fi.experiments._upload import UploadStalledError
from fi.experiments.errors import JournalError, NotSupportedByServerError, UsageError
from tests.experiments.unit.contract_server import ContractServer, client_for, item_hash

ROWS = [
    {"id": "T0", "question": "where is order 1?", "expected": "shipped"},
    {"id": "T1", "question": "where is order 2?", "expected": "lost"},
    {"id": "T2", "question": "where is order 3?", "expected": "shipped"},
]


def task(row):
    return "shipped"


def correct(output, expected) -> bool:
    return output == expected


def _run(server, dataset=ROWS, evaluators=(correct,), **kw):
    kw.setdefault("trace", False)
    kw.setdefault("progress", False)
    if isinstance(dataset, list):  # inline rows on an uploaded run need a name
        dataset = experiments.dataset(dataset, name=kw.pop("dataset_name", "support-rows"))
    return experiments.run(dataset, kw.pop("task", task), list(evaluators), client=client_for(server), **kw)


def _stall(monkeypatch, server, **kw):
    """Run until the upload gives up (one 503, no patience): every trial journaled, nothing acked."""
    monkeypatch.setattr(_upload, "BACKOFF_S", (0.01,))
    monkeypatch.setattr(_upload, "GIVE_UP_S", 0.0)
    server.fail_ingest = [503]
    with pytest.raises(UploadStalledError):
        _run(server, **kw)
    [run_id] = [r for r in server.runs if not server.runs[r]["items"]]
    monkeypatch.setattr(_upload, "GIVE_UP_S", 300.0)
    return run_id


def _version_posts(server):
    return server.count("POST", r"/model-hub/datasets/.*/versions/")


# ---- M1: the content hash normalises integral floats as the server does -------------------------


@pytest.mark.parametrize("raw, server_value", [(2.0, 2), (1e20, 100000000000000000000), (-0.0, 0), (10.0, 10)])
def test_integral_floats_hash_as_the_server_stores_them(raw, server_value):
    ours = item_content_hash({"price": raw}, [raw, 2.5], {"weight": raw})
    assert ours == item_content_hash({"price": server_value}, [server_value, 2.5], {"weight": server_value})
    # the stand-in's hash is the backend's _strict_json rule, copied from the backend
    assert ours == item_hash({"input": {"price": raw}, "expected": [raw, 2.5], "metadata": {"weight": raw}})
    assert item_content_hash({"price": 2.5}, None, {}) != item_content_hash({"price": 2}, None, {})


def test_identical_rows_with_integral_floats_reuse_one_version():
    server = ContractServer()
    rows = [{"id": "r1", "question": "q1", "expected": 2.0, "metadata.price": 10.0},
            {"id": "r2", "question": "q2", "expected": 1e20, "metadata.price": -0.0}]
    results = [_run(server, dataset=rows, evaluators=()) for _ in range(3)]
    [ds] = server.datasets.values()
    assert len(ds["versions"]) == 1
    assert {r.dataset_version_id for r in results} == {ds["versions"][0]["id"]}


# ---- M2: the printed resume command parses and resumes -------------------------------------------


def test_the_upload_resume_line_parses():
    from fi._cli.main import build_parser
    from fi.experiments._cli.commands import resume_line
    from fi.experiments.errors import RunInterrupted
    from fi.experiments._cli.commands import _interrupt_message

    line = resume_line(["upload", "results.jsonl", "--dataset", "support.jsonl"], "RUN-1")
    args = build_parser().parse_args(shlex.split(line)[1:])
    assert args.command == "upload" and args.resume == "RUN-1" and args.file == "results.jsonl"
    msg = _interrupt_message(RunInterrupted("RUN-2", 1, 3), ["upload", "r.jsonl", "--dataset", "d"])
    assert build_parser().parse_args(shlex.split(msg.splitlines()[-1].strip())[1:]).resume == "RUN-2"


def test_a_stalled_upload_prints_a_command_that_resumes_it(tmp_path, monkeypatch, capsys):
    from fi._cli.main import main
    import fi.experiments._log_results as lr

    server = ContractServer()
    rows_path, res_path = tmp_path / "support.jsonl", tmp_path / "results.jsonl"
    rows_path.write_text("\n".join(json.dumps(r) for r in ROWS))
    res_path.write_text("\n".join(json.dumps({"id": r["id"], "output": "shipped"}) for r in ROWS))
    real = lr.log_results
    monkeypatch.setattr(lr, "log_results", lambda *a, **k: real(*a, client=client_for(server), **k))
    monkeypatch.setattr(_upload, "BACKOFF_S", (0.01,))
    monkeypatch.setattr(_upload, "GIVE_UP_S", 0.0)
    server.fail_ingest = [503]
    argv = ["upload", str(res_path), "--dataset", str(rows_path), "--dataset-name", "support", "--quiet",
            "--no-env-file"]
    monkeypatch.setattr(sys, "argv", ["futureagi-py", *argv])  # the console script's argv
    assert main(argv) == 3
    err = capsys.readouterr().err
    assert "send the rest with: futureagi-py upload" in err
    resume = shlex.split(err.split("send the rest with: ", 1)[1].strip())
    assert resume[0] == "futureagi-py" and "--resume" in resume
    monkeypatch.setattr(_upload, "GIVE_UP_S", 300.0)
    monkeypatch.setattr(sys, "argv", resume)
    assert main(resume[1:]) == 0, capsys.readouterr().err
    [run] = server.runs.values()
    assert len(run["items"]) == 3 and server.count("POST", r"/model-hub/experiment-runs/") == 2


def test_python_gets_resume_equals_in_the_message(monkeypatch):
    server = ContractServer()
    monkeypatch.setattr(_upload, "BACKOFF_S", (0.01,))
    monkeypatch.setattr(_upload, "GIVE_UP_S", 0.0)
    server.fail_ingest = [503]
    with pytest.raises(UploadStalledError) as info:
        _run(server)
    [run_id] = server.runs
    assert str(info.value).endswith(f"send the rest with: resume={run_id!r}")


# ---- M4: a dataset the SDK made runs by name later -------------------------------------------------


def test_a_dataset_made_from_a_file_runs_by_name_later(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "support.jsonl").write_text("\n".join(json.dumps(r) for r in ROWS))
    server = ContractServer()
    first = _run(server, dataset=experiments.dataset("support.jsonl", name="support"))  # a file needs a name
    posts = _version_posts(server)
    by_name = _run(server, dataset="support")
    assert by_name.status == "completed" and _version_posts(server) == posts  # nothing new snapshotted
    assert by_name.dataset_version_id == first.dataset_version_id
    assert {i.example_id for i in by_name.items} == {i.example_id for i in first.items}
    logged = experiments.log_results("support", [{"id": "T1", "output": "lost"}], client=client_for(server),
                                     progress=False)  # rows named by the file's id column still match
    assert len(logged.items) == 1 and logged.dataset_version_id == first.dataset_version_id


def test_an_empty_dataset_with_no_versions_is_one_line():
    server = ContractServer()
    server.add_dataset("empty")
    with pytest.raises(UsageError, match="dataset 'empty' has no rows"):
        _run(server, dataset="empty")


# ---- M5 + S4: a resume pins the run's own version and its own evaluators -------------------------


def test_resume_refuses_an_edited_or_added_evaluator(monkeypatch):
    server = ContractServer()
    run_id = _stall(monkeypatch, server)

    def correct(output, expected) -> bool:  # the same name, edited code
        return output.strip() == expected

    def extra(output) -> float:
        return 1.0

    with pytest.raises(JournalError, match=r"the evaluators changed since the run started \(edited: correct\)"):
        _run(server, evaluators=(correct,), resume=run_id)
    with pytest.raises(JournalError, match=r"added: extra"):
        _run(server, evaluators=(globals()["correct"], extra), resume=run_id)
    with pytest.raises(JournalError, match=r"removed: correct"):
        _run(server, evaluators=(), resume=run_id)
    assert server.runs[run_id]["items"] == {}  # nothing was sent under the old metric
    done = _run(server, resume=run_id)  # the same evaluators: resumes
    assert done.status == "completed" and len(server.runs[run_id]["items"]) == 3


def test_resume_pins_the_journaled_version_even_after_a_newer_one(monkeypatch):
    server = ContractServer()
    run_id = _stall(monkeypatch, server)
    edited = [dict(r) for r in ROWS]
    edited[1]["expected"] = "found"
    _run(server, dataset=edited)  # someone snapshots a newer version of the same dataset
    posts = _version_posts(server)
    done = _run(server, resume=run_id)
    assert _version_posts(server) == posts  # the resume created nothing
    assert done.status == "completed" and len(server.runs[run_id]["items"]) == 3
    assert done.dataset_version_id == load_journal(run_id).plan["upload_session"]["dataset_version_id"]


def test_resume_refuses_rows_that_changed(monkeypatch):
    server = ContractServer()
    run_id = _stall(monkeypatch, server)
    edited = [dict(r) for r in ROWS]
    edited[0]["question"] = "where is order one?"
    posts = _version_posts(server)
    with pytest.raises(DatasetChangedError, match="1 new or edited, 0 removed"):
        _run(server, dataset=edited, resume=run_id)
    assert _version_posts(server) == posts


# ---- should-fix 1: the server's own reason for a refused template metric ---------------------------


def _template_client(server):
    from tests.experiments.unit.test_hosted_mapping import FIXTURE

    def handler(request):
        if request.url.path == "/sdk/api/v1/get-evals/":
            return httpx.Response(200, json=FIXTURE["response"])
        if request.url.path == "/sdk/api/v1/new-eval/":
            return httpx.Response(200, json={"result": [{"evaluations": [{"output": "Passed", "reason": "ok"}]}]})
        return server(request)

    from fi.futureagi_client import FutureAGIClient

    c = FutureAGIClient(api_key="k-test-1234", secret_key="s-test-1234", base_url="http://srv.test")
    c.generated_client.get_httpx_client()._transport = httpx.MockTransport(handler)
    return c


def test_a_refused_template_metric_shows_the_servers_reason():
    from fi.experiments.evaluators.binding import MetricBindingError
    from tests.experiments.unit.contract_server import err

    refusal = "External metrics are ingested through the experiment results API and cannot be configured here."
    server = ContractServer()
    real = server.__call__

    def refusing(request):
        if request.url.path.endswith("/add_user_eval/"):
            return err(400, refusal)
        return real(request)

    with pytest.raises(MetricBindingError, match="refused the metric for template 'is_json': External metrics"):
        experiments.run(experiments.dataset(ROWS, name="support-rows"), task, ["is_json"], client=_template_client(refusing), trace=False, progress=False)


def test_a_name_that_exists_is_found_again(monkeypatch):
    from fi.experiments.evaluators import binding

    server = ContractServer()
    experiments.run(experiments.dataset(ROWS, name="support-rows"), task, ["is_json"], client=_template_client(server), trace=False, progress=False)
    real, calls = binding._find_user_eval, []

    def miss_once(*a):  # a concurrent run created it between our list and our add
        calls.append(a)
        return None if len(calls) == 1 else real(*a)

    monkeypatch.setattr(binding, "_find_user_eval", miss_once)
    result = experiments.run(experiments.dataset(ROWS, name="support-rows"), task, ["is_json"], client=_template_client(server), trace=False, progress=False)
    assert result.status == "completed" and server.count("POST", r"/model-hub/develops/.*/add_user_eval/") == 2


# ---- should-fix 2: each context gets a hint that works there ---------------------------------------


def test_upload_without_keys_names_no_local_mode(tmp_path, monkeypatch, capsys):
    from fi._cli.main import main

    for k in ("FI_API_KEY", "FI_SECRET_KEY"):
        monkeypatch.delenv(k, raising=False)
    monkeypatch.setenv("FI_BASE_URL", "http://127.0.0.1:9")
    monkeypatch.setenv("FI_LOGIN_FILE", str(tmp_path / "none.json"))
    (tmp_path / "r.jsonl").write_text(json.dumps({"number": 1, "output": "a"}) + "\n")
    assert main(["upload", str(tmp_path / "r.jsonl"), "--dataset", "x.jsonl", "--dataset-name", "x", "--quiet",
                 "--no-env-file"]) == 3
    err = capsys.readouterr().err
    assert "futureagi-py login" in err and "store the results on the server, so they need keys" in err
    assert "upload=False" not in err and "--no-upload" not in err
    with pytest.raises(Exception) as info:
        experiments.log_results(experiments.dataset(ROWS, name="support-rows"), [{"id": "T0", "output": "x"}], progress=False)
    assert "upload=False" not in str(info.value) and "need keys" in str(info.value)


def test_missing_server_features_name_a_way_out_that_exists(monkeypatch):
    server = ContractServer()
    first = _run(server)

    def old_server(request):  # the published image: no SRV-3 / SRV-5 routes, the web server's own 404
        if "external-metrics" in request.url.path or request.url.path.endswith(f"/experiment-runs/{first.run_id}/"):
            return httpx.Response(404, text="<h1>Not Found</h1>", headers={"content-type": "text/html"})
        return server(request)

    from fi.futureagi_client import FutureAGIClient

    c = FutureAGIClient(api_key="k-test-1234", secret_key="s-test-1234", base_url="http://srv.test")
    c.generated_client.get_httpx_client()._transport = httpx.MockTransport(old_server)
    monkeypatch.setenv("FI_RUN_DIR", "/nonexistent-run-dir-for-test")
    with pytest.raises(NotSupportedByServerError) as info:
        experiments.run(experiments.dataset(ROWS, name="support-rows"), task, client=c, rows=experiments.failed(first.run_id), trace=False, progress=False)
    assert "upload=False" not in str(info.value) and "FI_RUN_DIR" in str(info.value)
    with pytest.raises(NotSupportedByServerError) as info:
        experiments.log_results(experiments.dataset(ROWS, name="support-rows"), [{"id": "T0", "output": "x", "scores": {"human": 1}}], client=c, progress=False)
    assert "SRV-5" in str(info.value) and "upload=False" not in str(info.value)
    assert "no local mode" in str(info.value)


# ---- should-fix 6, 7 and the small items -----------------------------------------------------------


def test_a_name_taken_by_an_unlisted_dataset_is_one_line(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "support.jsonl").write_text("\n".join(json.dumps(r) for r in ROWS))
    server = ContractServer()
    server.add_dataset("support", listed=False)  # e.g. a scenario dataset: not in get-datasets-names
    with pytest.raises(UsageError, match="already has a dataset named 'support' that runs cannot use"):
        _run(server, dataset=experiments.dataset("support.jsonl", name="support"))


def test_a_failed_run_stops_the_uploader(monkeypatch):
    from fi.experiments._engine import Engine
    from fi.experiments._upload import Uploader

    aborted = []
    real_abort = Uploader.abort
    monkeypatch.setattr(Uploader, "abort", lambda self: aborted.append(self) or real_abort(self))

    async def broken(self, *a, **k):
        raise RuntimeError("an engine bug")

    monkeypatch.setattr(Engine, "_run_all", broken)
    with pytest.raises(RuntimeError, match="an engine bug"):
        _run(ContractServer())
    assert len(aborted) == 1


def test_latest_version_orders_by_time_not_by_string():
    from fi.experiments._server_rows import latest_version

    class Versions:
        def list(self, dataset_id, limit, offset):
            return {"result": {"versions": [
                {"id": "older", "created_at": "2026-10-22T00:00:01Z"},
                {"id": "newer", "created_at": "2026-10-22T00:00:01.500000Z"},
            ], "has_more": False}}

    class Datasets:
        versions = Versions()

    class Client:
        datasets = Datasets()

    assert latest_version(Client(), "d")["id"] == "newer"


def test_run_create_is_retried_through_5xx(monkeypatch):
    monkeypatch.setattr(_upload, "CREATE_RETRY_S", (0.0, 0.0, 0.0))
    server = ContractServer()
    server.fail_create = [503, 502]
    result = _run(server)
    assert result.status == "completed" and server.count("POST", r"/model-hub/experiment-runs/") == 3


def test_failed_rows_of_a_local_run_are_refused_on_an_uploaded_run():
    server = ContractServer()

    def flaky(row):
        if "2" in row["question"]:
            raise RuntimeError("tool returned 500")
        return "shipped"

    local = experiments.run(ROWS, flaky, [correct], upload=False, trace=False, progress=False)
    with pytest.raises(UsageError, match=r"was a --no-upload \(upload=False\) run, so its rows have local row ids"):
        _run(server, rows=experiments.failed(local.run_id))


def test_credential_named_span_attributes_are_replaced_whole():
    pytest.importorskip("opentelemetry.sdk")  # the export module needs it (absent on 3.14, TA-1)
    from fi.experiments._redact import Redactor
    from fi.experiments._tracing.export import scrub_attributes

    attrs = {
        "http.request.header.x-auth-token": "abc", "access_token": "abc", "oauth.bearer": "abc",
        "gcp.private_key": "abc", "client.credentials": "abc", "token": "abc",
        "gen_ai.usage.input_tokens": "12", "llm.token_count.prompt": "7", "max_tokens": "256", "note": "hi",
    }
    out = scrub_attributes(Redactor(), attrs)
    assert {k for k, v in out.items() if v == "[redacted]"} == {
        "http.request.header.x-auth-token", "access_token", "oauth.bearer", "gcp.private_key",
        "client.credentials", "token"}
