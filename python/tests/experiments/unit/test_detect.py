"""MRO detection with stub classes named like the frameworks' (unit only; FW rows use the real ones)."""

import asyncio

import pytest

from fi.experiments.adapters import resolve_task
from fi.experiments.adapters.callable import CallableRunner, FactoryRunner
from fi.experiments.errors import SharedStatefulTaskError, UsageError


def stub(module, name, base=object, **attrs):
    cls = type(name, (base,), attrs)
    cls.__module__ = module
    return cls


def test_plain_callables_and_factories():
    assert isinstance(resolve_task(lambda row: 1), CallableRunner)
    assert resolve_task(lambda row, ctx: 1).describe().endswith("(row, ctx)")

    async def atask(row):
        return 1

    assert resolve_task(atask).is_async
    assert isinstance(resolve_task(lambda: (lambda row: 1)), FactoryRunner)
    with pytest.raises(UsageError):
        resolve_task(42)


def test_langgraph_detected_before_langchain_and_called_async():
    Runnable = stub("langchain_core.runnables.base", "Runnable")
    Pregel = stub("langgraph.pregel.main", "Pregel", Runnable)

    class Graph(Pregel):
        channels = {"messages": object()}
        name = "support"

        async def ainvoke(self, payload, config=None):
            self.seen = (payload, config)
            return {"messages": [{"role": "ai", "content": "refund done"}]}

    Graph.__module__ = "langgraph.graph.state"
    g = Graph()
    runner = resolve_task(g)
    assert runner.framework == "langgraph" and runner.needs_single_input
    assert "ainvoke" in runner.describe()

    class Row:
        input = "where is my order"
        inputs = {"q": "where is my order"}

    class Ctx:
        params = {"model": "m"}
        run_id, example_id, trial = "R", "E", 2

    out = asyncio.run(runner.acall(Row(), Ctx()))
    assert out == "refund done"
    # a fresh LangGraph thread per trial (a checkpointed graph refuses to run without one)
    assert g.seen == ({"messages": [("user", "where is my order")]},
                      {"configurable": {"model": "m", "thread_id": "R:E:2"}})


def test_langchain_runnable_dict_input():
    Runnable = stub("langchain_core.runnables.base", "Runnable")

    class Chain(Runnable):
        def get_input_jsonschema(self):
            return {"type": "object", "properties": {"question": {}}}

        async def ainvoke(self, payload, config=None):
            return type("Msg", (), {"content": f"A:{payload['question']}"})()

    runner = resolve_task(Chain())
    assert runner.framework == "langchain" and not runner.needs_single_input

    class Row(dict):
        input = None

    out = asyncio.run(runner.acall(Row(question="q1"), type("C", (), {"params": {}})()))
    assert out == "A:q1"


def test_openai_agents_detected():
    Agent = stub("agents.agent", "Agent")
    runner = resolve_task(Agent())
    assert runner.framework == "openai_agents" and "Runner.run" in runner.describe()


def test_stateful_objects_need_a_factory_and_recipes_for_others():
    Stateful = stub("smolagents.agents", "MultiStepAgent")
    with pytest.raises(SharedStatefulTaskError) as info:
        resolve_task(Stateful())
    assert "fresh" in str(info.value) and "def task(row)" in str(info.value)
    Crew = stub("crewai.crew", "Crew")
    with pytest.raises(UsageError) as info:
        resolve_task(Crew())
    # no framework-specific recipe until a green FW row has executed one
    assert "not auto-detected" in str(info.value) and "def task(row)" in str(info.value)
    assert "kickoff" not in str(info.value)


def test_version_range_warning(monkeypatch):
    from fi.experiments.adapters import detect

    spec = detect.ADAPTERS[0]
    monkeypatch.setattr("importlib.metadata.version", lambda dist: "9.0.0")
    assert "outside the declared range" in detect.version_warning(spec)
    monkeypatch.setattr("importlib.metadata.version", lambda dist: "1.0.3")
    assert detect.version_warning(spec) is None
