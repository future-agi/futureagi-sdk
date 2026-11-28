"""Credentials go over ``http://`` only to a loopback host, or to any host when ``FI_ALLOW_INSECURE_HTTP=1``.

Every path that sends X-Api-Key, X-Secret-Key or an Authorization Bearer value is checked: refused for a host that is
not loopback, sent for a loopback host, sent with the opt-in. The loopback decision is the shared fixture
``tests/fixtures/loopback/hosts.json``, read as the host is written.
"""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from types import SimpleNamespace

import httpx
import pytest
from fi._core.http_security import (
    ALLOW_INSECURE_HTTP_ENV,
    check_http_security,
    require_secure_credential_headers,
    require_secure_credentials_url,
)
from fi._core.key_refusal_rules import spelling_problem
from fi.errors import ConfigurationError

from tests._judged_mock_transport import JudgedMockTransport

FIXTURE = Path(__file__).resolve().parents[3] / "tests" / "fixtures" / "loopback" / "hosts.json"
HOSTS = json.loads(FIXTURE.read_text(encoding="utf-8"))["hosts"]
KEYS = {"X-Api-Key": "key-not-a-secret", "X-Secret-Key": "secret-not-a-secret"}
REMOTE = "http://remote-credentials.test:8080"
LOOPBACK = "http://127.0.0.1:8080"


def _url(host: str, scheme: str = "http") -> str:
    bracketed = host if host.startswith("[") or ":" not in host else f"[{host}]"
    return f"{scheme}://{bracketed}:8080/path"


def _usable(entry) -> bool:
    try:
        httpx.URL(_url(entry["host"]))
    except httpx.InvalidURL:
        return False
    return True


USABLE = [entry for entry in HOSTS if _usable(entry)]


@pytest.fixture(autouse=True)
def _no_opt_in(monkeypatch):
    monkeypatch.delenv(ALLOW_INSECURE_HTTP_ENV, raising=False)


def _refused(call) -> ConfigurationError:
    with pytest.raises(ConfigurationError) as caught:
        call()
    message = str(caught.value)
    assert ALLOW_INSECURE_HTTP_ENV in message and "https://" in message and "Set " in message
    assert "key-not-a-secret" not in message and "secret-not-a-secret" not in message
    assert caught.value.code == "insecure_http_origin"
    return caught.value


@pytest.mark.parametrize("entry", USABLE, ids=[e["host"] for e in USABLE])
def test_the_shared_helper_follows_the_loopback_fixture(entry):
    url = _url(entry["host"])
    if entry["loopback"]:
        require_secure_credentials_url(url)
    elif "%" in entry["host"]:
        # a host written with a percent-encoded character is refused whatever the opt-in says
        for environ in ({}, {ALLOW_INSECURE_HTTP_ENV: "1"}):
            with pytest.raises(ConfigurationError):
                require_secure_credentials_url(url, environ=environ)
    else:
        _refused(lambda: require_secure_credentials_url(url))
        if spelling_problem(url, entry["host"].lower()) is not None:
            # 0.8.1: a trailing dot or a short, decimal, hex or octal IPv4 form is not unlocked by the opt-in
            with pytest.raises(ConfigurationError):
                require_secure_credentials_url(url, environ={ALLOW_INSECURE_HTTP_ENV: "1"})
        else:
            require_secure_credentials_url(url, environ={ALLOW_INSECURE_HTTP_ENV: "1"})
    require_secure_credentials_url(_url(entry["host"], "https"))


def test_the_message_names_the_setting_and_the_opt_in():
    error = _refused(lambda: require_secure_credentials_url(REMOTE, setting="FI_COLLECTOR_ENDPOINT"))
    assert "Set FI_COLLECTOR_ENDPOINT to an https:// address" in str(error)
    assert f"set {ALLOW_INSECURE_HTTP_ENV}=1" in str(error)


def test_headers_without_credentials_pass_and_any_credential_header_is_checked():
    require_secure_credential_headers(REMOTE, {"Accept": "application/json"})
    require_secure_credential_headers(REMOTE, None)
    for name in ("x-api-key", "X-SECRET-KEY", "Authorization"):
        _refused(lambda name=name: require_secure_credential_headers(REMOTE, {name: "v"}))


