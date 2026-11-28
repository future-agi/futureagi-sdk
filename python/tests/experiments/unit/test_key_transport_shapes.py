"""Where the SDK's keys go is decided from one reading of the endpoint, and from the headers that go out.

* An endpoint whose written host and dialed host can differ is refused with ``insecure_http_origin``: a backslash
  (also written ``%5C``), user information, an ``@`` in the path, an empty authority, or two parsers reading
  different hosts. Neither ``localhost`` nor a Future AGI host is decided from one parser alone.
* A gRPC exporter takes the plain-transport rule when the headers that go out hold the SDK's keys, whether they
  come from the exporter's headers, from ``OTEL_EXPORTER_OTLP_HEADERS``, or from both together.
"""

import pytest

from fi import _otlp_headers
from fi.errors import ConfigurationError
from fi.evals.otel._tracer_factories import _create_exporter
from fi.evals.otel.config import ExporterConfig, ExporterType
from tests.experiments.unit.test_fi_bound_authority_forms import clean_hosts  # noqa: F401

COLLECTOR = "collector.example.test"
FORMS = [
    "grpc://localhost\\@{c}:4317",
    "grpc://grpc.futureagi.com\\@{c}:4317",
    "grpc://localhost%5C@{c}:4317",
    "grpc://grpc.futureagi.com%5C@{c}:4317",
    "grpc://localhost/@{c}:4317",
    "grpc://grpc.futureagi.com/@{c}:4317",
    "grpc://user@{c}:4317",
    "grpc://user:secret@localhost:4317",
    "http://localhost\\@{c}:4318/v1/traces",
    "https://api.futureagi.com\\@{c}/v1/traces",
    "http://localhost%5C@{c}:4318/v1/traces",
    "http://localhost:4318/@{c}",
    "http://user@localhost:4318/v1/traces",
    "https://user:secret@{c}/v1/traces",
    "http://[::1]@{c}",
    "http://[::1]@{c}:4318/v1/traces",
    "https:///api.futureagi.com/",
    "http:///api.futureagi.com",
    "http:///{c}:4318/v1/traces",
    "https:///grpc.futureagi.com:4317",
]


@pytest.fixture
def quiet(monkeypatch, clean_hosts):  # noqa: F811
    for name in ("FI_ALLOW_INSECURE_HTTP", "HTTP_PROXY", "http_proxy", "HTTPS_PROXY", "https_proxy", "ALL_PROXY",
                 "all_proxy", "grpc_proxy", "no_proxy", "NO_PROXY", "OTEL_EXPORTER_OTLP_HEADERS",
                 "OTEL_EXPORTER_OTLP_TRACES_HEADERS", "OTEL_EXPORTER_OTLP_INSECURE", "FI_API_KEY", "FI_SECRET_KEY"):
        monkeypatch.delenv(name, raising=False)
    return monkeypatch


@pytest.mark.parametrize("form", FORMS)
def test_an_endpoint_that_can_be_read_as_two_hosts_is_ambiguous(quiet, form):
    assert _otlp_headers.is_ambiguous_endpoint(form.format(c=COLLECTOR))


@pytest.mark.parametrize("kind", [ExporterType.OTLP_GRPC, ExporterType.OTLP_HTTP, ExporterType.FUTUREAGI])
@pytest.mark.parametrize("form", FORMS)
def test_every_exporter_type_refuses_such_an_endpoint(quiet, form, kind):
    config = ExporterConfig(type=kind, endpoint=form.format(c=COLLECTOR), insecure=True)
    with pytest.raises(ConfigurationError) as refused:
        _create_exporter(config)
    assert refused.value.code == "insecure_http_origin"


@pytest.mark.parametrize("kind", [ExporterType.FUTUREAGI, ExporterType.OTLP_HTTP, ExporterType.ARIZE])
def test_an_at_sign_in_the_path_is_ambiguous_over_http_and_not_over_tls(quiet, kind):
    over_tls = ExporterConfig(type=kind, endpoint=f"https://{COLLECTOR}:4318/@localhost", headers=KEYS_HEADERS)
    assert _create_exporter(over_tls) is not None
    plain = ExporterConfig(type=kind, endpoint=f"http://{COLLECTOR}:4318/@localhost", headers=KEYS_HEADERS)
    with pytest.raises(ConfigurationError) as refused:
        _create_exporter(plain)
    assert refused.value.code == "insecure_http_origin"


KEYS_HEADERS = {"x-api-key": "key-value", "x-secret-key": "secret-value"}


@pytest.mark.parametrize("form", ["http://[::1]@{c}", "http://localhost\\@{c}", "http://localhost:4318/@{c}",
                                  "http://user@localhost:4318", "http:///{c}"])
def test_loopback_is_not_decided_from_one_parser(quiet, form):
    with pytest.raises(ConfigurationError) as refused:
        _otlp_headers.refuse_plain_http_futureagi(form.format(c=COLLECTOR), "FI_BASE_URL", keys=True)
    assert refused.value.code == "insecure_http_origin"


