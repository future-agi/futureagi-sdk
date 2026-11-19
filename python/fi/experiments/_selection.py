"""Row selection: ``rows=`` ids / numbers, ``failed(run)``,
``new_since(run)`` and ``sample(n, seed=0)``. Split out of ``_dataset.py`` (the 400-line module rule).
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Any, Optional, Sequence, Union

from fi.experiments._dataset import Row
from fi.experiments.errors import UsageError


@dataclass(frozen=True)
class RowSelector:
    kind: str  # "failed" | "new" | "sample"
    run_id: Optional[str] = None
    n: Optional[int] = None
    seed: int = 0

    @property
    def non_final(self) -> bool:
        return self.kind == "sample"

    def describe(self) -> str:
        if self.kind == "sample":
            return f"sample:{self.n} (seed {self.seed})"
        return f"{self.kind}:{self.run_id}"


def failed(run: Any) -> RowSelector:
    """A new run over ``run``'s failed, skipped or unfinished rows (from the local journal)."""
    return RowSelector("failed", run_id=_run_id_of(run))


def new_since(run: Any) -> RowSelector:
    """A new run over the rows that were not in ``run``'s plan."""
    return RowSelector("new", run_id=_run_id_of(run))


def sample(n: int, seed: int = 0) -> RowSelector:
    """``n`` random rows; the seed is fixed by default and printed, and the run is flagged non-final."""
    if int(n) <= 0:
        raise UsageError("sample(n) needs n >= 1")
    return RowSelector("sample", n=int(n), seed=int(seed))


def _run_id_of(run: Any) -> str:
    return str(getattr(run, "run_id", run))


def select_rows(
    rows: list[Row],
    selection: Union[None, RowSelector, Sequence[Union[str, int]]],
    limit: Optional[int] = None,
    *,
    journal_root: Any = None,
    remote: Any = None,
    uploaded: Optional[bool] = None,
) -> list[Row]:
    """``remote(run_id)``: the run's plan and item statuses from the server (SRV-3), used by
    ``failed:RUN`` / ``new:RUN`` when this machine has no journal for RUN. ``uploaded``: whether this
    run uploads; a local journal of the other kind names other ids (local row ids vs server example
    ids), so it is refused rather than silently selecting nothing."""
    chosen: list[Row]
    if selection is None:
        chosen = list(rows)
    elif isinstance(selection, RowSelector):
        if selection.kind == "sample":
            n = min(selection.n or 0, len(rows))
            picked = random.Random(selection.seed).sample(range(len(rows)), n)
            chosen = [rows[i] for i in sorted(picked)]
        else:
            from fi.experiments._journal import load
            from fi.experiments.errors import JournalError

            try:
                base = load(selection.run_id, journal_root)
            except JournalError:
                if remote is None:
                    raise
                base = remote(selection.run_id)
            else:
                if uploaded is not None and bool(base.plan.get("upload")) != uploaded:
                    then = "uploaded" if base.plan.get("upload") else "--no-upload (upload=False)"
                    raise UsageError(
                        f"run {selection.run_id} was a {then} run, so its rows have "
                        f"{'server example' if base.plan.get('upload') else 'local row'} ids that this "
                        f"{'uploaded' if uploaded else 'local'} run's rows do not carry. Run it the same way as "
                        f"run {selection.run_id}, or choose the rows by number or id"
                    )
            if selection.kind == "failed":
                want = set(base.failed_example_ids())
                chosen = [r for r in rows if r.id in want]
            else:
                had = set(base.example_ids())
                chosen = [r for r in rows if r.id not in had]
    else:
        if isinstance(selection, (str, bytes)):
            raise UsageError("rows= takes a list of ids or 1-based numbers, or a selector")
        by_id = {r.id: r for r in rows}
        chosen = []
        picked_ids: set[str] = set()
        for key in selection:
            if isinstance(key, bool):
                raise UsageError(f"rows= got {key!r}; use ids or 1-based numbers")
            if isinstance(key, int):
                if not 1 <= key <= len(rows):
                    raise UsageError(f"row number {key} is out of range 1..{len(rows)}")
                row = rows[key - 1]
            else:
                row = by_id.get(str(key))
                if row is None:
                    raise UsageError(f"no row with id {key!r}")
            if row.id not in picked_ids:  # by id: two rows with equal content are two rows
                picked_ids.add(row.id)
                chosen.append(row)
    if limit is not None:
        if limit < 0:
            raise UsageError("limit must be >= 0")
        chosen = chosen[:limit]
    return chosen