@pytest.mark.parametrize("value", ["1"])
def test_the_opt_in_values(monkeypatch, value):
    monkeypatch.setenv(ALLOW_INSECURE_HTTP_ENV, value)
    require_secure_credentials_url(REMOTE)


@pytest.mark.parametrize("value", ["", "0", "no", "false", "true", "yes", " 1"])
def test_other_values_are_not_the_opt_in(monkeypatch, value):
    monkeypatch.setenv(ALLOW_INSECURE_HTTP_ENV, value)
    _refused(lambda: require_secure_credentials_url(REMOTE))


# Path 1: the platform transport, keys mode and Bearer mode.
@pytest.mark.parametrize("mode", ["keys", "bearer"])
def test_the_platform_check_refuses_keys_and_bearer_alike(mode, capsys):
    _refused(lambda: check_http_security(httpx.URL(REMOTE), mode))
    check_http_security(httpx.URL(LOOPBACK), mode)
    check_http_security(httpx.URL(REMOTE), mode, environ={ALLOW_INSECURE_HTTP_ENV: "1"})
    check_http_security(httpx.URL("http://other-credentials.test"), mode, allow_insecure_http=True, environ={})


def test_an_explicit_false_wins_over_the_environment():
    _refused(lambda: check_http_security(
        httpx.URL(REMOTE), "keys", allow_insecure_http=False, environ={ALLOW_INSECURE_HTTP_ENV: "1"}))


# Path 2: the gateway client.
@pytest.mark.parametrize("entry", USABLE, ids=[e["host"] for e in USABLE])
def test_the_gateway_destination_follows_the_loopback_fixture(entry, monkeypatch):
    from fi.gateway._exceptions import AgentCCError
    from fi.gateway._http_security import validate_destination

    url = _url(entry["host"])
    if entry["loopback"]:
        validate_destination(url, url)
        return
    with pytest.raises(AgentCCError) as caught:
        validate_destination(url, url)
    assert "Set the base URL to an https:// address" in str(caught.value)
    monkeypatch.setenv(ALLOW_INSECURE_HTTP_ENV, "1")
    if "%" in entry["host"] or spelling_problem(url, entry["host"].lower()) is not None:
        with pytest.raises(AgentCCError):
            validate_destination(url, url)  # refused whatever the opt-in says (the 0.8.1 rule for these spellings)
        return
    assert ALLOW_INSECURE_HTTP_ENV in str(caught.value)
    validate_destination(url, url)


def _gateway_models_list(base_url):
    from fi.gateway import AgentCC

    seen = []

    def handle(request):
        seen.append(request)
        return httpx.Response(200, json={"object": "list", "data": []})

    with httpx.Client(transport=JudgedMockTransport(handle)) as http:
        with AgentCC(api_key="sk-test-key", base_url=base_url, http_client=http) as client:
            client.models.list()
    return seen


def test_the_gateway_refuses_before_the_request_is_sent(monkeypatch):
    from fi.gateway._exceptions import AgentCCError

    with pytest.raises(AgentCCError, match="FI_ALLOW_INSECURE_HTTP"):
        _gateway_models_list(REMOTE)
    assert len(_gateway_models_list(LOOPBACK)) == 1
    monkeypatch.setenv(ALLOW_INSECURE_HTTP_ENV, "1")
    assert len(_gateway_models_list(REMOTE)) == 1


def test_the_gateway_health_check_sends_nothing_to_a_refused_host(monkeypatch):
    from fi.gateway import health_check

    sent = []
    monkeypatch.setattr("fi.gateway._utils.httpx.get", lambda url, **kw: sent.append(url) or httpx.Response(200))
    result = health_check(base_url=REMOTE, api_key="sk-test-key")
    assert result["status"] == "error" and ALLOW_INSECURE_HTTP_ENV in result["error"] and sent == []
    assert health_check(base_url=LOOPBACK, api_key="sk-test-key")["status"] == "ok" and len(sent) == 1
    sent.clear()
    assert health_check(base_url=REMOTE)["status"] == "ok" and len(sent) == 1  # no key, nothing to protect
    sent.clear()
    monkeypatch.setenv(ALLOW_INSECURE_HTTP_ENV, "1")
    assert health_check(base_url=REMOTE, api_key="sk-test-key")["status"] == "ok"
    assert len(sent) == 1


