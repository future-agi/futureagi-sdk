"""pin_headers: an OTLP exporter built with ambient header settings in the environment ends up with
exactly the headers it is given, on the HTTP and gRPC exporters of the installed OpenTelemetry."""

import os

import pytest

from fi._otlp_headers import pin_headers
from fi.errors import ConfigurationError

AMBIENT = "Authorization=Bearer fake-ambient,x-ambient=1"
SDK = {"X-Api-Key": "k-test-1234", "X-Secret-Key": "s-test-1234"}


@pytest.fixture
def ambient(monkeypatch):
    monkeypatch.setenv("OTEL_EXPORTER_OTLP_HEADERS", AMBIENT)
    monkeypatch.setenv("OTEL_EXPORTER_OTLP_TRACES_HEADERS", AMBIENT)


def http_wire_headers(exporter):
    client = getattr(exporter, "_client", None)
    if client is not None and hasattr(client, "_headers"):
        return {k.lower(): v for k, v in client._headers.items()}
    return {k.lower(): v for k, v in exporter._session.headers.items()}


def test_http_exporter_sends_the_given_headers_and_its_own_defaults(ambient):
    from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter

    before = dict(os.environ)
    exporter = pin_headers(OTLPSpanExporter(endpoint="http://127.0.0.1:9/v1/traces", headers=SDK), SDK)
    wire = http_wire_headers(exporter)
    assert wire["x-api-key"] == "k-test-1234" and wire["x-secret-key"] == "s-test-1234"
    assert wire["content-type"] == "application/x-protobuf"
    assert "x-ambient" not in wire and wire.get("authorization") != "Bearer fake-ambient"
    assert dict(os.environ) == before


def test_http_exporter_without_headers_sends_none_from_the_environment(ambient):
    from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter

    exporter = pin_headers(OTLPSpanExporter(endpoint="http://127.0.0.1:9/v1/traces"), None)
    wire = http_wire_headers(exporter)
    assert "x-ambient" not in wire and "authorization" not in wire


def test_http_exporter_keeps_its_compression_header(ambient):
    from opentelemetry.exporter.otlp.proto.http import Compression
    from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter

    exporter = pin_headers(OTLPSpanExporter(endpoint="http://127.0.0.1:9/v1/traces", headers=SDK,
                                            compression=Compression.Gzip), SDK)
    assert http_wire_headers(exporter)["content-encoding"] == "gzip"


def test_grpc_exporter_sends_only_the_given_metadata(ambient):
    from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter

    exporter = OTLPSpanExporter(endpoint="127.0.0.1:9", insecure=True)
    assert ("x-ambient", "1") in exporter._headers  # the standard behaviour the pin replaces
    pin_headers(exporter, SDK)
    assert dict(exporter._headers) == {"x-api-key": "k-test-1234", "x-secret-key": "s-test-1234"}
    exporter.shutdown()


def test_an_exporter_of_an_unknown_shape_is_refused_instead_of_pretending(ambient):
    class Odd:
        pass

    with pytest.raises(ConfigurationError, match="OTEL_EXPORTER_OTLP_HEADERS"):
        pin_headers(Odd(), SDK)
