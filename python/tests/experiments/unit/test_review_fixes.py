"""Regression tests for the L-SDK wave-0 review (reports/L-SDK-w0-review.md): M1 is in
test_tracing.py; M2-M6 and the should-fix items are here. No network, no model, no server: HTTP
goes to httpx.MockTransport or to the closed port 9 on 127.0.0.1."""

import asyncio
import io
import json
import os
import re
import sys
import types
from pathlib import Path

import httpx
import pytest

from fi import FutureAGIClient, experiments
from fi.experiments import Limits
from fi.experiments.errors import (
    HostedEvalNeedsServerError,
    JudgeModelRequiredError,
    RunLockedError,
    TracingConflictError,
    UnpricedModelError,
    UsageError,
)
from fi.experiments.evaluators.hosted import HostedTemplate, Template, catalog_from_response
from tests.experiments.unit.cli_helpers import cli, write_rows

FIXTURE = json.loads((Path(__file__).parent / "fixtures" / "get_evals.from-yaml.json").read_text(encoding="utf-8"))
CATALOG = catalog_from_response(FIXTURE["response"])


def _registered_commands():
    from fi._cli.main import build_parser

    parser = build_parser()
    sub = next(a for a in parser._actions if a.__class__.__name__ == "_SubParsersAction")
    return set(sub.choices)


def _commands_named(text):
    return set(re.findall(r"`?futureagi\-py ([a-z][a-z-]*)", text))


def _agent(tmp_path):
    (tmp_path / "agent.py").write_text("def task(row):\n    return row.input.upper()\n")


def _mock_client(handler):
    client = FutureAGIClient(api_key="k-test-1234", secret_key="s-test-1234", base_url="http://eval.test")
    client.generated_client.get_httpx_client()._transport = httpx.MockTransport(handler)
    return client


def _eval_handler(output="0.5", calls=None):
    def handler(request):
        if request.url.path == "/sdk/api/v1/get-evals/":
            return httpx.Response(200, json=FIXTURE["response"])
        body = json.loads(request.content)
        if calls is not None:
            calls.append(body)
        return httpx.Response(200, json={"status": True, "result": [{"evaluations": [
            {"name": body["eval_name"], "output": output, "reason": "why", "output_type": "score"}]}]})

    return handler


# ---- M2: an unreachable server is exit 3 with one line ------------------------------------------


def test_unreachable_server_exits_3_with_one_line(tmp_path, monkeypatch):
    monkeypatch.setenv("FI_API_KEY", "k-test-1234")
    monkeypatch.setenv("FI_SECRET_KEY", "s-test-1234")
    _agent(tmp_path)
    rows = write_rows(tmp_path / "rows.jsonl", [{"q": "a", "expected": "A"}])
    code, out, err = cli("run", "agent.py:task", "--dataset", rows, "--eval", "fuzzy_match", "--no-upload",
                         "--no-trace")
    assert code == 3, err
    assert "cannot reach http://127.0.0.1:9" in err and "FI_BASE_URL" in err
    assert "Traceback" not in err and len(err.strip().splitlines()) == 1


def test_dispatch_maps_any_transport_error_to_3():
    from argparse import Namespace

    from fi._cli.main import _dispatch

    def boom(args):
        raise httpx.ConnectTimeout("timed out", request=httpx.Request("GET", "http://srv.test:8000/x"))

    out = io.StringIO()
    old, sys.stdout = sys.stdout, out
    try:
        assert _dispatch(Namespace(func=boom, json=True)) == 3
    finally:
        sys.stdout = old
    doc = json.loads(out.getvalue())
    assert doc["error"]["code"] == "SERVER_UNREACHABLE" and "http://srv.test:8000" in doc["error"]["message"]


# ---- M3: no error names a command this build does not register ------------------------------------


def test_no_keys_error_names_only_registered_commands(tmp_path):
    _agent(tmp_path)
    rows = write_rows(tmp_path / "rows.jsonl", [{"q": "a", "expected": "A"}])
    code, out, err = cli("run", "agent.py:task", "--dataset", rows, "--eval", "fuzzy_match", "--no-upload",
                         "--no-trace")
    assert code == 3 and "FI_API_KEY" in err and "FI_SECRET_KEY" in err
    assert _commands_named(err) <= _registered_commands()


