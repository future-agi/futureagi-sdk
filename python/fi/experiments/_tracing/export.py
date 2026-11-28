"""Span export for uploaded runs: traceAI's OTLP exporter behind a scrubbing wrapper.

Every exported span passes through :class:`ScrubbingExporter` first: string attribute values (and
event attributes) have every known secret value replaced (``Redactor``), and string attributes whose
key names a credential (``_redact.is_credential_key``: ``authorization``, ``api_key``,
``x-api-key``, ``secret``, ``password``, ``cookie``, ``bearer``, ``private_key``, ``credential``,
or a name ending in the word ``token`` such as ``access_token`` / ``x-auth-token``) are replaced
whole. Token counts (``*_tokens``, ``token_count``, ``max_tokens``) are not credentials and stay.
The exporter sends to the full ``FI_COLLECTOR_ENDPOINT`` URL, or to ``{base_url}/tracer/v1/traces``
when that setting is absent or empty, with the run's own keys, not ambient OTEL credentials or
destinations. The run client's extra headers (``FI_EXTRA_HEADERS``; ``fi._extra_headers``) remain
bound to the client's origin and base path, and the provider is not installed globally.

Where the spans are stored: in the **Observe** project named by ``project``
(default ``"<dataset> · experiments"``). The trace collector (fi-collector) creates every project as
an Observe project and does not read the resource's ``project_type`` or ``project_version_*``, so a
run has no experiment-typed project and no project version of its own. A run and its traces are
joined by run id: every span carries ``fi.experiment.run_id`` (the trial root's attribute and
baggage, copied onto child spans), and every uploaded item carries its ``trace_id`` and
``root_span_id``.
"""

from __future__ import annotations

import os
import re
import threading
from collections import OrderedDict
from ipaddress import ip_address
from typing import Any, Callable, Mapping, Sequence
from urllib.parse import unquote, urlsplit

import idna

from opentelemetry.sdk.trace import Event, ReadableSpan
from opentelemetry.sdk.trace.export import SpanExporter, SpanExportResult

from fi._core.http_security import require_secure_credentials_url
from fi._core.loopback import is_loopback_host
from fi._otlp_headers import (
    pin_headers,
    refuse_ambiguous_endpoint,
    refuse_plain_http_futureagi,
    refuse_unreadable_exporter_target,
)
from fi.errors import ConfigurationError
from fi.experiments._redact import REDACTED, Redactor, is_credential_key
from fi.experiments.errors import PlanTooLargeError

_AFTER_DEADLINE = "fi.trial.after_deadline"
_MAX_TRIAL_DEADLINES = PlanTooLargeError.MAX_ITEMS


class _TrialDeadlines:
    """Exporter-local cutoffs retained after roots end, through the final batch flush.

    At most 10,000 trace IDs (the supported run's trial limit), each with only its root ID
    and epoch-nanosecond deadline. Oldest registrations are evicted on overflow; ordinary
    valid runs fit in full. Shutdown clears the registry and prevents late repopulation.
    """

    def __init__(self) -> None:
        self._entries: OrderedDict[int, tuple[int, int]] = OrderedDict()
        self._lock = threading.Lock()
        self._closed = False

    def register(self, trace_id: int, root_span_id: int, deadline_ns: int) -> None:
        with self._lock:
            if self._closed or trace_id in self._entries:
                return
            self._entries[trace_id] = (root_span_id, deadline_ns)
            if len(self._entries) > _MAX_TRIAL_DEADLINES:
                self._entries.popitem(last=False)

    def is_late(self, span: ReadableSpan) -> bool:
        context = span.context
        if context is None or span.end_time is None:
            return False
        with self._lock:
            entry = self._entries.get(context.trace_id)
        return entry is not None and context.span_id != entry[0] and span.end_time >= entry[1]

    def shutdown(self) -> None:
        with self._lock:
            self._closed = True
            self._entries.clear()


def _scrub_value(redactor: Redactor, key: str, value: Any) -> Any:
    if isinstance(value, str):
        return REDACTED if value and is_credential_key(key) else redactor.text(value)
    if isinstance(value, (list, tuple)):
        return tuple(_scrub_value(redactor, key, v) for v in value)
    return value


def scrub_attributes(redactor: Redactor, attributes: Mapping[str, Any] | None) -> dict:
    return {k: _scrub_value(redactor, k, v) for k, v in (attributes or {}).items()}


