"""Datasets, rows, column roles and row selection.

Local sources in this build: ``list[dict]`` and ``rows.jsonl``. Server datasets (name, id,
``fi.datasets.Dataset``) are pinned to a version by ``_server_dataset.py`` on upload.

Column roles, in order:
1. explicit: ``experiments.dataset(src, input="question", expected="answer", metadata=["tier"])``;
2. reserved control columns are never inputs (stored as metadata, read by their feature);
3. expected: the first of ``expected, expected_output, expected_text, answer, reference``;
4. metadata: ``metadata.*`` columns and a ``metadata`` dict column;
5. the id: ``id`` or ``example_id``;
6. input: every remaining column.
"""

from __future__ import annotations

import json
import uuid
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterator, Optional, Sequence, Union

from fi.experiments._plan import content_hash
from fi.experiments.errors import AmbiguousInputError, UsageError

RESERVED_COLUMNS = frozenset(
    {
        "tool_mocks",
        "start_state",
        "check",
        "setup",
        "trials",
        "criteria",
        # voice scenario columns
        "persona",
        "goal",
        "facts",
        "opening_line",
        "expected_outcome",
        "audio_conditions",
        "interruption_script",
    }
)
EXPECTED_NAMES = ("expected", "expected_output", "expected_text", "answer", "reference")
ID_NAMES = ("id", "example_id")
_ID_NAMESPACE = uuid.UUID("6f0f7d2e-3c1a-4c55-9a43-6b1f0e2a9d11")


class Row(Mapping):
    """One dataset row. ``row["question"]`` works; so do ``id``, ``number``, ``input``, ``inputs``,
    ``expected`` and ``metadata``."""

    __slots__ = ("id", "number", "inputs", "expected", "metadata", "_data", "_input_columns")

    def __init__(
        self,
        id: str,
        number: int,
        data: Mapping[str, Any],
        inputs: Mapping[str, Any],
        expected: Any = None,
        metadata: Optional[Mapping[str, Any]] = None,
    ) -> None:
        self.id = str(id)
        self.number = int(number)
        self._data = dict(data)
        self.inputs = dict(inputs)
        self.expected = expected
        self.metadata = dict(metadata or {})
        self._input_columns = list(self.inputs)

    @property
    def input(self) -> Any:
        if len(self._input_columns) == 1:
            return self.inputs[self._input_columns[0]]
        if not self._input_columns:
            return None
        raise AmbiguousInputError(self._input_columns)

    def __getitem__(self, key: str) -> Any:
        return self._data[key]

    def __iter__(self) -> Iterator[str]:
        return iter(self._data)

    def __len__(self) -> int:
        return len(self._data)

    def __repr__(self) -> str:
        return f"Row(id={self.id!r}, number={self.number}, inputs={self.inputs!r})"

    def to_dict(self) -> dict[str, Any]:
        return dict(self._data)


@dataclass(frozen=True)
class DatasetSpec:
    """``experiments.dataset(source, input=..., expected=..., metadata=[...], name=..., add_version=...)``."""

    source: Any
    input: Optional[Union[str, Sequence[str]]] = None
    expected: Optional[str] = None
    metadata: Sequence[str] = ()
    exclude_expected: Optional[str] = None  # the from_column(...) column is not "expected"
    name: Optional[str] = None  # the server dataset that local rows are stored in (uploaded runs)
    add_version: bool = False  # may add a version to an existing dataset fi.experiments did not create


def dataset(
    source: Any,
    *,
    input: Optional[Union[str, Sequence[str]]] = None,
    expected: Optional[str] = None,
    metadata: Sequence[str] = (),
    name: Optional[str] = None,
    add_version: bool = False,
) -> DatasetSpec:
    """Column roles for ``source``; for local rows on an uploaded run, the server dataset they go to.

    ``name``: the server dataset that ``list[dict]`` rows or a rows file are stored in; required for both when
    the run uploads (a file's stem is never the name: stems such as ``rows`` collide across projects).
    ``add_version=True``: the explicit opt-in to add these rows as a new version of an existing dataset that
    fi.experiments cannot tell it made (it has table rows, no version yet, or a first version the SDK did not
    write); without it such a dataset is never changed. An empty dataset with no version (a run that
    stopped before storing its rows leaves one) needs it too, until the server can create a first version only
    when there is none; with it, the run header says it wrote that dataset's first version. Both go with local
    rows on an uploaded run only: on a server dataset they are refused, and with ``upload=False`` they warn
   ."""
    if name is not None and (not isinstance(name, str) or not name.strip()):
        raise UsageError("dataset(name=...) must be a non-empty string")
    return DatasetSpec(source, input, expected, tuple(metadata), None, name.strip() if name else None,
                       bool(add_version))


def dataset_arg(source: Any, *, input: Any = None, expected: Optional[str] = None, name: Optional[str] = None,
                add_version: bool = False) -> Any:
    """``source`` with the CLI's column, name and opt-in flags applied (the CLI's ``--dataset`` value)."""
    if source is None or not (input or expected or name or add_version):
        return source
    spec = source if isinstance(source, DatasetSpec) else DatasetSpec(source)
    return dataset(spec.source, input=input or spec.input, expected=expected or spec.expected,
                   metadata=spec.metadata, name=name or spec.name, add_version=add_version or spec.add_version)