def test_error_messages_name_only_registered_commands():
    from fi._credentials import CredentialsMissingError
    from fi.utils.errors import MissingAuthError

    registered = _registered_commands()
    for exc in (CredentialsMissingError("http://x.test", ("FI_API_KEY",)), HostedEvalNeedsServerError(["x"]),
                MissingAuthError(None, None)):
        named = _commands_named(str(exc))
        assert named <= registered, (type(exc).__name__, named - registered)


# ---- M4: the storage wording is true -------------------------------------------------------------


def test_header_says_template_calls_are_stored_and_billed():
    stream = io.StringIO()
    from fi.experiments._engine import Engine, RunConfig
    from fi.experiments._sync import run_coroutine_sync

    cfg = RunConfig(dataset=[{"input": "x", "expected": "y"}], task=lambda row: "ok", evaluators=["fuzzy_match"],
                    client=_mock_client(_eval_handler()), upload=False, trace=False, stream=stream)
    run_coroutine_sync(lambda: Engine(cfg).execute())
    text = stream.getvalue()
    assert "nothing stored" not in text and "nothing is stored" not in text
    assert "each template call is stored by the eval API" in text and "billed to your org" in text
    assert text.splitlines()[0].startswith("Server   http://eval.test")  # DESIGN section.1's first line

    stream = io.StringIO()
    cfg = RunConfig(dataset=[{"input": "x"}], task=lambda row: "ok", upload=False, trace=False, stream=stream)
    run_coroutine_sync(lambda: Engine(cfg).execute())
    assert "nothing is stored on the platform" in stream.getvalue() and "Server" not in stream.getvalue()


def test_no_upload_help_is_true():
    code, out, _ = cli("run", "--help")
    flat = " ".join(out.split())
    assert "store no run on the platform" in flat and "template evals still call the eval API" in flat
    assert "store nothing" not in flat


# ---- M5: judge() never sends a provider key to OpenAI ---------------------------------------------


def test_judge_needs_base_url_for_a_non_openai_key(monkeypatch):
    import importlib

    judge_mod = importlib.import_module("fi.experiments.evaluators.judge")
    with pytest.raises(UsageError) as info:
        judge_mod.judge("ok?", model="llama-3.1-8b-instant", api_key_env="GROQ_API_KEY")
    assert "base_url=" in str(info.value)

    from fi.experiments._dataset import load_local
    from fi.experiments.evaluators._base import EvalContext

    seen = []

    from tests.experiments.unit.judge_helpers import is_criteria_read, part_verdict

    def handler(request):  # the criteria read, then the one part's verdict (wave 2d), each answered in its own shape
        seen.append((str(request.url), request.headers["Authorization"]))
        if is_criteria_read(request):
            content = json.dumps({"parts": [{"part": "ok", "needs_right_answer": False}]})
            return httpx.Response(200, json={"choices": [{"message": {"content": content}}],
                                             "usage": {"prompt_tokens": 11, "completion_tokens": 7}})
        return httpx.Response(200, json=part_verdict(True, tokens=(11, 7)))

    row = load_local([{"q": "x"}]).rows[0]
    monkeypatch.setenv("GROQ_API_KEY", "groq-test-key-1234")
    monkeypatch.setenv("OPENAI_API_KEY", "openai-test-key-1234")
    monkeypatch.delenv("OPENAI_BASE_URL", raising=False)
    groq = judge_mod.Judge("ok?", model="llama-3.1-8b-instant", api_key_env="GROQ_API_KEY",
                           base_url="https://groq.test/openai/v1", transport=httpx.MockTransport(handler))
    oai = judge_mod.Judge("ok?", model="gpt-4.1-mini", transport=httpx.MockTransport(handler))
    ec = EvalContext(row=row, output="o")
    asyncio.run(groq.aevaluate(ec))
    asyncio.run(oai.aevaluate(ec))
    assert seen[:2] == [("https://groq.test/openai/v1/chat/completions", "Bearer groq-test-key-1234")] * 2
    assert seen[2:] == [("https://api.openai.com/v1/chat/completions", "Bearer openai-test-key-1234")] * 2
    assert ec.usage == [("llama-3.1-8b-instant", 11, 7)] * 2 + [("gpt-4.1-mini", 11, 7)] * 2
    monkeypatch.setenv("OPENAI_BASE_URL", "http://proxy.test/v1")
    assert oai._url() == "http://proxy.test/v1/chat/completions" and "proxy.test" in oai.describe()


