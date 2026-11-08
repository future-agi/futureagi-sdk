"""Server datasets for uploaded runs: name / id / ``fi.datasets.Dataset`` / local rows → one pinned
dataset version.

The run plan names server ``example_id`` values, so every uploaded run is pinned to a version:

- ``version=V``: read V's items; nothing is created.
- otherwise the current rows are compared with the latest version, item by item, with the server's
  own content hash (sha256 of ``{"input", "expected", "metadata"}`` as canonical JSON). Equal →
  "using version … (unchanged)". Different → one new version whose parent is the latest, so rows
  that did not change keep their ``example_id`` (through ``external_id`` or the legacy row id).

Current rows come from a local ``list[dict]`` / ``rows.jsonl``, or from the server dataset's table
(``get-dataset-table``, data columns only). ``versions.create`` is not idempotent, so it is never
retried here.

Datasets made as a side effect:
- local rows are stored in a dataset with a real name: ``experiments.dataset(rows, name=...)`` /
  ``--dataset-name``, required for a ``list[dict]`` and for a rows file alike (there are no
  ``rows <hash>`` names, and a file's stem is never the name: dataset service decision S3 (a));
- local rows never add a version to an existing dataset that fi.experiments did not create (one made
  in the UI or by another tool). That is refused, naming the dataset, unless the caller opts in with
  ``add_version=True`` / ``--add-version``. A dataset counts as the SDK's when it was created by this
  call, or when its table has no rows and its first version was written by fi.experiments (its
  metadata carries ``fi.experiments.roles``). The refusal says only what it saw (table rows, or a
  first version the SDK did not write; regression coverage). A dataset that is empty and has no version needs the
  opt-in too until the server can create a first version only when there is none (dataset service decision S1 under
  the atomic-create contract); with it, the run header says it wrote that first version. Rows equal to the
  latest version add nothing, so they are never refused. A server dataset passed by its own name or id is the
  caller's explicit choice and is snapshotted as before; ``name=`` / ``add_version=`` on it are refused,
  never ignored.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Mapping, Optional, Sequence

from fi.experiments._dataset import DatasetSpec, Roles, Row, _infer_roles, is_local_source, load_local
from fi.experiments._dataset_owner import (  # noqa: F401  (re-exported: the dataset contract's checks)
    INLINE_NAME_NEEDED,
    LOCAL_ONLY,
    DatasetNameRequiredError,
    DatasetNotOwnedError,
    check_local_name,
    check_local_only,
    first_version_note,
    local_dataset_name,
    made_by_sdk,
    not_made_by_sdk,
    refuse_foreign_version,
)
from fi.experiments._server_rows import (  # noqa: F401  (re-exported: the pin's public helpers)
    DATA_ORIGINS,
    PAGE,
    ROLES_KEY,
    _created,
    _plain,
    _roles_meta,
    _result,
    item_content_hash,
    item_for,
    latest_version,
    list_versions,
    rows_from_items,
    server_json,
    table_records,
    version_items,
)
from fi.experiments.errors import (
    AmbiguousDatasetError,
    DatasetNotFoundError,
    JournalError,
    PlanTooLargeError,
    UsageError,
)

_UUID_RE = re.compile(r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$")


@dataclass
class ServerDataset:
    """The engine's view of a pinned server dataset version (duck-compatible with LocalDataset)."""

    name: str
    rows: list[Row]
    roles: Roles
    dataset_id: str
    version_id: str
    note: str
    source_kind: str = "server"
    created_version: bool = False
    content_hashes: list[str] = field(default_factory=list)

    @property
    def id(self) -> str:
        return self.dataset_id


# ---- name / id ----------------------------------------------------------------------------------


def is_uuid(value: Any) -> bool:
    return isinstance(value, str) and bool(_UUID_RE.match(value))


