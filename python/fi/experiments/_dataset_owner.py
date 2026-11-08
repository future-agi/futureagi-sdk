"""Datasets made as a side effect: the name local rows are stored under, and the refusal to add a
version to a dataset fi.experiments did not create. Split from ``_server_dataset.py`` (the 400-line module rule);
``_server_dataset`` re-exports every name here.

- Local rows on an uploaded run need a dataset name, inline rows **and files** (the dataset contract as written; dataset service decision
  after wave 2b, S3 (a)): ``experiments.dataset(rows, name=...)`` / ``--dataset-name``. A file's stem is never the
  name, since stems such as ``rows``, ``data`` or ``test`` collide across the projects of one organization. The
  error shows the exact command or call with the stem filled in, so the fix is one copy-paste. When one CLI command
  selects several declared runs (a run file or a directory), ``--dataset-name`` would apply to all of them, so the
  command shown selects the run alone with ``--filter``, next to the run-file call; and ``--dataset-name`` /
  ``--add-version`` over runs that read different rows are refused before any request (``_cli/file_mode.py``;
  L-SDK2c regression coverage). ``log_results`` always stores, so its refusal offers no ``upload=False``.
- ``name=`` / ``add_version=`` go with local rows only: on a server dataset they are refused, never ignored (review
  S2).
- Local rows never add a version to an existing dataset that fi.experiments cannot tell it made, unless
  ``add_version=True`` / ``--add-version``; the refusal says only what it saw. That includes a dataset
  that is **empty and has no version** (a first run that stopped before its first version landed leaves one): the
  dataset service decision after wave 2b (S1) lets it take its first version without an opt-in only when "empty and unversioned"
  is checked and the version created in ONE conditional server operation, so two concurrent first writes can never
  both land. The server's ``versions.create`` has no such condition yet (no create-if-no-version, no
  unique version 1), so the opt-in stays required for this case too; the refusal says what it saw and that a run of
  the caller's that stopped early leaves exactly this. With the opt-in, the run header says "wrote the first version
  of the existing empty dataset 'NAME' (N rows)".
"""

from __future__ import annotations

import json
import shlex
from collections.abc import Mapping
from pathlib import Path
from typing import Any, Optional, Sequence

from fi.experiments._dataset import DatasetSpec, is_local_source, load_local
from fi.experiments._server_rows import ROLES_KEY, _created, _result, list_versions
from fi.experiments.errors import UsageError

INLINE_NAME_NEEDED = (
    "rows passed as a list are stored on the server in a dataset, and a list has no name. Name it: "
    "experiments.run(experiments.dataset(rows, name=\"support-cases\"), ...), or pass upload=False to run "
    "without storing anything"
)
# log_results / futureagi-py upload always store: storing nothing is run(..., upload=False), never an option here
INLINE_NAME_NEEDED_LOG = (
    "rows passed as a list are stored on the server in a dataset, and a list has no name. Name it: "
    "experiments.log_results(experiments.dataset(rows, name=\"support-cases\"), results)"
)


class DatasetNameRequiredError(UsageError):
    code = "DATASET_NAME_REQUIRED"


def _py(text: str) -> str:
    return json.dumps(text, ensure_ascii=False)  # a double-quoted Python string literal


def cli_line(argv: Sequence[str], extra: Sequence[str] = (), drop: Sequence[str] = ()) -> tuple[str, str]:
    """``(the command, the note for its redacted values)``: this invocation's argv with its secrets redacted,
    without the ``drop`` flags, plus ``extra``."""
    from fi.experiments._cli.commands import drop_flags, hidden_values
    from fi.experiments._redact import Redactor

    line = shlex.join(["futureagi-py", *Redactor().value([*drop_flags(argv, drop), *extra])])
    hidden = hidden_values(list(argv))
    note = (f"The command shows {', '.join(hidden)} as [redacted]: put the real value(s) back before you run "
            "it. ") if hidden else ""
    return line, note


def file_name_needed(source: Any, argv: Optional[Sequence[str]] = None, *, run_file: Optional[str] = None,
                     run_filter: Optional[str] = None, suggest: Optional[str] = None,
                     stores_always: bool = False) -> str:
    """The error for a rows file on an uploaded run without a dataset name: the exact command (CLI, from this
    invocation's argv with its secrets redacted) or call (Python) with the file's stem filled in. ``run_file`` is
    set when a CLI command selected several declared runs: ``--dataset-name`` applies to every one of them, so the
    command shown selects this run alone (``--filter run_filter``), or, when no filter can, only the run-file call is
    shown. ``stores_always`` (log_results) drops the upload=False way out, which it has not."""
    path = str(source)
    stem = suggest or Path(path).stem or "rows"
    call = f"experiments.dataset({_py(path)}, name={_py(stem)})"
    why = (f"the rows file {path!r} needs a dataset name: an uploaded run stores its rows in a server dataset, and a "
           f"file's own name is never used for it (names such as {_py(Path(path).stem or 'rows')}, \"data\" or "
           "\"test\" collide across the projects of one organization). ")
    if argv:
        tail = ", or add --no-upload to store nothing" if argv[0] == "run" else ""
        if run_file is None:
            line, note = cli_line(argv, ["--dataset-name", stem])
            return f"{why}{note}Name it (or choose another name): {line}    (in a run file: {call}){tail}"
        if run_filter is not None:
            line, note = cli_line(argv, ["--filter", run_filter, "--dataset-name", stem], drop=("--filter",))
            return (f"{why}{note}Name it (or choose another name): {line}    (in a run file, for every run of it: "
                    f"{call} in {run_file}){tail}. --dataset-name applies to every run a command selects, so this "
                    "command selects this run alone")
        return (f"{why}Name it (or choose another name) in its run file: {call} in {run_file}{tail}. No "
                "--dataset-name command is shown: it applies to every run a command selects, and no --filter selects "
                "this run alone (give each experiments.run(...) its own name=)")
    tail = "" if stores_always else ", or pass upload=False to store nothing"
    return f"{why}Name it (or choose another name): {call}    (CLI: --dataset-name {shlex.quote(stem)}){tail}"


