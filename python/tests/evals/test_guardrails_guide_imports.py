"""Run the discovery and factory guide snippets with offline backend stand-ins."""

from pathlib import Path


GUIDE = Path(__file__).resolve().parents[2] / "fi/evals/guardrails/README.md"


def _snippet(heading):
    section = GUIDE.read_text().split(heading, 1)[1]
    return section.split("```python\n", 1)[1].split("```", 1)[0]


def test_discovery_example_imports_and_uses_public_class_methods(monkeypatch, capsys):
    from fi.evals.guardrails import GuardrailModel, Guardrails

    model = GuardrailModel.OPENAI_MODERATION
    monkeypatch.setattr(Guardrails, "discover_backends", staticmethod(lambda: [model]))
    monkeypatch.setattr(Guardrails, "get_backend_details", staticmethod(lambda: {
        model.value: {"status": "available", "reason": "offline example"},
    }))
    namespace = {}
    exec(compile(_snippet("## Discover Available Backends"), "<discovery-example>", "exec"), namespace)
    assert namespace["available"] == [model]
    assert "offline example" in capsys.readouterr().out


def test_gateway_factory_example_imports_and_constructs_each_variant(monkeypatch):
    from fi.evals.guardrails import GuardrailsGateway

    calls = []
    names = ["auto", "with_openai", "with_azure", "with_local_model", "with_ensemble"]

    def factory(name):
        def construct(*args, **kwargs):
            calls.append((name, args, kwargs))
            return object()
        return staticmethod(construct)

    for name in names:
        monkeypatch.setattr(GuardrailsGateway, name, factory(name))
    namespace = {}
    exec(compile(_snippet("### Factory Methods"), "<gateway-example>", "exec"), namespace)
    assert [call[0] for call in calls] == names
    assert calls[-2][1] == (namespace["GuardrailModel"].WILDGUARD_7B,)
    assert calls[-1][2]["aggregation"] is namespace["AggregationStrategy"].ANY
