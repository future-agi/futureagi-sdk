"""``register(subparsers)`` for the experiments group: ``futureagi-py run TARGET``.

Imports only argparse at module level. ``--help`` shows the 13 everyday flags; ``--help-all``
shows every flag of this build, grouped.

The CLI core (``fi/_cli``, the shared base) imports nothing from ``fi.experiments``; what it used to
do for this group is registered here: ``run`` in the Evaluate help section, the ``run --`` check
(a pre-parse hook), the resume line on Ctrl-C (an interrupt hook), the flush of abandoned task
threads (an exit hook), the install line for a missing extra (``install_hint``) and the
``doctor`` arguments its section reads.
"""

from __future__ import annotations

import argparse
import sys
from typing import Optional, Sequence

INSTALL_HINT = 'pip install "futureagi[experiments]"'

EVERYDAY_TITLE = "everyday options"

# (group title, [(flags, kwargs)]) for --help-all. Every flag here is parsed and acts in this build.
MORE: list[tuple[str, list[tuple[tuple[str, ...], dict]]]] = [
    ("Data", [
        (("--version",), dict(dest="version", metavar="V",
                              help="pin this server dataset version (default: the latest if unchanged, else a new snapshot)")),
        (("--input-column",), dict(dest="input_column", metavar="COL", help="the input column when there are several")),
        (("--expected-column",), dict(dest="expected_column", metavar="COL", help="the expected column")),
        (("--rows",), dict(dest="rows", metavar="SEL", help="3,7,T12 (numbers or ids) | failed:RUN | new:RUN | sample:N")),
        (("--seed",), dict(dest="seed", type=int, metavar="S", help="seed for --rows sample:N (default 0)")),
        (("--from-column",), dict(dest="from_column", metavar="COL", help="score-only: the outputs are this column")),
        (("--dataset-name",), dict(dest="dataset_name", metavar="NAME",
                                   help="the server dataset a rows.jsonl is stored in (needed to upload one)")),
        (("--add-version",), dict(dest="add_version", action="store_true", default=False,
                                  help="allow adding a version to an existing dataset fi.experiments did not create")),
    ]),
    ("Evaluation", [
        (("--eval-map",), dict(dest="eval_map", action="append", metavar="EVAL:key=column|@file|==literal",
                               help="map a template key (repeatable)")),
        (("--pass-label",), dict(dest="pass_label", action="append", metavar="EVAL=LABEL",
                                 help="the passing label of a choices template (repeatable)")),
    ]),
    ("Identity", [
        (("--description",), dict(dest="description")),
        (("--metadata",), dict(dest="metadata", action="append", metavar="k=v", help="run metadata (repeatable)")),
        (("--experiment",), dict(dest="experiment", metavar="ID",
                                 help="attach the stored run to this experiment (an id)")),
        (("--project",), dict(dest="project", help='tracing project (default "<dataset> · experiments")')),
    ]),
    ("Limits", [
        (("--retries",), dict(dest="retries", type=int, metavar="N", help="re-run a trial that raised, N times")),
        (("--fail-fast",), dict(dest="fail_fast", type=int, metavar="N",
                                help="stop when the first N trials fail with one error (default 5; 0 = off)")),
        (("--price",), dict(dest="price", action="append", metavar="MODEL=IN,OUT",
                            help="USD per 1M input/output tokens, for --max-cost-usd (repeatable)")),
    ]),
    ("Params", [
        (("--param-str",), dict(dest="param_str", action="append", metavar="k=v", help="a string param (repeatable)")),
    ]),
    ("Tracing", [
        (("--no-trace",), dict(dest="no_trace", action="store_true", default=None, help="no spans")),
        (("--instrument",), dict(dest="instrument", metavar="auto|none|NAME,...", help="traceAI instrumentors")),
    ]),
    ("Output and CI", [
        (("--json",), dict(dest="json", action="store_true", default=False,
                           help="one JSON object on stdout (schema: fi/experiments/schemas/cli-json.schema.json)")),
        (("--max-error-rate",), dict(dest="max_error_rate", type=float, metavar="X",
                                     help="exit 5 above this error rate: trials that failed or got an error score "
                                          "(default 0 under CI=true)")),
        (("--error-policy",), dict(dest="error_policy", choices=("zero", "exclude"), metavar="zero|exclude",
                                   help="a failed trial in pass rates and --fail-under: zero (0, a fail; "
                                        "default) or exclude (left out); error scores are left out either way and "
                                        "count in --max-error-rate")),
        (("--resume",), dict(dest="resume", metavar="RUN", help="continue a journaled run")),
        (("--list",), dict(dest="list_runs", action="store_true", default=False, help="list a run file's runs")),
        (("--filter",), dict(dest="filter", action="append", metavar="NAME", help="run only matching declared runs")),
        (("--quiet", "-q"), dict(dest="quiet", action="store_true", default=False, help="no progress or header")),
        (("--verbose", "-v"), dict(dest="verbose", action="store_true", default=False, help="debug logging")),
    ]),
    ("Environment", [
        (("--env-file",), dict(dest="env_file", metavar="PATH", help="load this file instead of ./.env")),
        (("--no-env-file",), dict(dest="no_env_file", action="store_true", default=False, help="load no .env")),
    ]),
]

