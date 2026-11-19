"""The run's closing lines, and the resume hint a stopped upload ends with.

Split out of ``_engine.py`` (the 400-line module rule).
"""

from __future__ import annotations

from collections import Counter
from typing import Any, Callable, Mapping, Optional, Sequence

from fi.experiments._provider_errors import sentence_in
from fi.experiments._sync import running_task_threads
from fi.experiments.results import RUN_PAGE_IS, ExperimentResult, counts_note


def run_page(header: Mapping[str, Any], uploaded: bool) -> tuple[Optional[str], Optional[str]]:
    """``(url, url_note)`` for the result (FN-05): the ``app_url`` the server returned for the run (SRV-4, built from
    the deployment's configured frontend URL), or None and why. A link is never made up."""
    if not uploaded:
        return None, "the run was not uploaded (upload=False / --no-upload), so it has no page in the app"
    if not header:
        return None, "the server never confirmed the run, so no page is known for it"
    if "app_url" not in header:
        return None, "the server returned no app_url for the run (it predates SRV-4)"
    url = header.get("app_url")
    if isinstance(url, str) and url.strip().lower().startswith(("http://", "https://")):
        return url.strip(), None
    if url in (None, ""):
        return None, ("the server knows no app URL: its deployment sets no frontend URL (FRONTEND_URL or APP_URL), "
                      "so it returned none for the run")
    return None, f"the server's app_url for the run is not an http(s) link ({str(url)[:120]!r})"


def judge_reads(evaluators: Sequence[Any], rows: Sequence[Any] = ()) -> dict[str, Any]:
    """``result.metadata["judge_criteria"]``: for each ``judge()``, what its one read of the CRITERIA decided for every
    row of the run (L-SDK2c regression coverage; before this it was only on the spans): its checklist (``parts``, each judged on
    its own, wave 2d), whether a part asks about correctness, whether this run's rows had EXPECTED and whether some had
    none (computed from the run's own rows, never carried over from an earlier run of the same judge: L-SDK2d review
    S5), and whether EXPECTED was shown (only for such a part, on rows that have one). ``asks_correctness`` and
    ``parts`` are None when no row reached the judge."""
    had = any(getattr(r, "expected", None) is not None for r in rows)
    lacked = any(getattr(r, "expected", None) is None for r in rows)
    out = {}
    for ev in evaluators:
        if getattr(ev, "kind", None) != "judge" or not hasattr(ev, "asks_correctness"):
            continue
        parts = getattr(ev, "parts", None)
        out[ev.names[0]] = {"asks_correctness": ev.asks_correctness, "rows_had_expected": had,
                            "rows_without_expected": lacked, "expected_shown": bool(ev.asks_correctness) and had,
                            "parts": [p.as_dict() for p in parts] if parts else None}
    return {"judge_criteria": out} if out else {}


def _part_line(n: int, part: dict, had: bool, lacked: bool) -> str:
    """What one part of the checklist saw in this run (``_judge_prompt.part_request``/``shows_input``); a count the
    SDK made itself says so (wave 2f, ``_judge_count``)."""
    count = part.get("count")
    if isinstance(count, dict) and count.get("only"):
        from fi.experiments.evaluators._judge_count import Count

        asks = Count(**count).asks()
        return f"{n}. {part['part']}" + ("" if part.get("required", True) else " (optional)") + (
            f" [counted by the SDK: {asks}; no model call]")
    sees = []
    if part.get("needs_input"):
        sees.append("INPUT")
    elif part.get("needs_right_answer") and lacked:  # no reference: judged against the INPUT
        sees.append("INPUT on rows with no EXPECTED" if had else "INPUT (the rows have no EXPECTED)")
    if part.get("needs_right_answer") and had:
        sees.append("EXPECTED")
    counted = ""
    if isinstance(count, dict):
        from fi.experiments.evaluators._judge_count import Count

        counted = f"; its count ({Count(**count).asks()}) made by the SDK"
    return f"{n}. {part['part']}" + ("" if part.get("required", True) else " (optional)") + (
        f" [OUTPUT, {', '.join(sees)}{counted}]" if sees else f" [OUTPUT only{counted}]")


SHOWN_ERRORS = 3  # distinct error texts printed per evaluator and per error type
_ERROR_CUT = 300


def _said(text: Optional[str]) -> str:
    """What one error says, for the closing lines: a retirement's sentence (it names the model), else the text's
    first line, cut."""
    retired = sentence_in(text)
    if retired:
        return retired
    first = (text or "").strip().splitlines()[0] if (text or "").strip() else ""
    return first if len(first) <= _ERROR_CUT else first[:_ERROR_CUT] + "…"


def distinct_errors(texts: Sequence[Optional[str]]) -> list[tuple[str, int]]:
    """Each distinct error once, with how many rows said it: a retirement first, then the most frequent."""
    counts = Counter(_said(t) for t in texts)
    return sorted(counts.items(), key=lambda kv: (sentence_in(kv[0]) is None, -kv[1], kv[0]))


def _error_lines(label: str, texts: Sequence[Optional[str]]) -> list[str]:
    """``label: N errors: <what it said>`` for each distinct error, up to SHOWN_ERRORS of them (a judge on a retired model said only "errors 3", and the model's name was only inside each row's score)."""
    shown = distinct_errors(texts)
    lines = [f"  {label}: {n} error{'s' if n != 1 else ''}: {text}" for text, n in shown[:SHOWN_ERRORS] if text]
    rest = len(shown) - SHOWN_ERRORS
    if rest > 0:
        lines.append(f"  {label}: {rest} other distinct error{'s' if rest != 1 else ''} (each row's own is in its "
                     "score or error)")
    return lines


