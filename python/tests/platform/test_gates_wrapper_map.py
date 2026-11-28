"""The wrapper map's rules (one public path per method, in both languages), and proof the checker
catches each kind of violation."""

from __future__ import annotations

import copy
import typing

import pytest

from ._gates_support import PLATFORM, SCOPED, guard_sockets, load, read_json


@pytest.fixture(autouse=True)
def no_egress(monkeypatch: pytest.MonkeyPatch) -> None:
    guard_sockets(monkeypatch)


@pytest.fixture(scope="module")
def spec() -> dict[str, typing.Any]:
    return read_json(SCOPED)


def test_wrapper_map_rules(spec: dict[str, typing.Any]) -> None:
    checker = load("platform_wrapper_map", "scripts/platform/wrapper_map.py")
    mapping = read_json(PLATFORM / "wrapper-map.json")
    assert checker.check(mapping, spec) == []
    assert "sha256:" + mapping["contract_sha256"] == read_json(PLATFORM / "source.json").get("source_digest")


def _first(mapping: dict[str, typing.Any], name: str) -> dict[str, typing.Any]:
    return mapping["operations"][name]["methods"][0]


@pytest.mark.parametrize(
    ("mutate", "expected"),
    [
        (
            lambda m: _first(m, "runs.cancel").update(
                py="Run.interrupt", ts="Run.interrupt"
            ),
            "duplicate py path",
        ),
        (
            lambda m: _first(m, "runs.list").update(
                py="client.agents.runs", ts="client.agents.runs"
            ),
            "shadows the namespace",
        ),
        (lambda m: _first(m, "runs.send").pop("ts"), "missing language twin"),
        (
            lambda m: _first(m, "runs.fork").update(ts="Run.forkIt"),
            "differ after case conversion",
        ),
        (
            lambda m: m["operations"]["runs.continue"].pop("rename"),
            "no rename is listed",
        ),
        (
            lambda m: m["operations"]["runs.fork"].update(
                rename={"from": "fork", "to": "fork", "why": "x"}
            ),
            "rename listed",
        ),
        (
            lambda m: _first(m, "runs.list").update(ts_args=["options.limit"]),
            "keyword arguments differ",
        ),
        (
            lambda m: m["operations"]["runs.events"].pop("internal"),
            "query parameters no argument covers",
        ),
        (
            lambda m: m["operations"].update(
                {"runs.tree": {"unwrapped": "x", "until": "later"}}
            ),
            "unwrapped, but the scoped spec has it",
        ),
        (lambda m: m["operations"].pop("deployments.health"), "no wrapper-map entry"),
        (
            lambda m: _first(m, "deployments.health").update(handle="Run"),
            "does not start at its handle",
        ),
        (
            lambda m: _first(m, "runs.create").update(
                py_args=["*", "wait"], ts_args=["options.wait"]
            ),
            "so its method takes idempotency_key",
        ),
        (
            lambda m: _first(m, "platform.environments.create").update(
                py_args=["*", "idempotency_key"], ts_args=[]
            ),
            "so its method takes idempotency_key",
        ),
        (
            lambda m: _first(m, "platform.agents.create").update(
                py_args=["*", "idempotency_key", "wait"],
                ts_args=["options.idempotencyKey", "options.wait"],
            ),
            "not idempotent, so it takes no idempotency key",
        ),
    ],
)
def test_wrapper_map_checker_catches(
    spec: dict[str, typing.Any], mutate: typing.Any, expected: str
) -> None:
    checker = load("platform_wrapper_map", "scripts/platform/wrapper_map.py")
    mapping = copy.deepcopy(read_json(PLATFORM / "wrapper-map.json"))
    mutate(mapping)
    findings = checker.check(mapping, spec)
    assert any(expected in f for f in findings), findings
