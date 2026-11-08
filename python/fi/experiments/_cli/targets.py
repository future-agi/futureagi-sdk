"""The TARGET grammar of ``futureagi-py run``, limited to the kinds this build has.

Order: a URL; a path that exists or ends in .py or a JS/TS suffix (``JS_TS_SUFFIXES``); something
with ``:`` (a module attribute); a reserved word. Kinds that are not built yet (URLs, ``mcp``,
harness and voice names, JS/TS files and JS/TS code objects such as ``src/agent.ts:agent`` or
``agent.cjs:run``, ``-- CMD``) resolve to ``UnknownTargetError``, which lists only the built kinds.
"""

from __future__ import annotations

import importlib
import importlib.util
import re
import sys
import types
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

from fi._cli.extra_roots import extra_for_module
from fi.experiments.errors import UnknownTargetError, UsageError

BUILT_KINDS = (
    "run.py: a run file (its experiments.run(...) calls run once each; flags are overlays)",
    "evals/: a directory; every *_eval.py and eval_*.py file in it",
    "agent.py:graph or pkg.mod:make_agent: a code object (needs --dataset)",
    "(none) with --from-column COL: score a column that already holds the outputs",
)
_URL = re.compile(r"^[A-Za-z][A-Za-z0-9+.-]*://")
# a JS or TS file (a later release in rev3 section.2): every suffix Node and TypeScript load, so none is read as a Python module path
JS_TS_SUFFIXES = (".ts", ".tsx", ".mts", ".cts", ".js", ".jsx", ".mjs", ".cjs")


@dataclass(frozen=True)
class Target:
    kind: str  # "file" | "dir" | "object" | "none"
    text: Optional[str] = None
    path: Optional[Path] = None
    module: Optional[str] = None
    attr: Optional[str] = None


def unknown(text: str) -> UnknownTargetError:
    return UnknownTargetError(text, BUILT_KINDS)


def parse_target(text: Optional[str], *, from_column: Optional[str] = None) -> Target:
    if text is None or text == "":
        if from_column:
            return Target("none")
        raise UsageError("TARGET is required: a run file, a directory, a code object (file.py:attr), "
                         "or none with --from-column COL. See `futureagi-py run --help`.")
    if text == "--" or _URL.match(text):
        raise unknown(text)
    path = Path(text)
    if path.exists():
        if path.is_dir():
            return Target("dir", text, path=path)
        if path.suffix == ".py":
            return Target("file", text, path=path)
        raise unknown(text)
    if text.endswith(".py"):
        raise UsageError(f"{text} does not exist (a relative path is read from {Path.cwd()}). Check the path, or "
                         "run from the directory that holds it.")
    if text.endswith(JS_TS_SUFFIXES):
        raise unknown(text)
    if ":" in text:
        module, attr = text.rsplit(":", 1)
        if module.endswith(JS_TS_SUFFIXES):  # a JS/TS code object (src/agent.ts:agent, agent.cjs:run) is a later release: say so,
            raise unknown(text)  # never "cannot import src/agent.ts" (CLI-04; L-SDK2g Regression coverage: every JS/TS suffix)
        if not module or not attr:
            raise UsageError(f"{text!r}: a code object is FILE.py:ATTR or package.module:ATTR")
        return Target("object", text, module=module, attr=attr)
    raise unknown(text)


def discover(directory: Path) -> list[Path]:
    files = sorted(set(directory.glob("*_eval.py")) | set(directory.glob("eval_*.py")))
    if not files:
        raise UsageError(f"{directory} has no *_eval.py or eval_*.py files")
    return files


def load_object(target: Target) -> Any:
    assert target.kind == "object" and target.module and target.attr
    module_text = target.module
    if module_text.endswith(".py") or Path(module_text).is_file():
        path = Path(module_text).resolve()
        if not path.is_file():
            raise UsageError(f"{module_text} does not exist")
        if str(path.parent) not in sys.path:
            sys.path.insert(0, str(path.parent))
        name = f"_fi_target_{path.stem}"
        spec = importlib.util.spec_from_file_location(name, path)
        if spec is None or spec.loader is None:
            raise UsageError(f"cannot import {module_text}")
        mod = importlib.util.module_from_spec(spec)
        sys.modules[name] = mod
        try:
            spec.loader.exec_module(mod)
        except ModuleNotFoundError as exc:
            if extra_for_module(exc.name):
                raise
            raise UsageError(f"cannot import {module_text!r}: {exc}") from exc
    else:
        if "" not in sys.path and str(Path.cwd()) not in sys.path:
            sys.path.insert(0, str(Path.cwd()))
        try:
            mod = importlib.import_module(module_text)
        except ModuleNotFoundError as exc:
            if extra_for_module(exc.name):
                raise
            raise UsageError(f"cannot import module {module_text!r}: {exc}") from exc
    obj: Any = mod
    for part in target.attr.split("."):
        if not hasattr(obj, part):
            raise UsageError(f"{module_text} has no attribute {target.attr!r}. {_callables_of(obj)}")
        obj = getattr(obj, part)
    return obj


def _framework_label(value: Any) -> Optional[str]:
    """What the CLI makes of a module-level object that is not a plain callable: the framework it auto-detects
    (``LangGraph``), or a recognised framework it does not (``CrewAI, not auto-detected``); None for anything else."""
    from fi.experiments.adapters.detect import NOT_DETECTED, STATEFUL, _mro_match, detect_framework

    spec = detect_framework(value)
    if spec is not None:
        return _FRAMEWORK_NAMES.get(spec.name, spec.name)
    for prefix, cls_name, label in STATEFUL + NOT_DETECTED:
        if _mro_match(value, prefix, cls_name):
            return f"{label}, not auto-detected"
    return None


_FRAMEWORK_NAMES = {"langgraph": "LangGraph", "langchain": "LangChain", "openai_agents": "OpenAI Agents"}


def _callables_of(obj: Any, limit: int = 12) -> str:
    """The next step for a missing attribute (DX-02): the public names of the module (or object) that the CLI can
    run, by name. A module lists the framework objects it holds that ``detect_framework`` recognises (a LangGraph
    graph, a LangChain Runnable, an OpenAI Agents Agent: none is callable, and each one's ``__module__`` is its
    framework's), named with their framework, first; then the functions and classes it defines. Modules, imported
    functions and imported classes are left out. A recognised framework that is not auto-detected
    is named as such."""
    module = isinstance(obj, types.ModuleType)
    own = getattr(obj, "__name__", None) if module else None
    found: list[str] = []
    plain: list[str] = []
    for name in sorted(n for n in dir(obj) if not n.startswith("_")):
        try:
            value = getattr(obj, name)
        except Exception:  # a lazy attribute that fails to load is not something to offer
            continue
        if isinstance(value, types.ModuleType):
            continue
        label = _framework_label(value) if not isinstance(value, type) else None
        if label is not None:
            found.append(f"{name} ({label})")
        elif callable(value) and (own is None or getattr(value, "__module__", None) == own):
            plain.append(name)
    names = found + plain
    if not names:
        return ("It has nothing the CLI can run (a function, a class, or a LangGraph, LangChain or OpenAI Agents "
                "object); name the object that runs your agent (FILE.py:ATTR).")
    more = f" and {len(names) - limit} more" if len(names) > limit else ""
    return f"What it has that the CLI can run: {', '.join(names[:limit])}{more}."
