"""Every host check in the Python client answers the shared loopback table the same way.

The rows are tests/fixtures/loopback/hosts.json. Each row goes through every place that decides whether a
host is the local machine: the shared rule, the platform HTTP policy, the origin guard, the sandbox origin
rule, the gateway warning for plain HTTP, the trace collector endpoint check and the channel connect. The name
``localhost.`` (trailing dot) goes to name resolution, so it is not loopback anywhere.
"""

from __future__ import annotations

import json
import re
import socket
import threading
from pathlib import Path

import httpx
import pytest
from fi._core import loopback, origins
from fi._core.http_security import is_insecure_http
from fi._core.loopback import is_loopback_host
from fi._credentials import Credentials
from fi.errors import ConfigurationError
from fi.sandbox import _connection
from fi.sandbox._channel import connect

ROOT = Path(__file__).resolve().parents[3]
ROWS = json.loads((ROOT / "tests" / "fixtures" / "loopback" / "hosts.json").read_text())["hosts"]
IDS = [row["host"] for row in ROWS]
FI_SOURCES = Path(__file__).resolve().parents[2] / "fi"


def rows():
    return pytest.mark.parametrize("row", ROWS, ids=IDS)


def authority(host: str) -> str:
    return f"[{host}]" if ":" in host and not host.startswith("[") else host


def url_for(host: str, scheme: str = "http") -> httpx.URL | None:
    try:
        url = httpx.URL(f"{scheme}://{authority(host)}/")
    except Exception:
        return None
    return url if url.raw_host else None


@rows()
def test_the_shared_rule(row):
    assert is_loopback_host(row["host"]) is row["loopback"]


@rows()
def test_the_url_form_of_the_rule(row):
    url = url_for(row["host"])
    if url is None:
        pytest.skip("a URL cannot carry this host")
    assert loopback.is_loopback_url(url) is row["loopback"]


@rows()
def test_the_platform_http_policy(row):
    url = url_for(row["host"])
    if url is None:
        pytest.skip("a URL cannot carry this host")
    assert is_insecure_http(url) is (not row["loopback"])


@rows()
def test_the_origin_guard(row):
    assert origins.is_loopback(row["host"]) is row["loopback"]
    url = url_for(row["host"])
    if url is not None:
        assert origins.host_allowed(url) is row["loopback"]


@rows()
def test_the_sandbox_origin_rule(row):
    assert _connection.is_loopback(row["host"]) is row["loopback"]


@rows()
def test_the_gateway_plain_http_refusal(row, monkeypatch):
    from fi.gateway._exceptions import AgentCCError
    from fi.gateway._http_security import validate_destination
    from httpx import InvalidURL

    monkeypatch.delenv("FI_ALLOW_INSECURE_HTTP", raising=False)

    base = f"http://{authority(row['host'])}/"
    refused = False
    try:
        validate_destination(base, base)
    except AgentCCError as error:
        if "Credentials are not sent over http://" not in str(error):
            pytest.skip("a URL cannot carry this host")
        refused = True
    except InvalidURL:
        pytest.skip("a URL cannot carry this host")
    assert refused is (not row["loopback"])


@rows()
def test_the_collector_endpoint_check(row):
    pytest.importorskip("opentelemetry.sdk.trace")
    from fi.experiments._tracing.export import _validate_collector_endpoint
    from fi.experiments.errors import ExperimentError

    endpoint = f"http://{authority(row['host'])}:4318/v1/traces"
    try:
        _validate_collector_endpoint(endpoint, base_url="https://api.example.test")
        accepted = True
    except ExperimentError:
        accepted = False
    # A different-host HTTP base does not rescue a non-loopback host, so acceptance is the loopback answer.
    assert accepted is row["loopback"]


@rows()
def test_the_channel_connect(row):
    assert connect._is_loopback(row["host"]) is row["loopback"]


def test_no_source_file_asks_an_address_object_for_is_loopback():
    offenders = [
        f"{path.relative_to(FI_SOURCES)}:{number}"
        for path in FI_SOURCES.rglob("*.py")
        for number, line in enumerate(path.read_text().splitlines(), 1)
        if re.search(r"\.is_loopback\b", line) and not line.lstrip().startswith("#")
    ]
    assert offenders == []


def test_a_trailing_dot_name_is_refused_as_insecure_and_not_sent_through_the_proxy(monkeypatch):
    listener = socket.socket()
    listener.bind(("127.0.0.1", 0))
    listener.listen(5)
    listener.settimeout(0.3)
    accepted: list[int] = []

    def serve():
        try:
            conn, _ = listener.accept()
            accepted.append(1)
            conn.close()
        except OSError:
            pass

    thread = threading.Thread(target=serve, daemon=True)
    thread.start()
    port = listener.getsockname()[1]
    monkeypatch.setenv("HTTP_PROXY", f"http://127.0.0.1:{port}")
    monkeypatch.setenv("http_proxy", f"http://127.0.0.1:{port}")
    monkeypatch.delenv("NO_PROXY", raising=False)
    monkeypatch.delenv("no_proxy", raising=False)
    creds = Credentials(
        api_key=None, secret_key=None, base_url=f"http://localhost.:{port}", keys_source="none",
        base_url_source="argument", platform_base_url=f"http://localhost.:{port}",
        platform_base_url_source="argument", platform_token="tok-test-1234", platform_token_source="argument",
    )
    try:
        with pytest.raises(ConfigurationError) as raised:
            origins.resolve_platform(creds, environ={})
        assert raised.value.code == "insecure_http_origin"
        thread.join(1)
    finally:
        listener.close()
    assert accepted == []
