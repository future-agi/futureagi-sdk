"""The OTLP HTTP exporters check the TLS files named by the OpenTelemetry settings for an ``https://`` endpoint, the
one the exporter sends to: the endpoint given, else the one read from ``FI_BASE_URL`` or ``OTEL_EXPORTER_OTLP_*ENDPOINT``,
else the type's default. A plain ``http://`` endpoint is sent without reading the CA certificate or the client key, so
a missing file there does not stop the export.

``requests`` checks that the client certificate file exists on every scheme, so a missing
``OTEL_EXPORTER_OTLP_*CLIENT_CERTIFICATE`` is refused for ``http://`` as well. A plain endpoint that answers with a
redirect to ``https://`` reaches the ``https`` listener only with the files in place: ``requests`` stops the redirected
request before it connects.

Host names resolve to loopback (the ``rig`` helper); the listeners count connections, POST requests and marker bytes
at the target, at a ``CONNECT``-aware proxy sink and at the redirect targets.
"""

import pytest

from fi.errors import ConfigurationError
from fi.evals.otel.config import ExporterConfig
from fi.evals.otel.types import ExporterType
from tests.core.test_exporter_headers_are_read_once import export_one_span
from tests.experiments.unit.oracle_probe import Sink
from tests.experiments.unit.test_header_key_senders import MARKER, rig, wire_count  # noqa: F401

pytest.importorskip("opentelemetry.sdk.trace")

READ_ONLY_OVER_TLS = [
    "OTEL_EXPORTER_OTLP_TRACES_CERTIFICATE",
    "OTEL_EXPORTER_OTLP_CERTIFICATE",
    "OTEL_EXPORTER_OTLP_TRACES_CLIENT_KEY",
    "OTEL_EXPORTER_OTLP_CLIENT_KEY",
]
CLIENT_CERTIFICATE = ["OTEL_EXPORTER_OTLP_TRACES_CLIENT_CERTIFICATE", "OTEL_EXPORTER_OTLP_CLIENT_CERTIFICATE"]
ENDPOINT_SETTINGS = ["OTEL_EXPORTER_OTLP_TRACES_ENDPOINT", "OTEL_EXPORTER_OTLP_ENDPOINT", "FI_BASE_URL"]
OWN_COLLECTOR = [ExporterType.OTLP_HTTP, ExporterType.ARIZE, ExporterType.PHOENIX, ExporterType.LANGFUSE]


@pytest.fixture
def plain(rig, monkeypatch):  # noqa: F811
    for name in READ_ONLY_OVER_TLS + CLIENT_CERTIFICATE + ENDPOINT_SETTINGS:
        monkeypatch.delenv(name, raising=False)
    return rig


def posts(sink):
    return b"".join(sink.data).count(b"POST /")


def missing(tmp_path):
    return str(tmp_path / "absent-dir" / "absent.pem")


def send(kind, endpoint, headers=None):
    from fi.evals.otel._tracer_factories import _create_exporter

    try:
        exporter = _create_exporter(ExporterConfig(type=kind, endpoint=endpoint, headers=headers))
    except ConfigurationError as error:
        return error
    assert exporter is not None
    export_one_span(exporter)
    return None


def delivered_once(rig, marker_bytes=0):  # noqa: F811
    """One connection and one POST at the target, the expected marker count there, nothing at any other sink."""
    others = [sink for sink in rig.sinks if sink is not rig.target]
    assert (rig.target.connections, posts(rig.target), wire_count(rig.target)) == (1, 1, marker_bytes)
    assert sum(sink.connections for sink in others) == 0
    assert sum(wire_count(sink) for sink in others) == 0


@pytest.mark.parametrize("variable", READ_ONLY_OVER_TLS)
@pytest.mark.parametrize("kind", OWN_COLLECTOR)
def test_a_plain_localhost_collector_receives_the_export_with_a_missing_tls_file(plain, monkeypatch, tmp_path, kind, variable):
    monkeypatch.setenv(variable, missing(tmp_path))
    error = send(kind, f"http://localhost:{plain.target.port}/v1/traces")
    assert error is None, error
    delivered_once(plain)


@pytest.mark.parametrize("variable", READ_ONLY_OVER_TLS)
@pytest.mark.parametrize("kind", [ExporterType.OTLP_HTTP, ExporterType.ARIZE])
def test_a_keyed_plain_localhost_collector_receives_the_export_with_a_missing_tls_file(
    plain, monkeypatch, tmp_path, kind, variable
):
    monkeypatch.setenv(variable, missing(tmp_path))
    error = send(kind, f"http://localhost:{plain.target.port}/v1/traces", headers={"X-Api-Key": MARKER})
    assert error is None, error
    delivered_once(plain, marker_bytes=1)


@pytest.mark.parametrize("variable", READ_ONLY_OVER_TLS)
def test_futureagi_on_a_plain_localhost_base_url_receives_the_export_with_a_missing_tls_file(
    plain, monkeypatch, tmp_path, variable
):
    monkeypatch.setenv(variable, missing(tmp_path))
    monkeypatch.setenv("FI_BASE_URL", f"http://localhost:{plain.target.port}")
    monkeypatch.setenv("FI_API_KEY", MARKER)
    monkeypatch.setenv("FI_SECRET_KEY", "fi-secret-value")
    error = send(ExporterType.FUTUREAGI, None)
    assert error is None, error
    delivered_once(plain, marker_bytes=1)


