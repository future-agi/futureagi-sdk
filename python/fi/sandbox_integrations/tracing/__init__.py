"""Trace context for sandbox commands.

::

    from fi.sandbox_integrations.tracing import tracing_env, run_traced

    sbx.commands.run("python job.py", env=tracing_env())   # TRACEPARENT / TRACESTATE of the current span
    result = run_traced(sbx, "python job.py")               # the same, inside a ``sandbox.exec`` client span

Inside the sandbox, ``context_from_env()`` turns those variables back into an OpenTelemetry context
to attach before starting spans. No new extra: it uses the app's own OpenTelemetry when present, and
without it adds no trace keys. Only ``TRACEPARENT`` and ``TRACESTATE`` pass by default; every other
key is opt-in. Credential names (:data:`REFUSED_ENV_NAMES`) do not go into a command's ``env``. The
package path, the function names and the span attribute names are provisional. See ``README.md``.
"""

from ._env import REFUSED_ENV_NAMES, context_from_env, tracing_env
from ._run import arun_traced, run_traced

__all__ = [
    "REFUSED_ENV_NAMES",
    "tracing_env",
    "context_from_env",
    "run_traced",
    "arun_traced",
]