# Path 3: the legacy requests-based client, its file uploads and the knowledge base.
class _Session:
    def __init__(self):
        self.calls = []

    def request(self, **kwargs):
        self.calls.append(kwargs)
        return SimpleNamespace(result=lambda: SimpleNamespace(status_code=200))


def _legacy(base_url):
    from fi.api.auth import APIKeyAuth

    session = _Session()
    return APIKeyAuth(fi_api_key="key-not-a-secret", fi_secret_key="secret-not-a-secret",
                      fi_base_url=base_url, session=session), session


def _request(client, url):
    from fi.api.types import HttpMethod, RequestConfig

    return client.request(RequestConfig(method=HttpMethod.GET, url=url, retry_attempts=1))


def test_the_legacy_client_request(monkeypatch):
    client, session = _legacy(REMOTE)
    _refused(lambda: _request(client, REMOTE + "/x"))
    assert session.calls == []
    client, session = _legacy(LOOPBACK)
    _request(client, LOOPBACK + "/x")
    assert len(session.calls) == 1
    monkeypatch.setenv(ALLOW_INSECURE_HTTP_ENV, "1")
    client, session = _legacy(REMOTE)
    _request(client, REMOTE + "/x")
    assert len(session.calls) == 1


def test_the_legacy_client_file_upload_arguments(monkeypatch):
    client, _ = _legacy(REMOTE)
    _refused(lambda: client._direct_kwargs({"url": REMOTE + "/x", "headers": dict(KEYS)}))
    client._direct_kwargs({"url": REMOTE + "/x", "headers": {"Accept": "application/json"}})
    client, _ = _legacy(LOOPBACK)
    assert client._direct_kwargs({"url": LOOPBACK + "/x", "headers": dict(KEYS)})["url"] == LOOPBACK + "/x"
    monkeypatch.setenv(ALLOW_INSECURE_HTTP_ENV, "1")
    client, _ = _legacy(REMOTE)
    assert client._direct_kwargs({"url": REMOTE + "/x", "headers": dict(KEYS)})["url"] == REMOTE + "/x"


def test_the_knowledge_base_upload(monkeypatch, tmp_path):
    from fi.kb.client import KnowledgeBase
    from fi.utils.routes import Routes

    posted = []
    monkeypatch.setattr("fi._core.requests_session.LoopbackDirectSession.request", lambda _session, _method, **kw: posted.append(kw) or SimpleNamespace(
        status_code=200, raise_for_status=lambda: None, request=SimpleNamespace(method="POST"),
        url="http://kb.test/" + Routes.knowledge_base.value,
        json=lambda: {"status": True, "result": {"kb_id": "00000000-0000-0000-0000-000000000001", "kb_name": "n", "file_ids": []}}))
    document = tmp_path / "notes.txt"
    document.write_text("text")

    def create(base_url):
        kb = KnowledgeBase(fi_api_key="key-not-a-secret", fi_secret_key="secret-not-a-secret", fi_base_url=base_url)
        return kb.create_kb(name="n", file_paths=str(tmp_path))

    _refused(lambda: create(REMOTE))
    assert posted == []
    create(LOOPBACK)
    assert len(posted) == 1
    monkeypatch.setenv(ALLOW_INSECURE_HTTP_ENV, "1")
    create(REMOTE)
    assert len(posted) == 2


# Path 4: the eval template registry.
def test_the_eval_registry_request(monkeypatch, caplog):
    from fi.evals.core import cloud_registry

    sent = []
    body = {"status": True, "result": []}
    monkeypatch.setattr("fi._core.requests_session.LoopbackDirectSession.get", lambda _session, url, **kw: sent.append(url) or SimpleNamespace(
        status_code=200, raise_for_status=lambda: None, json=lambda: body))
    with pytest.raises(ConfigurationError) as refused:
        cloud_registry.load_registry(REMOTE, "key-not-a-secret", "secret-not-a-secret", force_refresh=True)
    assert sent == [] and ALLOW_INSECURE_HTTP_ENV in str(refused.value) and refused.value.code == "insecure_http_origin"
    cloud_registry.load_registry(LOOPBACK, "key-not-a-secret", "secret-not-a-secret", force_refresh=True)
    assert len(sent) == 1
    monkeypatch.setenv(ALLOW_INSECURE_HTTP_ENV, "1")
    cloud_registry.load_registry(REMOTE, "key-not-a-secret", "secret-not-a-secret", force_refresh=True)
    assert len(sent) == 2


