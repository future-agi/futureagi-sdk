"""Tracing for experiment runs.

One routed global provider; one delegate provider per run; one root span per trial with the run
identity as span attributes and W3C baggage; in-memory capture of each trial's spans for local
evaluators and the cost meter.

An uploaded run's spans are stored in an Observe project (default ``"<dataset> · experiments"``) and
joined to the run by run id (``fi.experiment.run_id`` on every span; ``trace_id`` / ``root_span_id``
on every item). There is no experiment-typed project.
"""

from fi.experiments._tracing.session import NullRunTracing, RunTracing, TrialTrace, setup_run_tracing

__all__ = ["RunTracing", "NullRunTracing", "TrialTrace", "setup_run_tracing"]
