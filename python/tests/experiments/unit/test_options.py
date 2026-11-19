"""_options.yaml is the release gate's list: every offered option, each with its real e2e rows.
This fails on an orphan in either direction (a public name or flag missing from the file, or a
file entry the code no longer offers) and on an option that names no row."""

import argparse
import inspect
from pathlib import Path

import pytest

yaml = pytest.importorskip("yaml")

OPTIONS = Path(__file__).resolve().parents[3] / "fi" / "experiments" / "_options.yaml"


def _flags(parser: argparse.ArgumentParser) -> set[str]:
    out = set()
    for action in parser._actions:
        if isinstance(action, argparse._HelpAction) or isinstance(action, argparse._SubParsersAction):
            continue
        if action.option_strings:
            out.add(max(action.option_strings, key=len) if action.dest != "no_upload" else "--no-upload")
        else:
            out.add(action.dest.upper())
    return out


def surface() -> set[str]:
    from fi import experiments
    from fi._cli import main as main_mod
    from fi.experiments import evaluators

    keys = {f"py:{n}" for n in experiments.__all__}
    keys |= {f"py:evaluators.{n}" for n in evaluators.__all__}
    keys |= {f"py:run({p})" for p in inspect.signature(experiments.run).parameters}
    keys |= {f"py:log_results({p})" for p, v in inspect.signature(experiments.log_results).parameters.items()
             if v.kind is not inspect.Parameter.VAR_KEYWORD}
    assert inspect.signature(experiments.run).parameters.keys() == inspect.signature(experiments.arun).parameters.keys()
    parser = main_mod.build_parser()
    sub = next(a for a in parser._actions if isinstance(a, argparse._SubParsersAction))
    for command in ("run", "upload", "login", "logout", "doctor"):
        keys.add(f"cli:{command}")
        for flag in _flags(sub.choices[command]):
            keys.add(f"cli:{command} {flag}")
    return keys


def test_every_offered_option_is_listed_and_every_listed_option_is_offered():
    listed = yaml.safe_load(OPTIONS.read_text(encoding="utf-8"))["options"]
    offered = surface()
    assert sorted(offered - set(listed)) == [], "public options missing from _options.yaml"
    assert sorted(set(listed) - offered) == [], "_options.yaml lists options the code does not offer"


def test_every_option_names_at_least_one_row():
    listed = yaml.safe_load(OPTIONS.read_text(encoding="utf-8"))["options"]
    empty = [k for k, rows in listed.items() if not rows or not all(isinstance(r, str) and r for r in rows)]
    assert empty == []
