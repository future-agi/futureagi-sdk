"""FI_EXTRA_HEADERS in fi.experiments: the redactor knows each header value, the trace exporter sends them."""

from __future__ import annotations

import pytest

from fi._extra_headers import ENV_VAR, ExtraHeaders

# a made-up value, low entropy on purpose (never a real token)
TOKEN = "fake-identity-token-" + "x" * 12
VALUE = f"Bearer {TOKEN}"


@pytest.fixture(autouse=True)
def _no_setting(monkeypatch):
    monkeypatch.delenv(ENV_VAR, raising=False)


def test_experiments_redactor_scrubs_each_header_value_and_token(monkeypatch):
    pytest.importorskip("fi.experiments._redact")
    from fi.experiments._redact import REDACTED, Redactor, client_secret_values

    monkeypatch.setenv(ENV_VAR, f"Proxy-Authorization={VALUE}")
    r = Redactor()
    assert r.text(f"token {TOKEN} and {VALUE}") == f"token {REDACTED} and {REDACTED}"

    class _Client:
        _extra_headers = ExtraHeaders("https://team.example", {"X-Team-Secret": "argument-secret-1"})

    assert "argument-secret-1" in client_secret_values(_Client())
    assert TOKEN in client_secret_values(_Client()) and TOKEN in client_secret_values(object())


def test_otlp_exporter_gets_the_run_clients_headers(monkeypatch):
    pytest.importorskip("fi_instrumentation.otel")
    from fi.experiments._tracing import export

    captured = {}

    class _Exporter:
        def __init__(self, *, endpoint, headers, session=None):
            captured.update(endpoint=endpoint, headers=headers)

        def export(self, spans):  # pragma: no cover - nothing is exported here
            return None

        def shutdown(self):
            return None

    monkeypatch.setattr("fi_instrumentation.otel.HTTPSpanExporter", _Exporter)
    from fi.experiments._redact import Redactor

    make = export.exporter_factory(base_url="http://platform.test", api_key="ak", secret_key="sk", project="p",
                                   run_name="r", run_id="id", redactor=Redactor([]),
                                   extra_headers={"Proxy-Authorization": VALUE})
    make().shutdown()
    assert captured["endpoint"] == "http://platform.test/tracer/v1/traces"
    assert captured["headers"] == {"Proxy-Authorization": VALUE, "X-Api-Key": "ak", "X-Secret-Key": "sk"}
