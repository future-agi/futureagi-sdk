"""``futureagi-py evals``: run evaluations and list eval templates from the command line.

It replaces the ``fi`` console script that the retired ai-evaluation package installed.

    futureagi-py evals list [--json]
    futureagi-py evals run TEMPLATE [--input KEY=VALUE ...] [--inputs FILE] [--model NAME] [--json]

Both commands call :class:`fi.evals.Evaluator`, so keys come from the same place as every other
command: ``FI_API_KEY`` / ``FI_SECRET_KEY``, else the saved ``futureagi-py login``. Exit codes follow the
CLI's table (``fi/_cli/README.md``): 0 when every evaluation returned an output, 2 for a usage error,
3 when the keys are missing, the server could not be reached or refused the request, or an
evaluation came back with no output.

Only ``argparse`` is imported at module level, so ``futureagi-py --help`` stays fast.
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any, Dict, List, Optional

INSTALL_HINT = 'pip install "futureagi[evals]"'


def register(subparsers: Any) -> None:
    from fi._cli import registry

    p = subparsers.add_parser("evals", help="run evaluations and list eval templates")
    p.set_defaults(install_hint=INSTALL_HINT, func=_usage(p))
    sub = p.add_subparsers(dest="evals_command", metavar="COMMAND")

    ls = sub.add_parser("list", help="list the eval templates your keys can run")
    ls.add_argument("--json", action="store_true", help="print one JSON object")
    ls.set_defaults(func=list_command)

    run = sub.add_parser("run", help="run one eval template on one set of inputs")
    run.add_argument("template", metavar="TEMPLATE", help="the eval template name, for example toxicity")
    run.add_argument("--input", dest="inputs", action="append", default=[], metavar="KEY=VALUE",
                     help="one input (repeat for more); the value is a string")
    run.add_argument("--inputs", dest="inputs_file", metavar="FILE",
                     help="a JSON object of inputs ('-' reads standard input); --input values override it")
    run.add_argument("--model", dest="model", metavar="NAME", help="the evaluator model, for example turing_flash")
    run.add_argument("--timeout", dest="timeout", type=int, metavar="SECONDS", help="the request timeout")
    run.add_argument("--json", action="store_true", help="print one JSON object")
    run.set_defaults(func=run_command)

    registry.set_section("evals", "evaluate")


def _usage(parser: argparse.ArgumentParser):
    def show(args: Any) -> int:
        parser.print_help(sys.stderr)
        return 2

    return show


_ERROR_CLASS: Any = None


def _error(message: str, cause: Optional[BaseException] = None, *, code: str = "EVALS_FAILED", exit_code: int = 3):
    """An ``SDKException`` the CLI core reports as ``error: <message>`` (or the ``--json`` error
    object) with this exit code. The class is made on first use, so nothing but ``argparse`` is
    imported when the group registers."""
    global _ERROR_CLASS
    if _ERROR_CLASS is None:
        from fi._sdk_exception import SDKException

        class EvalsCommandError(SDKException):
            code = "EVALS_FAILED"
            exit_code = 3

            def get_error_code(self) -> str:
                return self.code

        _ERROR_CLASS = EvalsCommandError
    err = _ERROR_CLASS(message, cause)
    err.code = code
    err.exit_code = exit_code
    return err


def _evaluator():
    from fi.evals.evaluator import Evaluator

    return Evaluator()


def _call(what: str, fn, *args: Any, **kwargs: Any) -> Any:
    """Run one SDK call; a failure that is not already an SDK error becomes one (exit 3)."""
    from fi._sdk_exception import SDKException

    try:
        return fn(*args, **kwargs)
    except SDKException:
        raise
    except (KeyboardInterrupt, ImportError):
        raise
    except Exception as exc:  # requests errors and the evaluator's plain exceptions
        raise _error(f"{what} failed: {exc}", exc) from exc


def _out(args: Any):
    return getattr(args, "stdout", None) or sys.stdout


def list_command(args: Any) -> int:
    evaluator = _evaluator()
    templates = _call("listing the eval templates", evaluator.list_evaluations) or []
    out = _out(args)
    if getattr(args, "json", False):
        print(json.dumps({"templates": templates}, default=str), file=out)
        return 0
    rows = [t for t in templates if isinstance(t, dict)]
    if not rows:
        print("No eval templates.", file=out)
        return 0
    for row in sorted(rows, key=lambda r: str(r.get("name", ""))):
        keys = ", ".join((row.get("config") or {}).get("required_keys") or [])
        print(f"{row.get('name', '?')}" + (f"  (inputs: {keys})" if keys else ""), file=out)
    return 0


def _read_inputs(args: Any) -> Dict[str, Any]:
    inputs: Dict[str, Any] = {}
    source = getattr(args, "inputs_file", None)
    if source:
        stdin = getattr(args, "stdin", None) or sys.stdin
        try:
            text = stdin.read() if source == "-" else open(source, encoding="utf-8").read()
        except OSError as exc:
            raise _error(f"cannot read --inputs {source}: {exc}", exc, code="EVALS_USAGE", exit_code=2) from exc
        try:
            loaded = json.loads(text)
        except ValueError as exc:
            raise _error(f"--inputs {source} is not JSON: {exc}", exc, code="EVALS_USAGE", exit_code=2) from exc
        if not isinstance(loaded, dict):
            raise _error(f"--inputs {source} must hold one JSON object", code="EVALS_USAGE", exit_code=2)
        inputs.update(loaded)
    for pair in getattr(args, "inputs", None) or []:
        key, sep, value = pair.partition("=")
        if not sep or not key.strip():
            raise _error(f"--input {pair!r} is not KEY=VALUE", code="EVALS_USAGE", exit_code=2)
        inputs[key.strip()] = value
    if not inputs:
        raise _error("give the inputs with --input KEY=VALUE or --inputs FILE", code="EVALS_USAGE", exit_code=2)
    return inputs


def _row(result: Any) -> Dict[str, Any]:
    if result is None:
        return {"name": None, "output": None, "reason": "no result"}
    data = result.model_dump() if hasattr(result, "model_dump") else dict(vars(result))
    return {k: data.get(k) for k in ("name", "output", "reason", "output_type", "eval_id", "model")}


def run_command(args: Any) -> int:
    inputs = _read_inputs(args)
    evaluator = _evaluator()
    kwargs: Dict[str, Any] = {"model_name": getattr(args, "model", None)}
    if getattr(args, "timeout", None):
        kwargs["timeout"] = args.timeout
    batch = _call(f"evaluating {args.template}", evaluator.evaluate, args.template, inputs, **kwargs)
    rows: List[Dict[str, Any]] = [_row(r) for r in (getattr(batch, "eval_results", None) or [])]
    failed = [r for r in rows if r.get("output") is None]
    out = _out(args)
    if getattr(args, "json", False):
        print(json.dumps({"template": args.template, "results": rows}, default=str), file=out)
    else:
        for r in rows:
            reason = f" ({r['reason']})" if r.get("reason") else ""
            print(f"{r.get('name') or args.template}: {r.get('output')}{reason}", file=out)
        if not rows:
            print(f"{args.template}: no result", file=out)
    return 3 if failed or not rows else 0
