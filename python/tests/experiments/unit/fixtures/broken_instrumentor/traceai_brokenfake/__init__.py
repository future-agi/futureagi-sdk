"""A stand-in for an installed traceAI instrumentor whose own import fails (an add-on built against a missing module).

Provenance, corrected in wave 2c: e2e FW-16bL-TA implementation (venv/laptop-anth1: anthropic 1.17.0 + traceAI-anthropic 0.1.10)
records ``ModuleNotFoundError: No module named 'anthropic.resources.completions'``, but that error is raised inside
``AnthropicInstrumentor().instrument()`` (traceai_anthropic/__init__.py line 43), not by ``import traceai_anthropic``,
which works (e2e tracing regression, 10-23). ``traceai_instrumentfake`` is that real shape; this module keeps the import-time
shape. The missing module is one no environment has, so the import fails the same way (a real ModuleNotFoundError
from the import system, not a patched exception) on every Python.
"""

from fi_test_absent_provider.resources.completions import Completions  # noqa: F401


class AnthropicInstrumentor:  # never reached: the import above fails first
    def instrument(self, tracer_provider=None):
        raise AssertionError("unreachable")
