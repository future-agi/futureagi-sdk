"""``futureagi-py run TARGET``: build the run(s) from TARGET and the flags, run them, apply the gates."""

from __future__ import annotations

import dataclasses
import json
import os
import sys
from pathlib import Path
from typing import Any, Optional

from fi.experiments._cli.targets import Target, discover, load_object, parse_target
from fi.experiments.errors import EXIT_CI_ERRORS, EXIT_GATE, EXIT_OK, UsageError


# ---- .env ----------------------------------------------------------------------------------------


def _parse_env_text(text: str) -> dict[str, str]:
    values: dict[str, str] = {}
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[len("export "):].lstrip()
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        key, value = key.strip(), value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        elif " #" in value:
            value = value.split(" #", 1)[0].rstrip()
        if key:
            values[key] = value
    return values


def load_env_file(args: Any, stream: Any) -> Optional[str]:
    """Load ``.env`` (or ``--env-file``). The real environment wins. Prints the file and the names it
    set (never a value), and calls out any ``*_BASE_URL``: provider SDKs and ``judge()`` read
    ``OPENAI_BASE_URL``, so a cloned repo's ``.env`` could send your real key to its own host. An
    FI_BASE_URL from here disables the saved login's keys (fi._credentials)."""
    if getattr(args, "no_env_file", False):
        return None
    path = Path(args.env_file) if getattr(args, "env_file", None) else Path.cwd() / ".env"
    if not path.is_file():
        if getattr(args, "env_file", None):
            raise UsageError(f"--env-file {path} does not exist")
        return None
    try:
        from dotenv import dotenv_values

        values = {k: v for k, v in dotenv_values(path).items() if v is not None}
    except ImportError:
        values = _parse_env_text(path.read_text(encoding="utf-8"))
    added: list[str] = []
    for key, value in values.items():
        if key not in os.environ:
            os.environ[key] = value
            added.append(key)
    base_urls = [k for k in added if k.upper().endswith("_BASE_URL")]
    if not getattr(args, "quiet", False):
        names = ", ".join(added) if added else "none"
        print(f"Env      loaded {path}: set {names} ({len(added)} of {len(values)}; the environment wins)",
              file=stream)
    for key in base_urls:  # printed even under --quiet: it decides where keys are sent
        print(f"Warning  {path} sets {key} to {_host_of(os.environ[key])}: requests that read it, and the "
              "keys they carry, go to that host", file=stream)
    return str(path)


def _host_of(url: str) -> str:
    """``scheme://host[:port]`` only: a URL may carry credentials, which are never printed."""
    from urllib.parse import urlsplit

    try:
        parts = urlsplit(url)
        port = f":{parts.port}" if parts.port else ""
        return f"{parts.scheme}://{parts.hostname}{port}" if parts.hostname else "a URL that does not parse"
    except ValueError:
        return "a URL that does not parse"


# ---- flags → run() keyword arguments --------------------------------------------------------------


def _kv(text: str, flag: str) -> tuple[str, str]:
    if "=" not in text:
        raise UsageError(f"{flag} takes k=v, got {text!r}")
    k, v = text.split("=", 1)
    if not k.strip():
        raise UsageError(f"{flag} takes k=v, got {text!r}")
    return k.strip(), v


def parse_rows(text: str, seed: Optional[int]) -> Any:
    from fi import experiments

    if text.startswith("failed:"):
        return experiments.failed(text.split(":", 1)[1])
    if text.startswith("new:"):
        return experiments.new_since(text.split(":", 1)[1])
    if text.startswith("sample:"):
        try:
            n = int(text.split(":", 1)[1])
        except ValueError:
            raise UsageError(f"--rows sample:N needs a number, got {text!r}") from None
        return experiments.sample(n, seed=seed or 0)
    out: list[Any] = []
    for token in (t.strip() for t in text.split(",")):
        if not token:
            continue
        out.append(int(token) if token.isdigit() else token)
    if not out:
        raise UsageError("--rows is empty")
    return out


def parse_prices(items: Optional[list[str]]) -> Optional[dict[str, tuple[float, float]]]:
    if not items:
        return None
    prices: dict[str, tuple[float, float]] = {}
    for item in items:
        model, pair = _kv(item, "--price")
        try:
            pin, pout = (float(x) for x in pair.split(","))
        except ValueError:
            raise UsageError(f"--price takes MODEL=IN,OUT (USD per 1M tokens), got {item!r}") from None
        prices[model] = (pin, pout)
    return prices


def parse_fail_under(items: Optional[list[str]]) -> Any:
    if not items:
        return None
    mapping: dict[str, float] = {}
    single: Optional[float] = None
    for item in items:
        try:
            if "=" in item:
                k, v = item.rsplit("=", 1)
                mapping[k] = float(v)
            else:
                single = float(item)
        except ValueError:
            raise UsageError(f"--fail-under takes X or EVAL=X, got {item!r}") from None
    if single is not None and mapping:
        raise UsageError("--fail-under takes either one X or EVAL=X pairs, not both")
    return single if single is not None else mapping