@pytest.mark.parametrize("endpoint", [f"{COLLECTOR}:4317", "dns:///localhost:4317", "localhost:4317",
                                      "https://collector.example.test:4317", "ipv4:127.0.0.1:4317"])
def test_a_plain_host_is_not_ambiguous(quiet, endpoint):
    assert not _otlp_headers.is_ambiguous_endpoint(endpoint)


KEYS = {"x-api-key": "key-value", "x-secret-key": "secret-value"}
ENV_KEYS = "x-api-key=key-value,x-secret-key=secret-value"


def grpc_config(headers, endpoint=f"{COLLECTOR}:4317"):
    return ExporterConfig(type=ExporterType.OTLP_GRPC, endpoint=endpoint, insecure=True, headers=headers)


@pytest.mark.parametrize("name,value", [("OTEL_EXPORTER_OTLP_HEADERS", ENV_KEYS),
                                         ("OTEL_EXPORTER_OTLP_TRACES_HEADERS", ENV_KEYS),
                                         ("OTEL_EXPORTER_OTLP_HEADERS", "X-Api-Key=key-value")])
def test_keys_in_the_environment_are_refused_for_a_target_that_is_not_bound_for_future_agi(quiet, name, value):
    quiet.setenv(name, value)
    with pytest.raises(ConfigurationError) as refused:
        _create_exporter(grpc_config(None))
    assert refused.value.code == "otel_env_key_headers"


def test_keys_from_the_headers_take_the_rule(quiet):
    with pytest.raises(ConfigurationError) as refused:
        _create_exporter(grpc_config(KEYS))
    assert refused.value.code == "insecure_http_origin"


def test_keys_split_between_the_headers_and_the_environment_are_refused(quiet):
    quiet.setenv("OTEL_EXPORTER_OTLP_HEADERS", "x-secret-key=secret-value")
    with pytest.raises(ConfigurationError) as refused:
        _create_exporter(grpc_config({"x-api-key": "key-value"}))
    assert refused.value.code == "otel_env_key_headers"


@pytest.mark.parametrize("headers,env", [(None, None), ({"x-request-id": "1"}, "x-team=blue")])
def test_a_channel_without_the_keys_takes_no_rule(quiet, headers, env):
    if env:
        quiet.setenv("OTEL_EXPORTER_OTLP_HEADERS", env)
    assert _create_exporter(grpc_config(headers)) is not None


def test_the_opt_in_allows_the_keys_over_a_plain_channel(quiet):
    quiet.setenv("FI_ALLOW_INSECURE_HTTP", "1")
    assert _create_exporter(grpc_config(KEYS)) is not None


def test_a_proxy_in_the_environment_does_not_change_the_rule_for_the_keys(quiet):
    quiet.setenv("grpc_proxy", "http://127.0.0.1:3128")
    with pytest.raises(ConfigurationError) as refused:
        _create_exporter(grpc_config(KEYS))
    assert refused.value.code == "insecure_http_origin"
    quiet.setenv("FI_ALLOW_INSECURE_HTTP", "1")
    assert _create_exporter(grpc_config(KEYS)) is not None


def channel_options(quiet, config):
    """The options the exporter hands to gRPC when it opens its channel."""
    from opentelemetry.exporter.otlp.proto.grpc import exporter as grpc_exporter

    seen = {}
    real = grpc_exporter.insecure_channel

    def spy(*args, **kwargs):
        seen["options"] = dict(kwargs.get("options") or ())
        return real(*args, **kwargs)

    quiet.setattr(grpc_exporter, "insecure_channel", spy)
    assert _create_exporter(config) is not None
    return seen["options"]


def test_a_plain_channel_with_the_keys_ignores_the_proxy_settings_of_the_environment(quiet):
    quiet.setenv("FI_ALLOW_INSECURE_HTTP", "1")
    assert channel_options(quiet, grpc_config(KEYS)).get("grpc.enable_http_proxy") == 0
    assert channel_options(quiet, grpc_config(KEYS, "127.0.0.1:4317")).get("grpc.enable_http_proxy") == 0


def test_a_plain_channel_without_the_keys_keeps_the_proxy_settings_of_the_environment(quiet):
    assert "grpc.enable_http_proxy" not in channel_options(quiet, grpc_config(None))


def test_loopback_with_the_keys_is_unchanged(quiet):
    assert _create_exporter(grpc_config(KEYS, "127.0.0.1:4317")) is not None


def test_a_loopback_channel_bound_for_future_agi_names_loopback_in_its_refusal(quiet):
    quiet.setenv("FI_GRPC_URL", "127.0.0.1:4317")
    with pytest.raises(ConfigurationError) as refused:
        _create_exporter(grpc_config(None, "127.0.0.1:4317"))
    assert refused.value.code == "insecure_loopback_grpc"
    text = str(refused.value)
    assert "loopback" in text and "Future AGI" not in text
    assert text.endswith("(insecure_loopback_grpc)")


def test_a_future_agi_channel_keeps_its_own_refusal(quiet):
    with pytest.raises(ConfigurationError) as refused:
        _create_exporter(grpc_config(None, "grpc.futureagi.com:4317"))
    assert refused.value.code == "INSECURE_HTTP_REFUSED"
