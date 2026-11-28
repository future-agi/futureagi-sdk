# ruff: noqa: F811
"""A Future AGI host is the same host however it is written.

``api.futureagi.com.`` (a trailing dot), ``API.FUTUREAGI.COM`` and a punycode or Unicode spelling reach the
same machine over DNS, so an exporter pointed at one of them is bound for Future AGI: it sends the SDK's own
headers and nothing from ``OTEL_EXPORTER_OTLP_*``. A host that only looks like a Future AGI host, or carries
one in its user-info, stays the user's own endpoint.
"""

import pytest

from tests.experiments.unit.test_fi_bound_exporter_headers import ambient  # noqa: F401

DEFAULT_HOSTS = ("api.futureagi.com", "grpc.futureagi.com")


@pytest.fixture
def clean_hosts(monkeypatch):
    for name in ("FI_BASE_URL", "FI_GRPC_URL", "FI_TRACES_URL"):
        monkeypatch.delenv(name, raising=False)


def bound(endpoint):
    from fi._otlp_headers import is_future_agi_endpoint

    return is_future_agi_endpoint(endpoint)


@pytest.mark.parametrize("host", DEFAULT_HOSTS)
@pytest.mark.parametrize(
    "form",
    [
        "https://{host}./tracer/v1/traces",
        "https://{host}.:443/tracer/v1/traces",
        "{host}.:443",
        "{host}.",
        "HTTPS://{HOST}/tracer/v1/traces",
        "{HOST}.:443",
    ],
)
def test_the_default_hosts_in_any_spelling_are_futureagi(clean_hosts, host, form):
    assert bound(form.format(host=host, HOST=host.upper())) is True


@pytest.mark.parametrize(
    ("name", "value"),
    [
        ("FI_BASE_URL", "https://API.Example.Test"),
        ("FI_BASE_URL", "https://api.example.test."),
        ("FI_TRACES_URL", "https://traces.example.test./tracer/v1/traces"),
        ("FI_GRPC_URL", "GRPC.EXAMPLE.TEST.:443"),
    ],
)
@pytest.mark.parametrize(
    "endpoint",
    [
        "https://api.example.test/tracer/v1/traces",
        "https://api.example.test./tracer/v1/traces",
        "https://traces.example.test/v1/traces",
        "https://traces.example.test./v1/traces",
        "grpc.example.test:443",
        "grpc.example.test.:443",
    ],
)
def test_a_configured_host_matches_in_any_spelling(
    clean_hosts, monkeypatch, name, value, endpoint
):
    from fi._otlp_headers import _host

    monkeypatch.setenv(name, value)
    configured = _host(value)
    assert (_host(endpoint) == configured) is bound(endpoint)


def test_a_configured_upper_case_and_trailing_dot_base_url_counts(
    clean_hosts, monkeypatch
):
    monkeypatch.setenv("FI_BASE_URL", "https://API.EU.Example.Test.")
    assert bound("https://api.eu.example.test/tracer/v1/traces") is True
    assert bound("https://api.eu.example.test./tracer/v1/traces") is True


def test_an_idna_spelling_is_the_same_host(clean_hosts, monkeypatch):
    monkeypatch.setenv("FI_BASE_URL", "https://bücher.example.test")
    assert bound("https://xn--bcher-kva.example.test/tracer/v1/traces") is True
    monkeypatch.setenv("FI_BASE_URL", "https://xn--bcher-kva.example.test.")
    assert bound("https://BÜCHER.example.test/tracer/v1/traces") is True


@pytest.mark.parametrize(
    "endpoint",
    [
        "https://api.futureagi.com@other-origin.example.test/v1/traces",
        "https://api.futureagi.com.@other-origin.example.test/v1/traces",
        "https://api.futureagi.com.other-origin.example.test/v1/traces",
        "https://otherapi.futureagi.com/v1/traces",
        "https://api.futureagi.com.example./v1/traces",
        "https://collector.example.test./v1/traces",
        "grpc.futureagi.com.other-origin.test:443",
        "other-origin.test.:443",
    ],
)
def test_lookalikes_and_other_hosts_stay_the_users_own(clean_hosts, endpoint):
    assert bound(endpoint) is False


@pytest.mark.parametrize("endpoint", ["grpc.futureagi.com.:443", "GRPC.FUTUREAGI.COM:443"])
def test_a_grpc_exporter_at_a_respelled_futureagi_host_is_pinned(
    clean_hosts, ambient, endpoint
):
    from fi.evals.otel._tracer_factories import _create_exporter
    from fi.evals.otel.config import ExporterConfig, ExporterType

    exporter = _create_exporter(
        ExporterConfig(type=ExporterType.OTLP_GRPC, endpoint=endpoint)
    )
    sent = {key.lower(): value for key, value in exporter._headers}
    assert "x-ambient" not in sent
    assert "authorization" not in sent


@pytest.mark.parametrize(
    "endpoint",
    [
        "https://api.futureagi.com./tracer/v1/traces",
        "https://API.FUTUREAGI.COM/tracer/v1/traces",
    ],
)
def test_an_http_exporter_at_a_respelled_futureagi_host_is_pinned(
    clean_hosts, ambient, endpoint
):
    from fi.evals.otel._tracer_factories import _create_exporter
    from fi.evals.otel.config import ExporterConfig, ExporterType

    exporter = _create_exporter(
        ExporterConfig(type=ExporterType.OTLP_HTTP, endpoint=endpoint)
    )
    from fi._otlp_headers import _session_of

    session = _session_of(exporter)
    client = getattr(exporter, "_client", None)
    held = dict(getattr(client, "_headers", None) or session.headers)
    sent = {key.lower(): value for key, value in held.items()}
    assert "x-ambient" not in sent
    assert "authorization" not in sent
    # netrc credentials are not applied: the session has an auth that does nothing.
    assert session.auth is not None


