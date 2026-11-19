"""The TARGET grammar: only the kinds built in this release resolve; everything else lists them."""

import pytest

from fi.experiments._cli.targets import BUILT_KINDS, load_object, parse_target
from fi.experiments.errors import UnknownTargetError, UsageError


def test_kinds(tmp_path, monkeypatch):
    (tmp_path / "run.py").write_text("x = 1\n")
    (tmp_path / "evals").mkdir()
    assert parse_target("run.py").kind == "file"
    assert parse_target("evals").kind == "dir"
    t = parse_target("agent.py:graph")
    assert (t.kind, t.module, t.attr) == ("object", "agent.py", "graph")
    assert parse_target("pkg.mod:make_agent").module == "pkg.mod"
    assert parse_target(None, from_column="answer").kind == "none"


@pytest.mark.parametrize("text", ["https://host/agent", "wss://x/y", "mcp", "claude-code", "livekit", "vapi",
                                  "agent.ts", "--", "hello",
                                  # a TS/JS code object is unknown too, never "cannot import"
                                  "src/agent.ts:agent", "agent.js:run", "agent.mjs:graph",
                                  # L-SDK2g Regression coverage: every JS/TS suffix, as a file and as a code object
                                  "agent.cjs:run", "agent.mts:run", "agent.cts:run", "src/agent.tsx:agent",
                                  "agent.jsx:run", "agent.cjs", "agent.tsx", "agent.mts", "agent.cts", "agent.jsx"])
def test_unbuilt_kinds_are_unknown_and_list_built(text):
    with pytest.raises(UnknownTargetError) as info:
        parse_target(text)
    for kind in BUILT_KINDS:
        assert kind in str(info.value)
    assert "vapi" not in str(info.value).lower().replace(repr(text).lower(), "")


def test_missing_file_and_target_required():
    with pytest.raises(UsageError):
        parse_target("nope.py")
    with pytest.raises(UsageError):
        parse_target(None)


def test_load_object_from_file_and_module(tmp_path, monkeypatch):
    (tmp_path / "agent.py").write_text("class A:\n    class B:\n        f = 3\ngraph = 'G'\n")
    monkeypatch.chdir(tmp_path)
    assert load_object(parse_target("agent.py:graph")) == "G"
    assert load_object(parse_target("agent.py:A.B.f")) == 3
    (tmp_path / "pkgx").mkdir()
    (tmp_path / "pkgx" / "__init__.py").write_text("")
    (tmp_path / "pkgx" / "mod.py").write_text("def make_agent():\n    return 1\n")
    assert callable(load_object(parse_target("pkgx.mod:make_agent")))
    with pytest.raises(UsageError):
        load_object(parse_target("agent.py:missing"))


