"""Framework detection by MRO.

``type(obj).__mro__`` is matched against ``(module prefix, class name)`` pairs kept per adapter,
so no framework is imported unless the user's object already is one, and a class that moves
inside its framework is still found. this release auto-detects four kinds: a plain callable, LangGraph,
LangChain and the OpenAI Agents SDK. Any other framework runs through a plain function task; its
error says so. A framework-specific recipe is printed only once a green FW row has executed it
(none yet).

``declared`` version ranges are what each adapter is written against. They are not a tested
claim: each FW-L row records the exact version it passed on, and the range narrows to that.
"""

from __future__ import annotations

import importlib
import re
import sys
import warnings
from dataclasses import dataclass
from typing import Any, Optional

from fi.experiments.adapters._base import TaskRunner
from fi.experiments.adapters.callable import CallableRunner, FactoryRunner, positional_arity
from fi.experiments.errors import SharedStatefulTaskError, UsageError


@dataclass(frozen=True)
class AdapterSpec:
    name: str
    matches: tuple[tuple[str, str], ...]
    loader: str  # "module:Class"
    distribution: str
    declared: tuple[str, str]  # [min, max) by release number; narrowed by FW-L rows


# Order matters: a LangGraph graph is also a LangChain Runnable.
ADAPTERS: tuple[AdapterSpec, ...] = (
    AdapterSpec(
        "langgraph",
        (("langgraph.", "CompiledStateGraph"), ("langgraph.", "Pregel")),
        "fi.experiments.adapters.langchain:LangGraphRunner",
        "langgraph",
        ("0.3", "2"),
    ),
    AdapterSpec(
        "langchain",
        (("langchain_core.", "Runnable"),),
        "fi.experiments.adapters.langchain:LangChainRunner",
        "langchain-core",
        ("0.3", "2"),
    ),
    AdapterSpec(
        "openai_agents",
        (("agents.", "Agent"),),
        "fi.experiments.adapters.openai_agents:OpenAIAgentsRunner",
        "openai-agents",
        ("0.1", "2"),
    ),
)

# Objects that keep history between calls: passing one directly would share it across trials.
STATEFUL: tuple[tuple[str, str, str], ...] = (
    ("autogen_agentchat.", "BaseChatAgent", "AutoGen AgentChat"),
    ("autogen_agentchat.", "BaseGroupChat", "AutoGen AgentChat"),
    ("smolagents.", "MultiStepAgent", "smolagents"),
    ("strands.", "Agent", "Strands"),
    ("autogen.", "ConversableAgent", "AG2"),
)

# Frameworks not auto-detected in this release, recognised so the error names them. No per-framework recipe
# text until a green FW row has executed it.
NOT_DETECTED: tuple[tuple[str, str, str], ...] = (
    ("crewai.", "Crew", "CrewAI"),
    ("llama_index.", "BaseWorkflowAgent", "LlamaIndex"),
    ("llama_index.", "Workflow", "LlamaIndex"),
    ("llama_index.", "BaseQueryEngine", "LlamaIndex"),
    ("google.adk.", "BaseAgent", "Google ADK"),
    ("pydantic_ai.", "Agent", "Pydantic AI"),
    ("agno.", "Agent", "Agno"),
    ("agno.", "Team", "Agno"),
    ("dspy.", "Module", "DSPy"),
    ("haystack.", "Pipeline", "Haystack"),
)

FUNCTION_TASK = (
    "Pass a function instead: def task(row) (or async def task(row, ctx)) that calls your {label} "
    "object with row.input (or the row's columns) and returns the answer."
)


def _mro_match(obj: Any, prefix: str, cls_name: str) -> bool:
    for klass in type(obj).__mro__:
        if klass.__name__ == cls_name and (klass.__module__ + ".").startswith(prefix):
            return True
    return False


def _release(text: str) -> tuple[int, ...]:
    parts = []
    for piece in text.split("."):
        m = re.match(r"\d+", piece)
        if not m:
            break
        parts.append(int(m.group()))
    return tuple(parts) or (0,)


def version_warning(spec: AdapterSpec) -> Optional[str]:
    try:
        from importlib.metadata import version

        installed = version(spec.distribution)
    except Exception:
        return None
    lo, hi = _release(spec.declared[0]), _release(spec.declared[1])
    if not (lo <= _release(installed) < hi):
        return (
            f"{spec.distribution} {installed} is outside the declared range "
            f">={spec.declared[0]},<{spec.declared[1]} for the {spec.name} adapter"
        )
    return None


def detect_framework(obj: Any) -> Optional[AdapterSpec]:
    for spec in ADAPTERS:
        if any(_mro_match(obj, p, c) for p, c in spec.matches):
            return spec
    return None


def resolve_task(task: Any, *, from_factory: bool = False) -> TaskRunner:
    if task is None:
        raise UsageError("task is None")
    spec = detect_framework(task)
    if spec is not None:
        module, cls = spec.loader.split(":")
        runner_cls = getattr(importlib.import_module(module), cls)
        runner = runner_cls(task)
        warning = version_warning(spec)
        if warning:
            warnings.warn(f"{warning}; resolved call: {runner.describe()}", stacklevel=3)
            runner.version_warning = warning
        return runner
    for prefix, cls_name, label in STATEFUL:
        if _mro_match(task, prefix, cls_name):
            if from_factory:
                raise UsageError(
                    f"{label} is not auto-detected in this version, so a factory that returns one cannot "
                    f"run either. Pass a function that builds a fresh {label} object and calls it: "
                    "def task(row) that returns the answer."
                )
            raise SharedStatefulTaskError(
                f"{label} objects keep history between calls, so trials would share it. Pass a function "
                f"that builds a fresh {label} object for each trial and calls it with row.input: "
                "def task(row) that returns the answer."
            )
    for prefix, cls_name, label in NOT_DETECTED:
        if _mro_match(task, prefix, cls_name):
            raise UsageError(f"{label} objects are not auto-detected in this version. " + FUNCTION_TASK.format(label=label))
    if callable(task):
        if positional_arity(task) == 0:
            return FactoryRunner(task, resolve_task)
        return CallableRunner(task)
    raise UsageError(
        f"task {type(task).__name__} is not callable and not a known framework object. A task is "
        "a function (row) / (row, ctx), a zero-argument factory, or a LangGraph / LangChain / "
        "OpenAI Agents object."
    )
