"""Column roles, local sources and row selection."""

import json

import pytest

from fi import experiments
from fi.experiments._dataset import load_local, select_rows
from fi.experiments.errors import AmbiguousInputError, UsageError


def test_roles_inferred():
    ds = load_local([
        {"id": "T1", "question": "q", "expected_text": "e", "tool_mocks": {}, "metadata.tier": "gold", "persona": "p"}
    ])
    assert ds.roles.input == ["question"]
    assert ds.roles.expected == "expected_text"
    assert ds.roles.reserved == ["tool_mocks", "persona"]
    row = ds.rows[0]
    assert (row.id, row.input, row.expected) == ("T1", "q", "e")
    assert row.metadata == {"tier": "gold", "tool_mocks": {}, "persona": "p"}
    assert row["question"] == "q"


def test_expected_priority_and_explicit_roles():
    ds = load_local(experiments.dataset([{"a": 1, "b": 2, "answer": 3}], input="a", expected="b", metadata=["answer"]))
    assert (ds.roles.input, ds.roles.expected, ds.rows[0].metadata) == (["a"], "b", {"answer": 3})
    with pytest.raises(UsageError):
        load_local(experiments.dataset([{"a": 1}], input="nope"))


def test_ambiguous_input_raises_on_access():
    ds = load_local([{"question": "q", "notes": "n", "locale": "en"}])
    with pytest.raises(AmbiguousInputError) as info:
        ds.rows[0].input
    assert "--input-column question" in str(info.value)
    assert ds.rows[0].inputs == {"question": "q", "notes": "n", "locale": "en"}


def test_adapter_needing_a_string_stops_before_first_trial():
    from fi.experiments.adapters.openai_agents import OpenAIAgentsRunner

    class Agent:  # stands in for agents.Agent by MRO module/name
        pass

    Agent.__module__ = "agents.agent"
    calls = []
    with pytest.raises(AmbiguousInputError):
        experiments.run([{"a": 1, "b": 2}], Agent(), upload=False, progress=False)
    assert calls == [] and OpenAIAgentsRunner.needs_single_input


def test_jsonl_source_and_stable_ids(tmp_path):
    path = tmp_path / "rows.jsonl"
    path.write_text("\n".join(json.dumps({"q": f"x{i}"}) for i in range(3)) + "\n")
    first = load_local(str(path))
    path.write_text(json.dumps({"q": "new"}) + "\n" + path.read_text())
    second = load_local(str(path))
    assert [r.id for r in first.rows] == [r.id for r in second.rows[1:]]  # content-based ids
    assert first.name == "rows"


def test_select_ids_numbers_limit_and_errors():
    ds = load_local([{"id": f"T{i}", "q": i} for i in range(1, 6)])
    assert [r.id for r in select_rows(ds.rows, [3, "T5", 1])] == ["T3", "T5", "T1"]
    assert [r.id for r in select_rows(ds.rows, None, limit=2)] == ["T1", "T2"]
    with pytest.raises(UsageError):
        select_rows(ds.rows, [9])
    with pytest.raises(UsageError):
        select_rows(ds.rows, ["nope"])


def test_sample_is_repeatable_and_flagged_non_final():
    rows = [{"id": f"T{i}", "q": i} for i in range(20)]
    a = experiments.run(rows, lambda r: 1, rows=experiments.sample(5, seed=7), upload=False, progress=False)
    b = experiments.run(rows, lambda r: 1, rows=experiments.sample(5, seed=7), upload=False, progress=False)
    assert [i.example_id for i in a.items] == [i.example_id for i in b.items]
    assert len(a.items) == 5 and a.metadata["non_final"] is True


def test_failed_and_new_since_read_the_journal():
    rows = [{"id": f"T{i}", "q": i} for i in range(1, 5)]

    def task(row):
        if row["q"] in (2, 4):
            raise RuntimeError("tool returned 500")
        return "ok"

    from fi.experiments import Limits

    first = experiments.run(rows, task, upload=False, progress=False, limits=Limits(fail_fast=0))
    retry = experiments.run(rows, lambda r: "ok", rows=experiments.failed(first), upload=False, progress=False)
    assert [i.example_id for i in retry.items] == ["T2", "T4"] and retry.run_id != first.run_id
    more = rows + [{"id": "T9", "q": 9}]
    fresh = experiments.run(more, lambda r: "ok", rows=experiments.new_since(first.run_id), upload=False, progress=False)
    assert [i.example_id for i in fresh.items] == ["T9"]


def test_from_column_takes_the_column_out_of_expected():
    rows = [{"question": "q", "answer": "A", "reference": "A"}]
    result = experiments.run(rows, experiments.from_column("answer"), [lambda output, expected: output == expected],
                             upload=False, progress=False) if False else None
    from fi.experiments.evaluators.functions import evaluator

    @evaluator(name="same")
    def same(output, expected):
        return output == expected

    result = experiments.run(rows, experiments.from_column("answer"), [same], upload=False, progress=False)
    assert result.items[0].output == "A" and result.items[0].scores["same"].value == 1.0
