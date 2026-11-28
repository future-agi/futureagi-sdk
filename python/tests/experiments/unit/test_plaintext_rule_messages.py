"""Refusal messages carry their error code in the text, and the plain-transport opt-in warns once.

A self-managed target that would receive the SDK's keys over a plain transport (``http://``, or gRPC without TLS) is
refused with ``ConfigurationError`` (code ``insecure_http_origin``) unless ``FI_ALLOW_INSECURE_HTTP`` is exactly
``1``; the proxy settings of the environment do not decide it, and the opt-in logs one value-free warning per process.
Every refusal message names its code.
"""

import inspect
import logging

import pytest
import requests

from fi import _otlp_headers
from fi.errors import ConfigurationError
from tests.experiments.unit.test_fi_bound_authority_forms import clean_hosts  # noqa: F401

CODE = "insecure_http_origin"
SELF_HOSTED = "http://selfhosted.example.test:4318/tracer/v1/traces"
CONSTANT_MESSAGES = {
    "AMBIGUOUS_ENDPOINT_MESSAGE": "insecure_http_origin",
    "INSECURE_GRPC_MESSAGE": "INSECURE_HTTP_REFUSED",
    "INSECURE_LOOPBACK_GRPC_MESSAGE": "insecure_loopback_grpc",
    "ENDPOINT_TLS_FILE_MESSAGE": "unreadable_tls_file",
    "INSECURE_HTTP_MESSAGE": "INSECURE_HTTP_REFUSED",
    "_ADAPTER_REFUSAL": "unsupported_session_adapter",
    "ENV_KEY_HEADERS_MESSAGE": "otel_env_key_headers",
}


@pytest.fixture
def quiet(monkeypatch):
    for name in ("FI_ALLOW_INSECURE_HTTP", "HTTP_PROXY", "http_proxy", "HTTPS_PROXY", "https_proxy", "NO_PROXY",
                 "no_proxy", "FI_BASE_URL", "FI_GRPC_URL", "FI_TRACES_URL"):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setattr(_otlp_headers, "_PLAIN_OPT_IN_WARNED", False, raising=False)


@pytest.mark.parametrize("name,code", CONSTANT_MESSAGES.items())
def test_a_refusal_message_names_its_code(name, code):
    assert code in getattr(_otlp_headers, name)


@pytest.mark.parametrize("name,code", CONSTANT_MESSAGES.items())
def test_a_refusal_message_ends_with_its_code_and_no_period(name, code):
    assert getattr(_otlp_headers, name).endswith(f"({code})")


@pytest.mark.parametrize("name,code", [("INSECURE_TARGET_MESSAGE", CODE)])
def test_the_self_hosted_refusals_end_with_their_code_and_no_period(name, code):
    assert getattr(_otlp_headers, name).format(setting="FI_BASE_URL").endswith(f"({code})")


def test_the_unsupported_exporter_message_ends_with_its_code_and_no_period():
    class Foreign:
        pass

    with pytest.raises(ConfigurationError) as refused:
        _otlp_headers.pin_headers(Foreign(), {})
    assert str(refused.value).endswith("(unsupported_otlp_exporter)")


def test_the_unsupported_exporter_message_names_its_code():
    class Foreign:
        pass

    with pytest.raises(ConfigurationError) as refused:
        _otlp_headers.pin_headers(Foreign(), {})
    assert refused.value.code == "unsupported_otlp_exporter"
    assert "unsupported_otlp_exporter" in str(refused.value)


def test_a_redirect_answer_names_its_code():
    session = _otlp_headers.futureagi_session()

    class Answer:
        status_code = 307
        headers = {"Location": "https://example.test/next"}
        history = ()

        def close(self):
            pass

    original = requests.Session.send
    try:
        requests.Session.send = lambda self, request, **kwargs: Answer()
        with pytest.raises(requests.RequestException) as refused:
            session.send(requests.Request("POST", "https://example.test/").prepare())
    finally:
        requests.Session.send = original
    assert str(refused.value).endswith("(redirect_not_followed)")