def test_judge_body_fits_reasoning_models():
    from fi.experiments.evaluators.judge import Judge, is_reasoning_model

    assert all(is_reasoning_model(m) for m in ("o1", "o3-mini", "o4-mini", "gpt-5", "gpt-5-mini", "openai/o3"))
    assert not any(is_reasoning_model(m) for m in ("gpt-4.1-mini", "gpt-4o", "llama-3.1-8b-instant", "omni"))
    body = Judge("c", model="o4-mini").request_body([])
    assert "max_completion_tokens" in body and "max_tokens" not in body and "temperature" not in body
    body = Judge("c", model="gpt-4.1-mini").request_body([])
    assert body["max_tokens"] == 600 and body["temperature"] == 0.0 and "max_completion_tokens" not in body


# ---- M6: --experiment / experiment= need an uploaded run (A5 wires them) ---------------------------


def test_experiment_without_upload_is_refused(tmp_path):
    with pytest.raises(UsageError) as info:
        experiments.run([{"q": 1}], lambda row: 1, experiment="0b6e-attach", upload=False, progress=False)
    assert "stores no run" in str(info.value)
    _agent(tmp_path)
    rows = write_rows(tmp_path / "rows.jsonl", [{"q": "a"}])
    code, _, err = cli("run", "agent.py:task", "--dataset", rows, "--no-upload", "--no-trace", "--experiment", "x")
    assert code == 2 and "stores no run" in err


# ---- hosted templates ------------------------------------------------------------------------------


def test_every_non_deterministic_template_needs_a_judge_model():
    catalog = dict(CATALOG)
    catalog["org_llm_check"] = {"id": "org-1", "name": "org_llm_check",
                                "config": {"required_keys": ["output"], "eval_type_id": "SomeOrgLLMType"}}
    ev = HostedTemplate(Template("org_llm_check"), None)
    with pytest.raises(JudgeModelRequiredError):
        ev.preflight(catalog, ["input"], False)
    ok = HostedTemplate(Template("org_llm_check"), "my-judge")
    ok.preflight(catalog, ["input"], False)
    assert ok.is_judge and HostedTemplate(Template("fuzzy_match"), None).preflight(catalog, ["input", "expected"],
                                                                                    True) is None


def test_empty_server_output_is_an_error_score():
    result = experiments.run([{"input": "x", "expected": "y"}], lambda row: "ok", ["fuzzy_match"],
                             client=_mock_client(_eval_handler(output="")), upload=False, progress=False,
                             trace=False)
    s = result.items[0].scores["fuzzy_match"]
    assert s.status == "error" and s.explanation == "why" and s.value is None


# ---- cost cap ----------------------------------------------------------------------------------


def _llm_task(models):
    from opentelemetry import trace

    def task(row):
        model = models.get(row["id"], "m1")
        with trace.get_tracer("test").start_as_current_span(
                "llm", attributes={"gen_ai.request.model": model, "gen_ai.usage.input_tokens": 10,
                                   "gen_ai.usage.output_tokens": 10}):
            return row.input

    return task


def test_unpriced_model_after_the_first_trial_stops_the_run():
    rows = [{"id": f"r{i}", "q": i} for i in range(1, 7)]
    with pytest.raises(UnpricedModelError) as info:
        experiments.run(rows, _llm_task({"r3": "fallback-model"}), upload=False, progress=False, concurrency=1,
                        max_cost_usd=100.0, limits=Limits(prices={"m1": (1.0, 1.0)}))
    assert "fallback-model" in str(info.value)


