"""Hosted templates: the default mapping over a get-evals fixture, the printed fix line, and a run
whose new-eval calls go to an httpx.MockTransport (no server, no model).

Fixture provenance: fixtures/get_evals.from-yaml.json is GENERATED from the template YAMLs at
backend origin/dev the recorded revision (see its _provenance block and make_get_evals_fixture.py). Replace
it with a fixture recorded from the E2E image's get-evals in wave 1.
"""

import json
import re
from pathlib import Path

import httpx
import pytest

from fi import FutureAGIClient, experiments
from fi.experiments.errors import HostedEvalNeedsServerError, JudgeModelRequiredError, UnmappedEvalKeysError, UsageError
from fi.experiments.evaluators.hosted import (
    HostedTemplate,
    Template,
    catalog_from_response,
    default_mapping,
    fix_line,
    metric_body,
    metric_name,
)

FIXTURE = json.loads((Path(__file__).parent / "fixtures" / "get_evals.from-yaml.json").read_text(encoding="utf-8"))
CATALOG = catalog_from_response(FIXTURE["response"])


def _preflight(name, columns=("input", "expected"), has_expected=True, judge="j", **kw):
    ev = HostedTemplate(Template(name, **kw), judge)
    ev.preflight(CATALOG, list(columns), has_expected)
    return ev


def test_coverage_over_every_template_matches_the_design():
    maps = {"agent": 0, "function": 0, "specialty": 0}
    total = {"agent": 0, "function": 0, "specialty": 0}
    unmapped_keys = {}
    for rec in FIXTURE["response"]["result"]:
        req = (rec["config"] or {}).get("required_keys") or []
        plan = default_mapping(req, columns=[], has_expected=True, overrides={})
        total[rec["_folder"]] += 1
        if not plan.unmapped and not plan.note:
            maps[rec["_folder"]] += 1
        if rec["_folder"] != "specialty":
            for k in plan.unmapped:
                unmapped_keys[k] = unmapped_keys.get(k, 0) + 1
    # API design section item 4: 135 of the 173 (84 of 89 function, 51 of 84 judge templates). The
    # fixture holds 174: those 173 plus 1 specialty template (an AgentEvaluator), which DESIGN leaves out.
    assert (total["agent"], total["function"], total["specialty"]) == (84, 89, 1)
    assert (maps["agent"], maps["function"]) == (51, 84)
    assert unmapped_keys.get("agent_prompt") == 14 and unmapped_keys.get("context") == 10


def test_never_guesses_between_two_output_keys():
    two = [r for r in CATALOG.values() if sum(k in ("text", "generated_audio", "output", "response")
                                              for k in (r["config"].get("required_keys") or [])) > 1]
    assert two, "the fixture has a template naming two output keys"
    name = two[0]["name"]
    with pytest.raises(UnmappedEvalKeysError) as info:
        _preflight(name)
    assert f"--eval-map {name}:" in str(info.value)


def test_unmapped_key_prints_the_exact_line():
    with pytest.raises(UnmappedEvalKeysError) as info:
        _preflight("customer_agent_task_completion")
    err = info.value
    assert "agent_prompt" in err.keys
    assert "--eval-map customer_agent_task_completion:agent_prompt=COLUMN" in err.fix_line
    assert fix_line("x", ["a"]).startswith("--eval-map x:a=COLUMN")


def test_mapping_sources(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "prompt.txt").write_text("You are a support agent.")
    ev = _preflight("customer_agent_task_completion", columns=("question",),
                    map={"agent_prompt": "@prompt.txt"})
    assert ev.mapping["agent_prompt"] == "@prompt.txt"
    with pytest.raises(UsageError):
        _preflight("customer_agent_task_completion", map={"agent_prompt": "no_such_column"})


def test_judge_template_needs_a_judge_model():
    with pytest.raises(JudgeModelRequiredError) as info:
        _preflight("task_completion", judge=None)
    assert "--judge-model" in str(info.value)
    assert _preflight("fuzzy_match", judge=None).mapping == {"output": "output", "expected": "expected"}


def test_unknown_template_suggests_names():
    with pytest.raises(UsageError) as info:
        _preflight("task_complet")
    assert "task_completion" in str(info.value)


def test_metric_name_is_deterministic():
    tpl = Template("contains", {"keyword": "refund"})
    a = metric_name(tpl, {"text": "output"}, None)
    assert a == metric_name(tpl, {"text": "output"}, None) and re.fullmatch(r"sdk-contains-[0-9a-f]{8}", a)
    assert a != metric_name(tpl, {"text": "input"}, None)
    body = metric_body(CATALOG["contains"], tpl, {"text": "output"}, None)
    assert body["run"] is False and body["template_id"] == CATALOG["contains"]["id"]


def _client(handler):
    client = FutureAGIClient(api_key="k-test-1234", secret_key="s-test-1234", base_url="http://eval.test")
    client.generated_client.get_httpx_client()._transport = httpx.MockTransport(handler)
    return client


def test_run_calls_new_eval_per_trial_and_scores():
    calls = []

    def handler(request):
        if request.url.path == "/sdk/api/v1/get-evals/":
            return httpx.Response(200, json=FIXTURE["response"])
        body = json.loads(request.content)
        calls.append(body)
        out = "Passed" if body["eval_name"] == "task_completion" else 0.75
        return httpx.Response(200, json={"status": True, "result": [{"evaluations": [
            {"name": body["eval_name"], "output": out, "reason": "r", "output_type": "x", "runtime": 1}]}]})

    rows = [{"input": "refund please", "expected": "refunded"}, {"input": "hi", "expected": "hello"}]
    result = experiments.run(rows, lambda row: "ok", ["task_completion", experiments.template("fuzzy_match")],
                             judge_model="my-judge", client=_client(handler), upload=False, progress=False)
    assert len(calls) == 4
    tc = [c for c in calls if c["eval_name"] == "task_completion"]
    assert tc[0] == {"eval_name": "task_completion", "inputs": {"input": "refund please", "output": "ok"},
                     "model": "my-judge"}
    fm = [c for c in calls if c["eval_name"] == "fuzzy_match"][0]
    assert fm["inputs"] == {"output": "ok", "expected": "refunded"} and "model" not in fm
    s = result.summary().evaluators
    assert s["task_completion"].pass_rate == 1.0 and s["fuzzy_match"].mean == 0.75


def test_server_error_is_an_error_score():
    def handler(request):
        if request.url.path == "/sdk/api/v1/get-evals/":
            return httpx.Response(200, json=FIXTURE["response"])
        return httpx.Response(400, json={"status": False, "result": "bad input"})

    result = experiments.run([{"input": "x", "expected": "y"}], lambda row: "ok", ["fuzzy_match"],
                             client=_client(handler), upload=False, progress=False)
    s = result.items[0].scores["fuzzy_match"]
    assert s.status == "error" and "400" in s.explanation


def test_no_keys_refuses_before_the_first_trial():
    ran = []
    with pytest.raises(HostedEvalNeedsServerError) as info:
        experiments.run([{"input": "x"}], lambda row: ran.append(1), ["fuzzy_match"], upload=False, progress=False)
    assert "fuzzy_match" in str(info.value) and ran == []
