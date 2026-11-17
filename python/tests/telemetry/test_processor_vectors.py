import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from fi.telemetry._otel import CARRIER_KEY, allowlisted
from fi.telemetry._registry import registry
from fi.telemetry.processor import FutureAGISkillsSpanProcessor

VECTORS = json.loads((Path(__file__).parent / "vectors/processor_v1.json").read_text())["vectors"]


@pytest.mark.parametrize("vector", VECTORS, ids=lambda v: v["name"])
def test_processor_contract(tracing, vector):
    from opentelemetry.context import Context, set_value
    class Span:
        def __init__(self):
            self.attributes = dict(vector["explicit"])
        def get_span_context(self):
            return SimpleNamespace(trace_id=42)
        def set_attribute(self, key, value):
            self.attributes[key] = list(value) if isinstance(value, tuple) else value
    registry.get(42, create=True).attrs.update(vector["registry"])
    parent = Context()
    if vector["carrier"] is not None:
        parent = set_value(CARRIER_KEY, vector["carrier"], parent)
    span = Span()
    FutureAGISkillsSpanProcessor().on_start(span, parent)
    assert span.attributes == vector["expected"]


def test_attribute_limits():
    assert len(allowlisted({f"fi.context.k{i}": i for i in range(100)})) == 64
    attrs = allowlisted({"fi.context.name": "é" * 256, "fi.skills.refs": ["a"] * 40})
    assert len(attrs["fi.context.name"].encode()) <= 256
    assert len(attrs["fi.skills.refs"]) == 32


def test_sdk_carrier_is_a_detached_immutable_contract_mapping():
    from dataclasses import FrozenInstanceError
    from fi.telemetry._otel import carrier

    original = {"fi.skills.refs": ["refund@v1"], "private": "drop"}
    value = carrier(original, reset=True)
    original["fi.skills.refs"].append("other@v1")
    assert dict(value) == {
        "v": 1, "attrs": {"fi.skills.refs": ("refund@v1",)}, "reset_skills": True,
    }
    with pytest.raises(TypeError):
        value.attrs["fi.context.name"] = "changed"
    with pytest.raises(FrozenInstanceError):
        value.attrs = {}
    with pytest.raises(KeyError):
        _ = value["unknown"]


def test_sdk_carrier_fast_path_preserves_explicit_values(tracing):
    from opentelemetry.context import Context, set_value
    from fi.telemetry._otel import carrier

    tracer, exporter, _ = tracing
    parent = set_value(CARRIER_KEY, carrier({
        "gen_ai.agent.name": "parent", "fi.skills.refs": ["refund@v1"],
        "private": "drop",
    }), Context())
    span = tracer.start_span("child", context=parent, attributes={"gen_ai.agent.name": "child"})
    span.end()  # Also exercises OTel's _on_ending hook on recent SDK versions.
    assert exporter.get_finished_spans()[-1].attributes == {
        "gen_ai.agent.name": "child", "fi.skills.refs": ("refund@v1",),
    }


def test_ending_hooks_do_not_inspect_or_retain_the_span():
    class UnreadableSpan:
        def __getattribute__(self, name):
            raise AssertionError("End hooks must do no work")

    processor = FutureAGISkillsSpanProcessor()
    span = UnreadableSpan()
    processor._on_ending(span)
    processor.on_end(span)
    assert vars(processor) == {}
