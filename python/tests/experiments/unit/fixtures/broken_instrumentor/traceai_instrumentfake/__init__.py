"""A stand-in for an installed traceAI instrumentor that imports fine and fails inside ``instrument()``.

Provenance: the real F3 failure of traceAI-anthropic 0.1.10 with anthropic 1.17.0 (e2e venv/laptop-anth1, rows
FW-16bL-TA implementation and tracing regression, 10-23): ``import traceai_anthropic`` works, and ``AnthropicInstrumentor().instrument()``
raises ``ModuleNotFoundError: No module named 'anthropic.resources.completions'`` from its ``_instrument`` (line 43),
because anthropic 1.x removed that module. Here ``instrument()`` imports a module no environment has, so it fails the
same way (a real ModuleNotFoundError from the import system) on every Python.
"""


class AnthropicInstrumentor:
    def instrument(self, tracer_provider=None, **kwargs):
        from fi_test_absent_provider.resources.completions import Completions  # noqa: F401

    def uninstrument(self, **kwargs):
        pass
