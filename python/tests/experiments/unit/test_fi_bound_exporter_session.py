# ruff: noqa: F811
"""An exporter bound for Future AGI sends over a session of the SDK's own.

OpenTelemetry's HTTP exporters build their session from a credential provider named in
OTEL_PYTHON_EXPORTER_OTLP_HTTP_TRACES_CREDENTIAL_PROVIDER (or the shared variable) when none is passed,
and ``requests`` adds Basic auth from the user's netrc file. Both are meant for the user's own backend.
A Future AGI endpoint gets a fresh session with neither, and keeps the proxy and CA settings the user
configured. An endpoint the user chose keeps the standard behaviour.
"""

from types import SimpleNamespace

import pytest
import requests

from tests.experiments.unit.test_fi_bound_exporter_headers import (  # noqa: F401
    AMBIENT,
    AMBIENT_VARS,
    SDK_HEADERS,
    ambient,
    evals_exporter,
    export_one,
    export_spans,
    run_provider,
    sink,
)

PROVIDER_NAME = "fi-test-provider"
PROVIDER_VARS = (
    "OTEL_PYTHON_EXPORTER_OTLP_HTTP_TRACES_CREDENTIAL_PROVIDER",
    "OTEL_PYTHON_EXPORTER_OTLP_HTTP_CREDENTIAL_PROVIDER",
)
PROVIDER_HEADERS = {
    "x-provider-token": "provider-secret",
    "authorization": "Bearer provider-secret",
}


@pytest.fixture
def provider(monkeypatch):
    """A credential provider that adds its own headers to every request, found the way
    OpenTelemetry finds one: by the name in the environment variable, among the
    ``opentelemetry_otlp_credential_provider`` entry points."""

    def build():
        session = requests.Session()
        session.headers.update(
            {
                "x-provider-token": "provider-secret",
                "Authorization": "Bearer provider-secret",
            }
        )
        return session

    def entry_points(group, name):
        found = (
            group == "opentelemetry_otlp_credential_provider" and name == PROVIDER_NAME
        )
        return iter([SimpleNamespace(load=lambda: build)] if found else [])

    monkeypatch.setattr(
        "opentelemetry.exporter.otlp.proto.http._common.entry_points", entry_points
    )
    monkeypatch.setenv(PROVIDER_VARS[0], PROVIDER_NAME)
    monkeypatch.delenv(PROVIDER_VARS[1], raising=False)
    monkeypatch.delenv("FI_API_KEY", raising=False)
    monkeypatch.delenv("FI_SECRET_KEY", raising=False)


def custom(sink_, index=0):
    return sink_.custom(sink_.requests[index])


# ---- a credential provider's session ------------------------------------------------------------


def test_evals_futureagi_exporter_ignores_a_credential_provider_session(sink, provider):
    export_spans(evals_exporter(sink.base + "/tracer/v1/traces", SDK_HEADERS))
    assert custom(sink) == SDK_HEADERS


def test_run_exporter_ignores_a_credential_provider_session(sink, provider):
    export_one(run_provider(sink.base))
    assert custom(sink) == SDK_HEADERS


def test_a_user_chosen_endpoint_uses_the_credential_provider(sink, provider, monkeypatch):
    monkeypatch.setenv("FI_BASE_URL", "https://api.example.test")
    export_spans(evals_exporter(sink.base + "/v1/traces", kind="OTLP_HTTP"))
    assert custom(sink) == {k: v for k, v in PROVIDER_HEADERS.items()}


def test_a_user_chosen_endpoint_with_the_sdk_keys_gets_no_provider_headers(sink, provider, monkeypatch):
    # The SDK's keys travel on the SDK's own direct session only; the provider's headers stay off that send.
    monkeypatch.setenv("FI_BASE_URL", "https://api.example.test")
    export_spans(evals_exporter(sink.base + "/v1/traces", SDK_HEADERS, kind="OTLP_HTTP"))
    assert custom(sink) == SDK_HEADERS


