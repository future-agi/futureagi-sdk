"""Keep legacy HTTP behavior and scope explicit plaintext collectors without DNS."""
import socket

import pytest

from fi.experiments._redact import Redactor
from fi.experiments._tracing.export import collector_endpoint, exporter_factory
from fi.experiments.errors import ExperimentError


@pytest.fixture(autouse=True)
def isolated_environment_without_dns(monkeypatch):
    monkeypatch.delenv("FI_COLLECTOR_ENDPOINT", raising=False)

    def no_dns(*args, **kwargs):
        raise AssertionError("Endpoint selection must not perform DNS lookup")

    monkeypatch.setattr(socket, "getaddrinfo", no_dns)


def selected_or_refused(base):
    try:
        return collector_endpoint(base)
    except ExperimentError:
        return None


@pytest.mark.parametrize("base", ["http://10.0.0.5:8000", "http://api.example.test:8000"],
                         ids=["lan-ip", "lan-hostname"])
def test_legacy_http_api_keeps_its_derived_endpoint(base):
    assert selected_or_refused(base) == base + "/tracer/v1/traces"


_SCOPE_CASES = [
    ("http://10.0.0.5:8000", "http://10.0.0.5:4318/v1/traces", True, "same-ip-other-port"),
    ("http://collector.example:8000", "http://collector.example:4318/v1/traces", True, "same-name-other-port"),
    ("http://COLLECTOR.Example.:8000", "http://collector.example:4318/v1/traces", True, "base-case-trailing-dot"),
    ("http://collector.example:8000", "http://COLLECTOR.example.:4318/v1/traces", True, "endpoint-case-trailing-dot"),
    ("http://bücher.example:8000", "http://xn--bcher-kva.example:4318/v1/traces", True, "idna-equal"),
    ("http://[2001:db8::5]:8000", "http://[2001:0db8:0:0:0:0:0:5]:4318/v1/traces", True, "ipv6-equal"),
    ("https://api.example", "http://localhost:4318/v1/traces", True, "loopback-with-https-base"),
    ("https://api.example", "http://LOCALHOST.:4318/v1/traces", True, "loopback-case-trailing-dot"),
    ("https://api.example", "http://127.0.0.2:4318/v1/traces", True, "loopback-ipv4"),
    ("https://api.example", "http://[::1]:4318/v1/traces", True, "loopback-ipv6"),
    ("http://10.0.0.5:8000", "https://other.example/v1/traces", True, "other-host-https"),
    ("https://10.0.0.5:8000", "http://10.0.0.5:4318/v1/traces", False, "same-ip-https-base"),
    ("https://collector.example", "http://COLLECTOR.EXAMPLE.:4318/v1/traces", False, "same-name-https-base"),
    ("http://10.0.0.5:8000", "http://10.0.0.6:4318/v1/traces", False, "other-ip"),
    ("http://10.0.0.5:8000", "http://10.0.0.5.evil.test:4318/v1/traces", False, "ip-suffix-impostor"),
    ("http://collector.example:8000", "http://collector.example.evil.test:4318/v1/traces", False, "name-suffix-impostor"),
    ("http://collector.example:8000", "http://10.0.0.5:4318/v1/traces", False, "name-is-not-ip"),
    ("http://10.0.0.5:8000", "http://collector.example:4318/v1/traces", False, "ip-is-not-name"),
    ("http://10.0.0.5:8000", "http://[::ffff:10.0.0.5]:4318/v1/traces", False, "mapped-ipv6-is-not-ipv4"),
    ("http://[::ffff:10.0.0.5]:8000", "http://10.0.0.5:4318/v1/traces", False, "ipv4-is-not-mapped-ipv6"),
    ("http://collector.example:8000", "http://othercollector.example:4318/v1/traces", False, "name-prefix-impostor"),
]


@pytest.mark.parametrize("base,endpoint,allowed", [case[:3] for case in _SCOPE_CASES],
                         ids=[case[3] for case in _SCOPE_CASES])
def test_explicit_http_scope(monkeypatch, base, endpoint, allowed):
    monkeypatch.setenv("FI_COLLECTOR_ENDPOINT", endpoint)
    assert selected_or_refused(base) == (endpoint if allowed else None)


@pytest.mark.parametrize("endpoint", [
    "http://10.0.0.5:8000/tracer/v1/traces",
    "http://10.0.0.5:4318/v1/traces",
], ids=["legacy-snapshot", "explicit-snapshot"])
def test_validated_snapshot_is_accepted_without_environment_reread(monkeypatch, endpoint):
    monkeypatch.setenv("FI_COLLECTOR_ENDPOINT", "http://unrelated.example/v1/traces")
    try:
        factory = exporter_factory(
            base_url="http://10.0.0.5:8000", api_key="test-run-api", secret_key="test-run-secret",
            project="test-project", run_name="test-run", run_id="test-run-id",
            redactor=Redactor(), _endpoint=endpoint,
        )
    except ExperimentError:
        factory = None
    assert callable(factory)