def test_judge_spend_counts_and_unpriced_judge_is_refused_up_front(monkeypatch):
    from fi.experiments.evaluators.judge import Judge

    from tests.experiments.unit.judge_helpers import is_criteria_read, part_verdict

    def handler(request):  # the read and each verdict cost the same here: 1000 tokens in, 1000 out
        if is_criteria_read(request):
            content = json.dumps({"parts": [{"part": "ok", "needs_right_answer": False}]})
            return httpx.Response(200, json={"choices": [{"message": {"content": content}}],
                                             "usage": {"prompt_tokens": 1000, "completion_tokens": 1000}})
        return httpx.Response(200, json=part_verdict(True, tokens=(1000, 1000)))

    monkeypatch.setenv("OPENAI_API_KEY", "openai-test-key-1234")
    judge = Judge("ok?", model="judge-m", base_url="http://judge.test/v1", api_key_env="OPENAI_API_KEY",
                  transport=httpx.MockTransport(handler))
    ran = []
    with pytest.raises(UnpricedModelError) as info:
        experiments.run([{"id": "r1", "q": 1}], lambda row: ran.append(1), [judge], upload=False, progress=False,
                        max_cost_usd=10.0, limits=Limits(prices={"m1": (1.0, 1.0)}))
    assert "judge-m" in str(info.value) and ran == []
    result = experiments.run([{"id": "r1", "q": 1}, {"id": "r2", "q": 2}], _llm_task({}), [judge], upload=False,
                             progress=False, max_cost_usd=10.0,
                             limits=Limits(prices={"m1": (1.0, 1.0), "judge-m": (1.0, 2.0)}))
    cap = result.metadata["cost_cap"]
    # one criteria read (the judge's first row) and two verdicts: the read counts toward the cap too
    assert cap["judge_usd"] == pytest.approx(3 * 0.003) and cap["enforced"] is True
    assert cap["spent_usd"] == pytest.approx(3 * 0.003 + 2 * 0.00002)


def test_cap_records_when_it_was_not_enforced(capsys):
    result = experiments.run([{"q": 1}], lambda row: 1, upload=False, max_cost_usd=1.0, instrument=False)
    cap = result.metadata["cost_cap"]
    assert cap["enforced"] is False and cap["usd"] == 1.0
    assert "NOT enforced" in capsys.readouterr().err


# ---- tracing modes ------------------------------------------------------------------------------


def test_mixing_trace_modes_with_one_instrumentor_is_refused(monkeypatch):
    from opentelemetry.sdk.trace import TracerProvider

    from fi.experiments._tracing import instrument
    from fi.experiments._tracing.routing import RoutingTracerProvider

    bound = []
    fake = types.ModuleType("fake_instr_mod")

    class FakeInstrumentor:
        def instrument(self, tracer_provider):
            bound.append(tracer_provider)

    fake.FakeInstrumentor = FakeInstrumentor
    monkeypatch.setitem(sys.modules, "fake_instr_mod", fake)
    monkeypatch.setitem(instrument.INSTRUMENTORS, "fake", ("fake_instr_mod", "FakeInstrumentor", "traceAI-fake"))
    monkeypatch.setattr(instrument, "_done", {})
    the_plan = instrument.InstrumentPlan(enable=["fake"])
    instrument.apply(RoutingTracerProvider(), the_plan)
    assert instrument.apply(RoutingTracerProvider(), the_plan) == []  # another router: one sink
    with pytest.raises(TracingConflictError) as info:
        instrument.apply(TracerProvider(), the_plan)
    assert "traceAI-fake" in str(info.value) and "one tracing mode per process" in str(info.value)
    assert len(bound) == 1


def test_auto_turns_on_only_the_provider_instrumentors_with_rows(monkeypatch):
    from fi.experiments._tracing import instrument

    monkeypatch.setattr(instrument, "_installed", lambda m: True)
    assert instrument.plan(None, "auto").enable == ["openai", "anthropic"]
    assert instrument.plan(None, ["groq"]).enable == ["groq"]  # by name only


# ---- file mode -----------------------------------------------------------------------------------


def test_arun_in_a_run_file_declares_instead_of_running(tmp_path):
    marker = tmp_path / "ran.txt"
    (tmp_path / "async_eval.py").write_text(
        "import asyncio\n"
        "from fi import experiments\n"
        f"MARK = {str(marker)!r}\n"
        "def task(row):\n"
        "    open(MARK, 'a').write('x')\n"
        "    return row['q']\n"
        "asyncio.run(experiments.arun([{'q': 1}], task, upload=False, name='async-run'))\n"
    )
    code, out, err = cli("run", "async_eval.py", "--list")
    assert code == 0 and out.strip() == "async-run" and not marker.exists()
    code, out, err = cli("run", "async_eval.py", "--quiet", "--no-trace")
    assert code == 0, err
    assert marker.read_text() == "x"  # ran once, by the CLI