@pytest.mark.parametrize("setting", ["OTEL_EXPORTER_OTLP_TRACES_ENDPOINT", "OTEL_EXPORTER_OTLP_ENDPOINT"])
@pytest.mark.parametrize("kind", [ExporterType.ARIZE, ExporterType.PHOENIX, ExporterType.LANGFUSE])
def test_a_plain_endpoint_from_the_environment_receives_the_export_with_a_missing_tls_file(
    plain, monkeypatch, tmp_path, kind, setting
):
    monkeypatch.setenv("OTEL_EXPORTER_OTLP_CERTIFICATE", missing(tmp_path))
    base = f"http://localhost:{plain.target.port}"
    monkeypatch.setenv(setting, f"{base}/v1/traces" if setting.endswith("TRACES_ENDPOINT") else base)
    error = send(kind, None)
    assert error is None, error
    delivered_once(plain)


def test_the_plain_default_endpoint_builds_with_a_missing_tls_file(plain, monkeypatch, tmp_path):
    from fi.evals.otel._tracer_factories import _create_exporter

    monkeypatch.setenv("OTEL_EXPORTER_OTLP_CERTIFICATE", missing(tmp_path))
    assert _create_exporter(ExporterConfig(type=ExporterType.OTLP_HTTP)) is not None
    assert sum(sink.connections for sink in plain.sinks) == 0


@pytest.mark.parametrize("variable", CLIENT_CERTIFICATE)
@pytest.mark.parametrize("kind", OWN_COLLECTOR)
def test_a_missing_client_certificate_is_refused_for_a_plain_endpoint_too(plain, monkeypatch, tmp_path, kind, variable):
    monkeypatch.setenv(variable, missing(tmp_path))
    error = send(kind, f"http://localhost:{plain.target.port}/v1/traces")
    assert isinstance(error, ConfigurationError) and error.code == "unreadable_tls_file", error
    assert variable in str(error) and "absent" not in str(error)
    assert sum(sink.connections for sink in plain.sinks) == 0


@pytest.mark.parametrize("variable", READ_ONLY_OVER_TLS + CLIENT_CERTIFICATE)
@pytest.mark.parametrize("kind", [ExporterType.ARIZE, ExporterType.PHOENIX, ExporterType.LANGFUSE])
def test_an_https_endpoint_from_the_environment_is_refused_with_a_missing_tls_file(
    plain, monkeypatch, tmp_path, kind, variable
):
    monkeypatch.setenv(variable, missing(tmp_path))
    monkeypatch.setenv("OTEL_EXPORTER_OTLP_TRACES_ENDPOINT", f"https://collector.example.test:{plain.target.port}/v1/traces")
    error = send(kind, None)
    assert isinstance(error, ConfigurationError) and error.code == "unreadable_tls_file", error
    assert sum(sink.connections for sink in plain.sinks) == 0


@pytest.mark.parametrize("base_url", [None, "https://collector.example.test"])
@pytest.mark.parametrize("variable", READ_ONLY_OVER_TLS + CLIENT_CERTIFICATE)
def test_futureagi_on_an_https_base_url_is_refused_with_a_missing_tls_file(plain, monkeypatch, tmp_path, variable, base_url):
    monkeypatch.setenv(variable, missing(tmp_path))
    if base_url is None:
        monkeypatch.delenv("FI_BASE_URL", raising=False)
    else:
        monkeypatch.setenv("FI_BASE_URL", f"{base_url}:{plain.target.port}")
    error = send(ExporterType.FUTUREAGI, None)
    assert isinstance(error, ConfigurationError) and error.code == "unreadable_tls_file", error
    assert sum(sink.connections for sink in plain.sinks) == 0


@pytest.mark.parametrize("variable", ["OTEL_EXPORTER_OTLP_TRACES_CERTIFICATE", "OTEL_EXPORTER_OTLP_CERTIFICATE"])
@pytest.mark.parametrize("kind", OWN_COLLECTOR)
def test_a_redirect_to_https_does_not_reach_the_https_listener_with_a_missing_ca_file(
    plain, monkeypatch, tmp_path, kind, variable
):
    monkeypatch.setenv(variable, missing(tmp_path))
    landing = Sink(False)
    bouncer = Sink(False, redirect=f"https://localhost:{landing.port}/v1/traces")
    try:
        error = send(kind, f"http://localhost:{bouncer.port}/v1/traces")
        assert error is None, error
        assert (bouncer.connections, posts(bouncer)) == (1, 1)
        assert landing.connections == 0
        assert sum(sink.connections for sink in plain.sinks) == 0
    finally:
        landing.close()
        bouncer.close()



def test_the_same_redirect_reaches_the_https_listener_when_the_ca_file_is_there(plain, monkeypatch, tmp_path):
    from fi.evals.otel._tracer_factories import _create_exporter

    present = tmp_path / "present.pem"
    present.write_bytes(b"not a certificate")
    monkeypatch.setenv("OTEL_EXPORTER_OTLP_CERTIFICATE", str(present))
    landing = Sink(False)
    bouncer = Sink(False, redirect=f"https://localhost:{landing.port}/v1/traces")
    try:
        endpoint = f"http://localhost:{bouncer.port}/v1/traces"
        export_one_span(_create_exporter(ExporterConfig(type=ExporterType.OTLP_HTTP, endpoint=endpoint, timeout_ms=1000)))
        # The handshake fails on the file's content and the exporter retries; each attempt is redirected.
        assert bouncer.connections >= 1 and posts(bouncer) >= 1
        assert landing.connections >= 1 and posts(landing) == 0
    finally:
        landing.close()
        bouncer.close()