def scrub_span(span: ReadableSpan, redactor: Redactor, *, after_deadline: bool = False) -> ReadableSpan:
    attributes = scrub_attributes(redactor, span.attributes)
    attributes.pop(_AFTER_DEADLINE, None)  # reserved: a caller's value and type are replaced
    if after_deadline:
        attributes[_AFTER_DEADLINE] = True
    events = [Event(e.name, scrub_attributes(redactor, e.attributes), e.timestamp) for e in span.events]
    return ReadableSpan(
        name=span.name,
        context=span.context,
        parent=span.parent,
        resource=span.resource,
        attributes=attributes,
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
        self._deadlines = _TrialDeadlines()

    def export(self, spans: Sequence[ReadableSpan]) -> SpanExportResult:
        if self.outcome is None:
            return self.inner.export([scrub_span(s, self.redactor, after_deadline=self._deadlines.is_late(s)) for s in spans])
        self.outcome.begin_batch()
        try:
            result = self.inner.export([scrub_span(s, self.redactor, after_deadline=self._deadlines.is_late(s)) for s in spans])
        except Exception:  # batch processors swallow exceptions; do not log raw exception text
            result = SpanExportResult.FAILURE
        status = self.outcome.status_code
        if result != SpanExportResult.SUCCESS or (status is not None and not 200 <= status < 300):
            self.outcome.failed()
            return SpanExportResult.FAILURE
        return result

    def shutdown(self) -> None:
        try:
            self.inner.shutdown()
        finally:
            self._deadlines.shutdown()

    def force_flush(self, timeout_millis: int = 30000) -> bool:
        flush = getattr(self.inner, "force_flush", None)
        return bool(flush(timeout_millis)) if callable(flush) else True


def _normalized_host(host: str) -> Any:
    """Compare host identities without DNS; mapped IPv6 remains distinct from IPv4."""
    try:
        return ip_address(host)
    except ValueError:
        return idna.encode(host, uts46=True).decode("ascii").lower().removesuffix(".")


def _validate_collector_endpoint(endpoint: str, *, base_url: str, legacy: bool = False) -> str:
    """Validate without normalizing the transport URL or disclosing any of its value."""
    from fi.experiments.errors import ExperimentError

    try:
        # urlsplit silently strips some whitespace/controls: refuse them before parsing.
        if (any(c.isspace() or ord(c) < 32 or 127 <= ord(c) < 160 for c in endpoint)
                or any(c in endpoint for c in "?#\\")
                or re.search(r"%(?![0-9a-fA-F]{2})", endpoint)
                or any(ord(c) < 32 or 127 <= ord(c) < 160 or c == "\\" for c in unquote(endpoint))):
            raise ValueError
        parts = urlsplit(endpoint)
        host, port = parts.hostname or "", parts.port
        if (parts.scheme not in ("http", "https") or not host
                or parts.username is not None or parts.password is not None
                or "%" in parts.netloc
                or not re.fullmatch(r"(?:\[[^\]]+\]|[^:\[\]]+)(?::[0-9]+)?", parts.netloc)
                or port is not None and not 1 <= port <= 65535):
            raise ValueError
        try:
            ip_address(host)
        except ValueError:
            ascii_host = idna.encode(host, uts46=True).decode("ascii").removesuffix(".")
            if (parts.netloc.startswith("[") or len(ascii_host) > 253
                    or re.fullmatch(r"[0-9.]+", ascii_host)
                    or not all(re.fullmatch(r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?", label)
                               for label in ascii_host.split("."))):
                raise ValueError
        loopback = is_loopback_host(host)
        if parts.scheme == "http" and not (legacy or loopback):
            base = urlsplit(base_url)
            if base.scheme != "http" or _normalized_host(base.hostname or "") != _normalized_host(host):
                raise ValueError
    except (ValueError, UnicodeError):
        raise ExperimentError(
            "FI_COLLECTOR_ENDPOINT must be a full trace URL. Use HTTPS unless the collector is loopback "
            "or uses the same host as an HTTP API base. "
            "Use a valid host and port, with no userinfo, query, fragment, whitespace or control characters."
        ) from None
    return endpoint


def _endpoint_setting(endpoint: str) -> str:
    """The setting the run's trace endpoint comes from: ``FI_COLLECTOR_ENDPOINT`` when it is set, else ``FI_BASE_URL``."""
    explicit = os.environ.get("FI_COLLECTOR_ENDPOINT")
    return "FI_COLLECTOR_ENDPOINT" if explicit and explicit == endpoint else "FI_BASE_URL"


def collector_endpoint(base_url: str) -> str:
    """Use FI_COLLECTOR_ENDPOINT or derive the route from base_url; ignore ambient OTEL endpoints."""
    explicit = os.environ.get("FI_COLLECTOR_ENDPOINT")
    endpoint = explicit or base_url.rstrip("/") + "/tracer/v1/traces"
    return _validate_collector_endpoint(endpoint, base_url=base_url, legacy=not explicit)



def run_resource(project: str, run_name: str, run_id: str) -> Any:
    """The run's OpenTelemetry resource: the attributes traceAI's ``register`` would write (project, type, version
    name/id, convention), set here on the SDK's own provider; ``register`` itself is not called (``exporter_factory``).

    The collector uses ``project_name`` to choose the Observe project. The SDK includes ``project_type`` and
    ``project_version_*`` in the resource, but the collector does not use them to route spans (acceptance contract 48)."""
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


def _refusals() -> tuple[type[BaseException], ...]:
    """What a refused exporter raises: the SDK's configuration error, and the instrumentation package's
    own refusal when that package defines one."""
    errors: list[type[BaseException]] = [ConfigurationError]
    try:
        from fi_instrumentation.otel import UnsupportedOTLPExporterError

        errors.append(UnsupportedOTLPExporterError)
    except ImportError:
        pass
    return tuple(errors)


def exporter_factory(*, base_url: str, api_key: str, secret_key: str, project: str, run_name: str, run_id: str,
                     redactor: Redactor, inner: Any = None,
                     extra_headers: Mapping[str, str] | None = None, outcome: Any = None,
                     _endpoint: str | None = None) -> Callable[[], Any]:
    """A factory for the run's delegate provider: a plain OpenTelemetry provider with one batch
    processor over the scrubbing exporter. traceAI's ``register()`` is not used: it installs SIGINT
    and SIGTERM handlers that call ``sys.exit(0)`` (the run's Ctrl-C contract is exit 4 after the
    journal flush), and its provider drops every processor on the next ``add_span_processor``.

    ``extra_headers`` (the run client's ``FI_EXTRA_HEADERS`` / ``extra_headers=``, read when the run
    starts and scoped to the destination by UploadSession) go beside the run's keys; they do not
    become a span attribute. ``_endpoint`` is UploadSession's snapshot, shared with its header
    selection and status. Resolve it here only for callers without that snapshot, and not in ``make``.
    ``outcome`` records terminal batch failures for the engine to report after shutdown; a successful
    queue flush alone does not mean the collector accepted any spans."""
    from fi.experiments._tracing.export_status import ExportSession, ExportStatus

    endpoint = collector_endpoint(base_url) if _endpoint is None else _validate_collector_endpoint(
        _endpoint, base_url=base_url,
        legacy=_endpoint == base_url.rstrip("/") + "/tracer/v1/traces",
    )
    headers = {**(extra_headers or {}), "X-Api-Key": api_key, "X-Secret-Key": secret_key}
    require_secure_credentials_url(endpoint, setting="FI_COLLECTOR_ENDPOINT or the base URL", proxies_disabled=True)  # ExportSession sends plain HTTP direct
    if outcome is None:
        outcome = ExportStatus(run_id, endpoint, redactor)

    def make() -> Any:
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor

        exporter = inner
        try:
            if exporter is not None:
                # An exporter handed in is held to the same endpoint rule as the one built here.
                refuse_unreadable_exporter_target(exporter)
            else:
                from fi_instrumentation.otel import HTTPSpanExporter

                refuse_ambiguous_endpoint(endpoint, tls=endpoint.lower().startswith("https://"))
                # Future AGI hosts take https only, also when FI_BASE_URL itself is an http address.
                refuse_plain_http_futureagi(endpoint, _endpoint_setting(endpoint), keys=True)
                exporter = pin_headers(
                    HTTPSpanExporter(endpoint=endpoint, headers=headers, session=ExportSession(outcome)),
                    headers)
        except _refusals() as refusal:
            # Nothing is sent, and no exporter with unpinned headers takes its place. The run
            # records its items and reports the trace export failure at shutdown.
            # The SDK's refusals carry constant, value-free text that ends with their code.
            outcome.reason = (str(refusal) if isinstance(refusal, ConfigurationError)
                              else "exporter headers could not be set (unsupported_otlp_exporter)")
            outcome.failed()
            return TracerProvider(resource=run_resource(project, run_name, run_id))
        provider = TracerProvider(resource=run_resource(project, run_name, run_id))
        wrapper = ScrubbingExporter(exporter, redactor, outcome)
        provider._fi_trial_deadlines = wrapper._deadlines
        provider.add_span_processor(BatchSpanProcessor(wrapper))
        return provider

    return make
