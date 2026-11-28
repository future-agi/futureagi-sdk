"""The global provider ``setup_tracing`` installs answers with the active configuration's resource, as the provider of a
single configuration does: ``Evaluator.evaluate(trace_eval=True)`` reads ``project_name`` from it."""

from __future__ import annotations

from typing import Iterator

import pytest

pytest.importorskip("opentelemetry.sdk.trace")

from opentelemetry import trace  # noqa: E402
from opentelemetry.util._once import Once  # noqa: E402

from fi.evals.otel import tracer as tracer_module  # noqa: E402
from fi.evals.otel.config import TraceConfig  # noqa: E402


def _reset_global() -> None:
    trace._TRACER_PROVIDER_SET_ONCE = Once()
    trace._TRACER_PROVIDER = None


@pytest.fixture(autouse=True)
def _fresh() -> Iterator[None]:
    tracer_module.shutdown_tracing()
    _reset_global()
    yield
    tracer_module.shutdown_tracing()
    _reset_global()


def test_the_global_provider_has_the_active_configurations_resource():
    configured = tracer_module.setup_tracing(TraceConfig(service_name="svc-a", exporters=[]))
    provider = trace.get_tracer_provider()
    assert hasattr(provider, "resource")
    assert provider.resource is configured.resource
    assert provider.resource.attributes.get("service.name") == "svc-a"


def test_the_resource_follows_the_next_configuration():
    tracer_module.setup_tracing(TraceConfig(service_name="svc-a", exporters=[]))
    tracer_module.shutdown_tracing()
    assert not hasattr(trace.get_tracer_provider(), "resource")
    configured = tracer_module.setup_tracing(TraceConfig(service_name="svc-b", exporters=[]))
    assert trace.get_tracer_provider().resource is configured.resource
    assert trace.get_tracer_provider().resource.attributes.get("service.name") == "svc-b"