def test_a_self_hosted_http_target_is_refused_with_a_message_that_names_the_setting_and_the_code(quiet):
    with pytest.raises(ConfigurationError) as refused:
        _otlp_headers.refuse_plain_http_futureagi(SELF_HOSTED, "FI_BASE_URL", keys=True)
    assert refused.value.code == CODE
    text = str(refused.value)
    assert CODE in text and "FI_ALLOW_INSECURE_HTTP" in text and "FI_BASE_URL" in text
    assert "selfhosted" not in text


def test_the_refusal_does_not_apply_when_no_keys_are_attached(quiet):
    _otlp_headers.refuse_plain_http_futureagi(SELF_HOSTED, "The exporter endpoint", keys=False)


@pytest.mark.parametrize("value", ["", "true", "yes", "TRUE", "1 ", "01", "on"])
def test_only_exactly_one_opts_in(quiet, monkeypatch, value):
    monkeypatch.setenv("FI_ALLOW_INSECURE_HTTP", value)
    with pytest.raises(ConfigurationError) as refused:
        _otlp_headers.refuse_plain_http_futureagi(SELF_HOSTED, "FI_BASE_URL", keys=True)
    assert refused.value.code == CODE


def test_the_opt_in_logs_one_value_free_warning_per_process(quiet, monkeypatch, caplog):
    monkeypatch.setenv("FI_ALLOW_INSECURE_HTTP", "1")
    with caplog.at_level(logging.WARNING, logger="fi._otlp_headers"):
        for _ in range(3):
            _otlp_headers.refuse_plain_http_futureagi(SELF_HOSTED, "FI_BASE_URL", keys=True)
            _otlp_headers.refuse_plain_http_futureagi(
                "http://other-host.example.test:4318/v1/traces", "FI_BASE_URL", keys=True)
    warned = [record for record in caplog.records if "FI_ALLOW_INSECURE_HTTP" in record.getMessage()]
    assert len(warned) == 1
    assert "selfhosted" not in warned[0].getMessage() and "other-host" not in warned[0].getMessage()


def test_the_opt_in_does_not_apply_to_a_future_agi_host(quiet, monkeypatch):
    monkeypatch.setenv("FI_ALLOW_INSECURE_HTTP", "1")
    with pytest.raises(ConfigurationError) as refused:
        _otlp_headers.refuse_plain_http_futureagi("http://api.futureagi.com/tracer/v1/traces", "FI_BASE_URL", keys=True)
    assert refused.value.code == "INSECURE_HTTP_REFUSED"


@pytest.mark.parametrize("settings", [{"HTTP_PROXY": "http://127.0.0.1:3128"}, {"ALL_PROXY": "http://127.0.0.1:3128"},
                                      {"http_proxy": "http://127.0.0.1:3128", "NO_PROXY": "192.0.2.0/24"}])
def test_an_environment_proxy_does_not_change_the_opt_in(quiet, monkeypatch, settings):
    # The transport the SDK builds for a plain send ignores the environment's proxy, so the opt-in alone decides.
    for name, value in settings.items():
        monkeypatch.setenv(name, value)
    with pytest.raises(ConfigurationError) as refused:
        _otlp_headers.refuse_plain_http_futureagi(SELF_HOSTED, "FI_BASE_URL", keys=True)
    assert refused.value.code == CODE
    monkeypatch.setenv("FI_ALLOW_INSECURE_HTTP", "1")
    _otlp_headers.refuse_plain_http_futureagi(SELF_HOSTED, "FI_BASE_URL", keys=True)


def test_the_plain_http_check_takes_no_session():
    """No session a caller holds reaches the check: the SDK builds its own sessions, and they hold no proxies."""
    assert "session" not in inspect.signature(_otlp_headers.refuse_plain_http_futureagi).parameters