def overlay_from_args(args: Any) -> dict[str, Any]:
    """Only flags the user gave, as run() keyword arguments."""
    from fi.experiments._params import parse_cli_param

    out: dict[str, Any] = {}
    for key in ("judge_model", "trials", "concurrency", "limit", "timeout_s", "max_cost_usd", "name",
                "version", "description", "experiment", "project", "resume", "attach", "error_policy"):
        value = getattr(args, key, None)
        if value is not None:
            out[key] = value
    params: dict[str, Any] = {}
    for item in getattr(args, "param", None) or []:
        try:
            k, v = parse_cli_param(item)
        except ValueError as exc:
            raise UsageError(f"--param: {exc}") from None
        params[k] = v
    for item in getattr(args, "param_str", None) or []:
        k, v = parse_cli_param(item, as_string=True)
        params[k] = v
    if getattr(args, "model", None):
        params["model"] = args.model
    if params:
        out["params"] = params
    if getattr(args, "no_upload", None):
        out["upload"] = False
    if getattr(args, "rows", None):
        out["rows"] = parse_rows(args.rows, getattr(args, "seed", None))
    elif getattr(args, "seed", None) is not None:
        raise UsageError("--seed applies to --rows sample:N")
    if getattr(args, "metadata", None):
        out["metadata"] = dict(_kv(m, "--metadata") for m in args.metadata)
    if getattr(args, "no_trace", None):
        out["trace"] = False
    inst = getattr(args, "instrument", None)
    if inst is not None:
        out["instrument"] = "auto" if inst == "auto" else False if inst == "none" else [
            s.strip() for s in inst.split(",") if s.strip()]
    if getattr(args, "quiet", False):
        out["progress"] = False
    return out


def limits_overlay(args: Any) -> dict[str, Any]:
    out: dict[str, Any] = {}
    if getattr(args, "retries", None) is not None:
        out["retries"] = args.retries
    if getattr(args, "fail_fast", None) is not None:
        out["fail_fast"] = args.fail_fast
    prices = parse_prices(getattr(args, "price", None))
    if prices:
        out["prices"] = prices
    return out


def eval_overlay(args: Any) -> list[Any]:
    specs = getattr(args, "eval", None) or []
    if not specs:
        if getattr(args, "eval_map", None) or getattr(args, "pass_label", None):
            raise UsageError("--eval-map / --pass-label need an --eval")
        return []
    try:
        from fi.experiments.evaluators.hosted import templates_from_cli
    except ImportError:
        raise UsageError(
            "--eval runs platform templates through the hosted eval API, which this build does not include yet"
        ) from None
    return templates_from_cli(specs, getattr(args, "eval_map", None) or [], getattr(args, "pass_label", None) or [])


def _dataset_arg(args: Any, base: Any = None) -> Any:
    """``--dataset`` with ``--input-column`` / ``--expected-column`` / ``--dataset-name`` / ``--add-version``."""
    from fi.experiments._dataset import dataset_arg

    if getattr(args, "no_upload", None) and (getattr(args, "dataset_name", None) or getattr(args, "add_version", False)):
        raise UsageError("--dataset-name and --add-version say where an uploaded run stores its rows; with "
                         "--no-upload nothing is stored. Drop them, or drop --no-upload")

    return dataset_arg(getattr(args, "dataset", None) or base, input=getattr(args, "input_column", None),
                       expected=getattr(args, "expected_column", None), name=getattr(args, "dataset_name", None),
                       add_version=bool(getattr(args, "add_version", False)))


# ---- the command ----------------------------------------------------------------------------------


