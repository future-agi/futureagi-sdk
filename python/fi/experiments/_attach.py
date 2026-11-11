"""``futureagi-py run TARGET --run RUN``: run a target into a run that was created elsewhere (for example in the app).

The run is read back first (``GET /model-hub/experiment-runs/<run>/``): its pinned dataset version, its plan of
(example, trial) identities, the evaluator bindings pinned when it was created and its lifecycle. Nothing is
created on the server: no run, no dataset version, no metric.

- The dataset: the header's ``dataset_id`` when it has one, else the dataset of the run's experiment
  (``GET /model-hub/experiments/v2/<id>/``), else ``--dataset``. A ``--dataset`` given anyway must name that dataset.
  The rows are the items of the run's own version.
- The scores: the run's evaluator bindings. A platform template is found in the hosted eval API's catalog by its
  template id and runs with the binding's settings, its model, and the mapping entries this run can supply (an entry
  that names a column by id falls back to the default mapping). A metric scored by local code (an external metric)
  needs that code: a run file that declares the evaluator. ``--eval`` (and a run file's evaluators) must name exactly
  the run's evaluators. A run with no evaluators records unscored results.
- The plan: only planned identities with no recorded item run (``GET .../items/`` over every item status: an item
  still pending or running belongs to a trial someone else is running).
- Results go to the run's results route through the same journal and uploader as any run, so ``--resume RUN``
  continues it.

The OpenAPI spec the SDK is generated from has no operation for the run read or the items list, so both go
through the client's hand-written requests (``client.experiment_runs.get`` / ``list_items``), read by the small
parser here.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any, Mapping, Optional, Sequence

from fi.experiments.errors import ExperimentError, UsageError

ITEM_STATUSES = "pending,running,completed,failed,skipped"
PAGE = 500  # the largest page the items route serves
CLOSED = ("completed", "failed", "cancelled")
NEEDS_ROWS = ("this TARGET needs rows: add --dataset rows.jsonl (a local file) or --dataset NAME|ID (a server "
              "dataset)")
ROLE_SOURCES = ("output", "expected", "input")


class RunAttachError(UsageError):
    """The run cannot take results from this target."""

    code = "RUN_NOT_ATTACHABLE"


class RunReadError(ExperimentError):
    """The server's answer for a run could not be read."""

    code = "RUN_READ_FAILED"


@dataclass(frozen=True)
class RunHeader:
    id: str
    status: str
    task_kind: str
    dataset_version_id: str
    dataset_id: Optional[str] = None  # the header has none today; read when a server adds it
    experiment_id: Optional[str] = None
    expected_items: list = field(default_factory=list)  # [(example_id, trial_number)] in plan order
    bindings: list = field(default_factory=list)  # the evaluator bindings as the server sent them
    completed_at: Optional[str] = None
    raw: dict = field(default_factory=dict)


def _result(payload: Any) -> Any:
    return payload["result"] if isinstance(payload, Mapping) and "result" in payload else payload


def _text(value: Any) -> Optional[str]:
    return str(value).lower() if isinstance(value, str) and value else None


def parse_header(payload: Any, run_id: str) -> RunHeader:
    body = _result(payload)

    def bad(what: str) -> RunReadError:
        return RunReadError(f"the server's answer for run {run_id} has {what}, so results cannot be added to it")

    if not isinstance(body, Mapping):
        raise bad("no run in it")
    for key, kind in (("status", str), ("task_kind", str), ("dataset_version_id", str), ("expected_items", list),
                      ("evaluator_bindings", list)):
        if not isinstance(body.get(key), kind):
            raise bad(f"no valid {key!r}")
    items = []
    for entry in body["expected_items"]:
        if not isinstance(entry, Mapping) or not entry.get("example_id"):
            raise bad("a planned item without an example_id")
        items.append((str(entry["example_id"]), int(entry.get("trial_number") or 1)))
    for binding in body["evaluator_bindings"]:
        if not isinstance(binding, Mapping) or not binding.get("metric_id") or not binding.get("evaluator_version_id"):
            raise bad("an evaluator binding without a metric_id and evaluator_version_id")
    return RunHeader(id=str(body.get("id") or run_id), status=body["status"], task_kind=body["task_kind"],
                     dataset_version_id=body["dataset_version_id"], dataset_id=_text(body.get("dataset_id")),
                     experiment_id=_text(body.get("experiment_id")), expected_items=items,
                     bindings=[dict(b) for b in body["evaluator_bindings"]],
                     completed_at=body.get("completed_at") or None, raw=dict(body))


# ---- before any request ---------------------------------------------------------------------------