def test_an_existing_ts_code_object_is_unknown_with_the_kinds_listed(tmp_path, monkeypatch):
    """CLI-04 (wave 2g): `futureagi-py run src/agent.ts:agent` said "cannot import src/agent.ts"; the TS form is a later release, so
    the message must list the kinds this version runs, even when the .ts file exists."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "agent.ts").write_text("export const agent = async (row: any) => 'x';\n")
    with pytest.raises(UnknownTargetError) as info:
        parse_target("src/agent.ts:agent")
    assert "'src/agent.ts:agent' is not a TARGET this version can run" in str(info.value)
    assert all(kind in str(info.value) for kind in BUILT_KINDS)


def test_the_common_target_errors_name_their_next_step(tmp_path, monkeypatch):
    """DX-02 (wave 2g): a missing file says where it was looked for; a missing attribute lists the module's own public
    functions and classes (never what it imported)."""
    monkeypatch.chdir(tmp_path)
    with pytest.raises(UsageError, match=r"missing\.py does not exist \(a relative path is read from .*\)\. Check"):
        parse_target("missing.py")
    (tmp_path / "agent_dx.py").write_text("import json\nfrom os import path\n\ndef task(row):\n    return 'x'\n\n"
                                          "class Agent:\n    pass\n\n_hidden = 1\n")
    with pytest.raises(UsageError) as info:
        load_object(parse_target("agent_dx.py:nope"))
    assert str(info.value) == "agent_dx.py has no attribute 'nope'. What it has that the CLI can run: Agent, task."
    (tmp_path / "empty_dx.py").write_text("X = 1\n")
    with pytest.raises(UsageError, match="It has nothing the CLI can run"):
        load_object(parse_target("empty_dx.py:nope"))


def _hint(tmp_path, monkeypatch, name, body, attr):
    monkeypatch.chdir(tmp_path)
    monkeypatch.syspath_prepend(str(tmp_path))
    (tmp_path / name).write_text(body)
    with pytest.raises(UsageError) as info:
        load_object(parse_target(f"{name}:{attr}"))
    return str(info.value)


def test_a_typo_in_a_langgraph_module_lists_its_graph_first(tmp_path, monkeypatch):
    """L-SDK2g Regression coverage: a CompiledStateGraph is not callable and its __module__ is langgraph's, so the wave-2g hint
    listed only the state class and a node function ("S, step"), pushing the user to run a node as the agent."""
    pytest.importorskip("langgraph")
    body = ("from typing import TypedDict\nfrom langgraph.graph import StateGraph, START, END\n"
            "class S(TypedDict):\n    q: str\n"
            "def step(s: S) -> S:\n    return {'q': s['q']}\n"
            "b = StateGraph(S); b.add_node('step', step); b.add_edge(START, 'step'); b.add_edge('step', END)\n"
            "graph = b.compile()\n")
    said = _hint(tmp_path, monkeypatch, "lg_hint.py", body, "grap")
    assert said == "lg_hint.py has no attribute 'grap'. What it has that the CLI can run: graph (LangGraph), S, step."
    only = ("from typing import TypedDict\nfrom langgraph.graph import StateGraph, START, END\n"
            "class _S(TypedDict):\n    q: str\n"
            "_b = StateGraph(_S); _b.add_node('step', lambda s: s); _b.add_edge(START, 'step')\n"
            "_b.add_edge('step', END)\ngraph = _b.compile()\n")
    said = _hint(tmp_path, monkeypatch, "lg_only_hint.py", only, "grap")
    assert said == "lg_only_hint.py has no attribute 'grap'. What it has that the CLI can run: graph (LangGraph)."


def test_a_typo_in_an_openai_agents_module_lists_its_agent(tmp_path, monkeypatch):
    pytest.importorskip("agents")
    said = _hint(tmp_path, monkeypatch, "oa_hint.py",
                 "from agents import Agent, Runner\nagent = Agent(name='support', instructions='answer')\n", "agnt")
    # the imported Agent and Runner classes are not offered; the Agent object is, with its framework
    assert said == "oa_hint.py has no attribute 'agnt'. What it has that the CLI can run: agent (OpenAI Agents)."


def test_a_typo_in_a_langchain_module_lists_its_runnable(tmp_path, monkeypatch):
    pytest.importorskip("langchain_core")
    said = _hint(tmp_path, monkeypatch, "lc_hint.py",
                 "import json\nfrom langchain_core.runnables import RunnableLambda\n"
                 "chain = RunnableLambda(lambda x: x)\n", "chan")
    assert said == "lc_hint.py has no attribute 'chan'. What it has that the CLI can run: chain (LangChain)."


def test_a_framework_the_cli_does_not_auto_detect_is_named_as_such(tmp_path, monkeypatch):
    """A recognised framework object that this release does not auto-detect (adapters/detect.py STATEFUL / NOT_DETECTED) is named
    with that fact, so the hint never offers it as something the CLI runs as it is. The classes are stand-ins with the
    framework's module and class name (detection reads only those), so no framework is installed for this test."""
    body = ("class Crew:\n    pass\nCrew.__module__ = 'crewai.crew'\n"
            "class MultiStepAgent:\n    pass\nMultiStepAgent.__module__ = 'smolagents.agents'\n"
            "crew = Crew()\nhelper = MultiStepAgent()\n"
            "def make_crew():\n    return Crew()\n")
    said = _hint(tmp_path, monkeypatch, "crew_hint.py", body, "crw")
    assert said == ("crew_hint.py has no attribute 'crw'. What it has that the CLI can run: crew (CrewAI, not "
                    "auto-detected), helper (smolagents, not auto-detected), make_crew.")


def test_the_hint_leaves_out_modules_and_imported_names_and_caps_the_list(tmp_path, monkeypatch):
    body = "import os\nfrom json import dumps, JSONDecoder\n" + "".join(f"def f{i:02d}(row):\n    return 1\n"
                                                                          for i in range(14))
    said = _hint(tmp_path, monkeypatch, "many_hint.py", body, "nope")
    assert said.endswith("What it has that the CLI can run: " + ", ".join(f"f{i:02d}" for i in range(12))
                         + " and 2 more.")
    assert "os" not in said.split(":", 1)[1] and "dumps" not in said and "JSONDecoder" not in said


def test_a_missing_dataset_file_and_no_dataset_name_their_next_step(tmp_path, monkeypatch):
    """DX-02 (wave 2g): the rows-file and no-rows errors say what to do; --dataset also takes a server NAME or ID."""
    from fi import experiments
    from tests.experiments.unit.cli_helpers import cli

    monkeypatch.chdir(tmp_path)
    with pytest.raises(UsageError, match=r"dataset file 'nosuch\.jsonl' does not exist \(a relative path is read "
                                         r"from .*\)\. Check the path; a server dataset is named without a file suffix"):
        experiments.run(experiments.dataset("nosuch.jsonl"), lambda row: 1, [], upload=False, progress=False,
                        trace=False)
    (tmp_path / "agent_dx2.py").write_text("def task(row):\n    return 'x'\n")
    code, out, err = cli("run", "agent_dx2.py:task", "--no-upload")
    assert code == 2 and ("this TARGET needs rows: add --dataset rows.jsonl (a local file) or --dataset NAME|ID (a "
                          "server dataset)") in err, err
