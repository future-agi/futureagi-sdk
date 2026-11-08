"""judge(): the request shape and verdict parsing over an httpx.MockTransport (no network, no model)."""

import asyncio
import json

import httpx

from fi.experiments._dataset import load_local
from fi.experiments.evaluators._base import EvalContext
from fi.experiments.evaluators.judge import Judge, parse_part_verdict
from tests.experiments.unit.judge_helpers import part_verdict, with_criteria

ROW = load_local([{"question": "refund?", "expected": "yes"}]).rows[0]


def test_judge_request_and_score(monkeypatch):
    monkeypatch.setenv("JUDGE_KEY", "test-judge-key-123")
    seen = {}

    def handler(request):
        seen["url"] = str(request.url)
        seen["auth"] = request.headers["Authorization"]
        seen["body"] = json.loads(request.content)
        return httpx.Response(200, json=part_verdict(True, "policy followed"))

    j = Judge("Is the refund policy followed?", model="small-model", api_key_env="JUDGE_KEY",
              base_url="http://judge.local/v1", transport=httpx.MockTransport(with_criteria(handler)))
    scores = asyncio.run(j.aevaluate(EvalContext(row=ROW, output="yes, refunded")))
    s = scores["judge"]
    assert (s.value, s.passed, s.explanation) == (1.0, True, "policy followed")
    assert seen["url"] == "http://judge.local/v1/chat/completions"
    assert seen["auth"] == "Bearer test-judge-key-123"
    assert seen["body"]["model"] == "small-model" and "refund?" in seen["body"]["messages"][1]["content"]


def test_judge_errors_are_error_scores(monkeypatch):
    j = Judge("c", model="m", api_key_env="NOPE_KEY", base_url="http://j/v1")
    assert asyncio.run(j.aevaluate(EvalContext(row=ROW, output="o")))["judge"].status == "error"
    monkeypatch.setenv("K", "k" * 10)
    bad = Judge("c", model="m", api_key_env="K", base_url="http://j/v1",
                transport=httpx.MockTransport(lambda r: httpx.Response(500, text="down")))
    s = asyncio.run(bad.aevaluate(EvalContext(row=ROW, output="o")))["judge"]
    assert s.status == "error" and "500" in s.explanation


def test_parse_part_verdict():
    assert parse_part_verdict('```json\n{"facts": [], "reason": "ok", "met": true}\n```') == (True, "ok")
    for bad in ("no json", '{"score": 1, "pass": true}', '{"met": "yes"}', "[1, 2]"):
        try:
            parse_part_verdict(bad)
        except ValueError:
            continue
        raise AssertionError(bad)