def check_flags(cfg: Any) -> None:
    """``--run`` with a flag that makes or shapes a new run's plan is refused in one line."""
    try:
        uuid.UUID(str(cfg.attach))
    except ValueError:
        raise RunAttachError(f"--run takes a run id (a UUID), got {cfg.attach!r}") from None
    clashes = (
        ("--resume", cfg.resume is not None, "--run starts adding results to a run made elsewhere, and --resume "
                                             "continues a run journaled on this machine (one started with --run too). "
                                             "Keep one"),
        ("--experiment", cfg.experiment is not None, "the run already belongs to its experiment. Drop --experiment"),
        ("--no-upload", not cfg.upload, "--run stores results in a run on the server. Drop --no-upload"),
        ("--version", cfg.version is not None, "the run pins its own dataset version. Drop --version"),
        ("--rows", cfg.rows is not None, "the run's plan says which rows run. Drop --rows"),
        ("--limit", cfg.limit is not None, "the run's plan says which rows run. Drop --limit"),
        ("--trials", int(cfg.trials) != 1, "the run's plan says how many trials each row gets. Drop --trials"),
    )
    for flag, given, why in clashes:
        if given:
            raise RunAttachError(f"--run and {flag} do not go together: {why}")


def run_id_for(attach: Any, journal_root: Any) -> str:
    """The run's id in canonical form; a run journaled on this machine is continued with ``--resume``."""
    from fi.experiments._journal import runs_root

    run_id = str(uuid.UUID(str(attach)))
    if (runs_root(journal_root) / run_id / "plan.json").exists():
        raise RunAttachError(f"run {run_id} is already journaled on this machine: continue it with --resume {run_id} "
                             "instead of --run")
    return run_id


# ---- the run ----------------------------------------------------------------------------------------


def read_run(client: Any, run_id: str) -> RunHeader:
    from fi.errors import FutureAGIAPIError

    try:
        payload = client.experiment_runs.get(run_id)
    except FutureAGIAPIError as exc:
        if exc.status_code in (404, 405) and not isinstance(exc.payload, Mapping):  # the route itself is absent
            raise RunReadError(f"this server cannot read runs back (GET /model-hub/experiment-runs/<run>/ is "
                               f"missing), so results cannot be added to run {run_id} here") from exc
        if exc.status_code == 404:
            raise RunAttachError(f"run {run_id} was not found on {getattr(client, 'base_url', 'the server')}: check "
                                 "the id, and that these keys belong to the workspace that holds the run") from exc
        raise
    return parse_header(payload, run_id)


def check_open(run: RunHeader, run_id: str, *, resumed: bool = False) -> None:
    """Refuse a run that cannot take new results. A resume may re-send to a completed run (a replay is a no-op)."""
    again = "Start a new run" if resumed else "Start a new run without --run"
    if run.task_kind != "external":
        raise RunAttachError(f"run {run_id} is a {run.task_kind} run: the platform runs its task itself, so it takes "
                             f"no results from futureagi-py run. {again}")
    if resumed and run.status == "completed":
        return
    if run.status in CLOSED:
        raise RunAttachError(f"run {run_id} is {run.status} and takes no more results. {again}")
    if run.completed_at:
        raise RunAttachError(f"run {run_id} is closed (completed at {run.completed_at}) and takes no more results. "
                             f"{again}")


def recorded(client: Any, run_id: str) -> set:
    """``{(example_id, trial)}`` of every item the server holds for the run, in any status, page by page."""
    out: set = set()
    offset = 0
    while True:
        page = _result(client.experiment_runs.list_items(run_id, status=ITEM_STATUSES, limit=PAGE, offset=offset,
                                                         max_value_bytes=0))
        got = page.get("items") if isinstance(page, Mapping) else None
        if not isinstance(got, list):
            raise RunReadError(f"the server's list of run {run_id}'s items has no 'items', so the trials that "
                               "already have a result are unknown")
        for item in got:
            out.add((str(item["example_id"]), int(item.get("trial_number") or 1)))
        if not page.get("has_more") or not got:
            return out
        offset += len(got)


# ---- the dataset ------------------------------------------------------------------------------------


def experiment_dataset(client: Any, experiment_id: str) -> Optional[str]:
    """The dataset of the run's experiment (``ExperimentDetailV2.dataset_id``); None when the experiment is gone."""
    from fi.errors import FutureAGIAPIError

    try:
        body = _result(client.experiments_v2.get(experiment_id))
    except FutureAGIAPIError as exc:
        if exc.status_code == 404:
            return None
        raise
    return _text(body.get("dataset_id")) if isinstance(body, Mapping) else None