@dataclass
class Roles:
    input: list[str]
    expected: Optional[str]
    metadata: list[str]
    reserved: list[str]
    id: Optional[str]

    def require_single_input(self) -> str:
        if len(self.input) != 1:
            raise AmbiguousInputError(self.input) if self.input else UsageError(
                "the dataset has no input column; pass input='COLUMN'"
            )
        return self.input[0]

    def describe(self) -> str:
        exp = self.expected or "-"
        return f"input: {', '.join(self.input) or '-'} · expected: {exp}"


@dataclass
class LocalDataset:
    name: str
    rows: list[Row]
    roles: Roles
    source_kind: str  # "list" | "jsonl"
    content_hashes: list[str] = field(default_factory=list)

    @property
    def id(self) -> str:
        return "local:" + self.name


def _infer_roles(columns: list[str], spec: DatasetSpec) -> Roles:
    explicit_input = [spec.input] if isinstance(spec.input, str) else list(spec.input or [])
    for col in explicit_input + ([spec.expected] if spec.expected else []) + list(spec.metadata):
        if col not in columns:
            raise UsageError(f"column {col!r} is not in the dataset (columns: {', '.join(columns)})")
    id_col = next((c for c in ID_NAMES if c in columns), None)
    expected = spec.expected
    if expected is None:
        expected = next(
            (c for c in EXPECTED_NAMES if c in columns and c != spec.exclude_expected and c not in explicit_input),
            None,
        )
    reserved = [c for c in columns if c in RESERVED_COLUMNS]
    metadata = list(spec.metadata) + [
        c for c in columns if (c == "metadata" or c.startswith("metadata.")) and c not in spec.metadata
    ]
    if explicit_input:
        inputs = explicit_input
    else:
        taken = set(reserved) | set(metadata) | {expected, id_col}
        inputs = [c for c in columns if c not in taken]
    return Roles(input=inputs, expected=expected, metadata=metadata, reserved=reserved, id=id_col)


def _read_jsonl(path: Path) -> list[dict]:
    rows: list[dict] = []
    with path.open(encoding="utf-8") as fh:
        for n, line in enumerate(fh, 1):
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except ValueError as exc:
                raise UsageError(f"{path}:{n} is not valid JSON: {exc}") from exc
            if not isinstance(obj, dict):
                raise UsageError(f"{path}:{n} is not a JSON object")
            rows.append(obj)
    return rows


def is_local_source(source: Any) -> bool:
    if isinstance(source, DatasetSpec):
        return is_local_source(source.source)
    if isinstance(source, list):
        return True
    if isinstance(source, Path):
        return True
    if isinstance(source, str):
        return source.endswith((".jsonl", ".json")) or Path(source).is_file()
    return False


def load_local(source: Any) -> LocalDataset:
    spec = source if isinstance(source, DatasetSpec) else DatasetSpec(source)
    raw = spec.source
    if isinstance(raw, list):
        records, name, kind = raw, "rows", "list"
        if not all(isinstance(r, Mapping) for r in records):
            raise UsageError("a list dataset must contain dicts (one per row)")
    elif isinstance(raw, (str, Path)):
        path = Path(raw)
        if not path.is_file():
            raise UsageError(f"dataset file {str(path)!r} does not exist (a relative path is read from "
                             f"{Path.cwd()}). Check the path; a server dataset is named without a file suffix")
        if path.suffix == ".json":
            records = json.loads(path.read_text(encoding="utf-8"))
            if not isinstance(records, list):
                raise UsageError(f"{path} must hold a JSON list of row objects")
        else:
            records = _read_jsonl(path)
        name, kind = path.stem, "jsonl"
    else:
        raise UsageError(
            "server datasets (a name, an id or fi.datasets.Dataset) arrive with the upload step; "
            "this build runs list[dict] and rows.jsonl datasets"
        )
    if not records:
        raise UsageError("the dataset has no rows")
    columns: list[str] = []
    for rec in records:
        for key in rec:
            if key not in columns:
                columns.append(str(key))
    roles = _infer_roles(columns, spec)
    rows: list[Row] = []
    hashes: list[str] = []
    seen: dict[str, int] = {}
    ids: set[str] = set()
    for number, rec in enumerate(records, 1):
        h = content_hash(dict(rec))
        hashes.append(h)
        if roles.id and rec.get(roles.id) not in (None, ""):
            rid = str(rec[roles.id])
        else:
            occurrence = seen.get(h, 0)
            seen[h] = occurrence + 1
            rid = str(uuid.uuid5(_ID_NAMESPACE, f"{h}:{occurrence}"))
        if rid in ids:
            raise UsageError(f"duplicate row id {rid!r} (row {number})")
        ids.add(rid)
        meta: dict[str, Any] = {}
        for col in roles.metadata:
            if col in rec:
                if col == "metadata" and isinstance(rec[col], Mapping):
                    meta.update(rec[col])
                else:
                    meta[col.removeprefix("metadata.") if hasattr(col, "removeprefix") else col] = rec[col]
        for col in roles.reserved:
            if col in rec:
                meta[col] = rec[col]
        rows.append(
            Row(
                id=rid,
                number=number,
                data=rec,
                inputs={c: rec.get(c) for c in roles.input},
                expected=rec.get(roles.expected) if roles.expected else None,
                metadata=meta,
            )
        )
    return LocalDataset(name=name, rows=rows, roles=roles, source_kind=kind, content_hashes=hashes)


# row selection lives in _selection.py (the 400-line module rule); these names stay importable from here
from fi.experiments._selection import RowSelector, failed, new_since, sample, select_rows  # noqa: E402,F401