# --- A host is Future AGI only on its fully normalised ASCII name ----------------------------------------


@pytest.mark.parametrize(
    "endpoint",
    [
        "https://api.futurеagi.com/tracer/v1/traces",  # Cyrillic e
        "https://api.futureagi.cоm/tracer/v1/traces",  # Cyrillic o
        "https://αpi.futureagi.com/tracer/v1/traces",  # Greek alpha
        "https://api.futureagi.comа/tracer/v1/traces",  # mixed script tail
        "https://apі.futureagi.com/tracer/v1/traces",  # Cyrillic i
    ],
)
def test_confusable_lookalikes_are_not_futureagi(clean_hosts, endpoint):
    assert bound(endpoint) is False


@pytest.mark.parametrize(
    "endpoint",
    [
        "https://api.futurеagi.com/tracer/v1/traces",
        "https://αpi.futureagi.com/tracer/v1/traces",
    ],
)
def test_a_lookalike_gets_no_futureagi_keys(clean_hosts, ambient, monkeypatch, endpoint):
    from fi.evals.otel._tracer_factories import _create_exporter
    from fi.evals.otel.config import ExporterConfig, ExporterType

    monkeypatch.setenv("FI_API_KEY", "fi-key-value")
    monkeypatch.setenv("FI_SECRET_KEY", "fi-secret-value")
    exporter = _create_exporter(ExporterConfig(type=ExporterType.OTLP_HTTP, endpoint=endpoint))
    from fi._otlp_headers import _session_of

    session = _session_of(exporter)
    client = getattr(exporter, "_client", None)
    held = dict(getattr(client, "_headers", None) or session.headers)
    sent = {key.lower(): str(value) for key, value in held.items()}
    assert "x-api-key" not in sent and "x-secret-key" not in sent
    assert "fi-key-value" not in " ".join(sent.values())


LONG = "a" * 70


@pytest.mark.parametrize("name", ["FI_BASE_URL", "FI_TRACES_URL", "FI_GRPC_URL"])
def test_an_unencodable_endpoint_is_not_futureagi_even_when_configured_the_same(
    clean_hosts, monkeypatch, name
):
    monkeypatch.setenv(name, f"https://{LONG}.example.test")
    assert bound(f"https://{LONG}.example.test/tracer/v1/traces") is False
    assert bound(f"{LONG}.example.test:443") is False


def test_an_unencodable_configured_host_is_ignored_and_logged_without_its_value(
    clean_hosts, monkeypatch, caplog
):
    from fi._otlp_headers import future_agi_hosts

    monkeypatch.setenv("FI_BASE_URL", f"https://{LONG}.example.test")
    with caplog.at_level("WARNING"):
        hosts = future_agi_hosts()
    assert hosts == {"api.futureagi.com", "grpc.futureagi.com"}
    assert "FI_BASE_URL" in caplog.text
    assert LONG not in caplog.text


@pytest.mark.parametrize(
    "endpoint",
    [
        "https://api.futureagi.com../tracer/v1/traces",
        "grpc.futureagi.com..:443",
        "https://api..futureagi.com/tracer/v1/traces",
        "https://.api.futureagi.com/tracer/v1/traces",
        "https://api.futureagi.com\x00/tracer/v1/traces",
    ],
)
def test_malformed_spellings_are_not_futureagi(clean_hosts, endpoint):
    assert bound(endpoint) is False


def test_a_malformed_configured_host_never_matches_the_same_malformed_endpoint(
    clean_hosts, monkeypatch
):
    monkeypatch.setenv("FI_BASE_URL", "https://api.example.test..")
    assert bound("https://api.example.test../tracer/v1/traces") is False


def test_default_hosts_always_normalise(clean_hosts):
    from fi._otlp_headers import (
        DEFAULT_FUTUREAGI_HOSTS,
        _normalized_host,
        future_agi_hosts,
    )

    assert [_normalized_host(host) for host in DEFAULT_FUTUREAGI_HOSTS] == list(DEFAULT_HOSTS)
    assert future_agi_hosts() == set(DEFAULT_HOSTS)


def _mutations(host):
    out = {host + "x", "x" + host, host + ".other-origin.test", host.replace(".", "..", 1), host + "..", "." + host}
    swaps = {"a": "а", "e": "е", "o": "о", "i": "і", "c": "с", "p": "р", "g": "ɡ"}
    for index, char in enumerate(host):
        if char in swaps:
            out.add(host[:index] + swaps[char] + host[index + 1 :])
        if char == ".":
            out.add(host[:index] + "-" + host[index + 1 :])
            out.add(host[:index] + host[index + 1 :])
        out.add(host[:index] + host[index + 1 :])
        out.add(host[:index] + "-" + host[index:])
    out.add(host.replace("futureagi", "futureag1"))
    out.add(host.replace("futureagi", "futureagi\u200b"))
    out.add(host.replace("com", "cöm"))
    out.add(host.replace("api", "a" * 64 + "x"))
    return out - {host}


def test_any_mutated_spelling_of_a_default_host_that_normalises_differently_is_not_futureagi(
    clean_hosts,
):
    from fi._otlp_headers import _normalized_host

    cases = sorted({m for host in DEFAULT_HOSTS for m in _mutations(host)})
    assert len(cases) >= 50
    for spelling in cases:
        normal = _normalized_host(spelling)
        for form in (f"https://{spelling}/v1/traces", f"{spelling}:443"):
            if normal in DEFAULT_HOSTS:
                continue
            assert bound(form) is False, spelling
