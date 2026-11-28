"""The reds the order names, each with no marker byte at any sink, and the gRPC rows of the sealed oracle."""

from __future__ import annotations

import os
import time
from typing import Optional
from unittest import mock

import httpx
import pytest

from fi._credentials import Credentials
from fi._http import LazyKeyAuth
from fi.errors import ConfigurationError
from tests.core._plaintext_oracle import *  # noqa: F401,F403
from tests.core._plaintext_oracle import sinks  # noqa: F401  (the fixture)


# --- the REDs named by the order, each with no marker byte at any sink ---------------------------------------


def _refused_with_env(sinks, env: dict[str, str], url_host: str, caller: str = "none") -> tuple[str, dict[str, int]]:
    for each in sinks.values():
        each.reset()
    fixed = {k: v.replace("{A}", str(sinks["sinkA"].port)).replace("{B}", str(sinks["sinkB"].port)) for k, v in env.items()}
    cleaned = {k: v for k, v in os.environ.items() if k not in PROXY_NAMES}
    with mock.patch.dict(os.environ, {**cleaned, **fixed}, clear=True):
        outcome = _send(f"http://{url_host}:{sinks['target'].port}/", caller, sinks)
    return outcome, {name: each.marker_bytes for name, each in sinks.items()}


@pytest.mark.parametrize("name,env", [
    ("http_proxy_with_dot_no_proxy", {"HTTP_PROXY": "http://127.0.0.1:{A}", "NO_PROXY": ".example.com", "FI_ALLOW_INSECURE_HTTP": "1"}),
    ("all_proxy_only", {"ALL_PROXY": "http://127.0.0.1:{A}", "FI_ALLOW_INSECURE_HTTP": "1"}),
    ("case_mix", {"HTTP_PROXY": "http://127.0.0.1:{A}", "http_proxy": "http://127.0.0.1:{B}", "FI_ALLOW_INSECURE_HTTP": "1"}),
    ("no_proxy_with_port", {"HTTP_PROXY": "http://127.0.0.1:{A}", "NO_PROXY": "example.com:80", "FI_ALLOW_INSECURE_HTTP": "1"}),
    ("cidr_no_proxy", {"HTTP_PROXY": "http://127.0.0.1:{A}", "NO_PROXY": "192.0.2.0/24", "FI_ALLOW_INSECURE_HTTP": "1"}),
])
def test_a_caller_client_is_refused_when_the_environment_proxies_it(sinks, name, env):
    """The caller's own client reads the environment (trust_env); the either-rule refuses it, no byte anywhere."""
    for each in sinks.values():
        each.reset()
    fixed = {k: v.replace("{A}", str(sinks["sinkA"].port)).replace("{B}", str(sinks["sinkB"].port)) for k, v in env.items()}
    cleaned = {k: v for k, v in os.environ.items() if k not in PROXY_NAMES}
    creds = Credentials(api_key=MARKER_KEY, secret_key=MARKER_SECRET, base_url="http://example.com", keys_source="argument", base_url_source="argument")
    with mock.patch.dict(os.environ, {**cleaned, **fixed}, clear=True):
        with httpx.Client(auth=LazyKeyAuth(lambda: creds), timeout=1.5, trust_env=True) as client:
            with pytest.raises(ConfigurationError):
                client.get(f"http://example.com:{sinks['target'].port}/")
    assert all(each.marker_bytes == 0 for each in sinks.values())


@pytest.mark.parametrize("name,env", [
    ("http_proxy_with_dot_no_proxy", {"HTTP_PROXY": "http://127.0.0.1:{A}", "NO_PROXY": ".example.com", "FI_ALLOW_INSECURE_HTTP": "1"}),
    ("all_proxy_only", {"ALL_PROXY": "http://127.0.0.1:{A}", "FI_ALLOW_INSECURE_HTTP": "1"}),
    ("case_mix", {"HTTP_PROXY": "http://127.0.0.1:{A}", "http_proxy": "http://127.0.0.1:{B}", "FI_ALLOW_INSECURE_HTTP": "1"}),
    ("no_proxy_with_port", {"HTTP_PROXY": "http://127.0.0.1:{A}", "NO_PROXY": "example.com:80", "FI_ALLOW_INSECURE_HTTP": "1"}),
    ("cidr_no_proxy", {"HTTP_PROXY": "http://127.0.0.1:{A}", "NO_PROXY": "192.0.2.0/24", "FI_ALLOW_INSECURE_HTTP": "1"}),
])
def test_an_sdk_built_plain_http_send_goes_direct_whatever_the_environment_says(sinks, name, env):
    """The transport the SDK builds for a plain-HTTP opt-in send has proxies off: the request reaches the target
    and no proxy sink sees a byte."""
    outcome, counts = _refused_with_env(sinks, env, "example.com")
    assert outcome == "sent"
    assert counts["sinkA"] == 0 and counts["sinkB"] == 0
    assert sinks["target"].marker_bytes > 0


