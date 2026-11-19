"""``futureagi-py run --verbose`` (and ``logging.getLogger("fi.experiments").setLevel(logging.DEBUG)`` in code): what a
run decided and did, one DEBUG line each, on the ``fi.experiments`` logger (e2e CLI-17).

What is logged: the run's effective settings, each trial's outcome (row, trial, status, latency, attempts, the error's
type and each evaluator's score status), each judge request (host and path, the answer's status, the retry), and each
upload batch (items, the answer). Never a key, a header, an output, an input or a score's text: a value can hold
anything the task or the provider put there, so only ids, counts, statuses and timings are written.
"""

from __future__ import annotations

import logging
from typing import Any, Optional

log = logging.getLogger("fi.experiments")


def run_settings(cfg: Any, run_id: str, rows: int, journal_dir: Any) -> None:
    if not log.isEnabledFor(logging.DEBUG):
        return
    log.debug("run %s: %d rows x %s trial(s), concurrency %s, limit %s, timeout_s %s, upload %s, trace %s, "
              "error_policy %s, judge_model %s, max_cost_usd %s, journal %s", run_id, rows, cfg.trials,
              cfg.concurrency, cfg.limit, cfg.timeout_s, cfg.upload, _trace(cfg.trace), cfg.error_policy,
              cfg.judge_model or "(the default)", cfg.max_cost_usd, journal_dir)


def _trace(trace: Any) -> str:
    return trace if isinstance(trace, bool) else type(trace).__name__


def trial(row_id: str, trial_no: int, status: str, latency_ms: Optional[float], attempts: int, error: Any,
          scores: dict) -> None:
    if not log.isEnabledFor(logging.DEBUG):
        return
    took = f"{latency_ms:.0f} ms" if latency_ms is not None else "-"
    why = f" ({error.type})" if error is not None else ""
    graded = ", ".join(f"{n}={s.status}" + ("" if s.passed is None else f"/{'pass' if s.passed else 'fail'}")
                       for n, s in scores.items()) or "none"
    log.debug("trial %s#%d %s%s in %s, %d attempt(s); scores: %s", row_id, trial_no, status, why, took, attempts,
              graded)


def http(what: str, url: Any, status: int, retry: int = 0) -> None:
    if not log.isEnabledFor(logging.DEBUG):
        return
    try:
        import httpx

        u = httpx.URL(str(url))
        where = f"{u.scheme}://{u.host}{f':{u.port}' if u.port else ''}{u.path}"  # no userinfo, no query
    except Exception:
        where = "(unreadable URL)"
    log.debug("%s %s -> HTTP %s%s", what, where, status, f" (retry {retry})" if retry else "")
