"""The asyncio engine: plan rows x trials, run them under an adaptive concurrency limit, bound
each trial's task attempts (including retries) with ``timeout_s``, enforce fail-fast and the
run budget, score each trial, and journal every item before anything else happens to it.
Evaluators use their own limits, not ``timeout_s``; evaluator timeouts produce error scores.
See ``_engine_trial`` for slot release, cooperative cancellation and the current async late-result limitation.

With ``upload=True`` (the default) the dataset is pinned to a server version, the metrics are
bound, the run is created before the first trial, spans are exported (scrubbed), and each journaled
item is streamed to the server (``_upload_session.py``). ``upload=False`` stores nothing.
"""

from __future__ import annotations

import asyncio
import dataclasses
import datetime as _dt
import os
import platform
import sys
import uuid
from typing import Any, Sequence

from fi.experiments import _debug, _judge_checklists as checklists, _params
from fi.experiments._cost import RunBudget, lookup_price
from fi.experiments._dataset import DatasetSpec, LocalDataset, RowSelector, is_local_source, load_local, select_rows
from fi.experiments._engine_config import (  # noqa: F401  (re-exported: the engine's public names)
    FromColumn,
    RunConfig,
    _git_metadata,
    _task_label,
    _text,
    default_run_name,
    from_column,
    resolve_evaluators,
)
from fi.experiments._engine_pool import AdaptiveLimiter, PoolMixin, TransientInfo, _Shared, transient_info  # noqa: F401
from fi.experiments._engine_summary import add_resume_hint, judge_reads, print_summary, run_page
from fi.experiments._engine_trial import TrialMixin, _result_from_item
from fi.experiments._journal import Journal, load as load_journal, sdk_version
from fi.experiments._limits import Limits
from fi.experiments._redact import Redactor, client_secret_values
from fi.experiments._resume_params import check as check_resume_params, redacted_names
from fi.experiments._sync import running_task_threads
from fi.experiments.adapters import resolve_task
from fi.experiments.errors import (
    CapNotEnforceableError,
    JournalError,
    PlanTooLargeError,
    RunInterrupted,
    UnpricedModelError,
    UsageError,
)
from fi.experiments.evaluators._base import Evaluator
from fi.experiments.results import ExperimentResult, TrialResult