def local_dataset_name(spec: Any, local: Any = None, argv: Optional[Sequence[str]] = None, **fix: Any) -> str:
    """The server dataset local rows go to: ``dataset(..., name=)``. Inline rows and files both need one
    (no ``rows <hash>`` names; dataset service decision S3 (a): a file's stem is never the name). ``fix`` is
    ``file_name_needed``'s context (``RunConfig.name_fix()``)."""
    spec = spec if isinstance(spec, DatasetSpec) else DatasetSpec(spec)
    if spec.name:
        return spec.name
    if isinstance(spec.source, list):
        raise DatasetNameRequiredError(INLINE_NAME_NEEDED_LOG if fix.get("stores_always") else INLINE_NAME_NEEDED)
    raise DatasetNameRequiredError(file_name_needed(spec.source, argv, **fix))


LOCAL_ONLY = (
    "name= / --dataset-name and add_version= / --add-version say where local rows (a list or a rows file) are "
    "stored, and {source!r} is a server dataset, which is used as it is. Drop them, or pass the rows themselves"
)


def check_local_only(spec: Any) -> None:
    """Before any request: ``name=`` / ``add_version=`` on a server dataset are refused, never ignored."""
    if isinstance(spec, DatasetSpec) and (spec.name or spec.add_version) and not is_local_source(spec.source):
        raise UsageError(LOCAL_ONLY.format(source=getattr(spec.source, "name", None) or spec.source))


def check_local_name(source: Any, argv: Optional[Sequence[str]] = None, **fix: Any) -> None:
    """Before any request: local rows on an uploaded run must be named; ``name=`` / ``add_version=`` only
    go with local rows. ``argv`` (the CLI's) makes the error show the exact command; ``fix`` is the rest of
    ``file_name_needed``'s context."""
    check_local_only(source)
    if is_local_source(source):
        local_dataset_name(source, argv=argv, **fix)


class DatasetNotOwnedError(UsageError):
    code = "DATASET_NOT_CREATED_BY_SDK"


EMPTY_NO_VERSION = "is empty and has no version yet"


def not_made_by_sdk(client: Any, dataset_id: str) -> Optional[str]:
    """None when fi.experiments made this dataset: no table rows (the SDK stores rows as versions only)
    and its first version carries the SDK's roles metadata. Otherwise what was seen instead, said only as
    seen: the SDK cannot know who made a dataset, only what is in it."""
    res = _result(client.datasets.get_table(dataset_id, page_size=1, current_page_index=0)) or {}
    if (res.get("table") if isinstance(res, Mapping) else None):
        return "has table rows, which fi.experiments never writes (rows added in the app or by another tool)"
    versions = list_versions(client, dataset_id)
    if not versions:
        return EMPTY_NO_VERSION
    first = min(versions, key=_created)
    if isinstance(first.get("metadata"), Mapping) and ROLES_KEY in first["metadata"]:
        return None
    return "has a first version that fi.experiments did not write"


def made_by_sdk(client: Any, dataset_id: str) -> bool:
    return not_made_by_sdk(client, dataset_id) is None


def first_version_note(name: str, rows: int) -> str:
    return f"wrote the first version of the existing empty dataset {name!r} ({rows} rows)"


def refuse_foreign_version(cur: Any, spec: DatasetSpec, client: Any, *, has_version: bool) -> bool:
    """Local rows that differ from the latest version would add one: refused for a dataset that fi.experiments
    cannot tell it made, unless ``add_version=True``. True when the caller opted in and the dataset is
    empty with no version: the caller says it wrote that dataset's first version. An empty, versionless dataset is
    refused without the opt-in as well, until the server can create a first version only when there is none
    (dataset service decision S1 under the atomic-create contract)."""
    if not cur.local or cur.created:
        return False
    if spec.add_version:
        return not has_version and not_made_by_sdk(client, cur.dataset_id) == EMPTY_NO_VERSION
    seen = not_made_by_sdk(client, cur.dataset_id)
    if seen is None:
        return False
    file_arg = _py(str(spec.source)) if not isinstance(spec.source, list) else "rows"
    opt_in = (f"experiments.dataset({file_arg}, name={cur.name!r}, add_version=True) "
              f"(CLI: --dataset-name {shlex.quote(cur.name)} --add-version)")
    keep_apart = "To keep them apart, choose another name: dataset(..., name=\"...\") (CLI: --dataset-name NAME)"
    if seen == EMPTY_NO_VERSION:
        raise DatasetNotOwnedError(
            f"dataset {cur.name!r} already exists on the server and {seen}. An earlier run that stopped before "
            "storing its rows (a failed request, a lost connection or Ctrl-C) leaves a dataset like this; so does "
            "making an empty dataset in the app. Nothing was stored in it and nothing was changed: fi.experiments "
            "writes the first version of an existing empty dataset only when you opt in, since two runs started at "
            f"once could otherwise both write one. To store these rows as its first version: {opt_in}. {keep_apart}"
        )
    raise DatasetNotOwnedError(
        f"dataset {cur.name!r} already exists on the server and {seen}. fi.experiments cannot tell that it "
        "made it, so these rows were not stored in it and nothing was changed. To store them as a new version of "
        f"{cur.name!r}, opt in explicitly: {opt_in}. {keep_apart}"
    )
