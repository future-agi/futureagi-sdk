"""Cloud-only microbenchmark. Run with the SDK and its otel extra installed."""
from statistics import median
from time import perf_counter_ns
from types import SimpleNamespace

from opentelemetry.context import Context, set_value

from fi.telemetry._otel import CARRIER_KEY, carrier
from fi.telemetry.processor import FutureAGISkillsSpanProcessor


class Span:
    attributes = {}

    def set_attribute(self, key, value):
        pass

    def get_span_context(self):
        return SimpleNamespace(trace_id=1)


def main():
    attrs = {"fi.skills.ids": ("a", "b", "c"), "fi.skills.version_ids": ("1", "2", "3"),
             "fi.skills.refs": ("a@v1", "b@v2", "c@v3"), "fi.skills.count": 3}
    parent = set_value(CARRIER_KEY, carrier(attrs), Context())
    processor, span = FutureAGISkillsSpanProcessor(), Span()
    timings = []
    for _ in range(10000):
        start = perf_counter_ns()
        processor.on_start(span, parent)
        timings.append(perf_counter_ns() - start)
    p50 = median(timings) / 1000
    print(f"processor.on_start p50: {p50:.3f} microseconds")
    assert p50 <= 5, "Processor exceeds the 5 microsecond p50 budget"


if __name__ == "__main__":
    main()
