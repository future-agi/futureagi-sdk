"""Flags → run() keyword arguments."""

import argparse

import pytest

from fi import experiments
from fi.experiments._cli import commands
from fi.experiments._cli.run import limits_overlay, overlay_from_args, parse_fail_under, parse_rows
from fi.experiments._dataset import RowSelector
from fi.experiments.errors import UsageError


def parse(*argv):
    parser = argparse.ArgumentParser(prog="futureagi-py")
    sub = parser.add_subparsers(dest="command")
    commands.register(sub)
    return parser.parse_args(["run", *argv])


def test_everyday_flags_map_to_run_kwargs():
    args = parse("agent.py:g", "--dataset", "rows.jsonl", "--trials", "2", "--concurrency", "3", "--limit", "5",
                 "--timeout-s", "9.5", "--max-cost-usd", "1.5", "--param", "temperature=0.2", "--param",
                 'tags=["a"]', "--model", "gpt-x", "--name", "n1", "--local", "--judge-model", "j")
    kw = overlay_from_args(args)
    assert kw == {"judge_model": "j", "trials": 2, "concurrency": 3, "limit": 5, "timeout_s": 9.5,
                  "max_cost_usd": 1.5, "name": "n1", "params": {"temperature": 0.2, "tags": ["a"], "model": "gpt-x"},
                  "upload": False}


def test_more_flags():
    args = parse("run.py", "--rows", "3,7,T12", "--param-str", "n=007", "--metadata", "team=x", "--no-trace",
                 "--instrument", "openai,anthropic", "--retries", "2", "--fail-fast", "0", "--price", "m=1,2",
                 "--quiet", "--resume", "R1", "--project", "p")
    kw = overlay_from_args(args)
    assert kw["rows"] == [3, 7, "T12"] and kw["params"] == {"n": "007"} and kw["metadata"] == {"team": "x"}
    assert kw["trace"] is False and kw["instrument"] == ["openai", "anthropic"] and kw["progress"] is False
    assert kw["resume"] == "R1" and kw["project"] == "p"
    assert limits_overlay(args) == {"retries": 2, "fail_fast": 0, "prices": {"m": (1.0, 2.0)}}


def test_rows_selectors():
    assert parse_rows("failed:R1", None) == RowSelector("failed", run_id="R1")
    assert parse_rows("new:R2", None) == RowSelector("new", run_id="R2")
    assert parse_rows("sample:20", 7) == experiments.sample(20, seed=7)
    with pytest.raises(UsageError):
        parse_rows("sample:x", None)


def test_fail_under_forms():
    assert parse_fail_under(["0.8"]) == 0.8
    assert parse_fail_under(["task_completion=0.85", "exact=1"]) == {"task_completion": 0.85, "exact": 1.0}
    with pytest.raises(UsageError):
        parse_fail_under(["0.8", "a=1"])


def test_bad_values_are_usage_errors():
    with pytest.raises(UsageError):
        overlay_from_args(parse("x.py", "--metadata", "novalue"))
    with pytest.raises(UsageError):
        limits_overlay(parse("x.py", "--price", "m=abc"))
    with pytest.raises(UsageError):
        overlay_from_args(parse("x.py", "--seed", "3"))
