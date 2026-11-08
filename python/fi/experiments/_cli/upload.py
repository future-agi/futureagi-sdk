"""``futureagi-py upload FILE --dataset D [--eval ...]``: store results made elsewhere as a run.

The CLI face of ``experiments.log_results``. Each line of FILE is one result
(``example_id`` / ``id`` / ``number``, ``trial``, ``output``, ``error``, ``latency_ms``,
``cost_usd``, ``trace_id``, ``scores``). Nothing is re-executed.
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any

HELP = "store results made elsewhere (a results.jsonl) as a run on a dataset"


def register_upload(subparsers: Any, install_hint: str) -> None:
    p = subparsers.add_parser(
        "upload",
        help=HELP,
        description="Store results made elsewhere as a run. Each line of FILE names its row (example_id, id or "
                    "number) and may carry trial, output, error, latency_ms, cost_usd, trace_id and scores.",
    )
    p.add_argument("file", metavar="FILE", help="results.jsonl")
    p.add_argument("--dataset", required=True, metavar="NAME|ID|rows.jsonl", help="the dataset the results belong to")
    p.add_argument("--version", metavar="V", help="the dataset version the results were made on")
    p.add_argument("--dataset-name", dest="dataset_name", metavar="NAME",
                   help="the server dataset a rows.jsonl is stored in (needed to upload one)")
    p.add_argument("--add-version", dest="add_version", action="store_true",
                   help="allow adding a version to an existing dataset fi.experiments did not create")
    p.add_argument("--eval", action="append", metavar="NAME[:k=v,...]", help="score the outputs with a template")
    p.add_argument("--eval-map", dest="eval_map", action="append", metavar="EVAL:key=column|@file|==literal")
    p.add_argument("--pass-label", dest="pass_label", action="append", metavar="EVAL=LABEL")
    p.add_argument("--judge-model", dest="judge_model", metavar="M")
    p.add_argument("--name", help="the run name (default log_results)")
    p.add_argument("--description")
    p.add_argument("--metadata", action="append", metavar="k=v")
    p.add_argument("--experiment", metavar="ID", help="attach the run to this experiment")
    p.add_argument("--resume", metavar="RUN", help="send what a stalled or interrupted upload of FILE did not")
    p.add_argument("--json", action="store_true",
                   help="print one JSON object (schema: fi/experiments/schemas/cli-json.schema.json)")
    p.add_argument("--quiet", action="store_true")
    p.add_argument("--env-file", dest="env_file", metavar="PATH")
    p.add_argument("--no-env-file", dest="no_env_file", action="store_true")
    p.set_defaults(func=_upload_command, install_hint=install_hint)

    from fi._cli import registry

    registry.set_section("upload", "evaluate")


def _upload_command(args: argparse.Namespace) -> int:
    """``upload_command`` with this command's own missing-keys line: it has no ``--no-upload``."""
    from fi._credentials import CredentialsMissingError
    from fi.experiments._log_results import NO_KEYS_HINT

    try:
        return upload_command(args)
    except CredentialsMissingError as exc:
        if exc.hint == NO_KEYS_HINT:
            raise
        raise CredentialsMissingError(exc.base_url, exc.missing, exc.login_skipped, hint=NO_KEYS_HINT) from exc


def upload_command(args: argparse.Namespace) -> int:
    from fi.experiments._cli.run import _dataset_arg, _kv, eval_overlay, load_env_file
    from fi.experiments._log_results import log_results
    from fi.experiments.errors import EXIT_OK

    load_env_file(args, sys.stderr)
    result = log_results(
        _dataset_arg(args),
        args.file,
        eval_overlay(args),
        name=args.name,
        description=args.description,
        metadata=dict(_kv(m, "--metadata") for m in args.metadata or []),
        experiment=args.experiment,
        version=args.version,
        judge_model=args.judge_model,
        resume=args.resume,
        progress=not args.json and not args.quiet,
        argv=list(sys.argv[1:]),
    )
    if args.json:
        print(json.dumps({"run_id": result.run_id, "status": result.status, "url": result.url,
                          "url_note": result.url_note, "dataset_id": result.dataset_id,
                          "dataset_version_id": result.dataset_version_id, "items": len(result.items),
                          "summary": result.summary().model_dump(mode="json")}, sort_keys=True))
    return EXIT_OK
