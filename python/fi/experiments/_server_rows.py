"""Reading server datasets for uploaded runs, and the server's own item rules: the per-item
content hash over ``_strict_json`` values, version and table paging, and version items ↔ rows.

Split out of ``_server_dataset.py`` (the pin) to keep each module under the 400-line rule.
"""

from __future__ import annotations

import datetime as _dt
import hashlib
import json
from decimal import Decimal
from typing import Any, Mapping, Optional, Sequence

from fi.experiments._dataset import Roles, Row

DATA_ORIGINS = frozenset({None, "", "OTHERS", "others"})  # derived columns (evals, prompts...) are not data
PAGE = 500
ROLES_KEY = "fi.experiments"  # version metadata key holding the column roles


# ---- small helpers ------------------------------------------------------------------------------


def _result(payload: Any) -> Any:
    if isinstance(payload, Mapping) and "result" in payload:
        return payload["result"]
    return payload


def _plain(obj: Any) -> Any:
    to_dict = getattr(obj, "to_dict", None)
    return to_dict() if callable(to_dict) else obj


def server_json(value: Any) -> Any:
    """A value as the server hashes and stores it (``_strict_json`` in ``dataset_version_service.py``
    @ the recorded revision): an integral float becomes an int, as JSONB reads it back (``2.0`` → ``2``,
    ``1e20`` → ``100000000000000000000``, ``-0.0`` → ``0``); lists and objects recursively. Tuples are
    lists, as they are once sent as JSON."""
    if isinstance(value, float) and value.is_integer():
        return int(Decimal(str(value)))
    if isinstance(value, (list, tuple)):
        return [server_json(v) for v in value]
    if isinstance(value, Mapping):
        return {k: server_json(v) for k, v in value.items()}
    return value


def item_content_hash(input: Any, expected: Any, metadata: Mapping[str, Any]) -> str:
    """The server's per-item hash (``canonical_content_hash`` in ``dataset_version_service.py``):
    sha256 of the normalised ``{"input", "expected", "metadata"}`` as canonical JSON."""
    payload = {"input": server_json(input), "expected": server_json(expected), "metadata": server_json(dict(metadata))}
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _cell(value: Any) -> Any:
    if isinstance(value, Mapping):
        return value.get("cell_value", value.get("cellValue"))
    return value


# ---- reading versions and tables ----------------------------------------------------------------


def list_versions(client: Any, dataset_id: str) -> list[dict]:
    out: list[dict] = []
    offset = 0
    while True:
        page = _plain(_result(_plain(client.datasets.versions.list(dataset_id, limit=100, offset=offset))))
        got = page.get("versions") or []
        out.extend(got)
        if not page.get("has_more") or not got:
            return out
        offset += len(got)  # the server may cap the page below the limit asked for


def _created(version: Mapping[str, Any]) -> _dt.datetime:
    """``created_at`` as a time: DRF drops a zero microsecond part, so the strings do not sort
    (``…:01Z`` sorts after the newer ``…:01.500000Z``). Dataset versions carry no ``version_number``."""
    raw = str(version.get("created_at") or "")
    try:
        parsed = _dt.datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        return _dt.datetime.min.replace(tzinfo=_dt.timezone.utc)
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=_dt.timezone.utc)


def latest_version(client: Any, dataset_id: str) -> Optional[dict]:
    """The newest version. The server lists newest first (``-created_at, -id``); a tie on the time
    keeps the server's order."""
    versions = list_versions(client, dataset_id)
    if not versions:
        return None
    newest = max(_created(v) for v in versions)
    return next(v for v in versions if _created(v) == newest)


def version_items(client: Any, dataset_id: str, version_id: str) -> tuple[dict, list[dict]]:
    items: list[dict] = []
    offset, version = 0, {}
    while True:
        page = _plain(_result(_plain(client.datasets.versions.get(dataset_id, version_id, limit=PAGE, offset=offset))))
        version = page.get("version") or version
        got = page.get("items") or []
        items.extend(got)
        if not page.get("has_more") or not got:
            return version, items
        offset += len(got)  # the server may cap the page below the limit asked for


def table_records(client: Any, dataset_id: str) -> list[tuple[str, dict]]:
    """``(row_id, {column name: value})`` for every row, data columns only, in table order."""
    out: list[tuple[str, dict]] = []
    page_index = 0
    while True:
        res = _result(client.datasets.get_table(dataset_id, page_size=PAGE, current_page_index=page_index)) or {}
        columns = {
            str(c.get("id")): str(c.get("name"))
            for c in res.get("column_config") or res.get("columnConfig") or []
            if (c.get("origin_type", c.get("originType")) in DATA_ORIGINS)
        }
        table = res.get("table") or []
        for row in table:
            row_id = str(row.get("row_id") or row.get("rowId"))
            out.append((row_id, {name: _cell(row.get(cid)) for cid, name in columns.items()}))
        total_pages = int((res.get("metadata") or {}).get("total_pages") or 0)
        page_index += 1
        if not table or page_index >= total_pages:
            return out


# ---- items ↔ rows -------------------------------------------------------------------------------


def item_for(row: Row) -> dict[str, Any]:
    """The version item for one row: ``input`` holds every input column by name."""
    return {"input": dict(row.inputs), "expected": row.expected, "metadata": dict(row.metadata)}


def _roles_meta(roles: Roles) -> dict[str, Any]:
    return {"input": list(roles.input), "expected": roles.expected, "metadata": list(roles.metadata),
            "id": roles.id}


def rows_from_items(items: Sequence[Mapping[str, Any]], roles_meta: Optional[Mapping[str, Any]]) -> tuple[list[Row], Roles]:
    """Rows read back from version items. A dataset whose rows had an id column gets it back from
    each item's ``external_id`` (so ``log_results`` rows named by ``id`` still match)."""
    expected_name = (roles_meta or {}).get("expected") or "expected"
    id_col = (roles_meta or {}).get("id") or None
    input_cols: list[str] = []
    rows: list[Row] = []
    for number, item in enumerate(items, 1):
        raw_input = item.get("input")
        inputs = dict(raw_input) if isinstance(raw_input, Mapping) else {"input": raw_input}
        for col in inputs:
            if col not in input_cols:
                input_cols.append(col)
        metadata = dict(item.get("metadata") or {})
        data = {**inputs, **metadata}
        if id_col and item.get("external_id") not in (None, "") and id_col not in data:
            data = {id_col: item["external_id"], **data}
        if item.get("expected") is not None:
            data[expected_name] = item.get("expected")
        rows.append(Row(id=str(item["example_id"]), number=number, data=data, inputs=inputs,
                        expected=item.get("expected"), metadata=metadata))
    has_expected = any(r.expected is not None for r in rows)
    roles = Roles(input=list((roles_meta or {}).get("input") or input_cols),
                  expected=expected_name if has_expected else None,
                  metadata=list((roles_meta or {}).get("metadata") or []), reserved=[], id=id_col)
    return rows, roles