# Path 5: the evals trace exporters.
@pytest.mark.parametrize("kind", ["OTLP_HTTP", "ARIZE", "PHOENIX", "LANGFUSE", "FUTUREAGI"])
def test_the_evals_exporters(monkeypatch, kind):
    pytest.importorskip("opentelemetry.exporter.otlp.proto.http.trace_exporter")
    from fi.evals.otel._tracer_factories import _create_exporter
    from fi.evals.otel.config import ExporterConfig, ExporterType

    def config(endpoint):
        return ExporterConfig(type=getattr(ExporterType, kind), endpoint=endpoint, headers={"x-api-key": "key-not-a-secret"})

    _refused(lambda: _create_exporter(config(REMOTE + "/v1/traces")))
    assert _create_exporter(config(LOOPBACK + "/v1/traces")) is not None
    monkeypatch.setenv(ALLOW_INSECURE_HTTP_ENV, "1")
    assert _create_exporter(config(REMOTE + "/v1/traces")) is not None


def test_the_evals_futureagi_exporter_reads_the_keys_and_base_url_from_the_environment(monkeypatch):
    pytest.importorskip("opentelemetry.exporter.otlp.proto.http.trace_exporter")
    from fi.evals.otel._tracer_factories import _create_exporter
    from fi.evals.otel.config import ExporterConfig, ExporterType

    monkeypatch.setenv("FI_API_KEY", "key-not-a-secret")
    monkeypatch.setenv("FI_SECRET_KEY", "secret-not-a-secret")
    monkeypatch.setenv("FI_BASE_URL", REMOTE)
    _refused(lambda: _create_exporter(ExporterConfig(type=ExporterType.FUTUREAGI)))
    monkeypatch.setenv("FI_BASE_URL", LOOPBACK)
    assert _create_exporter(ExporterConfig(type=ExporterType.FUTUREAGI)) is not None


# Path 6: the experiments collector export and the judge.
def _collector(base_url, endpoint=None):
    pytest.importorskip("opentelemetry.sdk.trace")
    from fi.experiments._redact import Redactor
    from fi.experiments._tracing import export

    return export.exporter_factory(
        base_url=base_url, api_key="key-not-a-secret", secret_key="secret-not-a-secret", project="p",
        run_name="r", run_id="i", redactor=Redactor(), _endpoint=endpoint)


def test_the_experiments_collector_export(monkeypatch):
    _refused(lambda: _collector(REMOTE))
    _collector(LOOPBACK)
    _collector("https://api.example.test")
    monkeypatch.setenv(ALLOW_INSECURE_HTTP_ENV, "1")
    _collector(REMOTE)


def test_the_collector_error_names_the_collector_setting():
    assert "FI_COLLECTOR_ENDPOINT" in str(_refused(lambda: _collector(REMOTE)))


def _judge_post(url):
    from fi.experiments.evaluators import _judge_http

    seen = []

    def handler(request):
        seen.append(request)
        return httpx.Response(200, json={"ok": True})

    async def run():
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http:
            return await _judge_http.post(http, url, {"m": 1}, "key-not-a-secret")

    return run, seen


def test_the_judge_request(monkeypatch):
    run, seen = _judge_post(REMOTE + "/v1/chat/completions")
    with pytest.raises(ConfigurationError) as caught:
        asyncio.run(run())
    assert "OPENAI_BASE_URL" in str(caught.value) and ALLOW_INSECURE_HTTP_ENV in str(caught.value) and seen == []
    run, seen = _judge_post(LOOPBACK + "/v1/chat/completions")
    asyncio.run(run())
    assert len(seen) == 1
    monkeypatch.setenv(ALLOW_INSECURE_HTTP_ENV, "1")
    run, seen = _judge_post(REMOTE + "/v1/chat/completions")
    asyncio.run(run())
    assert len(seen) == 1