EVERYDAY: list[tuple[tuple[str, ...], dict]] = [
    (("--dataset",), dict(dest="dataset", metavar="NAME|ID|rows.jsonl",
                          help="a server dataset (name or id) or a local rows.jsonl")),
    (("--eval",), dict(dest="eval", action="append", metavar="NAME[:k=v,...]",
                       help="a platform template, by name (repeatable)")),
    (("--judge-model",), dict(dest="judge_model", metavar="M", help="judge for LLM-judge templates (or FI_JUDGE_MODEL)")),
    (("--trials",), dict(dest="trials", type=int, metavar="N", help="trials per row (default 1)")),
    (("--concurrency",), dict(dest="concurrency", type=int, metavar="N", help="trials in flight (default 4)")),
    (("--limit",), dict(dest="limit", type=int, metavar="N", help="the first N rows")),
    (("--timeout-s",), dict(dest="timeout_s", type=float, metavar="S",
                            help="seconds for task attempts, including retries, per trial (default 300); "
                                 "not evaluators, which need their own limits and yield error scores on timeout. "
                                 "On handled task timeout, sets ctx.cancelled, abandons the attempt and records a timeout; "
                                 "releases the slot without waiting for sync threads, which can exceed concurrency "
                                 "until they return (cooperative stop; no forced kill). Task-started default-executor "
                                 "work can keep workers occupied until return. Async cancellation can be delayed; "
                                 "tasks suppressing it can still have late results recorded instead of a timeout, "
                                 "with ctx.cancelled unset; this is being fixed")),
    (("--max-cost-usd",), dict(dest="max_cost_usd", type=float, metavar="X", help="stop starting trials past this spend")),
    (("--param",), dict(dest="param", action="append", metavar="k=v", help="a JSON-typed param (repeatable)")),
    (("--model",), dict(dest="model", metavar="M", help="shorthand for --param-str model=M")),
    (("--name",), dict(dest="name", help="the run name")),
    (("--no-upload", "--local"), dict(dest="no_upload", action="store_true", default=None,
                                      help="run for real; store no run on the platform (template "
                                           "evals still call the eval API, which stores and bills each call)")),
    (("--fail-under",), dict(dest="fail_under", action="append", metavar="X|EVAL=X",
                             help="exit 1 when a pass rate is below X (repeatable)")),
]


class _HelpAll(argparse.Action):
    def __init__(self, option_strings, dest, **kwargs):
        super().__init__(option_strings, dest, nargs=0, default=argparse.SUPPRESS, help="show every option, grouped")

    def __call__(self, parser, namespace, values, option_string=None):
        print(help_all_text(parser.prog), file=sys.stdout)
        parser.exit(0)


def help_all_text(prog: str) -> str:
    def row(flags: tuple, kw: dict) -> str:
        meta = kw.get("metavar")
        left = ", ".join(flags) + (f" {meta}" if meta and kw.get("action") not in ("store_true",) else "")
        return f"  {left:<44} {kw.get('help', '')}".rstrip()

    lines = [f"usage: {prog} TARGET [options]", "", "TARGET: a run file (run.py), a directory of *_eval.py files,",
             "        a code object (agent.py:graph, pkg.mod:make_agent), or none with --from-column.", "",
             f"{EVERYDAY_TITLE}:"]
    lines += [row(f, k) for f, k in EVERYDAY]
    for title, opts in MORE:
        lines += ["", f"{title}:"] + [row(f, k) for f, k in opts]
    return "\n".join(lines)