def build_runs(args: Any, target: Target) -> list[dict[str, Any]]:
    from fi import experiments
    from fi.experiments._cli import file_mode
    from fi.experiments._limits import Limits

    overlay = overlay_from_args(args)
    lim = limits_overlay(args)
    extra_evals = eval_overlay(args)
    argv = sys.argv[1:]
    runs: list[dict[str, Any]] = []
    if target.kind in ("file", "dir"):
        paths = [target.path] if target.kind == "file" else discover(target.path)  # type: ignore[list-item]
        collected = file_mode.collect(paths)
        declared = file_mode.select(collected, getattr(args, "filter", None))
        if getattr(args, "from_column", None):
            raise UsageError("--from-column replaces the task; use it without a run file")
        if "resume" in overlay and len(declared) != 1:
            names = ", ".join(d.name for d in declared)
            raise UsageError(
                f"--resume continues one run, and {len(declared)} declared runs are selected ({names}). "
                "Add --filter NAME to select the interrupted one."
            )
        if "attach" in overlay and len(declared) != 1:
            names = ", ".join(d.name for d in declared)
            raise UsageError(f"--run adds results to one run, and {len(declared)} declared runs are selected "
                             f"({names}). Add --filter NAME to select one.")
        several = (file_mode.name_contexts(declared, collected, getattr(args, "dataset", None))
                   if len(declared) > 1 and not getattr(args, "list_runs", False) else [])
        file_mode.refuse_one_name_for_many(several, args, argv)  # one --dataset-name for many rows files (M1)
        for i, d in enumerate(declared):
            kw = dict(d.kwargs)
            kw.pop("_source", None)
            kw.update(overlay)
            ds = _dataset_arg(args, kw.get("dataset"))
            if ds is not None:
                kw["dataset"] = ds
            if several:  # the name refusal shows a fix for this run alone
                kw["declared"] = {k: several[i][k] for k in ("run_file", "run_filter", "suggest")}
            if lim:
                base = kw.get("limits") or Limits()
                kw["limits"] = dataclasses.replace(base, **lim)
            if extra_evals:
                kw["evaluators"] = list(kw.get("evaluators") or ()) + extra_evals
            kw["_label"] = d.name
            runs.append(kw)
        return runs
    if getattr(args, "list_runs", False) or getattr(args, "filter", None):
        raise UsageError("--list and --filter apply to run files")
    dataset = _dataset_arg(args)
    if dataset is None and getattr(args, "attach", None) is None and getattr(args, "resume", None) is None:
        from fi.experiments._attach import NEEDS_ROWS  # --run reads the run's own rows; a resume checks its journal

        raise UsageError(NEEDS_ROWS)
    if target.kind == "none":
        task = experiments.from_column(args.from_column)
    else:
        if getattr(args, "from_column", None):
            raise UsageError("--from-column replaces the task; pass no TARGET with it")
        task = load_object(target)
    kw: dict[str, Any] = {"dataset": dataset, "task": task, "evaluators": extra_evals, **overlay}
    if lim:
        kw["limits"] = Limits(**lim)
    kw["_label"] = target.text or f"from_column:{args.from_column}"
    runs.append(kw)
    return runs


def run_command(args: Any) -> int:
    from fi import experiments

    stream = sys.stderr
    load_env_file(args, stream)
    target = parse_target(getattr(args, "target", None), from_column=getattr(args, "from_column", None))
    runs = build_runs(args, target)
    if getattr(args, "list_runs", False):
        for kw in runs:
            print(kw["_label"])
        return EXIT_OK
    if len(runs) > 1:
        check_names_first(runs)
    fail_under = parse_fail_under(getattr(args, "fail_under", None))
    max_error_rate = getattr(args, "max_error_rate", None)
    if max_error_rate is None and os.environ.get("CI", "").lower() == "true":
        max_error_rate = 0.0
    worst = EXIT_OK
    report: list[dict[str, Any]] = []
    several = len(runs) > 1
    for kw in runs:
        label = kw.pop("_label")
        kw.setdefault("progress", not getattr(args, "json", False) and not getattr(args, "quiet", False))
        from fi.experiments._engine import Engine, RunConfig
        from fi.experiments._sync import run_coroutine_sync

        cfg = RunConfig(**kw, argv=list(sys.argv[1:]), resume_label=label if several else None)
        try:
            result = run_coroutine_sync(lambda cfg=cfg: Engine(cfg).execute())
        except KeyboardInterrupt as exc:
            if several:  # the resume line must select exactly this declared run
                exc.resume_filter = label  # type: ignore[attr-defined]
            raise
        gate = result.assert_passing(fail_under, max_error_rate=max_error_rate, raise_on_fail=False)
        if not gate.passed and not getattr(args, "json", False):
            for reason in gate.reasons:
                print(f"Gate     {label}: {reason}", file=stream)
        worst = max(worst, gate.exit_code, key=_severity)
        report.append({
            "label": label,
            "run_id": result.run_id,
            "name": result.name,
            "status": result.status,
            "url": result.url,
            "url_note": result.url_note,
            "journal_dir": result.journal_dir,
            "summary": result.summary().model_dump(mode="json"),
            "gate": gate.model_dump(mode="json"),
        })
    if getattr(args, "json", False):
        print(json.dumps({"runs": report, "exit_code": worst}, sort_keys=True))
    return worst


def check_names_first(runs: list[dict[str, Any]]) -> None:
    """Several declared runs: each uploaded one's rows are checked for a dataset name before the first run starts,
    so a refusal never comes after another run already stored something."""
    from fi.experiments._engine import RunConfig
    from fi.experiments._server_dataset import check_local_name

    for kw in runs:
        if kw.get("upload", True) and kw.get("resume") is None:
            cfg = RunConfig(**{k: v for k, v in kw.items() if k != "_label"}, argv=list(sys.argv[1:]))
            check_local_name(cfg.dataset, **cfg.name_fix())


def _severity(code: int) -> int:
    return {EXIT_OK: 0, EXIT_CI_ERRORS: 1, EXIT_GATE: 2}.get(code, 3)


# ---- doctor (moved to doctor_section.py: the 400-line module rule) --------------------------------


def doctor_lines(args: Any) -> list[str]:
    from fi.experiments._cli.doctor_section import doctor_lines as lines

    return lines(args)