def dataset_name(client: Any, dataset_id: str) -> str:
    from fi.errors import FutureAGIAPIError

    try:
        listed = (_result(client.datasets.list_names()) or {}).get("datasets") or []
    except FutureAGIAPIError:
        return dataset_id
    return next((str(d.get("name")) for d in listed
                 if str(d.get("dataset_id") or d.get("id")).lower() == dataset_id and d.get("name")), dataset_id)


def run_dataset(client: Any, run: RunHeader, run_id: str, source: Any) -> Any:
    """The run's rows: its pinned version, under the dataset the run names (see the module docstring)."""
    from fi.errors import FutureAGIAPIError
    from fi.experiments._dataset import DatasetSpec, is_local_source
    from fi.experiments._server_dataset import dataset_ref, from_version

    given = source.source if isinstance(source, DatasetSpec) else source
    if given is not None and is_local_source(given):
        raise RunAttachError("--run reads the rows from the run's own dataset version, so --dataset takes that "
                             "dataset's name or id, not a rows file")
    dataset_id, where = run.dataset_id, "named by the run"
    if dataset_id is None and run.experiment_id:
        dataset_id = experiment_dataset(client, run.experiment_id)
        where = f"the dataset of experiment {run.experiment_id}"
    shown = None
    if given is not None:
        given_id, shown = dataset_ref(client, given)
        if dataset_id is not None and given_id.lower() != dataset_id:
            raise RunAttachError(f"--dataset {shown!r} is not the dataset of run {run_id} ({dataset_id}, {where}): "
                                 "drop --dataset, or pass that dataset")
        dataset_id = given_id.lower()
    if dataset_id is None:
        raise RunAttachError(f"the server does not say which dataset run {run_id} belongs to: pass its dataset with "
                             "--dataset NAME|ID")
    shown = shown or dataset_name(client, dataset_id)
    version_id = run.dataset_version_id
    try:
        return from_version(client, dataset_id, shown, version_id, f"version {version_id[:8]} (the run's own)")
    except FutureAGIAPIError as exc:
        if exc.status_code != 404:
            raise
        raise RunAttachError(f"run {run_id} is pinned to dataset version {version_id}, which is not in dataset "
                             f"{shown!r}: pass the run's own dataset with --dataset NAME|ID") from exc


@dataclass
class Attached:
    """A run read back for ``--run`` (or for a resume of one): the header, its rows and the identities with a
    result."""

    run: RunHeader
    dataset: Any
    done: set = field(default_factory=set)

    def plan(self, rows: Sequence[Any], journaled: Optional[Sequence[Mapping[str, Any]]] = None) -> tuple:
        """``(rows in plan order, [(row, trial)])``: the planned identities with no result yet, or on a resume the
        journaled ones."""
        run_id = self.run.id
        if journaled is not None:
            wanted = [(str(i["example_id"]), int(i["trial"])) for i in journaled]
        else:
            wanted = [k for k in self.run.expected_items if k not in self.done]
            if not wanted:
                raise RunAttachError(f"every planned trial of run {run_id} already has a result (or is running "
                                     "elsewhere), so there is nothing to add")
        by_id = {r.id: r for r in rows}
        missing = sorted({e for e, _ in wanted if e not in by_id})
        if missing:
            raise RunReadError(f"run {run_id} plans {len(missing)} example(s) its dataset version does not have "
                               f"({', '.join(m[:8] for m in missing[:3])}), so it cannot be run")
        return [by_id[e] for e in dict.fromkeys(e for e, _ in wanted)], [(by_id[e], t) for e, t in wanted]

    def counts(self) -> tuple:
        """``(planned, already recorded)``."""
        planned = self.run.expected_items
        return len(planned), sum(1 for k in planned if k in self.done)


def open_attached(client: Any, source: Any, run_id: str, section: Mapping[str, Any], name: str) -> Attached:
    """Read the run and its rows. On a resume (``section``: the journaled upload section) the journaled version is
    read back and nothing is listed: the journal says which trials are this machine's."""
    from fi.experiments._server_dataset import from_version

    run = read_run(client, run_id)
    check_open(run, run_id, resumed=bool(section))
    if section:
        version_id = str(section["dataset_version_id"])
        note = f"version {version_id[:8]} (the run's own)"
        return Attached(run, from_version(client, str(section["dataset_id"]), name, version_id, note))
    ds = run_dataset(client, run, run_id, source)
    return Attached(run, ds, recorded(client, run_id))


# ---- the scores ---------------------------------------------------------------------------------------


def _external(binding: Mapping[str, Any]) -> Optional[Mapping[str, Any]]:
    snapshot = binding.get("config_snapshot")
    external = snapshot.get("external") if isinstance(snapshot, Mapping) else None
    return external if isinstance(external, Mapping) and isinstance(external.get("name"), str) else None


