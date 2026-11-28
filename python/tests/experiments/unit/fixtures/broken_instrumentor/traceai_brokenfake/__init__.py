"""A stand-in for an installed traceAI instrumentor whose own import fails (an add-on built against a missing module).

With anthropic 1.17.0 and traceAI-anthropic 0.1.10, ``import traceai_anthropic`` succeeds but
``AnthropicInstrumentor().instrument()`` raises
``ModuleNotFoundError: No module named 'anthropic.resources.completions'``. The ``traceai_instrumentfake`` fixture
models that instrumentation failure. This fixture models an import-time failure by importing an absent module,
so Python itself raises ``ModuleNotFoundError`` without monkeypatching.
"""

from fi_test_absent_provider.resources.completions import Completions  # noqa: F401


class AnthropicInstrumentor:  # unreachable because the import above fails
    def instrument(self, tracer_provider=None):
        raise AssertionError("unreachable")
