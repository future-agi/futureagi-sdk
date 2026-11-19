"""Span export for uploaded runs: traceAI's OTLP exporter behind a scrubbing wrapper.

Every exported span passes through :class:`ScrubbingExporter` first: string attribute values (and
event attributes) have every known secret value replaced (``Redactor``), and string attributes whose
key names a credential (``_redact.is_credential_key``: ``authorization``, ``api_key``,
``x-api-key``, ``secret``, ``password``, ``cookie``, ``bearer``, ``private_key``, ``credential``,
or a name ending in the word ``token`` such as ``access_token`` / ``x-auth-token``) are replaced
whole. Token counts (``*_tokens``, ``token_count``, ``max_tokens``) are not credentials and stay.
The exporter sends to ``{base_url}/tracer/v1/traces`` with the run's own keys, never the
environment's, plus the run client's extra headers (``FI_EXTRA_HEADERS``; ``fi._extra_headers``),
and the provider is never installed globally.

Where the spans are stored: in the **Observe** project named by ``project``
(default ``"<dataset> · experiments"``). The trace collector (fi-collector) creates every project as
an Observe project and does not read the resource's ``project_type`` or ``project_version_*``, so a
run has no experiment-typed project and no project version of its own. A run and its traces are
joined by run id: every span carries ``fi.experiment.run_id`` (the trial root's attribute and
baggage, copied onto child spans), and every uploaded item carries its ``trace_id`` and
``root_span_id``.
"""

from __future__ import annotations

from typing import Any, Callable, Mapping, Sequence

from opentelemetry.sdk.trace import Event, ReadableSpan
from opentelemetry.sdk.trace.export import SpanExporter, SpanExportResult

from fi.experiments._redact import REDACTED, Redactor, is_credential_key


def _scrub_value(redactor: Redactor, key: str, value: Any) -> Any:
    if isinstance(value, str):
        return REDACTED if value and is_credential_key(key) else redactor.text(value)
    if isinstance(value, (list, tuple)):
        return tuple(_scrub_value(redactor, key, v) for v in value)
    return value


def scrub_attributes(redactor: Redactor, attributes: Mapping[str, Any] | None) -> dict:
    return {k: _scrub_value(redactor, k, v) for k, v in (attributes or {}).items()}


def scrub_span(span: ReadableSpan, redactor: Redactor) -> ReadableSpan:
    events = [Event(e.name, scrub_attributes(redactor, e.attributes), e.timestamp) for e in span.events]
    return ReadableSpan(
        name=span.name,
        context=span.context,
        parent=span.parent,
        resource=span.resource,
        attributes=scrub_attributes(redactor, span.attributes),
        events=events,
        links=span.links,
        kind=span.kind,
        status=span.status,
        start_time=span.start_time,
        end_time=span.end_time,
        instrumentation_scope=span.instrumentation_scope,
    )


class ScrubbingExporter(SpanExporter):
    def __init__(self, inner: SpanExporter, redactor: Redactor, outcome: Any = None) -> None:
        self.inner = inner
        self.redactor = redactor
        self.outcome = outcome

    def export(self, spans: Sequence[ReadableSpan]) -> SpanExportResult:
        if self.outcome is None:
            return self.inner.export([scrub_span(s, self.redactor) for s in spans])
        self.outcome.begin_batch()
        try:
            result = self.inner.export([scrub_span(s, self.redactor) for s in spans])
        except Exception:  # batch processors swallow exceptions; never log raw exception text
            result = SpanExportResult.FAILURE
        status = self.outcome.status_code
        if result != SpanExportResult.SUCCESS or (status is not None and not 200 <= status < 300):
            self.outcome.failed()
            return SpanExportResult.FAILURE
        return result

    def shutdown(self) -> None:
        self.inner.shutdown()

    def force_flush(self, timeout_millis: int = 30000) -> bool:
        flush = getattr(self.inner, "force_flush", None)
        return bool(flush(timeout_millis)) if callable(flush) else True


def collector_endpoint(base_url: str) -> str:
    return base_url.rstrip("/") + "/tracer/v1/traces"


def run_resource(project: str, run_name: str, run_id: str) -> Any:
    """The run's OpenTelemetry resource: the attributes traceAI's ``register`` would write (project, type, version
    name/id, convention), set here on the SDK's own provider; ``register`` itself is not called (``exporter_factory``).

    Only ``project_name`` decides where the spans are stored today: the collector stores them in the
    Observe project of that name and ignores ``project_type`` and ``project_version_*`` (the trace-storage contract;
    the collector fix, the acceptance contract 48, needs no SDK change because they are already written)."""
    from opentelemetry.sdk.resources import Resource

    return Resource(attributes={
        "project_name": project,
        "project_type": "experiment",
        "project_version_name": run_name,
        "project_version_id": run_id,
        "eval_tags": "[]",
        "metadata": "{}",
        "semantic_convention": "fi",
    })


def exporter_factory(*, base_url: str, api_key: str, secret_key: str, project: str, run_name: str, run_id: str,
                     redactor: Redactor, inner: Any = None,
                     extra_headers: Mapping[str, str] | None = None, outcome: Any = None) -> Callable[[], Any]:
    """A factory for the run's delegate provider: a plain OpenTelemetry provider with one batch
    processor over the scrubbing exporter. traceAI's ``register()`` is not used: it installs SIGINT
    and SIGTERM handlers that call ``sys.exit(0)`` (the run's Ctrl-C contract is exit 4 after the
    journal flush), and its provider drops every processor on the next ``add_span_processor``.

    ``extra_headers`` (the run client's ``FI_EXTRA_HEADERS`` / ``extra_headers=``, read when the run
    starts) go on every export to the collector, beside the run's keys; they never become a span
    attribute. ``outcome`` records terminal batch failures for the engine to report after shutdown;
    a successful queue flush alone does not mean the collector accepted any spans."""
    from fi.experiments._tracing.export_status import ExportSession, ExportStatus

    if outcome is None:
        outcome = ExportStatus(run_id, collector_endpoint(base_url), redactor)

    def make() -> Any:
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor

        exporter = inner
        if exporter is None:
            from fi_instrumentation.otel import HTTPSpanExporter

            headers = {**(extra_headers or {}), "X-Api-Key": api_key, "X-Secret-Key": secret_key}
            exporter = HTTPSpanExporter(endpoint=collector_endpoint(base_url), headers=headers,
                                        session=ExportSession(outcome))
        provider = TracerProvider(resource=run_resource(project, run_name, run_id))
        provider.add_span_processor(BatchSpanProcessor(ScrubbingExporter(exporter, redactor, outcome)))
        return provider

    return make
