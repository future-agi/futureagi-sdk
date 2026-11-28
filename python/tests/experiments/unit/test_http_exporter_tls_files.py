"""The OTLP HTTP exporters refuse an unreadable TLS file named by the OpenTelemetry settings (code
``unreadable_tls_file``, naming only the setting), and a gRPC exporter for Future AGI refuses an ``http://`` target
whether ``insecure`` is unset or False. Fake keys and nothing sent."""

import pytest

from fi.errors import ConfigurationError
from tests.experiments.unit.test_fi_bound_ambiguous_endpoints import build
from tests.experiments.unit.test_fi_bound_authority_forms import clean_hosts  # noqa: F401

TLS_SETTINGS = [
    "OTEL_EXPORTER_OTLP_TRACES_CERTIFICATE",
    "OTEL_EXPORTER_OTLP_CERTIFICATE",
    "OTEL_EXPORTER_OTLP_TRACES_CLIENT_KEY",
    "OTEL_EXPORTER_OTLP_CLIENT_KEY",
    "OTEL_EXPORTER_OTLP_TRACES_CLIENT_CERTIFICATE",
    "OTEL_EXPORTER_OTLP_CLIENT_CERTIFICATE",
]
HTTP_EXPORTERS = [
    ("OTLP_HTTP", "https://collector.example.test/v1/traces"),
    ("OTLP_HTTP", "https://api.futureagi.com/tracer/v1/traces"),
    ("FUTUREAGI", "https://api.futureagi.com/tracer/v1/traces"),
    ("ARIZE", "https://collector.example.test/v1/traces"),
    ("PHOENIX", "https://collector.example.test/v1/traces"),
    ("LANGFUSE", "https://collector.example.test/v1/traces"),
]


@pytest.fixture
def keys(monkeypatch, clean_hosts):  # noqa: F811
    for name in TLS_SETTINGS:
        monkeypatch.delenv(name, raising=False)
    monkeypatch.delenv("FI_ALLOW_INSECURE_HTTP", raising=False)
    monkeypatch.setenv("FI_API_KEY", "fi-key-value")
    monkeypatch.setenv("FI_SECRET_KEY", "fi-secret-value")


@pytest.mark.parametrize("kind,endpoint", HTTP_EXPORTERS)
@pytest.mark.parametrize("variable", TLS_SETTINGS)
def test_an_http_exporter_refuses_an_unreadable_tls_file(keys, monkeypatch, tmp_path, kind, endpoint, variable):
    monkeypatch.setenv(variable, str(tmp_path / "secret-dir-name" / "missing.pem"))
    with pytest.raises(ConfigurationError) as refused:
        build(kind, endpoint)
    assert refused.value.code == "unreadable_tls_file"
    message = str(refused.value)
    assert variable in message
    assert "secret-dir-name" not in message and "missing.pem" not in message


@pytest.mark.parametrize("kind,endpoint", HTTP_EXPORTERS)
def test_an_http_exporter_builds_with_readable_tls_files(keys, monkeypatch, tmp_path, kind, endpoint):
    present = tmp_path / "present.pem"
    present.write_bytes(b"not a certificate")
    for variable in TLS_SETTINGS[:2]:
        monkeypatch.setenv(variable, str(present))
    assert build(kind, endpoint) is not None


@pytest.mark.parametrize("insecure", [None, False])
@pytest.mark.parametrize("target", ["http://grpc.futureagi.com:443", "http://api.futureagi.com:443"])
@pytest.mark.parametrize("source", ["headers", "environment"])
def test_an_http_grpc_target_for_futureagi_is_refused_whether_insecure_is_unset_or_false(
    keys, monkeypatch, source, target, insecure
):
    headers = {"X-Api-Key": "fi-key-value", "X-Secret-Key": "fi-secret-value"} if source == "headers" else None
    with pytest.raises(ConfigurationError) as refused:
        build("OTLP_GRPC", target, insecure=insecure, headers=headers)
    assert refused.value.get_error_code() == "INSECURE_HTTP_REFUSED" or refused.value.code == "insecure_http_origin"


@pytest.mark.parametrize("target", ["http://collector.example.test:4317"])
def test_an_http_grpc_target_with_keys_has_one_outcome_for_unset_and_false(keys, monkeypatch, target):
    headers = {"X-Api-Key": "fi-key-value", "X-Secret-Key": "fi-secret-value"}
    outcomes = []
    for insecure in (None, False):
        try:
            build("OTLP_GRPC", target, insecure=insecure, headers=headers)
            outcomes.append("built")
        except ConfigurationError as error:
            outcomes.append(error.code)
    assert outcomes[0] == outcomes[1] == "insecure_http_origin"