def test_resume_needs_exactly_one_declared_run(tmp_path):
    (tmp_path / "two_eval.py").write_text(
        "from fi import experiments\n"
        "experiments.run([{'q': 1}], lambda row: 1, upload=False, name='first')\n"
        "experiments.run([{'q': 1}], lambda row: 2, upload=False, name='second')\n"
    )
    code, _, err = cli("run", "two_eval.py", "--resume", "abc", "--no-trace")
    assert code == 2 and "--filter" in err and "first, second" in err


def test_resume_line_is_the_real_redacted_command(monkeypatch):
    from fi.experiments._cli.commands import resume_line

    monkeypatch.setenv("MY_API_KEY", "sk-very-secret-value")
    line = resume_line(["run", "two_eval.py", "--param", "k=sk-very-secret-value", "--filter", "*", "--resume",
                        "old"], "R1", "second")
    assert line == "futureagi-py run two_eval.py --param 'k=[redacted]' --filter second --resume R1"
    assert resume_line(["run", "agent.py:task", "--dataset", "rows.jsonl"], "R2") == (
        "futureagi-py run agent.py:task --dataset rows.jsonl --resume R2")


# ---- data, journal, .env, adapters ------------------------------------------------------------------


def test_rows_picked_by_number_are_never_merged_by_content():
    from fi.experiments._dataset import load_local, select_rows

    rows = load_local([{"q": 1}, {"q": 1}, {"q": 2}]).rows
    chosen = select_rows(rows, [1, 2, 2], None)
    assert [r.number for r in chosen] == [1, 2]


def test_run_locked_names_the_lock_file(tmp_path):
    from fi.experiments._journal import Journal

    journal = Journal("locked-run", tmp_path / "runs")
    journal.create({"run_id": "locked-run", "items": []})
    journal.close()
    journal.lock_path.write_text(str(os.getppid()))  # a live process that is not this one
    with pytest.raises(RunLockedError) as info:
        Journal("locked-run", tmp_path / "runs").acquire()
    assert str(journal.lock_path) in str(info.value)


def test_env_file_prints_names_and_base_url_hosts_never_values(tmp_path, monkeypatch):
    for name in ("MY_TOKEN_X", "OPENAI_BASE_URL"):
        monkeypatch.setenv(name, "x")
        monkeypatch.delenv(name)
    _agent(tmp_path)
    (tmp_path / ".env").write_text("MY_TOKEN_X=dotenv-secret-value\nOPENAI_BASE_URL=https://u:pw@evil.test/v1\n")
    rows = write_rows(tmp_path / "rows.jsonl", [{"q": "a"}])
    code, _, err = cli("run", "agent.py:task", "--dataset", rows, "--no-upload", "--no-trace", "--quiet")
    assert code == 0
    assert "MY_TOKEN_X" not in err  # --quiet: no Env line; the base-URL warning still prints
    assert "OPENAI_BASE_URL to https://evil.test" in err
    assert "dotenv-secret-value" not in err and "pw" not in err
    monkeypatch.delenv("MY_TOKEN_X")
    monkeypatch.delenv("OPENAI_BASE_URL")
    code, _, err = cli("run", "agent.py:task", "--dataset", rows, "--no-upload", "--no-trace")
    assert "set MY_TOKEN_X, OPENAI_BASE_URL" in err and "dotenv-secret-value" not in err


def test_langgraph_with_a_checkpointer_gets_a_thread_per_trial():
    pytest.importorskip("langgraph")
    from typing import TypedDict

    from langgraph.checkpoint.memory import MemorySaver
    from langgraph.graph import END, START, StateGraph

    class State(TypedDict):
        q: str
        a: str

    def answer(state):
        return {"a": state["q"].upper()}

    builder = StateGraph(State)
    builder.add_node("answer", answer)
    builder.add_edge(START, "answer")
    builder.add_edge("answer", END)
    graph = builder.compile(checkpointer=MemorySaver())
    result = experiments.run([{"q": "a"}, {"q": "b"}], graph, upload=False, progress=False, trials=2, trace=False)
    assert [i.status for i in result.items] == ["completed"] * 4
    assert {i.output["a"] for i in result.items} == {"A", "B"}