def test_an_uninspectable_caller_transport_is_refused_with_no_byte(sinks):
    outcome, counts = _refused_with_env(sinks, {"FI_ALLOW_INSECURE_HTTP": "1"}, "example.com", caller="uninspectable_transport")
    assert outcome == "refused:proxied" and not any(counts.values())


def test_a_3xx_on_a_key_carrying_send_is_not_followed_and_is_an_error(sinks):
    """The target answers a redirect to the second proxy sink's address; the SDK client does not follow it, and
    its answer is an error, not a redirect response."""
    from fi import FutureAGIClient
    from fi import errors

    redirecting = Sink(status=b"302 Found", location=f"http://127.0.0.1:{sinks['sinkB'].port}/steal")
    try:
        sinks["sinkB"].reset()
        client = FutureAGIClient(api_key=MARKER_KEY, secret_key=MARKER_SECRET, base_url=f"http://127.0.0.1:{redirecting.port}", retries=0)
        with pytest.raises(errors.UnexpectedRedirectError):
            client.users.current()
        assert sinks["sinkB"].requests == 0 and sinks["sinkB"].marker_bytes == 0
        assert redirecting.marker_bytes > 0  # the keys went to the base URL only
    finally:
        redirecting.close()


def test_otel_env_headers_with_fi_keys_are_refused_for_a_non_fi_exporter(sinks):
    from fi.evals.otel.config import ExporterConfig
    from fi.evals.otel.types import ExporterType
    from fi.evals.otel._tracer_factories import _create_exporter

    for name in ("OTEL_EXPORTER_OTLP_HEADERS", "OTEL_EXPORTER_OTLP_TRACES_HEADERS"):
        for each in sinks.values():
            each.reset()
        cleaned = {k: v for k, v in os.environ.items() if not k.startswith("OTEL_EXPORTER_OTLP")}
        endpoint = f"http://127.0.0.1:{sinks['target'].port}/v1/traces"
        with mock.patch.dict(os.environ, {**cleaned, name: f"x-api-key={MARKER_KEY},x-secret-key={MARKER_SECRET}"}, clear=True):
            with pytest.raises(ConfigurationError) as info:
                _create_exporter(ExporterConfig(type=ExporterType.OTLP_HTTP, endpoint=endpoint))
        assert MARKER_KEY not in str(info.value) and MARKER_SECRET not in str(info.value)
        assert all(each.marker_bytes == 0 for each in sinks.values())


# --- the gRPC rows: the OTLP gRPC exporter is the SDK's one gRPC channel; the SDK builds it, there is no caller channel ----


def _grpc_rows() -> list[dict]:
    return [r for r in ORACLE["rows"] if r["transport"] == "grpc" and r["source"] in (DRIVEN_SOURCE, "*", "tls")]


def _grpc_exporter(authority: str, insecure: bool):
    from fi.evals.otel._tracer_factories import _create_exporter
    from fi.evals.otel.config import ExporterConfig
    from fi.evals.otel.types import ExporterType

    return _create_exporter(ExporterConfig(
        type=ExporterType.OTLP_GRPC, endpoint=authority, insecure=insecure, timeout_ms=1000,
        headers={"x-api-key": MARKER_KEY, "x-secret-key": MARKER_SECRET},
    ))


def _grpc_env(row: dict, opt_value: Optional[str], sinks: dict[str, Sink], authority: str) -> dict[str, str]:
    env: dict[str, str] = {}
    for name, value in ENV_VALUES[row["env"]].items():
        env[name] = value.replace("{A}", str(sinks["sinkA"].port)).replace("{B}", str(sinks["sinkB"].port))
    env.update(_noproxy_env(row["no_proxy"], authority, sinks["target"].port))
    if opt_value is not None:
        env["FI_ALLOW_INSECURE_HTTP"] = opt_value
    return env


def _grpc_decide(
    row: dict, secure: bool, opt_value: Optional[str], sinks: dict[str, Sink]
) -> tuple[str, Optional[ConfigurationError]]:
    authority = HOSTS[row["host"]]["authority"].replace("{T}", str(sinks["target"].port))
    cleaned = {k: v for k, v in os.environ.items() if k not in PROXY_NAMES}
    with mock.patch.dict(os.environ, {**cleaned, **_grpc_env(row, opt_value, sinks, HOSTS[row["host"]]["authority"])}, clear=True):
        from fi._core.http_security import require_secure_grpc_target

        try:
            require_secure_grpc_target(authority, {"x-api-key": MARKER_KEY, "x-secret-key": MARKER_SECRET}, insecure=not secure)
        except ConfigurationError as exc:
            reason = _oracle_error(str(exc)).replace("insecure_futureagi_http", "insecure_futureagi_grpc")
            return "refused:" + reason, exc
    return "build", None


