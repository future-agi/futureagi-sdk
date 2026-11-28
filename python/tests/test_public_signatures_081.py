"""Check call binding against the published futureagi 0.8.1 signatures."""

import importlib
import inspect
import json
from enum import Enum, EnumMeta
from functools import cache
from pathlib import Path

import pytest


_SIGNATURES = Path(__file__).with_name("fixtures") / "signatures_081.json"
_POSITIONAL = {"POSITIONAL_ONLY", "POSITIONAL_OR_KEYWORD"}
_KEYWORD = {"POSITIONAL_OR_KEYWORD", "KEYWORD_ONLY"}
_VARIADIC = {"VAR_POSITIONAL", "VAR_KEYWORD"}
_MARKER = object()

# These aliases inherited object.__init__; its inspected variadics were not valid constructor arguments.
_OBJECT_INIT = {
    "fi.gateway.AgentCCLogger.__init__",
    "fi.gateway.callbacks.AgentCCLogger.__init__",
    "fi.gateway.callbacks.custom_logger.AgentCCLogger.__init__",
}


@cache
def _import(name):
    return importlib.import_module(name)


def _resolve(name, modules):
    owner, _, attr = name.rpartition(".")
    if owner in modules:
        return getattr(_import(owner), attr)
    return getattr(_resolve(owner, modules), attr)


def _inspect_signature(name, modules):
    return _signature_of(_resolve(name, modules), name, modules)


def _signature_of(target, name, modules):
    if isinstance(target, EnumMeta) and type(target).__call__ is not EnumMeta.__call__:
        # A metaclass with its own __call__ decides how the enum is called; 3.12 and 3.13 report (*values) for it.
        return inspect.signature(type(target).__call__.__get__(target))
    signature = inspect.signature(target)
    # CPython 3.10/3.11 expose EnumMeta's functional API for populated enums, and 3.10
    # inherits object.__init__; normalize these stdlib defaults to the wheel census forms.
    if (
        isinstance(target, EnumMeta)
        and target.__members__
        and type(target).__call__ is EnumMeta.__call__
        and signature == inspect.signature(EnumMeta.__call__.__get__(target))
    ):
        return inspect.Signature([inspect.Parameter("values", inspect.Parameter.VAR_POSITIONAL)])
    if target is object.__init__ and target is Enum.__init__:
        owner, _, attr = name.rpartition(".")
        if attr == "__init__" and isinstance(_resolve(owner, modules), EnumMeta):
            return inspect.Signature([
                inspect.Parameter("self", inspect.Parameter.POSITIONAL_OR_KEYWORD),
                inspect.Parameter("args", inspect.Parameter.VAR_POSITIONAL),
                inspect.Parameter("kwds", inspect.Parameter.VAR_KEYWORD),
            ])
    return signature


def _bind_problem(published, signature):
    old_pos = [p for p in published if p["kind"] in _POSITIONAL]
    new_pos = [p.name for p in signature.parameters.values() if p.kind.name in _POSITIONAL]
    old_kinds = {p["kind"] for p in published}
    variadic = "VAR_POSITIONAL" in old_kinds
    any_keyword = "VAR_KEYWORD" in old_kinds
    extra = "_signature_probe"
    existing_names = {p["name"] for p in published} | signature.parameters.keys()
    while extra in existing_names:
        extra += "_"

    # Each positional length permits a range from required keywords to all keywords.
    # Binding the endpoints checks omission, named arguments and duplicate values.
    for count in range(len(old_pos) + 1):
        rest = old_pos[count:]
        if any(p["kind"] == "POSITIONAL_ONLY" and p["default_repr"] is None for p in rest):
            continue
        candidates = [p for p in rest if p["kind"] in _KEYWORD]
        candidates.extend(p for p in published if p["kind"] == "KEYWORD_ONLY")
        args = [_MARKER] * count
        required = {p["name"]: _MARKER for p in candidates if p["default_repr"] is None}
        all_named = {p["name"]: _MARKER for p in candidates}
        forms = [(args, required), (args, all_named)]
        if any_keyword:
            named = {**all_named, extra: _MARKER}
            named.update((p["name"], _MARKER) for p in old_pos[:count] if p["kind"] == "POSITIONAL_ONLY")
            forms.append((args, named))
        if variadic and count == len(old_pos):
            forms.append(([_MARKER] * (max(len(new_pos), count) + 1), all_named))
        for positional, named in forms:
            try:
                signature.bind(*positional, **named)
            except TypeError as error:
                return f"bind({len(positional)} positional, keywords {list(named)}): {error}"

    # Binding alone permits a positional argument to land on a different parameter.
    for index, parameter in enumerate(old_pos):
        received = new_pos[index] if index < len(new_pos) else "variadic positional arguments"
        if received != parameter["name"]:
            return f"positional slot {index + 1}: {parameter['name']} -> {received}"
    if variadic and len(new_pos) > len(old_pos):
        return f"positional slot {len(old_pos) + 1}: variadic positional arguments -> {new_pos[len(old_pos)]}"
    return None


def test_public_signatures_081():
    fixture = json.loads(_SIGNATURES.read_text(encoding="utf-8"))
    modules = set(fixture["modules"])
    failures = []
    for group in fixture["signatures"]:
        for name in group["callables"]:
            published = group["parameters"]
            if name in _OBJECT_INIT:
                published = [p for p in published if p["kind"] not in _VARIADIC]
            try:
                signature = _inspect_signature(name, modules)
            except (AttributeError, ImportError, TypeError, ValueError) as error:
                failures.append(f"{name}: {error}")
                continue
            problem = _bind_problem(published, signature)
            if problem:
                failures.append(f"{name}: {problem}")
    if failures:
        pytest.fail("\n".join([f"{len(failures)} incompatible callable paths:", *sorted(failures)]), pytrace=False)


def test_an_enum_metaclass_call_that_breaks_the_081_form_is_caught():
    fixture = json.loads(_SIGNATURES.read_text(encoding="utf-8"))
    name = "fi.api.types.HttpMethod"
    published = next(g["parameters"] for g in fixture["signatures"] if name in g["callables"])

    class Meta(EnumMeta):
        def __call__(cls, value, *, format):  # noqa: A002 - the keyword the published call does not give
            return super().__call__(value)

    class Changed(Enum, metaclass=Meta):
        GET = "GET"

    assert _bind_problem(published, _signature_of(Changed, name, set(fixture["modules"])))
