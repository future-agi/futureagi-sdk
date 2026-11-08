"""The type stub re-exports every public error class the runtime package exports.

Typed consumers import from ``fi/gateway/__init__.pyi``; an error missing there cannot
be imported under a type checker even though it exists at runtime.
"""

import ast
from pathlib import Path

import fi.gateway as gateway
from fi.gateway import _exceptions

STUB = Path(gateway.__file__).with_suffix(".pyi")


def _stub_names() -> set[str]:
    tree = ast.parse(STUB.read_text())
    return {
        alias.asname or alias.name
        for node in tree.body
        if isinstance(node, ast.ImportFrom)
        for alias in node.names
    }


def test_every_public_error_class_is_in_the_stub():
    public_errors = {name for name in gateway.__all__ if isinstance(getattr(_exceptions, name, None), type)}
    assert public_errors, "no public error classes found"
    assert sorted(public_errors - _stub_names()) == []