def find_dataset(client: Any, name: str) -> Optional[str]:
    """The id of the dataset named exactly ``name``; None when there is none."""
    datasets = (_result(client.datasets.list_names()) or {}).get("datasets") or []
    hits = [str(d.get("dataset_id") or d.get("id")) for d in datasets if str(d.get("name")) == name]
    if len(hits) > 1:
        raise AmbiguousDatasetError(name, hits)
    return hits[0] if hits else None


def dataset_ref(client: Any, source: Any) -> tuple[str, str]:
    """``(dataset_id, display name)`` for a server source: a name, an id, or ``fi.datasets.Dataset``."""
    config = getattr(source, "dataset_config", None)
    if config is not None and getattr(config, "id", None):
        return str(config.id), str(getattr(config, "name", "") or config.id)
    if not isinstance(source, str) or not source.strip():
        raise UsageError(f"{source!r} is not a dataset (a name, an id, fi.datasets.Dataset, list[dict] or rows.jsonl)")
    if is_uuid(source):
        return source.lower(), source
    found = find_dataset(client, source)
    if found is None:
        raise DatasetNotFoundError(
            f"no dataset named {source!r} in this workspace. Check the name, pass its id, or pass rows "
            "(list[dict] / rows.jsonl) to create it"
        )
    return found, source


NAME_TAKEN = "already exists"  # DATASET_EXIST_IN_ORG: "A dataset with this name already exists in your organization."


def ensure_dataset(client: Any, name: str) -> tuple[str, bool]:
    """Find the dataset named ``name`` or create it empty; ``(id, created)``.

    Names are unique per organization across every source (``validate_dataset_name_unique``), but
    ``get-datasets-names`` lists only demo / build / observe datasets, so a scenario, knowledge-base
    or experiment-snapshot dataset with this name is refused on create: that 400 is one clear line
   ."""
    from fi.errors import FutureAGIAPIError

    found = find_dataset(client, name)
    if found is not None:
        return found, False
    try:
        res = _result(client.datasets.create_empty({"new_dataset_name": name, "is_sdk": True}))
    except FutureAGIAPIError as exc:
        message = _server_message(exc)
        if exc.status_code == 400 and NAME_TAKEN in message:
            raise UsageError(
                f"this organization already has a dataset named {name!r} that runs cannot use (a scenario, "
                "knowledge-base or experiment dataset), so the rows cannot be stored under that name. Choose "
                "another name: experiments.dataset(..., name=\"...\") (CLI: --dataset-name NAME)"
            ) from exc
        if exc.status_code == 400:
            raise UsageError(f"the server refused to create the dataset {name!r}: {message}") from exc
        raise
    return str(res["dataset_id"]), True


def _server_message(exc: Any) -> str:
    payload = getattr(exc, "payload", None)
    if isinstance(payload, Mapping):
        for key in ("message", "detail", "error", "result"):
            if isinstance(payload.get(key), str) and payload[key]:
                return str(payload[key])[:500]
    return str(exc)[:500]


def from_version(client: Any, dataset_id: str, name: str, version_id: str, note: str) -> ServerDataset:
    """A dataset pinned to ``version_id``, its rows read from the version's items."""
    meta, items = version_items(client, dataset_id, version_id)
    rows, roles = rows_from_items(items, (meta.get("metadata") or {}).get(ROLES_KEY))
    return ServerDataset(name, rows, roles, dataset_id, str(meta.get("id") or version_id), note)


# ---- the pin -------------------------------------------------------------------------------------


@dataclass
class _Current:
    name: str
    rows: list[Row]
    roles: Roles
    keys: list[tuple[str, str]]  # ("external_id" | "legacy_row_id", value) per row
    dataset_id: str
    local: bool = False  # the rows came from list[dict] / rows.jsonl
    created: bool = False  # this call created the dataset


def _current_from_local(client: Any, source: Any) -> _Current:
    spec = source if isinstance(source, DatasetSpec) else DatasetSpec(source)
    local = load_local(spec)
    name = local_dataset_name(spec, local)
    dataset_id, created = ensure_dataset(client, name)
    return _Current(name, local.rows, local.roles, [("external_id", r.id) for r in local.rows], dataset_id,
                    local=True, created=created)


