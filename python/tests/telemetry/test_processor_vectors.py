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
