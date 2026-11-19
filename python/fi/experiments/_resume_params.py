"""A resume continues a journaled run with the params it started with.

- **Placeholders are refused.** The printed resume line and ``plan.json`` show a credential as
  ``[redacted]``. Running that line as printed would hand the remaining trials the placeholder in place
  of the key, so a param whose value is ``[redacted]`` (or, for a param the run journaled redacted,
  contains it) stops the resume with a UsageError that names the param and asks for the real value.
- **Changed params are refused**. A param that differs from the journaled plan, is missing, or
  is new stops the resume: one run never mixes two models. A value the journal holds only redacted cannot
  be compared, and is not. The message says how to start a new run instead: the same command without
  ``--resume`` (CLI, from this invocation's argv with its secrets redacted), or the same call without
  ``resume=`` (Python). The new run gets its own id; the resumed run's results stay as they are.
"""

from __future__ import annotations

import json
from typing import Any, Mapping, Optional, Sequence

from fi.experiments._redact import REDACTED, Redactor
from fi.experiments.errors import UsageError

_SHOW = 60


def _dump(value: Any) -> str:
    try:
        return json.dumps(value, sort_keys=True, ensure_ascii=False, default=repr)
    except (TypeError, ValueError):
        return repr(value)


def _show(value: Any) -> str:
    text = _dump(value)
    return text if len(text) <= _SHOW else text[: _SHOW - 1] + "…"


def _has_placeholder(value: Any) -> bool:
    if isinstance(value, str):
        return value == REDACTED
    if isinstance(value, Mapping):
        return any(_has_placeholder(v) for v in value.values())
    if isinstance(value, (list, tuple)):
        return any(_has_placeholder(v) for v in value)
    return False


def redacted_names(raw: Mapping[str, Any], journaled: Mapping[str, Any]) -> list[str]:
    """The params whose journaled value the redactor changed (the run specification's ``redacted_params``)."""
    return sorted(str(k) for k in raw if _dump(raw[k]) != _dump(journaled.get(k)))


def new_run_how(argv: Optional[Sequence[str]]) -> str:
    """How to start a new run instead of resuming: the CLI command without ``--resume``, or Python's call."""
    if argv:
        import shlex

        kept: list[str] = []
        skip = False
        for token in argv:
            if skip:
                skip = False
            elif token == "--resume":
                skip = True
            elif not token.startswith("--resume="):
                kept.append(token)
        from fi.experiments._cli.commands import hidden_values

        hidden = hidden_values(kept)
        note = (f" (it shows {', '.join(hidden)} as [redacted]: put the real value(s) back first, or the new run "
                "uses the placeholder)") if hidden else ""
        return f"run the same command without --resume{note}: {shlex.join(['futureagi-py', *Redactor().value(kept)])}"
    return "call run() / log_results() again without resume="


def check(run_id: str, plan: Mapping[str, Any], params: Mapping[str, Any], redactor: Redactor,
          argv: Optional[Sequence[str]] = None) -> None:
    """Refuse a resume whose params hold a placeholder or differ from the journaled run."""
    hidden = set(plan.get("redacted_params") or ())
    placeholders = [str(k) for k, v in params.items()
                    if _has_placeholder(v) or (str(k) in hidden and REDACTED in _dump(v))]
    if placeholders:
        names = ", ".join(placeholders)
        raise UsageError(
            f"resume={run_id}: param {names} is {REDACTED!r}, the placeholder the resume line and plan.json "
            f"print in place of a credential. Give the real value again (CLI: --param-str {placeholders[0]}=VALUE; "
            "Python: params=...); the run's other trials used it."
        )
    then = plan.get("params") or {}
    now = redactor.value(dict(params))
    diffs = []
    for k in sorted(set(then) | set(now)):
        if k not in now:
            diffs.append(f"{k} is missing (the run has {_show(then[k])})")
        elif k not in then:
            diffs.append(f"{k}={_show(now[k])} is not in the run")
        elif REDACTED not in _dump(then[k]) and _dump(then[k]) != _dump(now[k]):
            diffs.append(f"{k} is {_show(now[k])}, the run has {_show(then[k])}")
    if diffs:
        raise UsageError(
            f"resume={run_id}: the params differ from the journaled run ({'; '.join(diffs)}). A resume runs the "
            f"rest of the run with its own params, so it was refused and nothing was sent. To use the new params, "
            f"start a new run instead: {new_run_how(argv)} (it gets a new run id; run {run_id}'s results stay as "
            "they are)."
        )