def register(subparsers) -> None:
    p = subparsers.add_parser(
        "run",
        help="run a task over a dataset and score it",
        description="Run a task over a dataset, score every trial, keep the evidence.\n"
                    "TARGET: run.py | dir/ | agent.py:graph | pkg.mod:make_agent | none with --from-column.\n"
                    "More options: --help-all",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("target", nargs="?", metavar="TARGET")
    group = p.add_argument_group(EVERYDAY_TITLE)
    for flags, kw in EVERYDAY:
        group.add_argument(*flags, **kw)
    for _, opts in MORE:
        for flags, kw in opts:
            p.add_argument(*flags, **{**kw, "help": argparse.SUPPRESS})
    p.add_argument("--help-all", action=_HelpAll)
    p.set_defaults(func=_run_command, install_hint=INSTALL_HINT)

    from fi.experiments._cli.upload import register_upload

    register_upload(subparsers, INSTALL_HINT)

    from fi._cli import doctor, registry

    registry.set_section("run", "evaluate")
    registry.add_pre_parse(_pre_parse)
    registry.add_on_interrupt(_interrupt_message)
    registry.add_on_exit(_flush_task_threads)
    doctor.add_argument(subparsers, "target", nargs="?", help="a run file or code object to resolve (optional)")
    doctor.add_argument(subparsers, "--dataset", help="the dataset, to check column roles for TARGET")
    doctor.add_argument(subparsers, "--judge-model", dest="judge_model")
    doctor.add_section("experiments", _doctor_section)


def _pre_parse(argv: list) -> Optional[int]:
    """``futureagi-py run -- CMD`` (the command target, a later release) prints the TARGET kinds, exit 2."""
    if argv[:1] == ["run"] and "--" in argv:
        from fi.experiments._cli.targets import unknown

        print(f"error: {unknown('-- ' + ' '.join(argv[argv.index('--') + 1:]))}", file=sys.stderr)
        return 2
    return None


def _interrupt_message(exc: BaseException, argv: Sequence[str]) -> Optional[str]:
    run_id = getattr(exc, "run_id", None)
    if not run_id:
        return None
    line = resume_line(argv, run_id, getattr(exc, "resume_filter", None))
    return f"Interrupted. The journal is kept. {hidden_note(argv)}Resume with:\n  {line}"


def _flush_task_threads(code: int) -> None:
    """Abandoned timed-out task threads must not hold the process (console script only)."""
    sync = sys.modules.get("fi.experiments._sync")  # never imported: no run, nothing to flush
    if sync is not None and sync.running_task_threads():
        sync.exit_after_flush(code)


def resume_line(argv: Sequence[str], run_id: str, label: Optional[str] = None) -> str:
    """The exact command that resumes ``run_id``: this invocation's argv (secrets redacted), without
    any earlier ``--resume``; when a run file declared several runs, ``--filter LABEL`` replaces
    the given filters so exactly the interrupted run is selected."""
    import shlex

    from fi.experiments._redact import Redactor

    kept = drop_flags(argv, ("--resume", "--filter") if label else ("--resume",))
    if label:
        kept += ["--filter", label]
    return shlex.join(["futureagi-py", *Redactor().value(kept), "--resume", run_id])


def drop_flags(argv: Sequence[str], drop: Sequence[str]) -> list[str]:
    """``argv`` without the given value flags (``--flag VALUE`` and ``--flag=VALUE``)."""
    kept: list[str] = []
    skip = False
    for token in argv:
        if skip:
            skip = False
            continue
        if token in drop:
            skip = True
            continue
        if any(token.startswith(flag + "=") for flag in drop):
            continue
        kept.append(token)
    return kept


def hidden_values(argv: Sequence[str]) -> list[str]:
    """The names (or flags) whose values the resume line prints as ``[redacted]``, in argv order."""
    import re

    from fi.experiments._redact import REDACTED, Redactor

    redactor = Redactor()
    names: list[str] = []
    prev = None
    for token in argv:
        shown = redactor.value(token)
        if shown != token and REDACTED in shown:
            m = re.search(r"([A-Za-z_][A-Za-z0-9_.-]*)=\[redacted\]", shown)
            name = m.group(1) if m else (prev if prev and prev.startswith("-") else "a value")
            if name not in names:
                names.append(name)
        prev = token
    return names


def hidden_note(argv: Sequence[str]) -> str:
    """One sentence for a resume line that hides values; empty when it hides none (M2)."""
    names = hidden_values(argv)
    if not names:
        return ""
    return (f"The line below shows {', '.join(names)} as [redacted]: put the real value(s) back before you run it "
            "(a resume refuses the placeholder). ")


# The shared CredentialsMissingError names no CLI flag; `futureagi-py run` adds its own.
NO_KEYS_HINT = "Or add --no-upload to run locally without a server."


def _run_command(args) -> int:
    from fi._credentials import CredentialsMissingError
    from fi.experiments._cli.run import run_command

    try:
        return run_command(args)
    except CredentialsMissingError as exc:  # MissingAuthError too: one line with this group's flag
        from fi.experiments._upload_session import PY_NO_KEYS_HINT

        if exc.hint and exc.hint != PY_NO_KEYS_HINT:
            raise
        raise CredentialsMissingError(exc.base_url, exc.missing, exc.login_skipped, hint=NO_KEYS_HINT) from exc


def _doctor_section(args) -> list:
    from fi.experiments._cli.run import doctor_lines

    return doctor_lines(args)
