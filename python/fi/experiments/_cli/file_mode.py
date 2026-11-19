"""File mode: load run files in CLI context; their ``experiments.run(...)`` calls register instead
of running, then each runs once with the CLI flags as overlays."""

from __future__ import annotations

import fnmatch
import runpy
import sys
from pathlib import Path
from typing import Any, Mapping, Optional, Sequence

from fi.experiments import _registry
from fi.experiments.errors import UsageError


def collect(paths: Sequence[Path]) -> list[_registry.DeclaredRun]:
    declared: list[_registry.DeclaredRun] = []
    for path in paths:
        parent = str(Path(path).resolve().parent)
        added = parent not in sys.path
        if added:
            sys.path.insert(0, parent)
        try:
            with _registry.collect() as bucket:
                runpy.run_path(str(path), run_name="__main__")
        finally:
            if added and parent in sys.path:
                sys.path.remove(parent)
        if not bucket:
            raise UsageError(f"{path} declares no experiments.run(...) call")
        for run in bucket:
            run.kwargs.setdefault("_source", str(path))
        declared.extend(bucket)
    return declared


def select(declared: list[_registry.DeclaredRun], filters: Optional[Sequence[str]]) -> list[_registry.DeclaredRun]:
    if not filters:
        return declared
    chosen = [d for d in declared if any(fnmatch.fnmatch(d.name, f) or f == d.name for f in filters)]
    if not chosen:
        names = ", ".join(d.name for d in declared)
        raise UsageError(f"--filter matched no declared run (declared: {names})")
    return chosen


# ---- several declared runs and one --dataset-name ----------------------------------------------


def _rows_key(source: Any) -> Optional[tuple]:
    """The identity of a declared run's local rows (a resolved file path, or the list itself); None for a server
    dataset or none."""
    from fi.experiments._dataset import DatasetSpec, is_local_source

    src = source.source if isinstance(source, DatasetSpec) else source
    if src is None or not is_local_source(src):
        return None
    return ("list", id(src)) if isinstance(src, list) else ("file", str(Path(src).resolve()))


def name_contexts(declared: Sequence[_registry.DeclaredRun], collected: Sequence[_registry.DeclaredRun],
                  dataset_flag: Any = None) -> list[dict[str, Any]]:
    """For each of several selected declared runs: its run file, the ``--filter`` value that selects it alone among
    the declared runs (None when its name is shared), its rows source's identity, and the dataset name to suggest:
    the rows file's stem, with the run's name added when two different files of the selection share that stem (one
    suggestion per file, so following each never stores two files in one dataset)."""
    from fi.experiments._dataset import DatasetSpec

    out: list[dict[str, Any]] = []
    for d in declared:
        source = dataset_flag if dataset_flag is not None else d.kwargs.get("dataset")
        alone = len(select(list(collected), [d.name])) == 1 if d.name else False
        spec = source if isinstance(source, DatasetSpec) else None
        src = spec.source if spec is not None else source
        key = _rows_key(source)
        stem = (Path(str(src)).stem or "rows") if key is not None and key[0] == "file" else None
        out.append({"run_file": str(d.kwargs.get("_source") or ""), "run_filter": d.name if alone else None,
                    "key": key, "rows": src if stem is not None else "a list of rows",
                    "stem": stem, "name": d.name, "named": spec.name if spec is not None else None})
    for ctx in out:
        clash = {c["key"] for c in out if c["stem"] and c["stem"] == ctx["stem"]}
        ctx["suggest"] = (f"{ctx['stem']}-{ctx['name']}" if len(clash) > 1 else ctx["stem"]) if ctx["stem"] else None
    return out


def refuse_one_name_for_many(contexts: Sequence[Mapping[str, Any]], args: Any, argv: Sequence[str]) -> None:
    """Before any request: ``--dataset-name`` / ``--add-version`` apply to every selected declared run, so with
    several runs that read different local rows they are refused (one name would store different rows as versions
    of one dataset). The error shows each run file's own call and one command that selects a single run."""
    import json
    import shlex

    flags = [f for f, on in (("--dataset-name", getattr(args, "dataset_name", None)),
                             ("--add-version", getattr(args, "add_version", False))) if on]
    local = [c for c in contexts if c["key"] is not None]
    sources = {c["key"] for c in local}
    if not flags or len(sources) <= 1:
        return
    from fi.experiments._dataset_owner import cli_line

    opt = ", add_version=True" if "--add-version" in flags else ""

    def call(c: Mapping[str, Any]) -> str:
        rows = json.dumps(str(c["rows"])) if c["stem"] else "rows"
        name = c["named"] or c["suggest"] or "NAME"
        return f"experiments.dataset({rows}, name={json.dumps(name)}{opt}) in {c['run_file']}"

    reads = "; ".join(f"{c['name']} ({c['run_file']}) reads {shlex.quote(str(c['rows']))}" for c in local)
    harm = ("different rows would be stored as versions of one dataset" if "--dataset-name" in flags
            else "every one of their datasets would be opted in to a new version at once")
    pick = next((c for c in local if c["run_filter"]), None)
    alone, note = cli_line(argv, ["--filter", pick["run_filter"]], drop=("--filter",)) if pick else ("", "")
    raise UsageError(
        f"{' and '.join(flags)} {'are' if len(flags) > 1 else 'is'} for one rows file and applies to every selected "
        f"run, and these {len(contexts)} runs read {len(sources)} different rows files ({reads}). Applied to all of "
        f"them, {harm}, so the command is refused and nothing was sent. Say it in each run file instead: "
        + "; ".join(call(c) for c in local) + (f"; or select one run: {note}{alone}" if alone else ""))