def print_summary(say: Callable[[str], None], result: ExperimentResult,
                  redact: Callable[[str], str] = lambda text: text) -> None:
    """The closing lines. ``redact`` (the run's redactor) is applied to every error text printed: a score's
    explanation can quote a provider's answer."""
    s = result.summary()
    say(f"Done     {s.completed} completed · {s.failed} failed · {s.skipped} skipped · status {result.status}")
    for ev in s.evaluators.values():
        mean = f"{ev.mean:.3f}" if ev.mean is not None else "-"
        rate = f"{ev.pass_rate:.0%}" if ev.pass_rate is not None else "-"
        # both counts, failed trials and error scores, and how each was counted
        say(f"  {ev.name:<32} mean {mean:>6}  pass {rate:>5}  {counts_note(ev)}")
        if ev.errors:
            for line in _error_lines(ev.name, [it.scores[ev.name].explanation for it in result.items
                                               if ev.name in it.scores and it.scores[ev.name].status == "error"]):
                say(redact(line))
    for name, read in (result.metadata.get("judge_criteria") or {}).items():
        if read.get("parts"):
            had, lacked = bool(read.get("rows_had_expected")), bool(read.get("rows_without_expected"))
            say(f"Judge    {name}: its checklist, read once from the CRITERIA; each part judged on its own: "
                + "; ".join(_part_line(n, part, had, lacked) for n, part in enumerate(read["parts"], 1)))
        if read.get("asks_correctness") is not None and read.get("rows_had_expected"):
            say(f"Judge    {name}: EXPECTED " + (
                "shown to it (its one read of the CRITERIA: they ask about correctness)" if read["expected_shown"] else
                "not shown (its one read of the CRITERIA: they do not ask about correctness, so each OUTPUT was "
                "judged against them alone)"))
    cap = result.metadata.get("cost_cap")
    if cap:
        if cap["enforced"] or cap["judge_usd"]:
            judge = f" (judge ${cap['judge_usd']:.4f})" if cap["judge_usd"] else ""
            say(f"  cost cap ${cap['usd']:g}: spent ${cap['spent_usd']:.4f}{judge}")
        else:
            say(f"  cost cap ${cap['usd']:g}: NOT enforced (no trial showed token usage or cost)")
    lat = s.latency_ms
    if lat.get("p50") is not None:
        say(f"  latency p50 {lat['p50']:.0f} ms · p95 {lat['p95']:.0f} ms · p99 {lat['p99']:.0f} ms")
    if s.tokens.get("total"):
        cost = f" · ${s.cost_usd:.4f}" if s.cost_usd is not None else ""
        say(f"  tokens {s.tokens['total']}{cost}")
    for kind, count in s.errors_by_type.items():
        say(f"  {count} × {kind}")
        messages = [i.error.message for i in result.items
                    if i.status in ("failed", "skipped") and i.error and i.error.type == kind and i.error.message]
        for line in _error_lines(kind, messages):
            say(redact(line))
    from fi.experiments._tracing.instrument import INSTRUMENTORS, failure_line

    by_pkg = {pkg: name for name, (_, _, pkg) in INSTRUMENTORS.items()}
    tracing = result.metadata.get("tracing") or {}
    for pkg, why in (tracing.get("failed_instrumentors") or {}).items():
        say(f"Tracing  {failure_line(by_pkg[pkg], why) if pkg in by_pkg else f'{pkg} failed to load ({why})'}")
    cl = tracing.get("capture")
    if cl:
        say(f"Tracing  {cl['trials']} trial(s) hit the local span capture limit ({cl['max_spans']} spans and "
            f"{cl['max_bytes'] // (1024 * 1024)} MiB per trial, values cut at {cl['max_value_bytes'] // 1024} KB): "
            f"{cl['dropped_spans']} span(s) not kept, {cl['truncated_values']} value(s) cut. Trace evaluators "
            "saw those trials in part (tokens and cost count every span); their root spans carry "
            "fi.experiment.local_capture.*")
        if cl.get("usage_spans_lost"):
            say(f"Tracing  {cl['usage_spans_lost']} LLM span(s) past the capture's usage records are NOT in the "
                "tokens, the cost or the cost cap")
    threads = running_task_threads()
    if threads:
        say(f"  {threads} timed-out task thread(s) still running (abandoned; they never block exit)")
    up = result.metadata.get("upload")
    if up:
        retries = f", {up['retries']} retried" if up.get("retries") else ""
        say(f"Upload   {up['acked']} items stored in {up['batches']} batch(es){retries} · run "
                 f"{result.run_id} is {up.get('server_status') or 'unknown'} on the server")
        say(f"App      {result.url} ({RUN_PAGE_IS})" if result.url else f"App      no link: {result.url_note}")
    say(f"Journal  {result.journal_dir}")


def add_resume_hint(exc: BaseException, run_id: str, cfg: Any) -> None:
    """A stalled or refused upload ends with the exact way to send the rest: the CLI command that
    parses (``resume_line``: this argv plus ``--resume``), or ``resume=`` in Python. A 409 means
    the journal and the server disagree, so it names no resume (its message says to start anew)."""
    from fi.experiments._upload import UploadConflictError

    if isinstance(exc, UploadConflictError) or not hasattr(exc, "custom_message"):
        return
    if cfg.argv is not None:
        from fi.experiments._cli.commands import hidden_note, resume_line

        note, how = hidden_note(cfg.argv), resume_line(cfg.argv, run_id, cfg.resume_label)
    else:
        note, how = "", f"resume={run_id!r}"
    exc.custom_message = (  # type: ignore[attr-defined]
        f"{exc}. Every trial is journaled; {note}send the rest with: {how}")
