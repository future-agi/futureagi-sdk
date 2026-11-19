"""Exercise the SQL seed fixture without a backend, real credentials or network I/O."""

import socket
from unittest.mock import Mock

import httpx
import pytest
import test_all_operations_live as live


@pytest.fixture
def wire(monkeypatch):
    monkeypatch.setenv("FI_API_KEY", "synthetic-api")
    monkeypatch.setenv("FI_SECRET_KEY", "synthetic-secret")
    monkeypatch.setenv("FI_BASE_URL", "http://localhost:8100")
    monkeypatch.delenv("FI_COLLECTOR_OTLP_HTTP_PORT", raising=False)
    monkeypatch.setattr(socket, "getaddrinfo", lambda *a, **kw: pytest.fail("unexpected DNS lookup"))
    sdk = Mock()
    sdk.projects.list.side_effect = lambda *, name: {"projects": [{"id": "own-project", "name": name}]}
    requests = []
    client = httpx.Client

    def seed(body=b"{}", status=200, error=None):
        def record(request):
            requests.append(request)
            if error:
                raise error
            return httpx.Response(status, content=body, headers={"Location": "https://other.invalid/opaque-header"})

        def mock_client(**kwargs):
            assert kwargs["trust_env"] is False
            return client(transport=httpx.MockTransport(record), **kwargs)

        monkeypatch.setattr(httpx, "Client", mock_client)
        return live.sql_project.__wrapped__(sdk)

    return seed, requests, sdk


@pytest.mark.parametrize("base", [
    "https://example.invalid", "http://192.0.2.1", "https://localhost.example.invalid", "http://localhost.",
    "ftp://localhost", "//localhost", "http://name:opaque-userinfo@localhost", "http://@127.0.0.1",
    "http://127.1", "http://[::1]extra", "http://[::1%25scope]", "http://localhost:65536", "http://localhost:",
    "http://local\nhost", "http://localhost/path", "http://localhost?query", "http://localhost#fragment",
])
def test_sql_seed_rejects_origin_before_any_requests(wire, monkeypatch, base):
    seed, requests, sdk = wire
    monkeypatch.setenv("FI_BASE_URL", base)
    with pytest.raises(ValueError, match=r"^SQL fixture requires an HTTP\(S\) loopback API origin$"):
        seed()
    assert not requests and not sdk.mock_calls


@pytest.mark.parametrize(("base", "port", "expected"), [
    ("http://localhost:8100", None, "http://localhost:24318/v1/traces"),
    ("https://127.0.0.42/", "43518", "https://127.0.0.42:43518/v1/traces"),
    ("http://[::1]:8100", None, "http://[::1]:24318/v1/traces"),
])
def test_sql_seed_posts_once_to_derived_collector(wire, monkeypatch, base, port, expected):
    seed, requests, _ = wire
    monkeypatch.setenv("FI_BASE_URL", base)
    if port:
        monkeypatch.setenv("FI_COLLECTOR_OTLP_HTTP_PORT", port)
    project_id, _, spans = seed()
    assert project_id == "own-project" and len(spans) == 2
    request, = requests
    assert request.method == "POST" and str(request.url) == expected
    assert (request.headers["X-Api-Key"], request.headers["X-Secret-Key"]) == ("synthetic-api", "synthetic-secret")


@pytest.mark.parametrize("port", ["0", "65536", "other.invalid:4318"])
def test_sql_seed_rejects_invalid_collector_port(wire, monkeypatch, port):
    seed, requests, sdk = wire
    monkeypatch.setenv("FI_COLLECTOR_OTLP_HTTP_PORT", port)
    with pytest.raises(ValueError, match="^SQL fixture requires a valid collector port$"):
        seed()
    assert not requests and not sdk.mock_calls


@pytest.mark.parametrize("body", [
    b"", b" \t\r\n", "\ufeff\u00a0".encode(), b"{}", b'{"partialSuccess":{}}',
    b'{"partialSuccess":{"rejectedSpans":0,"errorMessage":""},"partial_success":{"rejected_spans":"00","error_message":""}}',
])
def test_sql_seed_accepts_clean_receipt(wire, body):
    seed, requests, _ = wire
    assert seed(body)[0] == "own-project"
    assert len(requests) == 1


@pytest.mark.parametrize("body", [
    b'{"partialSuccess":{"rejectedSpans":1}}', b'{"partial_success":{"rejected_spans":"1"}}',
    b'{"partialSuccess":{"rejectedSpans":0,"errorMessage":"opaque-body"}}',
    b'{"partial_success":{"error_message":"opaque-body"}}',
    b'{"partialSuccess":{},"partial_success":{"rejectedSpans":1}}',
    b'{"partial_success":{},"partialSuccess":{"error_message":"opaque-body"}}',
    b'{"partialSuccess":{"rejectedSpans":0,"rejected_spans":1}}',
    b'{"partial_success":{"errorMessage":"","error_message":"opaque-body"}}',
    b'{"partialSuccess":{"rejectedSpans":NaN,"rejectedSpans":0}}', b"\x1c",
    b"opaque-body", b"\xff", b"[]", b"null", b'{"opaque-body":0}', b'{"partial_success":null}',
    b'{"partialSuccess":{"opaque-body":0}}', b'{"partial_success":{"errorMessage":null}}',
    b'{"partialSuccess":{"rejectedSpans":false}}', b'{"partialSuccess":{"rejectedSpans":"0.0"}}',
])
def test_sql_seed_stops_on_unclean_receipt(wire, body):
    seed, requests, sdk = wire
    with pytest.raises(pytest.fail.Exception, match="^SQL fixture collector returned an invalid or partial OTLP receipt$") as failure:
        seed(body)
    assert not failure.value.pytrace  # do not show the body/headers in pytest diagnostics
    assert len(requests) == 1 and not sdk.mock_calls


@pytest.mark.parametrize("status", [307, 429, 503])
def test_sql_seed_does_not_redirect_or_replay(wire, status):
    seed, requests, sdk = wire
    with pytest.raises(ValueError, match=f"^SQL fixture collector returned HTTP {status}$"):
        seed(b"opaque-body", status)
    assert [str(request.url) for request in requests] == ["http://localhost:24318/v1/traces"]
    assert not sdk.mock_calls


def test_sql_seed_does_not_replay_after_ambiguous_transport_error(wire):
    seed, requests, sdk = wire
    with pytest.raises(ValueError, match="^SQL fixture collector request failed$"):
        seed(error=httpx.ReadError("synthetic-secret"))
    assert len(requests) == 1 and not sdk.mock_calls