def _current_from_table(client: Any, dataset_id: str, name: str, spec: DatasetSpec) -> Optional[_Current]:
    """The table's rows; None when the table is empty (a dataset the SDK made keeps its rows as
    versions only: version create writes no table rows)."""
    records = table_records(client, dataset_id)
    if not records:
        return None
    columns: list[str] = []
    for _, rec in records:
        for col in rec:
            if col not in columns:
                columns.append(col)
    roles = _infer_roles(columns, DatasetSpec(spec.source, spec.input, spec.expected, spec.metadata,
                                              spec.exclude_expected))
    rows: list[Row] = []
    for number, (row_id, rec) in enumerate(records, 1):
        meta = {c.removeprefix("metadata."): rec.get(c) for c in roles.metadata if c in rec}
        meta.update({c: rec.get(c) for c in roles.reserved if c in rec})
        rows.append(Row(id=row_id, number=number, data=rec, inputs={c: rec.get(c) for c in roles.input},
                        expected=rec.get(roles.expected) if roles.expected else None, metadata=meta))
    return _Current(name, rows, roles, [("legacy_row_id", r.id) for r in rows], dataset_id)


def _key_of(item: Mapping[str, Any], kind: str) -> Optional[str]:
    value = item.get("external_id") if kind == "external_id" else item.get("legacy_row") or item.get("legacy_row_id")
    return str(value) if value not in (None, "") else None


def pin_dataset(client: Any, source: Any, *, version: Any = None) -> ServerDataset:
    """Resolve ``source`` to one pinned version (see the module docstring)."""
    spec = source if isinstance(source, DatasetSpec) else DatasetSpec(source)
    check_local_only(spec)  # before any request (log_results and run alike)
    if version is not None:
        if is_local_source(spec.source):
            raise UsageError("version= selects a server dataset version; local rows have none")
        dataset_id, name = dataset_ref(client, spec.source)
        return from_version(client, dataset_id, name, str(version), f"version {str(version)[:8]} (pinned)")
    if is_local_source(spec.source):
        cur = _current_from_local(client, spec)
    else:
        dataset_id, name = dataset_ref(client, spec.source)
        table = _current_from_table(client, dataset_id, name, spec)
        if table is None:  # rows stored by the SDK: the latest version is the current rows
            latest = latest_version(client, dataset_id)
            if latest is None:
                raise UsageError(f"dataset {name!r} has no rows")
            return from_version(client, dataset_id, name, str(latest["id"]),
                                f"version {str(latest['id'])[:8]} (unchanged; the latest)")
        cur = table
    if len(cur.rows) > PlanTooLargeError.MAX_ITEMS:
        raise PlanTooLargeError(len(cur.rows))
    kind = cur.keys[0][0] if cur.keys else "external_id"
    ours = {key: item_content_hash(**item_for(row)) for (_, key), row in zip(cur.keys, cur.rows)}
    latest = latest_version(client, cur.dataset_id)
    theirs: dict[str, tuple[str, str]] = {}  # key -> (example_id, content_hash)
    if latest is not None:
        _, items = version_items(client, cur.dataset_id, str(latest["id"]))
        theirs = _theirs(items, kind)
        if _same(items, theirs, ours):
            return _pinned(cur, str(latest["id"]), {k: v[0] for k, v in theirs.items()},
                           f"version {str(latest['id'])[:8]} (unchanged)", created=False)
    first_of_empty = refuse_foreign_version(cur, spec, client, has_version=latest is not None)  # before any write
    added = sum(1 for k in ours if k not in theirs)
    changed = sum(1 for k, h in ours.items() if k in theirs and theirs[k][1] != h)
    removed = sum(1 for k in theirs if k not in ours)
    body: dict[str, Any] = {
        "items": [{**item_for(row), kind: key} for (_, key), row in zip(cur.keys, cur.rows)],
        "metadata": {ROLES_KEY: _roles_meta(cur.roles)},
        "description": "snapshot by fi.experiments",
    }
    if latest is not None:
        body["parent_version_id"] = str(latest["id"])
    from fi.generated.openapi_client.models.dataset_version_create import DatasetVersionCreate

    created = _plain(_result(_plain(client.datasets.versions.create(cur.dataset_id, DatasetVersionCreate.from_dict(body)))))
    version_id = str(created["id"])
    _, items = version_items(client, cur.dataset_id, version_id)
    ids = {key: str(it["example_id"]) for it in items if (key := _key_of(it, kind)) is not None}
    delta = f"+{added} rows, {changed} changed, {removed} removed" if latest is not None else f"{len(cur.rows)} rows"
    note = (f"version {version_id[:8]}: {first_version_note(cur.name, len(cur.rows))}" if first_of_empty
            else f"snapshotted version {version_id[:8]} ({delta})")
    return _pinned(cur, version_id, ids, note, created=True)


