"""The upload half of a run, as the engine sees it: pin the dataset, bind the metrics, create (or
replay) the run, export spans, stream the items, and report.

Everything here talks to the server through the sync platform client, on a worker thread, so the
run's event loop never blocks on the network.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Any, Callable, Mapping, Optional, Sequence

from fi.experiments._server_dataset import ServerDataset, pin_dataset, pin_resumed
from fi.experiments._upload import Uploader, create_body, create_run
from fi.experiments.errors import JournalError, server_unreachable
from fi.experiments.evaluators.binding import Binding, bind_all, bindings_from_plan, check_bindings, evaluators_changed


def _result(payload: Any) -> Any:
    return payload["result"] if isinstance(payload, Mapping) and "result" in payload else payload


PY_NO_KEYS_HINT = "Or pass upload=False to run locally without a server."


def require_keys(client: Any, hint: Optional[str] = PY_NO_KEYS_HINT) -> Any:
    """The resolved credentials, or ``CredentialsMissingError`` with the caller's hint: ``run()``'s
    ``upload=False`` line (the ``futureagi-py run`` CLI swaps it for ``--no-upload``); ``log_results``
    and ``futureagi-py upload`` have no local mode, so theirs names none."""
    from fi._credentials import CredentialsMissingError

    try:
        return client.auth
    except CredentialsMissingError as exc:  # MissingAuthError too: one line with the run's own hint
        if exc.hint or not hint:
            raise
        raise CredentialsMissingError(exc.base_url, exc.missing, exc.login_skipped, hint=hint) from exc


async def call(fn: Callable[..., Any], *args: Any, base_url: Optional[str] = None, **kwargs: Any) -> Any:
    """``fn`` on a worker thread; an unreachable server becomes one exit-3 line."""
    import httpx

    try:
        return await asyncio.to_thread(fn, *args, **kwargs)
    except httpx.TransportError as exc:
        raise server_unreachable(exc, base_url) from None


@dataclass
class UploadSession:
    client: Any
    dataset: ServerDataset
    bindings: dict[str, Binding] = field(default_factory=dict)
    body: Optional[dict] = None
    header: Optional[dict] = None
    uploader: Optional[Uploader] = None
    export_status: Any = None  # lazy: upload with trace=False never imports OpenTelemetry

    @property
    def base_url(self) -> str:
        return str(getattr(self.client, "base_url", ""))

    @classmethod
    async def pin(cls, client: Any, source: Any, version: Any, *, resumed: Optional[Mapping[str, Any]] = None,
                  no_keys_hint: Optional[str] = PY_NO_KEYS_HINT) -> "UploadSession":
        """Pin the dataset. On a resume (``resumed`` = the journaled plan) without ``version=``, the
        run's own version is read back and nothing is created."""
        require_keys(client, no_keys_hint)
        base_url = str(getattr(client, "base_url", ""))
        section = (resumed or {}).get("upload_session") or {}
        if version is None and section.get("dataset_id") and section.get("dataset_version_id"):
            name = str(((resumed or {}).get("dataset") or {}).get("name") or section["dataset_id"])
            ds = await call(pin_resumed, client, source, dataset_id=str(section["dataset_id"]),
                            version_id=str(section["dataset_version_id"]), name=name, base_url=base_url)
        else:
            ds = await call(pin_dataset, client, source, version=version, base_url=base_url)
        return cls(client=client, dataset=ds)

    async def bind(self, evaluators: Sequence[Any]) -> None:
        self.bindings = await call(bind_all, self.client, self.dataset.dataset_id, evaluators, base_url=self.base_url)

    def plan_section(self, *, run_id: str, identities: Sequence[tuple[str, int]], experiment: Any,
                     model_config: Mapping[str, Any], metadata: Mapping[str, Any]) -> dict[str, Any]:
        self.body = create_body(
            run_id=run_id, dataset_version_id=self.dataset.version_id, identities=identities,
            metric_ids=[b.metric_id for b in self.bindings.values()],
            experiment_id=str(experiment) if experiment is not None else None,
            model_config=model_config, metadata=metadata,
        )
        return {"dataset_id": self.dataset.dataset_id, "dataset_version_id": self.dataset.version_id,
                "create_body": self.body, "bindings": [b.to_json() for b in self.bindings.values()]}

    def restore(self, section: Mapping[str, Any], evaluators: Sequence[Any], run_id: str) -> None:
        """On ``--resume``: the journaled create body and bindings are re-used byte for byte, once the
        evaluators are shown to make exactly the journaled metrics: an edited evaluator
        would store new scores under the old metric, and an added one's scores would be dropped."""
        bindings = bindings_from_plan(section.get("bindings") or [])
        changed = evaluators_changed(bindings, evaluators)
        if changed is not None:
            raise JournalError(
                f"resume={run_id}: the evaluators changed since the run started ({changed}); a run never mixes "
                "two versions of an evaluator. Start a new run"
            )
        self.body = dict(section["create_body"])
        self.bindings = bindings

    async def create(self) -> dict[str, Any]:
        assert self.body is not None
        self.header = await call(create_run, self.client, self.body, base_url=self.base_url)
        self.bindings = check_bindings(self.bindings, self.header or {})
        return self.header or {}

    def start(self, run_id: str, on_ack: Callable[[list[str]], None], say: Callable[[str], None]) -> Uploader:
        self.uploader = Uploader(self.client, run_id, self.bindings, on_ack=on_ack, say=say)
        self.uploader.start()
        return self.uploader

    def exporter_factory(self, *, project: str, run_name: str, run_id: str, redactor: Any) -> Callable[[], Any]:
        from fi.experiments._tracing.export import collector_endpoint, exporter_factory
        from fi.experiments._tracing.export_status import ExportStatus

        creds = self.client.auth
        endpoint = collector_endpoint(self.base_url)
        self.export_status = ExportStatus(run_id, endpoint, redactor)
        return exporter_factory(base_url=self.base_url, api_key=creds.api_key, secret_key=creds.secret_key,
                                project=project, run_name=run_name, run_id=run_id, redactor=redactor,
                                extra_headers=self.extra_headers(endpoint), outcome=self.export_status)

    def warn_export_failure(self) -> None:
        if self.export_status is not None:
            self.export_status.warn()

    def check_export(self) -> None:
        if self.export_status is not None and self.export_status.error is not None:
            raise self.export_status.error

    def extra_headers(self, url: str) -> dict[str, str]:
        """The run client's extra headers for ``url`` (``FI_EXTRA_HEADERS`` and its ``extra_headers=``);
        a client without them (a test double) gets the setting's, under its base URL only."""
        extra = getattr(self.client, "_extra_headers", None)
        if extra is not None:
            return extra.for_url(url)
        from fi._extra_headers import ExtraHeaders

        return ExtraHeaders(self.base_url).for_url(url)

    def remote_journal(self, run_id: str) -> Any:
        """A run's plan and item statuses read from the server (SRV-3), in the journal's shape, for
        ``failed:RUN`` / ``new:RUN`` on a machine without RUN's journal."""
        from fi.experiments._journal import JournalRecord, LoadedJournal

        from fi.errors import FutureAGIAPIError
        from fi.experiments.errors import NotSupportedByServerError

        try:
            header = _result(self.client.experiment_runs.get(run_id)) or {}
        except FutureAGIAPIError as exc:
            if exc.status_code in (404, 405) and not isinstance(exc.payload, Mapping):  # the route is absent
                raise NotSupportedByServerError(
                    "SRV-3", f"There is no journal for run {run_id} here, and this server cannot read runs back "
                    "(GET /model-hub/experiment-runs/<run>/).",
                    hint=f"Run this where run {run_id} was started (its journal is under FI_RUN_DIR), or choose "
                    "the rows by number or id.",
                ) from exc
            raise
        loaded = LoadedJournal(run_id=run_id, plan={"items": [
            {"example_id": str(e["example_id"]), "trial": int(e.get("trial_number") or 1)}
            for e in header.get("expected_items") or []]})
        offset = 0
        while True:
            page = _result(self.client.experiment_runs.list_items(run_id, limit=500, offset=offset)) or {}
            got = page.get("items") or []
            for it in got:
                key = (str(it["example_id"]), int(it.get("trial_number") or 1))
                loaded.records[key] = JournalRecord(key[0], key[1], str(it["status"]), str(it.get("receipt_key")), b"{}")
            if not page.get("has_more") or not got:
                return loaded
            offset += len(got)

    def header_line(self) -> str:
        metrics = ", ".join(f"{n} ({b.kind})" for n, b in self.bindings.items()) or "no scores"
        return f"Upload   run stored on {self.base_url} · metrics: {metrics}"