@pytest.mark.parametrize("endpoint", [
    "http://127.0.0.1:4318/v1/traces", "http://localhost:4318/v1/traces", "http://LOCALHOST:4318/v1/traces",
    "http://[::1]:4318/v1/traces", "http://127.9.9.9:4318/v1/traces", "https://selfhosted.example.test/v1/traces",
])
def test_loopback_and_https_targets_are_unchanged(quiet, endpoint):
    _otlp_headers.refuse_plain_http_futureagi(endpoint, "FI_BASE_URL", keys=True)


@pytest.mark.parametrize("endpoint", [
    "http://localhost.example.test:4318/v1/traces", "http://127.0.0.1.example.test:4318/v1/traces",
    "http://api.futureagi.com.example.test/v1/traces", "http://192.0.2.5:4318/v1/traces",
    # Loopback is the host as it is written: these spellings are not loopback.
    "http://LOCALHOST.:4318/v1/traces", "http://127.0.0.1.:4318/v1/traces", "http://127.1:4318/v1/traces",
    "http://0x7f.0.0.1:4318/v1/traces", "http://0177.0.0.1:4318/v1/traces", "http://2130706433:4318/v1/traces",
    "http://app.localhost:4318/v1/traces",
])
def test_a_look_alike_of_loopback_or_of_a_future_agi_host_is_self_hosted(quiet, endpoint):
    with pytest.raises(ConfigurationError) as refused:
        _otlp_headers.refuse_plain_http_futureagi(endpoint, "FI_BASE_URL", keys=True)
    assert refused.value.code == CODE


def test_the_experiments_failure_reason_names_the_code(quiet, monkeypatch):
    """A self-managed HTTP base without the opt-in builds no exporter: the refusal carries the shared code
    ``insecure_http_origin`` and names the settings, and the status records no export failure."""
    from fi.experiments._redact import Redactor
    from fi.experiments._tracing.export import exporter_factory
    from fi.experiments._tracing.export_status import ExportStatus

    base = "http://selfhosted.example.test:4318"
    outcome = ExportStatus("run-1", base, Redactor([]))
    with pytest.raises(ConfigurationError) as refused:
        exporter_factory(base_url=base, api_key="k", secret_key="s", project="p", run_name="r", run_id="run-1",
                         redactor=Redactor([]), outcome=outcome)
    assert refused.value.code == "insecure_http_origin"
    assert "FI_COLLECTOR_ENDPOINT" in str(refused.value) and "FI_ALLOW_INSECURE_HTTP" in str(refused.value)
    assert outcome.error is None


def test_an_authority_that_is_not_loopback_is_refused_with_the_code(quiet):
    with pytest.raises(ConfigurationError) as refused:
        _otlp_headers.refuse_plain_http_futureagi("http://localhost..:4318", "FI_BASE_URL", keys=True)
    assert refused.value.code == CODE


def test_an_authority_with_user_information_is_refused_as_ambiguous(quiet):
    with pytest.raises(ConfigurationError) as refused:
        _otlp_headers.refuse_plain_http_futureagi("http://[::1]@collector.example", "FI_BASE_URL", keys=True)
    assert refused.value.code == "insecure_http_origin"


@pytest.mark.parametrize("endpoint", [
    " http://selfhosted.example.test:4318/v1/traces", "http://selfhosted.example.test:4318/v1/traces ",
    "\thttp://127.0.0.1:4318/v1/traces", "\nhttp://api.futureagi.com/v1/traces",
])
def test_an_http_endpoint_with_white_space_around_it_is_refused_as_ambiguous(quiet, endpoint):
    with pytest.raises(ConfigurationError) as refused:
        _otlp_headers.refuse_plain_http_futureagi(endpoint, "FI_BASE_URL", keys=True)
    assert refused.value.code == "insecure_http_origin"
