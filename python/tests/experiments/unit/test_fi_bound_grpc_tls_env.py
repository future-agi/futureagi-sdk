"""A Future AGI gRPC exporter reads its TLS files from the environment as the OpenTelemetry exporter does.

Upstream loads the client key and client certificate only when ``OTEL_EXPORTER_OTLP_TRACES_CERTIFICATE`` names
a file, and reads the traces variables only: nothing falls back to the generic ``OTEL_EXPORTER_OTLP_*`` ones.
"""

import grpc
import pytest

from fi._otlp_headers import futureagi_grpc_credentials

NAMES = [
    "OTEL_EXPORTER_OTLP_CERTIFICATE",
    "OTEL_EXPORTER_OTLP_CLIENT_KEY",
    "OTEL_EXPORTER_OTLP_CLIENT_CERTIFICATE",
    "OTEL_EXPORTER_OTLP_TRACES_CERTIFICATE",
    "OTEL_EXPORTER_OTLP_TRACES_CLIENT_KEY",
    "OTEL_EXPORTER_OTLP_TRACES_CLIENT_CERTIFICATE",
]


@pytest.fixture
def tls(monkeypatch, tmp_path):
    for name in NAMES:
        monkeypatch.delenv(name, raising=False)
    seen = {}

    def capture(**kwargs):
        seen.update(kwargs)
        return object()

    monkeypatch.setattr(grpc, "ssl_channel_credentials", capture)

    def file(label):
        path = tmp_path / label
        path.write_bytes(label.encode())
        return str(path)

    return seen, file, monkeypatch


def test_without_a_certificate_variable_nothing_is_read(tls):
    seen, _, _ = tls
    futureagi_grpc_credentials()
    assert seen == {
        "root_certificates": None,
        "private_key": None,
        "certificate_chain": None,
    }


def test_a_client_key_and_certificate_alone_are_not_read(tls):
    seen, file, env = tls
    env.setenv("OTEL_EXPORTER_OTLP_TRACES_CLIENT_KEY", file("key"))
    env.setenv("OTEL_EXPORTER_OTLP_TRACES_CLIENT_CERTIFICATE", file("chain"))
    futureagi_grpc_credentials()
    assert seen == {
        "root_certificates": None,
        "private_key": None,
        "certificate_chain": None,
    }


def test_the_generic_variables_are_not_read(tls):
    seen, file, env = tls
    env.setenv("OTEL_EXPORTER_OTLP_CERTIFICATE", file("ca"))
    env.setenv("OTEL_EXPORTER_OTLP_CLIENT_KEY", file("key"))
    env.setenv("OTEL_EXPORTER_OTLP_CLIENT_CERTIFICATE", file("chain"))
    futureagi_grpc_credentials()
    assert seen == {
        "root_certificates": None,
        "private_key": None,
        "certificate_chain": None,
    }


def test_the_generic_client_files_do_not_fill_in_for_missing_traces_ones(tls):
    seen, file, env = tls
    env.setenv("OTEL_EXPORTER_OTLP_TRACES_CERTIFICATE", file("ca"))
    env.setenv("OTEL_EXPORTER_OTLP_CLIENT_KEY", file("key"))
    env.setenv("OTEL_EXPORTER_OTLP_CLIENT_CERTIFICATE", file("chain"))
    futureagi_grpc_credentials()
    assert seen == {
        "root_certificates": b"ca",
        "private_key": None,
        "certificate_chain": None,
    }


def test_the_traces_files_are_read_when_the_certificate_is_named(tls):
    seen, file, env = tls
    env.setenv("OTEL_EXPORTER_OTLP_TRACES_CERTIFICATE", file("ca"))
    env.setenv("OTEL_EXPORTER_OTLP_TRACES_CLIENT_KEY", file("key"))
    env.setenv("OTEL_EXPORTER_OTLP_TRACES_CLIENT_CERTIFICATE", file("chain"))
    futureagi_grpc_credentials()
    assert seen == {
        "root_certificates": b"ca",
        "private_key": b"key",
        "certificate_chain": b"chain",
    }


def test_an_empty_certificate_variable_reads_nothing(tls):
    seen, file, env = tls
    env.setenv("OTEL_EXPORTER_OTLP_TRACES_CERTIFICATE", "")
    env.setenv("OTEL_EXPORTER_OTLP_TRACES_CLIENT_KEY", file("key"))
    futureagi_grpc_credentials()
    assert seen == {
        "root_certificates": None,
        "private_key": None,
        "certificate_chain": None,
    }
