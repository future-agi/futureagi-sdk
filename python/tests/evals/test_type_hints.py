"""Annotations resolve after the split exactly as they did in ai-evaluation 1.1.0.

``typing.get_type_hints`` (and ``inspect.signature(..., eval_str=True)``) resolves a function's
annotations in the globals of the module that defines it. A method moved into a ``_*Methods``
module therefore needs every name its annotations use, its own class included, in that module.
Under ``from __future__ import annotations`` nothing evaluates annotations at import time, so a
missing name shows only when a tool asks for the hints: these tests ask for every one.
"""

from __future__ import annotations

import ast
import builtins
import importlib
import json
from pathlib import Path

from tests.evals.tools import type_hints

PYTHON = Path(__file__).resolve().parents[2]
MANIFEST = json.loads((Path(__file__).parent / "fixtures/upstream-ai-evaluation-1.1.0.json").read_text())
LAYOUT = json.loads((Path(__file__).parent / "tools/port-layout.json").read_text())

# The only failures of the same sweep on the published ai-evaluation 1.1.0 (3.10 and 3.12): the
# annotation names OllamaLLM, which fi.evals.local.evaluator imports only under TYPE_CHECKING. The
# port keeps them as published.
_OLLAMA = "NameError: name 'OllamaLLM' is not defined"
FAIL_IN_1_1_0 = {
    "fi.evals.local.evaluator:HybridEvaluator.__init__": _OLLAMA,
    "fi.evals.local.evaluator:HybridEvaluator.set_local_llm": _OLLAMA,
    "fi.evals.local:HybridEvaluator.__init__": _OLLAMA,
    "fi.evals.local:HybridEvaluator.set_local_llm": _OLLAMA,
}
EXTRACTED_FAIL_IN_1_1_0 = {
    "fi.evals.local._evaluator_hybrid_evaluator_set_local_llm:_HybridEvaluatorSetLocalLlmMethods.set_local_llm": _OLLAMA,
}
# The SDK report stub points to fi.alk under RL2241, raises on import and defines no functions.
# fi.alk itself is ALK-owned, absent from the SDK, and never part of this sweep.
ALK_MOVED_STUBS = {
    row["module"]
    for row in json.loads((Path(__file__).parent / "fixtures/alk-compat-2213.json").read_text())["fi_evals_modules"]
}


def _is_literal(node: ast.AST) -> bool:
    return (isinstance(node, ast.Name) and node.id == "Literal") or (
        isinstance(node, ast.Attribute) and node.attr == "Literal")


def _annotation_names(node: ast.AST) -> set:
    """The names an annotation reads; a string annotation is parsed, Literal[...] holds values."""
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        try:
            node = ast.parse(node.value, mode="eval").body
        except SyntaxError:
            return set()
    names, stack = set(), [node]
    while stack:
        item = stack.pop()
        if isinstance(item, ast.Subscript) and _is_literal(item.value):
            stack.append(item.value)
        elif isinstance(item, ast.Name):
            names.add(item.id)
        elif isinstance(item, ast.Constant) and isinstance(item.value, str):
            names |= _annotation_names(item)
        else:
            stack.extend(ast.iter_child_nodes(item))
    return names


def _module_bindings(tree: ast.Module) -> set:
    """Names bound at module level, including inside if/try blocks (TYPE_CHECKING imports too)."""
    bound, stack = set(), list(tree.body)
    while stack:
        node = stack.pop()
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            bound |= {(a.asname or a.name).split(".")[0] for a in node.names}
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            bound.add(node.name)
        elif isinstance(node, (ast.Assign, ast.AnnAssign, ast.AugAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            bound |= {n.id for t in targets for n in ast.walk(t) if isinstance(n, ast.Name)}
        else:
            stack.extend(ast.iter_child_nodes(node))
    return bound


def _imported_in(functions: list) -> set:
    return {(a.asname or a.name).split(".")[0] for fn in functions for n in ast.walk(fn)
            if isinstance(n, (ast.Import, ast.ImportFrom)) for a in n.names}


def _unresolved(path: str) -> list:
    """(scope, name) for each annotation name the module does not bind. A variable annotation in a
    function body is never evaluated, so an import inside an enclosing function also binds it."""
    tree = ast.parse((PYTHON / path).read_text())
    bound = _module_bindings(tree) | set(dir(builtins))
    found = []

    def visit(node: ast.AST, enclosing: list) -> None:
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                args = child.args
                every = args.posonlyargs + args.args + args.kwonlyargs + [a for a in (args.vararg, args.kwarg) if a]
                annotations = [a.annotation for a in every if a.annotation is not None]
                annotations += [child.returns] if child.returns is not None else []
                for annotation in annotations:
                    found.extend((child.name, name) for name in sorted(_annotation_names(annotation) - bound))
                visit(child, enclosing + [child])
            elif isinstance(child, ast.AnnAssign):
                local = _imported_in(enclosing)
                scope = enclosing[-1].name if enclosing else "<module or class>"
                found.extend((scope, name) for name in sorted(_annotation_names(child.annotation) - bound - local))
                visit(child, enclosing)
            else:
                visit(child, enclosing)

    visit(tree, [])
    return found


def test_every_annotation_in_an_added_module_names_something_the_module_binds() -> None:
    failures = {path: _unresolved(path) for path in MANIFEST["added"] if path.endswith(".py")}
    assert {path: names for path, names in failures.items() if names} == {}


def test_every_function_of_an_added_module_has_resolvable_hints() -> None:
    facade_of = {helper: facade for facade, helpers in LAYOUT.items() for helper in helpers}
    outcomes = {}
    for path in sorted(p for p in MANIFEST["added"] if p.endswith(".py")):
        if type_hints.module_name(path) in ALK_MOVED_STUBS:
            continue
        if path in facade_of:  # a facade imports its helpers part-way through; it goes first
            importlib.import_module(type_hints.module_name(facade_of[path]))
        module = importlib.import_module(type_hints.module_name(path))
        for key, target in type_hints.defined_targets(module):
            outcomes[key] = type_hints.outcome(target)
    assert len(outcomes) > 400
    assert {k: v for k, v in outcomes.items() if v != "ok"} == EXTRACTED_FAIL_IN_1_1_0


def test_the_public_surface_resolves_its_hints_as_in_1_1_0() -> None:
    outcomes = type_hints.sweep(type_hints.upstream_modules(MANIFEST))
    assert len(outcomes) > 5000
    assert {k: v for k, v in outcomes.items() if v != "ok"} == FAIL_IN_1_1_0
