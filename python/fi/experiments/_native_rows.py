"""Materialize a newly created local dataset before creating its first version."""

from __future__ import annotations

from typing import Any, Mapping, Sequence
from uuid import uuid4

from fi.experiments._dataset import Roles, Row
from fi.experiments.errors import UsageError


def _column_type(values: Sequence[Any]) -> str:
    kinds: set[str] = set()
    for value in values:
        if value is None:
            continue
        if isinstance(value, bool):
            kinds.add("boolean")
        elif isinstance(value, int):
            kinds.add("integer")
        elif isinstance(value, float):
            kinds.add("float")
        elif isinstance(value, str):
            kinds.add("text")
        elif isinstance(value, Mapping):
            kinds.add("json")
        elif isinstance(value, (list, tuple)):
            kinds.add("array")
        else:
            raise UsageError("a native dataset column contains an unsupported value type")
    if kinds <= {"integer", "float"} and "float" in kinds:
        return "float"
    if len(kinds) > 1:
        raise UsageError("a native dataset column contains incompatible value types; use consistent column types")
    return next(iter(kinds), "text")


def materialize_rows(client: Any, dataset_id: str, rows: Sequence[Row], roles: Roles) -> list[str]:
    """Return client-generated native IDs only after the one-shot row POST succeeds.

    The caller must have created this dataset and must not supply a parent version. Existing
    tables are not synchronized here; parent external-ID inheritance could break row identity.
    """
    names = list(dict.fromkeys([*roles.input, *([roles.expected] if roles.expected else []),
                               *roles.metadata, *roles.reserved, *([roles.id] if roles.id else [])]))
    # Unselected local fields must not gain a new upload path through the native table.
    records = []
    for row in rows:
        data = row.to_dict()
        records.append({name: data.get(name) for name in names})
    columns = [{"name": name, "data_type": _column_type([record[name] for record in records])} for name in names]
    ids = [str(uuid4()) for _ in rows]
    body = {"rows": [{"id": rid, "cells": [{"column_name": name, "value": record[name]} for name in names]}
                     for rid, record in zip(ids, records)]}
    client.datasets.add_columns(dataset_id, {"new_columns_data": columns})
    client.datasets.add_rows(dataset_id, body)
    return ids