def _usable(mapping: Any, columns: Sequence[str]) -> dict:
    """The mapping entries this run can supply: a role, a ``==literal`` or a column of the rows (the app names
    columns by id; those keys fall back to the default mapping)."""
    if not isinstance(mapping, Mapping):
        return {}
    return {str(k): v for k, v in mapping.items()
            if isinstance(v, str) and (v in ROLE_SOURCES or v.startswith("==") or v in columns)}


def scorers(client: Any, run: RunHeader, local: Sequence[Any], judge_model: Optional[str],
            columns: Sequence[str]) -> tuple:
    """``(evaluators, {score name: Binding})`` from the run's evaluator bindings (see the module docstring)."""
    from fi.experiments.evaluators.binding import Binding, external_metric_body, output_type
    from fi.experiments.evaluators.hosted import HostedTemplate, Template

    run_id = run.id
    code = {n: ev for ev in local if ev.kind != "template" for n in ev.names}  # local evaluators, by score name
    asked = {ev.tpl.name: ev for ev in local if ev.kind == "template"}  # --eval, by template name
    by_id: dict = {}
    if any(_external(b) is None for b in run.bindings):
        by_id = {str(r.get("id")): r for r in _catalog(client).values()}
    names = []
    for b in run.bindings:
        external = _external(b)
        record = by_id.get(str(b.get("template_id"))) if external is None else None
        if external is None and record is None:
            raise RunAttachError(f"run {run_id} scores with template {b.get('template_id')}, which the eval API does "
                                 "not list for these keys, so it cannot be run here")
        names.append(external["name"] if external is not None else str(record["name"]))
    ours = list(dict.fromkeys([*code, *asked]))
    if ours and sorted(ours) != sorted(set(names)):
        extra, missing = [n for n in ours if n not in names], [n for n in dict.fromkeys(names) if n not in ours]
        parts = ([f"this command scores {', '.join(extra)}, which the run does not"] if extra else []) + (
            [f"the run scores {', '.join(missing)}, which this command does not"] if missing else [])
        raise RunAttachError(f"the evaluators differ from run {run_id}'s: {'; '.join(parts)}. Drop --eval (and the "
                             "run file's evaluators) to score with the run's own, or start a new run without --run")
    evaluators: list = []
    bindings: dict = {}
    for b, name in zip(run.bindings, names):
        external = _external(b)
        if external is not None:
            ev = code.get(name)
            if ev is None:
                raise RunAttachError(f"run {run_id} scores {name} with local code (an evaluator a run file declares), "
                                     "which this target does not have: run that file with --run, or start a new run "
                                     "without --run")
            source_hash = external.get("source_hash")
            if source_hash and external_metric_body(ev, name)["source_hash"] != source_hash:
                raise RunAttachError(f"the evaluator {name} changed since run {run_id} was made, so its scores would "
                                     "not match the run's. Start a new run without --run")
            if ev not in evaluators:
                evaluators.append(ev)
            score, kind, out_type = name, "external", output_type(ev)
        else:
            settings = b.get("binding_config") if isinstance(b.get("binding_config"), Mapping) else {}
            params = dict(settings.get("config")) if isinstance(settings.get("config"), Mapping) else {}
            mine = asked.get(name)
            if mine is not None and mine.tpl.config and dict(mine.tpl.config) != params:
                raise RunAttachError(f"--eval {name} sets {dict(mine.tpl.config)}, and run {run_id} pins {params}: drop "
                                     "the settings from --eval")
            mapping = {**_usable(settings.get("mapping"), columns), **(dict(mine.tpl.map) if mine else {})}
            tpl = Template(name, params, mapping, b.get("binding_model") or b.get("model") or None,
                           mine.tpl.pass_label if mine else None)
            ev = HostedTemplate(tpl, judge_model)
            evaluators.append(ev)
            score, kind, out_type = ev.names[0], "template", "template"
        if score in bindings:
            raise RunAttachError(f"run {run_id} binds {score} twice, so its scores cannot be told apart here")
        bindings[score] = Binding(name=score, metric_id=str(b["metric_id"]), kind=kind, output_type=out_type,
                                  evaluator_version_id=str(b["evaluator_version_id"]))
    return evaluators, bindings


def _catalog(client: Any) -> dict:
    import httpx

    from fi.experiments.errors import server_unreachable
    from fi.experiments.evaluators.hosted import catalog_from_response

    try:
        return catalog_from_response(client.evals.list_sdk_evals())
    except httpx.TransportError as exc:
        raise server_unreachable(exc, getattr(client, "base_url", None)) from None
