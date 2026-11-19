"""Each catalog namespace is declared on its owner class with the class it holds.

Type checkers read class-level declarations; an attribute set only at run time is
invisible to them (mypy reports it missing, pyright reports an attribute access
issue). The runtime type hints are the cheap proxy checked here.
"""
from __future__ import annotations

import json
import typing
from pathlib import Path

import pytest

from fi import AsyncFutureAGIClient, FutureAGIClient

ROOT = Path(__file__).resolve().parents[2]
ROWS = json.loads((ROOT / "openapi/catalog/operations.json").read_text())["operations"]
# Namespaces nested under an existing group. The sync client's ``tracing`` is the core
# tracing client, assigned in its constructor; the async client's is the catalog's own.
NESTED = {"tracing"}
CATALOG_HOLDERS = {AsyncFutureAGIClient: {"tracing"}, FutureAGIClient: set()}


def _owners(client: typing.Any) -> list[tuple[str, typing.Any, str]]:
    """(dotted name, owner object, attribute) for every catalog namespace."""
    found = []
    for root in sorted({row["public"].split(".")[0] for row in ROWS}):
        if root not in NESTED:
            found.append((root, client, root))
            continue
        if root in CATALOG_HOLDERS[type(client)]:
            found.append((root, client, root))
        owner = getattr(client, root)
        children = {row["public"].split(".")[1] for row in ROWS if row["public"].startswith(root + ".")}
        found += [(f"{root}.{child}", owner, child) for child in sorted(children)]
    return found


@pytest.mark.parametrize("cls", [FutureAGIClient, AsyncFutureAGIClient], ids=["sync", "async"])
def test_every_catalog_namespace_is_declared_with_its_class(cls: type) -> None:
    client = cls("fixture-api", "fixture-secret", base_url="http://localhost:9012")
    undeclared = []
    for name, owner, attribute in _owners(client):
        declared = typing.get_type_hints(type(owner)).get(attribute)
        if declared is not type(getattr(owner, attribute)):
            undeclared.append(f"{name}: declared {declared!r}, holds {type(getattr(owner, attribute))!r}")
    assert undeclared == []


@pytest.mark.parametrize("cls", [FutureAGIClient, AsyncFutureAGIClient], ids=["sync", "async"])
def test_option_copies_keep_the_declared_classes(cls: type) -> None:
    client = cls("fixture-api", "fixture-secret", base_url="http://localhost:9012")
    clone = client.with_options(timeout=2)
    for (name, owner, attribute), (_, copied, _) in zip(_owners(client), _owners(clone)):
        assert type(getattr(copied, attribute)) is type(getattr(owner, attribute)), name
