"""The experiments run exporter takes Future AGI hosts over https only.

The run's trace endpoint comes from ``FI_COLLECTOR_ENDPOINT`` or, when that is unset, from ``FI_BASE_URL``. An
``http://`` address on ``futureagi.com`` or a host below it builds no exporter, also when ``FI_BASE_URL`` is itself
such an address; building the exporter raises ``InsecureHttpRefusedError`` (code ``INSECURE_HTTP_REFUSED``, a
``ConfigurationError``) that names the settings, the same refusal the other senders give for that host. A listener standing in as the HTTP proxy of the process (``requests`` honours
``HTTP_PROXY``) records every request the exporter would send to the named host.
"""

import pytest

from fi.errors import ConfigurationError, InsecureHttpRefusedError
from fi.experiments._redact import Redactor
from fi.experiments._tracing.export import exporter_factory
from fi.experiments._tracing.export_status import ExportStatus
from tests.experiments.unit.test_fi_bound_authority_forms import clean_hosts  # noqa: F401
from tests.experiments.unit.test_fi_bound_exporter_headers import ambient, export_one, sink  # noqa: F401

CODE = "INSECURE_HTTP_REFUSED"
FUTURE_AGI_HTTP = [
    "http://api.futureagi.com",
    "http://api.futureagi.com:8000",
    "http://futureagi.com",
    "http://eu.api.futureagi.com",
    "http://API.FutureAGI.com.",
]


@pytest.fixture
def through_sink(sink, monkeypatch):  # noqa: F811
    """Every http:// request of this process goes to the sink, whatever host it names."""
    for name in ("HTTP_PROXY", "http_proxy"):
        monkeypatch.setenv(name, sink.base)
    for name in ("NO_PROXY", "no_proxy", "FI_COLLECTOR_ENDPOINT"):
        monkeypatch.delenv(name, raising=False)
    return sink


def provider(base, endpoint=None):
    outcome = ExportStatus("run-1", endpoint or base, Redactor([]))
    made = exporter_factory(base_url=base, api_key="k-test-1234", secret_key="s-test-1234", project="p",
                            run_name="r", run_id="run-1", redactor=Redactor([]), outcome=outcome)()
    return made, outcome


@pytest.mark.parametrize("base", FUTURE_AGI_HTTP)
def test_an_http_base_on_a_future_agi_host_sends_nothing_and_names_the_base_url(base, through_sink):
    with pytest.raises(InsecureHttpRefusedError) as refused:
        provider(base)
    assert isinstance(refused.value, ConfigurationError)
    assert refused.value.code == CODE
    assert "the base URL" in str(refused.value) and "FI_COLLECTOR_ENDPOINT" in str(refused.value)
    assert through_sink.requests == []


@pytest.mark.parametrize("base,endpoint", [
    ("http://api.futureagi.com", "http://api.futureagi.com/tracer/v1/traces"),
    ("http://collector.futureagi.com:8000", "http://collector.futureagi.com:4318/v1/traces"),
])
def test_an_http_collector_endpoint_on_a_future_agi_host_sends_nothing_and_names_it(base, endpoint, through_sink, monkeypatch):
    monkeypatch.setenv("FI_COLLECTOR_ENDPOINT", endpoint)
    with pytest.raises(InsecureHttpRefusedError) as refused:
        provider(base, endpoint=endpoint)
    assert refused.value.code == CODE
    assert "FI_COLLECTOR_ENDPOINT" in str(refused.value)
    assert through_sink.requests == []


def test_https_on_a_future_agi_host_is_not_refused(through_sink):
    made, outcome = provider("https://api.futureagi.com")
    assert outcome.error is None
    made.shutdown()


@pytest.mark.parametrize("name", ["loopback", "self-hosted"])
def test_loopback_and_a_self_hosted_http_base_export(name, sink, monkeypatch):  # noqa: F811
    for var in ("HTTP_PROXY", "http_proxy", "NO_PROXY", "no_proxy", "FI_COLLECTOR_ENDPOINT"):
        monkeypatch.delenv(var, raising=False)
    made, outcome = provider(sink.base)
    export_one(made)
    assert len(sink.requests) == 1
    assert outcome.error is None


def test_an_http_self_hosted_name_is_not_a_future_agi_host(through_sink, monkeypatch):
    """A prefix match takes the self-managed rule (code ``insecure_http_origin``),
    not the refusal for a host in the Future AGI zone."""
    monkeypatch.delenv("FI_ALLOW_INSECURE_HTTP", raising=False)
    with pytest.raises(ConfigurationError) as refused:
        provider("http://api.futureagi.com.example.test:8000")
    assert not isinstance(refused.value, InsecureHttpRefusedError)
    assert refused.value.code == "insecure_http_origin"
    assert "FI_ALLOW_INSECURE_HTTP" in str(refused.value)
    assert through_sink.requests == []


@pytest.mark.parametrize("variable", ["FI_TRACES_URL", "FI_GRPC_URL"])
def test_a_future_agi_host_named_by_the_traces_or_grpc_setting_is_refused_over_http(variable, monkeypatch):
    from fi.evals.otel._tracer_factories import _create_exporter
    from fi.evals.otel.config import ExporterConfig, ExporterType

    monkeypatch.setenv(variable, "http://edge.futureagi.com:4318")
    with pytest.raises(ConfigurationError) as refused:
        _create_exporter(ExporterConfig(type=ExporterType.OTLP_HTTP,
                                        endpoint="http://edge.futureagi.com:4318/v1/traces"))
    assert refused.value.code == CODE