def _theirs(items: Sequence[Mapping[str, Any]], kind: str) -> dict[str, tuple[str, str]]:
    out: dict[str, tuple[str, str]] = {}
    for it in items:
        key = _key_of(it, kind)
        if key is not None:
            out[key] = (str(it["example_id"]), str(it.get("content_hash") or ""))
    return out


def _same(items: Sequence[Any], theirs: Mapping[str, tuple[str, str]], ours: Mapping[str, str]) -> bool:
    return len(items) == len(ours) and all(theirs.get(k, ("", ""))[1] == h for k, h in ours.items())


class DatasetChangedError(JournalError):
    code = "DATASET_CHANGED"


def pin_resumed(client: Any, source: Any, *, dataset_id: str, version_id: str, name: str) -> ServerDataset:
    """``resume=``: the run's journaled version, read back. Nothing is created, and a newer version
    made since does not matter; the current rows must still hash to that version's items, or the
    resume is refused."""
    spec = source if isinstance(source, DatasetSpec) else DatasetSpec(source)
    _, items = version_items(client, dataset_id, version_id)
    if is_local_source(spec.source):
        local = load_local(spec)
        cur: Optional[_Current] = _Current(name, local.rows, local.roles, [("external_id", r.id) for r in local.rows],
                                           dataset_id)
    else:
        cur = _current_from_table(client, dataset_id, name, spec)
        if cur is None:  # rows stored by the SDK: the version is the rows
            return from_version(client, dataset_id, name, version_id, f"version {version_id[:8]} (the run's own)")
    kind = cur.keys[0][0] if cur.keys else "external_id"
    ours = {key: item_content_hash(**item_for(row)) for (_, key), row in zip(cur.keys, cur.rows)}
    theirs = _theirs(items, kind)
    if not _same(items, theirs, ours):
        changed = sum(1 for k, h in ours.items() if theirs.get(k, ("", ""))[1] != h)
        gone = sum(1 for k in theirs if k not in ours)
        raise DatasetChangedError(
            f"the rows changed since the run started ({changed} new or edited, {gone} removed against version "
            f"{version_id[:8]}); a resume needs the same rows. Start a new run"
        )
    return _pinned(cur, version_id, {k: v[0] for k, v in theirs.items()},
                   f"version {version_id[:8]} (the run's own)", created=False)


def _pinned(cur: _Current, version_id: str, ids: Mapping[str, str], note: str, *, created: bool) -> ServerDataset:
    rows: list[Row] = []
    for (_, key), row in zip(cur.keys, cur.rows):
        example_id = ids.get(key)
        if example_id is None:
            raise UsageError(f"the server version {version_id} has no item for row {key!r}; re-run to snapshot again")
        rows.append(Row(id=example_id, number=row.number, data=row.to_dict(), inputs=row.inputs,
                        expected=row.expected, metadata=row.metadata))
    return ServerDataset(cur.name, rows, cur.roles, cur.dataset_id, version_id, note, created_version=created)