def test_each_futureagi_exporter_gets_its_own_session(sink, provider):
    first = evals_exporter(sink.base + "/tracer/v1/traces", SDK_HEADERS)
    second = evals_exporter(sink.base + "/tracer/v1/traces", SDK_HEADERS)
    assert session_of(first) is not session_of(second)


def session_of(exporter):
    session = getattr(exporter, "_session", None)  # 1.39
    return (
        session if session is not None else exporter._client._transport._session
    )  # 1.45


# ---- an OTLP HTTP exporter at the Future AGI host ---------------------------------------------


def sent_headers(exporter):
    client = getattr(exporter, "_client", None)
    if isinstance(getattr(client, "_headers", None), dict):
        return {k.lower(): v for k, v in client._headers.items()}
    return {k.lower(): v for k, v in exporter._session.headers.items()}


def test_otlp_http_at_the_configured_base_url_host_is_pinned_like_futureagi(
    sink, ambient, monkeypatch
):
    monkeypatch.setenv("FI_BASE_URL", sink.base)
    export_spans(
        evals_exporter(sink.base + "/tracer/v1/traces", SDK_HEADERS, kind="OTLP_HTTP")
    )
    assert custom(sink) == SDK_HEADERS


def test_otlp_http_at_the_default_futureagi_host_is_pinned(ambient, monkeypatch):
    monkeypatch.delenv("FI_BASE_URL", raising=False)
    exporter = evals_exporter(
        "https://api.futureagi.com/tracer/v1/traces", SDK_HEADERS, kind="OTLP_HTTP"
    )
    seen = sent_headers(exporter)
    assert "authorization" not in seen and "x-ambient" not in seen
    assert seen["x-api-key"] == SDK_HEADERS["x-api-key"]


def test_otlp_http_at_the_futureagi_host_ignores_a_credential_provider_session(
    sink, provider, monkeypatch
):
    monkeypatch.setenv("FI_BASE_URL", sink.base)
    export_spans(
        evals_exporter(sink.base + "/tracer/v1/traces", SDK_HEADERS, kind="OTLP_HTTP")
    )
    assert custom(sink) == SDK_HEADERS


def test_otlp_http_at_another_host_keeps_the_ambient_headers(
    sink, ambient, monkeypatch
):
    monkeypatch.setenv("FI_BASE_URL", "https://api.example.test")
    export_spans(evals_exporter(sink.base + "/v1/traces", kind="OTLP_HTTP"))
    assert custom(sink) == {"authorization": "Bearer fake-ambient", "x-ambient": "1"}


# ---- netrc and proxies --------------------------------------------------------------------------


@pytest.fixture
def netrc(tmp_path, monkeypatch):
    path = tmp_path / "netrc"
    path.write_text("machine 127.0.0.1 login netrc-user password netrc-pass\n")
    path.chmod(0o600)
    monkeypatch.setenv("NETRC", str(path))
    for name in AMBIENT_VARS:
        monkeypatch.delenv(name, raising=False)


def test_evals_futureagi_exporter_does_not_send_netrc_credentials(sink, netrc):
    export_spans(evals_exporter(sink.base + "/tracer/v1/traces", SDK_HEADERS))
    assert "authorization" not in sink.requests[0]


def test_run_exporter_does_not_send_netrc_credentials(sink, netrc):
    export_one(run_provider(sink.base))
    assert "authorization" not in sink.requests[0]


def test_a_user_chosen_endpoint_gets_netrc_credentials(sink, netrc, monkeypatch):
    monkeypatch.setenv("FI_BASE_URL", "https://api.example.test")
    export_spans(evals_exporter(sink.base + "/v1/traces", kind="OTLP_HTTP"))
    assert sink.requests[0].get("authorization", "").startswith("Basic ")


def test_the_futureagi_session_keeps_the_users_proxy_and_certificate_settings(
    sink, provider
):
    session = session_of(evals_exporter(sink.base + "/tracer/v1/traces", SDK_HEADERS))
    assert session.trust_env is True
