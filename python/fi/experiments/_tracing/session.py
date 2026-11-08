"""Per-run tracing: the delegate provider, the trial root span, and in-memory capture."""

from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Any, Callable, Iterator, Mapping, Optional

MAX_ATTR_BYTES = 32 * 1024


def truncate(value: str, limit: int = MAX_ATTR_BYTES) -> str:
    """``value`` within ``limit`` UTF-8 bytes, the ``…[truncated]`` marker included."""
    data = value.encode("utf-8")
    if len(data) <= limit:
        return value
    marker = "…[truncated]"
    return data[: limit - len(marker.encode("utf-8"))].decode("utf-8", errors="ignore") + marker


@dataclass
class TrialTrace:
    trace_id: Optional[str] = None
    root_span_id: Optional[str] = None
    span: Any = None
    spans: list = field(default_factory=list)
    dropped: int = 0  # spans past the capture limits (not kept)
    capture: Any = None  # CaptureStats when the trial's capture hit a limit
    captured: bool = False  # False = no capture (trace=False / tracing unavailable)

    def set_io(self, input_text: Optional[str] = None, output_text: Optional[str] = None) -> None:
        if self.span is None:
            return
        if input_text is not None:
            self.span.set_attribute("input.value", truncate(input_text))
        if output_text is not None:
            self.span.set_attribute("output.value", truncate(output_text))

    def record_error(self, exc: BaseException) -> None:
        if self.span is None:
            return
        from opentelemetry.trace import Status, StatusCode

        self.span.record_exception(exc)
        self.span.set_status(Status(StatusCode.ERROR, str(exc)[:500]))


class NullRunTracing:
    enabled = False
    instrumentors: tuple = ()
    failed: tuple = ()  # (instrumentor name, why) for each one that failed to load

    def __init__(self, note: str = "off") -> None:
        self.header = f"Tracing  {note}"

    @contextmanager
    def trial(self, example_id: str, trial: int) -> Iterator[TrialTrace]:
        yield TrialTrace()

    def shutdown(self) -> None:
        return None

    def child_starter(self, tt: TrialTrace) -> None:
        return None


class RunTracing:
    enabled = True

    def __init__(
        self,
        delegate: Any,
        capture: Any,
        identity: Mapping[str, str],
        header: str,
        *,
        use_router: bool,
        owns_delegate: bool,
        instrumentors: tuple = (),
        failed: tuple = (),
    ) -> None:
        self.instrumentors = tuple(instrumentors)
        self.failed = tuple(failed)
        self.delegate = delegate
        self.capture = capture
        self.identity = dict(identity)
        self.header = header
        self._use_router = use_router
        self._owns = owns_delegate
        self._tracer = delegate.get_tracer("fi.experiments")

    @contextmanager
    def trial(self, example_id: str, trial: int) -> Iterator[TrialTrace]:
        from opentelemetry import baggage
        from opentelemetry import context as otel_context
        from opentelemetry import trace as trace_api

        from fi.experiments._tracing.routing import bind_delegate, unbind_delegate

        attrs = {
            **self.identity,
            "fi.experiment.example_id": str(example_id),
            "fi.experiment.trial": str(trial),
        }
        ctx = otel_context.Context()  # a fresh trace per trial, whatever the caller's context
        for key, value in attrs.items():
            ctx = baggage.set_baggage(key, value, ctx)
        d_token = bind_delegate(self.delegate) if self._use_router else None
        failed = {"fi.experiment.tracing.failed_instrumentors": tuple(
            f"{failed_package(n)}: {why}" for n, why in self.failed)} if self.failed else {}
        span = self._tracer.start_span(
            "experiment.trial",
            context=ctx,
            attributes={**attrs, "gen_ai.span.kind": "CHAIN", "fi.span.kind": "CHAIN", **failed},
        )
        sc = span.get_span_context()
        if self.capture is not None:
            self.capture.open(sc.trace_id)
        tt = TrialTrace(
            trace_id=format(sc.trace_id, "032x"),
            root_span_id=format(sc.span_id, "016x"),
            span=span,
            captured=self.capture is not None,
        )
        c_token = otel_context.attach(trace_api.set_span_in_context(span, ctx))
        try:
            yield tt
        finally:
            otel_context.detach(c_token)
            stats = self.capture.stats(sc.trace_id) if self.capture is not None else None
            if stats is not None and stats.limited:  # the exported root says the local copy was cut
                span.set_attributes(stats.marker())
            span.end()
            if d_token is not None:
                unbind_delegate(d_token)
            if self.capture is not None:
                tt.spans, stats = self.capture.close(sc.trace_id)
                tt.dropped = stats.dropped if stats is not None else 0
                tt.capture = stats if stats is not None and stats.limited else None

    def child_starter(self, tt: TrialTrace) -> Optional[Callable[[str, Mapping[str, Any]], Any]]:
        """``start(name, attributes)`` → a started span, child of the trial's root span, on the run's own
        provider (exported with an uploaded run). Evaluators run after the trial's span has ended; a child
        may still start then. Such a span is not in the trial's local capture (it is closed), so the task's
        token and cost meter never counts it. None when the trial has no root span."""
        root = tt.span
        if root is None:
            return None

        def start(name: str, attributes: Mapping[str, Any]) -> Any:
            from opentelemetry import baggage
            from opentelemetry import context as otel_context
            from opentelemetry import trace as trace_api

            ctx = otel_context.Context()
            for key, value in {**self.identity, **_trial_identity(root)}.items():
                ctx = baggage.set_baggage(key, value, ctx)
            return self._tracer.start_span(name, context=trace_api.set_span_in_context(root, ctx),
                                           attributes=dict(attributes))

        return start

    def shutdown(self) -> None:
        flush = getattr(self.delegate, "force_flush", None)
        if callable(flush):
            flush()
        if self._owns:
            stop = getattr(self.delegate, "shutdown", None)
            if callable(stop):
                stop()