class Engine(PoolMixin, TrialMixin):
    def __init__(self, cfg: RunConfig) -> None:
        cfg.validate()
        self.cfg = cfg
        self.limits = cfg.limits or Limits()
        self.params = _params.frozen(cfg.params)
        self.redactor = Redactor(client_secret_values(cfg.client))
        self.stream = cfg.stream if cfg.stream is not None else sys.stderr
        self.results: dict[tuple[str, int], TrialResult] = {}
        self.session: Any = None  # the upload half (UploadSession) when upload=True
        self.uploader: Any = None
        self.capture_limited: dict[str, int] = {}  # trials whose span capture hit a limit (F7)

    def _client(self) -> Any:
        if self.cfg.client is not None:
            return self.cfg.client
        from fi.futureagi_client import FutureAGIClient

        return FutureAGIClient()

    # -- output --
    def say(self, line: str) -> None:
        if self.cfg.progress:
            print(line, file=self.stream, flush=True)

    # -- planning --
    def _source(self) -> Any:
        source = self.cfg.dataset
        if isinstance(self.cfg.task, FromColumn):
            spec = source if isinstance(source, DatasetSpec) else DatasetSpec(source)
            source = dataclasses.replace(spec, exclude_expected=self.cfg.task.column)
        return source

    def _load_dataset(self) -> LocalDataset:
        source = self._source()
        if not is_local_source(source):
            raise UsageError(
                "a server dataset (a name, an id or fi.datasets.Dataset) is pinned to a version that the "
                "stored run names, so it needs upload; pass list[dict] or rows.jsonl for upload=False "
                "(CLI --no-upload)"
            )
        if self.cfg.version is not None:
            raise UsageError("version= selects a server dataset version; local datasets have none")
        if isinstance(source, DatasetSpec) and (source.name or source.add_version):  # Regression coverage: never silent
            import warnings

            warnings.warn("dataset(name=..., add_version=...) only says where an uploaded run stores its rows; "
                          "this run uploads nothing (upload=False), so they are not used", UserWarning, stacklevel=2)
        return load_local(source)

    async def execute(self) -> ExperimentResult:
        cfg = self.cfg
        self.session = self.uploader = None
        # Check everything needing no server before the first request (a pin may create a dataset/version).
        runner = resolve_task(cfg.task)
        judge_model = cfg.judge_model or os.environ.get("FI_JUDGE_MODEL") or None
        evaluators = resolve_evaluators(cfg.evaluators, judge_model)
        uses_templates = any(ev.kind == "template" for ev in evaluators)
        self._check_budget(evaluators)
        from fi.experiments._tracing.instrument import refuse_broken_explicit

        refuse_broken_explicit(cfg.instrument, cfg.trace)  # a broken add-on named explicitly
        resumed = None
        if cfg.resume is not None:  # read before the pin: a resume pins the run's own version
            run_id = str(getattr(cfg.resume, "run_id", cfg.resume))
            resumed = load_journal(run_id, cfg.journal_root)
            if bool(resumed.plan.get("upload")) != bool(cfg.upload):
                raise JournalError(
                    f"run {run_id} was journaled with upload={bool(resumed.plan.get('upload'))}; resume it the same way"
                )
            check_resume_params(run_id, resumed.plan, self.params, self.redactor, argv=cfg.argv)
            checklists.restore(run_id, resumed.checklists, evaluators, cfg.argv)  # one run, one checklist (S4)
        elif cfg.attach is not None:  # CLI --run: a run created elsewhere keeps its own id (_attach)
            from fi.experiments._attach import run_id_for

            run_id = run_id_for(cfg.attach, cfg.journal_root)
        else:
            run_id = str(uuid.uuid4())
        attached = cfg.attach is not None or bool(((resumed.plan if resumed is not None else {}).get(
            "upload_session") or {}).get("attached"))
        if cfg.dataset is None and not attached and cfg.argv is not None:  # CLI: only --run and --resume may omit it
            from fi.experiments._attach import NEEDS_ROWS

            raise UsageError(NEEDS_ROWS)
        if cfg.upload:
            from fi.experiments._server_dataset import check_local_name
            from fi.experiments._upload_session import PY_NO_KEYS_HINT, UploadSession

            if resumed is None and not attached:  # local rows need a dataset name before any request (S3 (a))
                check_local_name(self._source(), **cfg.name_fix())

            pin = UploadSession.attach if attached else UploadSession.pin
            self.session = await pin(
                self._client(), self._source(), run_id if attached else cfg.version,
                resumed=resumed.plan if resumed is not None else None,
                no_keys_hint=getattr(cfg.task, "no_keys_hint", PY_NO_KEYS_HINT),
            )
            ds = self.session.dataset
            if attached:  # the run's own evaluators score (--eval must name exactly them)
                evaluators = await self.session.scorers(evaluators, judge_model)
                uses_templates = any(ev.kind == "template" for ev in evaluators)
        else:
            ds = self._load_dataset()
        if runner.needs_single_input:
            ds.roles.require_single_input()
        server_line = None
        if uses_templates:
            from fi.experiments.evaluators.hosted import prepare

            client = self.session.client if self.session is not None else self._client()
            columns = list(ds.rows[0].keys()) if ds.rows else []
            prepare(evaluators, client=client, columns=columns, has_expected=ds.roles.expected is not None)
        if uses_templates or self.session is not None:
            client = self.session.client if self.session is not None else client
            creds = getattr(client, "auth", None)
            server_line = creds.describe() if hasattr(creds, "describe") else str(getattr(client, "base_url", ""))
        budget = RunBudget(cfg.max_cost_usd, self.limits.prices or {})
        selection = cfg.rows
        if isinstance(selection, RowSelector) and selection.run_id == run_id:
            raise UsageError("rows=failed(run)/new_since(run) makes a new run; use resume= to continue a run")
        remote = self.session.remote_journal if self.session is not None else None
        if attached:  # the run's planned trials with no result yet (on a resume: the journaled ones)
            journaled = resumed.plan.get("items", []) if resumed is not None else None
            chosen, identities = self.session.attached.plan(ds.rows, journaled)
        else:
            chosen = select_rows(ds.rows, selection, cfg.limit, journal_root=cfg.journal_root, remote=remote,
                                 uploaded=bool(cfg.upload))
            identities = [(r, t) for r in chosen for t in range(1, int(cfg.trials) + 1)]
        plan_identities = getattr(cfg.task, "plan_identities", None)  # log_results: exactly the recorded ones
        if callable(plan_identities):
            identities = plan_identities(chosen)
        if len(identities) > PlanTooLargeError.MAX_ITEMS:
            raise PlanTooLargeError(len(identities))
        framework = runner.framework
        task_label = _task_label(cfg.task, runner)
        name = cfg.name or default_run_name(task_label, self.params, framework)
        project = cfg.project or f"{ds.name} · experiments"
        auto_meta = {
            "sdk": sdk_version(),
            "python": platform.python_version(),
            "framework": framework,
            **_git_metadata(),
        }
        non_final = bool(isinstance(selection, RowSelector) and selection.non_final)
        plan = {
            "run_id": run_id,
            "name": name,
            "description": cfg.description,
            "experiment": str(cfg.experiment) if cfg.experiment is not None else None,
            "project": project,
            "dataset": {"name": ds.name, "kind": ds.source_kind, "rows": len(ds.rows)},
            "trials": int(cfg.trials),
            "items": [{"example_id": r.id, "number": r.number, "trial": t} for r, t in identities],
            "evaluators": [n for ev in evaluators for n in ev.names],
            "params": self.redactor.value(dict(self.params)),
            "redacted_params": redacted_names(self.params, self.redactor.value(dict(self.params))),
            "metadata": self.redactor.value({**auto_meta, **dict(cfg.metadata or {})}),
            "selection": selection.describe() if isinstance(selection, RowSelector) else (
                list(selection) if selection is not None else "all"),
            "non_final": non_final,
            "upload": bool(cfg.upload),
            "argv": self.redactor.value(list(cfg.argv)) if cfg.argv else None,
            "created_at": _dt.datetime.now(_dt.timezone.utc).isoformat(),
        }
        if self.session is not None:
            plan["dataset"].update(id=ds.dataset_id, version_id=ds.version_id)
            if resumed is not None:
                section = resumed.plan.get("upload_session") or {}
                if section.get("dataset_version_id") != ds.version_id:  # version= names another version
                    raise JournalError(
                        f"resume={run_id}: the dataset changed since the run started (version "
                        f"{str(section.get('dataset_version_id'))[:8]} → {ds.version_id[:8]}); resume needs the same rows"
                    )
                self.session.restore(section, evaluators, run_id)
            elif attached:
                plan["upload_session"] = self.session.attach_section(evaluators)
            else:
                await self.session.bind(evaluators)
                server_meta = self.redactor.value({
                    **plan["metadata"], "name": name, "description": cfg.description, "project": project,
                    "selection": plan["selection"], "non_final": non_final, "argv": plan["argv"],
                })
                plan["upload_session"] = self.session.plan_section(
                    run_id=run_id, identities=[(r.id, t) for r, t in identities], experiment=cfg.experiment,
                    model_config=plan["params"], metadata=server_meta,
                )

        journal = Journal(run_id, cfg.journal_root)
        if resumed is not None:
            planned = [(i["example_id"], int(i["trial"])) for i in resumed.plan.get("items", [])]
            if planned != [(r.id, t) for r, t in identities]:
                raise JournalError(
                    f"resume={run_id}: the dataset, rows, limit or trials differ from the journaled plan"
                )
            journal.reopen()
            sha_then = (resumed.plan.get("metadata") or {}).get("git_sha")
            if sha_then and auto_meta.get("git_sha") and sha_then != auto_meta.get("git_sha"):
                self.say(f"Warning  resuming run {run_id} created at {sha_then[:7]}; working tree is "
                         f"{auto_meta['git_sha'][:7]}{' (dirty)' if auto_meta.get('git_dirty') else ''}")
            for key, rec in resumed.records.items():
                if rec.status in ("completed", "failed", "skipped"):
                    self.results[key] = _result_from_item(rec.item, rec.receipt_key)
            name, project = resumed.plan.get("name", name), resumed.plan.get("project", project)
        else:
            journal.create(plan)

        from fi.experiments._tracing import setup_run_tracing

        identity = {
            "fi.experiment.run_id": run_id,
            "fi.experiment.schema_version": "1",
            "fi.dataset.id": ds.id,
            **({"fi.dataset.version_id": ds.version_id} if self.session is not None else {}),
            **{f"fi.experiment.param.{k}": _text(v)[:256] for k, v in self.redactor.value(dict(self.params)).items()},
        }
        try:
            checklists.journal(evaluators, journal, resumed.checklists if resumed is not None else {})
            if self.session is not None:  # the run exists on the server before any span or item is sent
                header = await self.session.create()
                journal.event("run_attached" if attached else "run_created", server_status=header.get("status"))
            factory = (self.session.exporter_factory(project=project, run_name=name, run_id=run_id,
                                                     redactor=self.redactor)
                       if self.session is not None and cfg.trace is True else None)
            tracing = setup_run_tracing(
                trace=cfg.trace, instrument=cfg.instrument, framework=framework if framework != "factory" else None,
                project=project, run_name=name, identity=identity, upload=factory is not None,
                exporter_factory=factory,
            )
        except BaseException:
            journal.close()
            raise
        if self.session is not None:
            self.uploader = self.session.start(run_id, journal.ack, self.say)
            if resumed is not None:  # re-send what the server never confirmed, byte for byte
                for rec in resumed.records.values():
                    if not rec.acked:
                        self.uploader.submit(rec.receipt_key, rec.item_bytes)
        from fi.experiments._tracing.instrument import FRAMEWORKS, INSTRUMENTORS

        inst_name = FRAMEWORKS.get(framework)
        self.instrument_hint = INSTRUMENTORS[inst_name][2] if inst_name else "a traceAI instrumentor for your framework"
        failed = dict(getattr(tracing, "failed", ()))
        if inst_name in failed:  # installed but broken: "install X" alone would mislead
            self.instrument_hint = f"a version of {self.instrument_hint} that loads (it failed: {failed[inst_name]})"
        self.tool_spans_expected = bool(
            getattr(tracing, "enabled", False)
            and (cfg.trace is not True or (inst_name is not None and inst_name in getattr(tracing, "instrumentors", ())))
        )

        todo = [(r, t) for r, t in identities if (r.id, t) not in self.results]
        sel_note = f" · rows {plan['selection']}" if plan["selection"] != "all" else ""
        if server_line:
            self.say(f"Server   {server_line}")
        self.say(f"Run      {name}  ({run_id})")
        version_note = f" · {ds.note}" if self.session is not None else ""
        self.say(f"Dataset  {ds.name}{version_note} · {ds.roles.describe()} · {len(chosen)} rows × {cfg.trials} "
                 f"trial(s){sel_note}" + (" · non-final sample" if non_final else ""))
        self.say(f"Task     {runner.describe()}")
        _debug.run_settings(cfg, run_id, len(chosen), journal.dir)  # --verbose: the effective settings
        if evaluators:
            hosted = " · templates on the hosted eval API" if uses_templates else ""
            self.say(f"Evals    {', '.join(ev.describe() for ev in evaluators)}{hosted}")
        elif attached:
            self.say(f"Evals    none: run {run_id} has no evaluators, so its results are recorded unscored")
        self.say(tracing.header)
        if budget.active:
            excl = " (template evals are not counted: the platform bills them in credits)" if uses_templates else ""
            self.say(f"Budget   max_cost_usd ${budget.cap:g} from LLM-span tokens and judge() calls{excl}")
        if self.session is not None:
            self.say(self.session.header_line())
        elif uses_templates:
            # the eval API stores each call as a standalone Evaluation (inputs + output) and bills it
            self.say("Upload   off (--no-upload): no run is stored; each template call is stored by the eval "
                     "API as a standalone evaluation and billed to your org")
        else:
            self.say("Upload   off (--no-upload): nothing is stored on the platform")
        if resumed is not None:
            self.say(f"Resume   {len(identities) - len(todo)} of {len(identities)} trials already done")
        elif attached:
            planned, done = self.session.attached.counts()
            self.say(f"Plan     {done} of {planned} planned trials already have a result and are skipped; "
                     f"running {len(todo)}")

        shared = _Shared()
        upload_stats = None
        try:
            await self._run_all(todo, runner, evaluators, budget, journal, tracing, run_id, shared, len(identities))
            if self.uploader is not None:
                upload_stats = await self.uploader.close()
        except asyncio.CancelledError:
            if self.uploader is not None:  # unacked items stay in the journal; --resume re-sends them
                self.uploader.abort()
            journal.close()
            raise RunInterrupted(run_id, len(self.results), len(identities)) from None
        except BaseException as exc:
            if self.uploader is not None:  # never post (or ack into a closed journal) after the run failed
                self.uploader.abort()
            journal.close()
            if self.uploader is not None and exc is self.uploader.fatal:
                add_resume_hint(exc, run_id, cfg)
            raise
        finally:
            tracing.shutdown()
            journal.close()
            if self.session is not None:
                self.session.warn_export_failure()
        if shared.fatal is not None:
            raise shared.fatal
        if self.session is not None:
            self.session.check_export()

        items = [self.results[(r.id, t)] for r, t in identities if (r.id, t) in self.results]
        header = (upload_stats.header if upload_stats is not None else None) or (
            self.session.header if self.session is not None else None) or {}
        status = shared.stop_reason or ("no_upload" if not cfg.upload else (
            "completed" if header.get("status") == "completed" else "partial"))
        url, url_note = run_page(header, bool(cfg.upload))
        result = ExperimentResult(
            run_id=run_id,
            name=name,
            url=url,
            url_note=url_note,
            dataset_id=ds.id,
            dataset_version_id=getattr(ds, "version_id", None),
            experiment_id=header.get("experiment_id"),
            status=status,  # type: ignore[arg-type]
            items=items,
            metadata={**plan["metadata"], "non_final": non_final, "abandoned_threads": running_task_threads(),
                      "peak_concurrency": getattr(self, "peak", None), "spent_usd": budget.spent if budget.active else None,
                      "cost_cap": budget.metadata(uses_templates),
                      **_tracing_metadata(failed, self.capture_limited), **judge_reads(evaluators, chosen),
                      **({"upload": {"acked": upload_stats.acked, "batches": upload_stats.batches,
                                     "retries": upload_stats.retries, "server_status": header.get("status")}}
                         if upload_stats is not None else {})},
            journal_dir=str(journal.dir),
            error_policy=cfg.error_policy,  # type: ignore[arg-type]
            evaluator_names=[n for ev in evaluators for n in ev.names],
        )
        if not cfg.upload:
            result.to_jsonl(journal.dir / "results.jsonl")
        if shared.stop_reason == "failed_fast" and shared.first_traceback:
            self.say("Stopped  the first trials all failed with one error (fail_fast):\n" + shared.first_traceback)
        self._print_summary(result)
        return result

    def _check_budget(self, evaluators: Sequence[Evaluator]) -> None:
        budget = RunBudget(self.cfg.max_cost_usd, self.limits.prices or {})
        if budget.active and self.cfg.trace is False:
            raise CapNotEnforceableError(
                "max_cost_usd measures spend from the LLM spans' token usage, so it needs trace=True "
                "(CLI: drop --no-trace)"
            )
        if budget.active:  # judge() calls count toward the cap, so their model needs a price up front
            judge_models = {getattr(ev, "model", None) for ev in evaluators if ev.kind == "judge"}
            unpriced_judges = sorted(m for m in judge_models if m and lookup_price(m, budget.prices) is None)
            if unpriced_judges:
                raise UnpricedModelError(unpriced_judges)

    def _print_summary(self, result: ExperimentResult) -> None:
        if self.cfg.progress:
            print_summary(self.say, result, redact=self.redactor.text)


def _tracing_metadata(failed: dict, capture_limited: dict) -> dict:
    """result.metadata["tracing"]: instrumentors that failed to load (F2), capture limits hit (F7)."""
    from fi.experiments._tracing.instrument import INSTRUMENTORS

    out: dict[str, Any] = {}
    if failed:
        out["failed_instrumentors"] = {INSTRUMENTORS[n][2]: why for n, why in failed.items()}
    if capture_limited:
        out["capture"] = dict(capture_limited)
    return {"tracing": out} if out else {}