def test_every_grpc_row_is_decided_as_the_oracle_decides_it(sinks):
    """The SDK's decision on the endpoint as written, for every gRPC row of a channel the SDK builds (caller 'none'):
    the plain rows by an insecure channel, the TLS rows by a secure one."""
    failures, tally = [], {"driven": 0, "matched": 0, "ruled_exception": 0, "plain": 0, "tls": 0}
    for row in _grpc_rows():
        for scheme, opt, opt_value, caller in _expand(row):
            if caller != "none":
                continue  # the SDK builds every gRPC channel itself; there is no caller channel
            secure = scheme == "https"
            tally["driven"] += 1
            tally["tls" if secure else "plain"] += 1
            got, exc = _grpc_decide(row, secure, opt_value, sinks)
            want = "build" if row["decision"] == "build" else "refused:" + row["error"]
            if is_excepted(row, scheme):
                tally["ruled_exception"] += 1
            elif got == want:
                tally["matched"] += 1
            elif (
                not secure
                and want == "build"
                and row["host"] in SPELLING_HOSTS
                and type(exc) is ConfigurationError
                and exc.code == "insecure_http_origin"
            ):
                tally["spelling_081"] = tally.get("spelling_081", 0) + 1
            else:
                error = f" ({type(exc).__name__}, code={exc.code!r})" if exc is not None else ""
                failures.append(f"{row_id(row)} {scheme}/{opt}: SDK {got}{error}, oracle {want}")
    print("conformance grpc", tally, "failures", len(failures))
    assert not failures, "\n".join(failures[:25])
    assert tally["plain"] > 1000 and tally["tls"] > 500
    assert tally["matched"] + tally["ruled_exception"] + tally.get("spelling_081", 0) == tally["driven"]
    # The plain cells of host s1_at_in_path (caller "none", the only caller of a channel the SDK builds), by the ruling.
    assert tally["ruled_exception"] == 32


@pytest.mark.parametrize("env_id", ["HTTP_PROXY", "http_proxy", "HTTPS_PROXY", "grpc_proxy", "all_proxy", "mixed_case"])
def test_a_plain_grpc_channel_the_sdk_builds_does_not_go_through_a_proxy(sinks, env_id):
    """Measured: with the opt-in on and a proxy variable set, the exporter's connection reaches the target and
    neither proxy sink sees a byte."""
    import time

    # app.localhost is a name that is not loopback by the written-host rule and that the resolver answers with 127.0.0.1
    row = {"env": env_id, "no_proxy": "none", "host": "wnl_app_localhost"}
    for each in sinks.values():
        each.reset()
    authority = HOSTS["wnl_app_localhost"]["authority"].replace("{T}", str(sinks["target"].port))
    cleaned = {k: v for k, v in os.environ.items() if k not in PROXY_NAMES}
    env = _grpc_env(row, "1", sinks, HOSTS["wnl_app_localhost"]["authority"])
    with mock.patch.dict(os.environ, {**cleaned, **env}, clear=True):
        exporter = _grpc_exporter(authority, insecure=True)
        assert exporter is not None
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import SimpleSpanProcessor

        provider = TracerProvider()
        provider.add_span_processor(SimpleSpanProcessor(exporter))
        with provider.get_tracer("conformance").start_as_current_span("s"):
            pass
        deadline = time.time() + 3
        while time.time() < deadline and not sinks["target"].requests and not sinks["sinkA"].requests and not sinks["sinkB"].requests:
            time.sleep(0.05)
        provider.shutdown()
    assert sinks["target"].requests > 0
    assert sinks["sinkA"].requests == 0 and sinks["sinkB"].requests == 0


def test_the_upload_call_with_keys_is_sent_direct_when_an_environment_proxy_is_set(sinks):
    """The file-upload calls go out on a session the SDK builds, which sends plain http direct whatever the proxy
    variables say: the call is not refused, and the proxy sink receives nothing."""
    from fi.api.auth import HttpClient

    for each in sinks.values():
        each.reset()
    cleaned = {k: v for k, v in os.environ.items() if k not in PROXY_NAMES}
    env = {"HTTP_PROXY": f"http://127.0.0.1:{sinks['sinkA'].port}"}
    with mock.patch.dict(os.environ, {**cleaned, **env}, clear=True):
        client = HttpClient.__new__(HttpClient)  # only the header helpers are used
        client._extra_headers = None
        for host in ("127.0.0.1", "localhost"):
            kwargs = {"url": f"http://{host}:{sinks['target'].port}/up", "headers": {"X-Api-Key": MARKER_KEY, "X-Secret-Key": MARKER_SECRET}}
            assert client._direct_kwargs(kwargs)["allow_redirects"] is False
    assert all(each.marker_bytes == 0 for each in sinks.values())
