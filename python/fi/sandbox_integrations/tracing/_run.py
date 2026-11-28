"""Run one sandbox command inside a client span, ``sandbox.exec``, whose trace context goes into the
command's ``env`` so that spans made inside the sandbox hang under it.

``run_traced`` / ``arun_traced`` refuse a credential name in ``env`` before anything is sent, call
``sandbox.commands.run`` exactly once (not retried), and record how the command ended as span
attributes. A non-zero exit, a timeout, a signal and a cancel are attributes, not an error status;
only a raised error sets the status to ERROR, and it is raised again. The command line goes on the
span only with ``record_command=True`` (a command line can carry secrets); no ``env`` value ever
does. Without OpenTelemetry both run the command once with the caller's ``env``.

The attribute names (``sandbox.id``, ``sandbox.exec.*``) are provisional: they may change before
the first release that includes them.
"""

from __future__ import annotations

from contextlib import contextmanager
from typing import TYPE_CHECKING, Any, Callable, Dict, Iterator, Mapping, Optional

from .._exit import shell_exit_code
from ._env import refuse_secret_names, tracing_env

if TYPE_CHECKING:
    from fi.sandbox import AsyncSandbox, CommandResult, Sandbox

OutputCallback = Callable[[str], Any]

#: The tracer name used when no ``tracer`` is passed.
TRACER_NAME = "fi.sandbox_integrations"

#: Exit-record fields recorded on the span, by attribute name. A field that is None is left off.
_RESULT_ATTRIBUTES = (
    ("sandbox.exec.id", "exec_id"),
    ("sandbox.exec.exit_code", "exit_code"),
    ("sandbox.exec.signal", "signal"),
    ("sandbox.exec.timed_out", "timed_out"),
    ("sandbox.exec.cancelled", "cancelled"),
    ("sandbox.exec.truncated", "truncated"),
    ("sandbox.exec.duration_ms", "duration_ms"),
)


@contextmanager
def _exec_span(
    sandbox: Any, command: str, span_name: str, tracer: Any, record_command: bool
) -> Iterator[Any]:
    """The CLIENT span around one exec, current while it runs; None without OpenTelemetry."""
    try:
        from opentelemetry import trace
        from opentelemetry.trace import SpanKind, Status, StatusCode
    except ImportError:
        have_otel = False
    else:
        have_otel = True
    if not have_otel:
        # Outside the except block: an error the body raises chains nothing.
        yield None
        return
    tracer = tracer if tracer is not None else trace.get_tracer(TRACER_NAME)
    attributes: Dict[str, Any] = {"sandbox.id": str(sandbox.id)}
    if record_command:
        attributes["sandbox.exec.command"] = command
    with tracer.start_as_current_span(
        span_name,
        kind=SpanKind.CLIENT,
        attributes=attributes,
        record_exception=False,
        set_status_on_exception=False,
    ) as span:
        try:
            yield span
        except BaseException as error:
            # The class only: an error's text can echo the command, which stays off by default.
            span.set_attribute("error.type", type(error).__name__)
            exec_id = getattr(error, "exec_id", None)
            if exec_id:
                span.set_attribute("sandbox.exec.id", str(exec_id))
            span.set_status(Status(StatusCode.ERROR, type(error).__name__))
            raise


def _merged_env(
    sandbox: Any, span: Any, env: Optional[Mapping[str, str]], tracing: Mapping[str, Any]
) -> Optional[Dict[str, str]]:
    """``tracing_env`` for the exec span under the caller's ``env`` (the caller wins on a clash).
    ``sandbox.id`` joins the resource attributes only when the caller passes ``resource_attributes``."""
    options = dict(tracing)
    if "span" in options:
        raise TypeError("run_traced: span is the exec span; pass the parent as the current span")
    if options.get("resource_attributes") is not None:
        options["resource_attributes"] = {"sandbox.id": str(sandbox.id), **options["resource_attributes"]}
    merged = tracing_env(span=span, **options)
    merged.update(env or {})
    return merged or (None if env is None else {})


def _record_result(span: Any, result: Any) -> None:
    if span is None:
        return
    for name, field in _RESULT_ATTRIBUTES:
        value = getattr(result, field, None)
        if value is not None:
            span.set_attribute(name, value)
    code = shell_exit_code(result)
    if code is not None:
        span.set_attribute("sandbox.exec.shell_exit_code", code)


def run_traced(
    sandbox: "Sandbox",
    command: str,
    *,
    cwd: Optional[str] = None,
    env: Optional[Mapping[str, str]] = None,
    timeout_seconds: Optional[int] = None,
    on_stdout: Optional[OutputCallback] = None,
    on_stderr: Optional[OutputCallback] = None,
    span_name: str = "sandbox.exec",
    tracer: Any = None,
    record_command: bool = False,
    **tracing: Any,
) -> "CommandResult":
    """``sandbox.commands.run(command, ...)`` inside a CLIENT span named ``span_name``.

    The command's ``env`` is the caller's ``env`` over :func:`tracing_env` for that span: by default
    ``TRACEPARENT`` and ``TRACESTATE`` only. ``**tracing`` takes the opt-ins of :func:`tracing_env`
    (``baggage``, ``collector``, ``project_name``, ``project_version_name``, ``privacy_flags``,
    ``resource_attributes``, ``environ``); ``resource_attributes`` also gets ``sandbox.id``.
    ``tracer`` defaults to the global provider's tracer ``fi.sandbox_integrations``.

    Raises ``fi.sandbox.ConfigurationError`` (code ``secret_in_env``) before anything is sent when
    ``env`` names a credential variable, and whatever ``commands.run`` raises, after marking the
    span ERROR. Returns the ``CommandResult``."""
    refuse_secret_names(env, "run_traced")
    with _exec_span(sandbox, command, span_name, tracer, record_command) as span:
        result = sandbox.commands.run(
            command,
            cwd=cwd,
            env=_merged_env(sandbox, span, env, tracing),
            timeout_seconds=timeout_seconds,
            on_stdout=on_stdout,
            on_stderr=on_stderr,
        )
        _record_result(span, result)
        return result


async def arun_traced(
    sandbox: "AsyncSandbox",
    command: str,
    *,
    cwd: Optional[str] = None,
    env: Optional[Mapping[str, str]] = None,
    timeout_seconds: Optional[int] = None,
    on_stdout: Optional[OutputCallback] = None,
    on_stderr: Optional[OutputCallback] = None,
    span_name: str = "sandbox.exec",
    tracer: Any = None,
    record_command: bool = False,
    **tracing: Any,
) -> "CommandResult":
    """:func:`run_traced` for an ``AsyncSandbox``: the same span, ``env`` and refusals."""
    refuse_secret_names(env, "arun_traced")
    with _exec_span(sandbox, command, span_name, tracer, record_command) as span:
        result = await sandbox.commands.run(
            command,
            cwd=cwd,
            env=_merged_env(sandbox, span, env, tracing),
            timeout_seconds=timeout_seconds,
            on_stdout=on_stdout,
            on_stderr=on_stderr,
        )
        _record_result(span, result)
        return result


__all__ = ["run_traced", "arun_traced"]