def _trial_identity(root: Any) -> dict[str, str]:
    attrs = getattr(root, "attributes", None) or {}
    return {k: str(attrs[k]) for k in ("fi.experiment.example_id", "fi.experiment.trial") if k in attrs}


def failed_package(name: str) -> str:
    from fi.experiments._tracing.instrument import INSTRUMENTORS

    return INSTRUMENTORS[name][2] if name in INSTRUMENTORS else name


def _keep_the_users_exporter(provider: Any) -> None:
    """traceAI's ``register()`` marks its exporting processor as the provider's default, and its
    ``add_span_processor()`` shuts that default down and drops it before adding the new one. The SDK's
    processors (baggage, local capture) are additions to the user's provider, never a replacement, so
    the default is unmarked first. Without this, ``trace=register(...)`` exported nothing at all (e2e
    tracing regression on dsx-e2e-1: no span reached the user's project). It stays unmarked after the run, so a
    processor the user adds later runs beside register()'s exporter instead of replacing it (marking it
    again would make that next add drop every processor added since)."""
    if getattr(provider, "_default_processor", None) is True:
        provider._default_processor = False


def _otel_available() -> bool:
    try:
        import opentelemetry.sdk.trace  # noqa: F401
    except ImportError:
        return False
    return True


def setup_run_tracing(
    *,
    trace: Any,
    instrument: Any,
    framework: Optional[str],
    project: str,
    run_name: str,
    identity: Mapping[str, str],
    upload: bool,
    exporter_factory: Optional[Callable[[], Any]] = None,
) -> Any:
    """Build the run's tracing. ``trace`` is True, False, or a TracerProvider to use as is."""
    if trace is False:
        return NullRunTracing("off (trace=False)")
    from fi.experiments._tracing import instrument as inst

    if trace is True:
        inst.require_supported_python()
        if not _otel_available():
            from fi.experiments.errors import MissingExtraError

            raise MissingExtraError("experiments", "OpenTelemetry (fi-instrumentation-otel), needed for trace=True,")
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.sdk.trace import TracerProvider

    from fi.experiments._tracing.baggage import BaggageAttributesProcessor
    from fi.experiments._tracing.capture import TrialCapture
    from fi.experiments._tracing.routing import install_router

    capture = TrialCapture()
    if trace is not True:
        provider = trace
        add = getattr(provider, "add_span_processor", None)
        if callable(add) and not getattr(provider, "_fi_experiments_processors", False):
            _keep_the_users_exporter(provider)
            add(BaggageAttributesProcessor())
            add(capture)
            setattr(provider, "_fi_experiments_processors", capture)
        else:
            capture = getattr(provider, "_fi_experiments_processors", None) or None
        the_plan = inst.plan(framework, instrument)
        inst.apply(provider, the_plan)
        return RunTracing(
            provider, capture, identity, f"Tracing  your provider · {the_plan.header()}",
            use_router=False, owns_delegate=False, instrumentors=tuple(the_plan.enable),
            failed=tuple(the_plan.failed),
        )

    router = install_router()
    if upload:
        if exporter_factory is None:
            raise RuntimeError("an exporting run needs an exporter factory")
        delegate = exporter_factory()
        where = f'project "{project}"'
    else:
        delegate = TracerProvider(
            resource=Resource.create(
                {"project_name": project, "project_type": "experiment", "project_version_name": run_name}
            )
        )
        where = "captured locally, nothing sent"
    delegate.add_span_processor(BaggageAttributesProcessor())
    delegate.add_span_processor(capture)
    the_plan = inst.plan(framework, instrument)
    inst.apply(router, the_plan)
    return RunTracing(
        delegate, capture, identity, f"Tracing  {the_plan.header()} · {where}",
        use_router=True, owns_delegate=True, instrumentors=tuple(the_plan.enable),
        failed=tuple(the_plan.failed),
    )
