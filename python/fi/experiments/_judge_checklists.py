"""One run keeps one ``judge()`` checklist: journaled, and reused by a resume.

A judge's checklist is its one read of its CRITERIA (model output, wave 2d), read on the judge's first row. Before this,
a resumed run read it again: its remaining rows could be judged on other parts than its first rows, and its metadata
showed only the new read. Now:

- ``journal`` (every run, once its journal is open): each judge journals a ``judge_checklist`` line before any row is
  judged on its checklist, at once when the judge already holds one (a judge object reused from an earlier run), else
  when it reads it (``Judge.on_checklist``). The line holds the judge's name, its model, a SHA-256 of its CRITERIA (the
  text itself stays out of the journal) and the parts.
- ``restore`` (a resume, before any request): each judge with a journaled checklist gets it back and reads nothing
  again. A judge whose CRITERIA or model differ from the journaled ones is refused, like a changed param (one run never mixes two judges), and the message says how to start a new run instead.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any, Mapping, Optional, Sequence

from fi.experiments._resume_params import new_run_how
from fi.experiments.errors import JournalError, UsageError


def _judges(evaluators: Sequence[Any]) -> list[Any]:
    return [ev for ev in evaluators if getattr(ev, "kind", None) == "judge" and hasattr(ev, "on_checklist")]


def criteria_sha256(criteria: str) -> str:
    return hashlib.sha256(criteria.encode("utf-8")).hexdigest()


def restore(run_id: str, checklists: Mapping[str, dict], evaluators: Sequence[Any],
            argv: Optional[Sequence[str]] = None) -> None:
    """Give each judge of a resumed run the checklist its run journaled; refuse a judge that changed."""
    from fi.experiments.evaluators._judge_prompt import parse_parts

    for ev in _judges(evaluators):
        then = checklists.get(ev.names[0])
        if then is None:  # never read before the stop (or an older SDK's journal): this run reads and journals it
            continue
        diffs = [what for what, changed in (
            ("its CRITERIA differ", then.get("criteria_sha256") != criteria_sha256(ev.criteria)),
            (f"its model is {ev.model!r}, the run's was {then.get('model')!r}", then.get("model") != ev.model),
        ) if changed]
        if diffs:
            raise UsageError(
                f"resume={run_id}: judge {ev.names[0]!r} differs from the journaled run ({'; '.join(diffs)}). A resume "
                "judges the rest of the run on the run's own checklist, so it was refused and nothing was sent. To "
                f"judge with the new settings, start a new run instead: {new_run_how(argv)} (it gets a new run id; run "
                f"{run_id}'s results stay as they are)."
            )
        try:
            ev.parts = parse_parts(json.dumps({"parts": then.get("parts")}))
        except (TypeError, ValueError) as exc:
            raise JournalError(f"resume={run_id}: the journaled checklist of judge {ev.names[0]!r} is unreadable "
                               f"({exc})") from exc


def journal(evaluators: Sequence[Any], run_journal: Any, restored: Mapping[str, dict]) -> None:
    """Journal each judge's checklist before any row of this run is judged on it (``restored`` ones are there)."""
    for ev in _judges(evaluators):
        def write(parts: Any, ev: Any = ev) -> None:
            try:
                run_journal.event("judge_checklist", judge=ev.names[0], model=ev.model,
                                  criteria_sha256=criteria_sha256(ev.criteria), parts=[p.as_dict() for p in parts])
            except JournalError:  # the run is over (its journal closed): a judge used after it journals nothing
                pass

        ev.on_checklist = write
        if ev.parts is not None and ev.names[0] not in restored:
            write(ev.parts)
