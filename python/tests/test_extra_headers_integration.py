"""FI_EXTRA_HEADERS end to end, against two local servers on 127.0.0.1 (never any other host).

``platform`` stands in for the Future AGI base URL and ``other`` for everything else (a judge model, a
redirect target). Each test sends real requests through the SDK's own clients and checks what the
servers received: the extra header reaches every request type to the platform, never ``other``, and
its value never shows in logs, errors, ``--json`` output, journals or exported traces.
"""

from __future__ import annotations

import asyncio
import gzip
import json
import logging
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest

from fi._extra_headers import ENV_VAR, ExtraHeadersError

# a made-up value, low entropy on purpose (never a real token)
TOKEN = "fake-identity-token-" + "x" * 12
VALUE = f"Bearer {TOKEN}"
SETTING = f"Proxy-Authorization={VALUE};X-Team=team-env-value"
DS = "00000000-0000-0000-0000-0000000000d5"


class Server:
    """A local HTTP server that records every request and answers from a small route table."""

    def __init__(self) -> None:
        self.requests: list[dict] = []
        self.routes: dict[str, tuple[int, dict, bytes]] = {}
        recorder = self

        class Handler(BaseHTTPRequestHandler):
            protocol_version = "HTTP/1.1"

            def _handle(self) -> None:
                length = int(self.headers.get("Content-Length") or 0)
                body = self.rfile.read(length) if length else b""
                if self.headers.get("Content-Encoding") == "gzip":
                    body = gzip.decompress(body)
                recorder.requests.append({"method": self.command, "path": self.path, "body": body,
                                          "headers": {k.lower(): v for k, v in self.headers.items()}})
                path = self.path.split("?")[0]
                status, headers, payload = recorder.routes.get(path, (200, {}, b"{}"))
                self.send_response(status)
                for name, value in {"Content-Type": "application/json", **headers}.items():
                    self.send_header(name, value)
                self.send_header("Content-Length", str(len(payload)))
                self.end_headers()
                self.wfile.write(payload)

            do_GET = do_POST = do_PUT = do_PATCH = do_DELETE = _handle

            def log_message(self, *args) -> None:
                pass

        self.httpd = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.url = f"http://127.0.0.1:{self.httpd.server_address[1]}"
        self.thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
        self.thread.start()

    def route(self, path: str, status: int = 200, payload: object = None, **headers: str) -> None:
        self.routes[path] = (status, headers, json.dumps({} if payload is None else payload).encode())

    def seen(self, path: str) -> list[dict]:
        return [r for r in self.requests if r["path"].split("?")[0] == path]

    def close(self) -> None:
        self.httpd.shutdown()
        self.httpd.server_close()


def carries(request: dict) -> bool:
    h = request["headers"]
    return h.get("proxy-authorization") == VALUE and h.get("x-team") == "team-env-value"


def carries_none(request: dict) -> bool:
    h = request["headers"]
    return "proxy-authorization" not in h and "x-team" not in h


@pytest.fixture
def servers(monkeypatch, tmp_path):
    platform, other = Server(), Server()
    monkeypatch.setenv(ENV_VAR, SETTING)
    monkeypatch.setenv("FI_BASE_URL", platform.url)
    monkeypatch.setenv("FI_API_KEY", "ak-test")
    monkeypatch.setenv("FI_SECRET_KEY", "sk-test")
    monkeypatch.setenv("FI_LOGIN_FILE", str(tmp_path / "no-login.json"))
    monkeypatch.setenv("FI_RUN_DIR", str(tmp_path / "runs"))
    yield platform, other
    platform.close()
    other.close()


@pytest.fixture
def logs(caplog):
    caplog.set_level(logging.DEBUG)
    yield caplog
    assert TOKEN not in caplog.text and "team-env-value" not in caplog.text


def test_http_client_session_and_its_redirects(servers, logs):
    from fi.api.auth import APIKeyAuth
    from fi.api.types import HttpMethod, RequestConfig

    platform, other = servers
    platform.route("/redir-same", 302, Location=f"{platform.url}/landed")
    platform.route("/redir-off", 302, Location=f"{other.url}/landing")
    client = APIKeyAuth()
    try:
        for url in (f"{platform.url}/model-hub/x", f"{other.url}/elsewhere", f"{platform.url}/redir-same",
                    f"{platform.url}/redir-off"):
            client.request(RequestConfig(method=HttpMethod.GET, url=url, retry_attempts=1))
    finally:
        client.close()
    assert carries(platform.seen("/model-hub/x")[0])
    assert carries_none(other.seen("/elsewhere")[0])
    # requests drops Proxy-Authorization on every redirect; the SDK puts it back under the base URL ...
    assert carries(platform.seen("/redir-same")[0]) and carries(platform.seen("/landed")[0])
    # ... and strips every extra header on a redirect anywhere else
    assert carries(platform.seen("/redir-off")[0]) and carries_none(other.seen("/landing")[0])


def test_knowledge_base_file_upload_path(servers, logs):
    from fi.kb.client import KnowledgeBase

    platform, _ = servers
    platform.route("/model-hub/knowledge-base/", 200, {"result": {"kb_id": DS, "kb_name": "kb", "file_ids": []}})
    KnowledgeBase().create_kb("kb")
    assert carries(platform.seen("/model-hub/knowledge-base/")[0])


def test_typed_clients_sync_and_async(servers, logs):
    from fi.futureagi_async_client import AsyncFutureAGIClient
    from fi.futureagi_client import FutureAGIClient

    platform, other = servers
    with FutureAGIClient() as client:
        http = client.generated_client.get_httpx_client()
        http.get("/model-hub/typed")
        http.get(f"{other.url}/absolute")  # an absolute URL off the base URL, through the same client
    assert carries(platform.seen("/model-hub/typed")[0]) and carries_none(other.seen("/absolute")[0])

    async def go():
        aclient = AsyncFutureAGIClient(extra_headers={"X-Team": "argument-wins"})
        try:
            await aclient.request("GET", "/model-hub/async")
        finally:
            await aclient.generated_client.get_async_httpx_client().aclose()

    asyncio.run(go())
    got = platform.seen("/model-hub/async")[0]["headers"]
    assert got["proxy-authorization"] == VALUE and got["x-team"] == "argument-wins"


def test_experiment_upload_and_read_paths_and_trace_export(servers, logs):
    pytest.importorskip("fi.experiments._upload")
    from fi.experiments._server_dataset import find_dataset
    from fi.experiments._server_rows import list_versions
    from fi.experiments._upload import create_body, create_run
    from fi.futureagi_client import FutureAGIClient

    platform, _ = servers
    client = FutureAGIClient()
    assert find_dataset(client, "rows") is None  # read: GET .../get-datasets-names/ (or the like)
    try:
        list_versions(client, DS)  # read: the dataset's versions
    except Exception:
        pass  # the stand-in answers {}; only the request matters here
    body = create_body(run_id="11111111-1111-1111-1111-111111111111", dataset_version_id=DS,
                       identities=[("22222222-2222-2222-2222-222222222222", 0)], metric_ids=[], experiment_id=None, model_config={}, metadata={})
    with pytest.raises(Exception):
        create_run(client, body, sleep=lambda s: None)  # upload: the run create (the stand-in's {} is no header)
    assert len(platform.requests) >= 3 and all(carries(r) for r in platform.requests)

    pytest.importorskip("fi_instrumentation.otel")
    from fi.experiments._redact import Redactor
    from fi.experiments._upload_session import UploadSession

    session = UploadSession(client=client, dataset=None)  # type: ignore[arg-type]
    provider = session.exporter_factory(project="p", run_name="r", run_id="id", redactor=Redactor())()
    with provider.get_tracer("t").start_as_current_span("trial", attributes={"note": f"saw {TOKEN}"}):
        pass
    provider.force_flush()
    provider.shutdown()
    export = platform.seen("/tracer/v1/traces")
    assert export and carries(export[0])
    assert TOKEN.encode() not in export[0]["body"] and b"trial" in export[0]["body"]


def test_webhooks_clients(servers, logs):
    from fi.webhooks import AsyncWebhooks, Webhooks

    platform, _ = servers
    with Webhooks() as wh:
        wh.event_types()

    async def go():
        async with AsyncWebhooks() as awh:
            await awh.egress_ips()

    asyncio.run(go())
    assert len(platform.requests) == 2 and all(carries(r) for r in platform.requests)


def test_cli_doctor_and_webhooks_with_json(servers, logs, capsys):
    from fi._cli.main import main

    platform, _ = servers
    platform.route("/accounts/user-info/", 200, {"result": {"email": "tester@team.test", "id": 1}})
    assert main(["doctor"]) == 0
    assert main(["doctor", "--json"]) == 0
    main(["webhooks", "ls", "--json"])
    out = capsys.readouterr()
    assert TOKEN not in out.out + out.err and "team-env-value" not in out.out + out.err
    assert "Headers    Proxy-Authorization, X-Team" in out.out and "tester@team.test" in out.out
    assert len(platform.seen("/accounts/user-info/")) == 2
    assert len(platform.requests) >= 3 and all(carries(r) for r in platform.requests)


def test_a_malformed_setting_fails_with_no_value_in_errors_or_json(servers, logs, monkeypatch, capsys):
    from fi._cli.main import main
    from fi.futureagi_client import FutureAGIClient

    platform, _ = servers
    monkeypatch.setenv(ENV_VAR, f"Proxy-Authorization {VALUE}")
    with pytest.raises(ExtraHeadersError) as info:
        FutureAGIClient().generated_client.get_httpx_client().get("/model-hub/x")
    assert ENV_VAR in str(info.value) and TOKEN not in str(info.value) and TOKEN not in repr(info.value)
    assert main(["webhooks", "ls", "--json"]) == 3
    doc = json.loads(capsys.readouterr().out)
    assert doc["error"]["code"] == "EXTRA_HEADERS_INVALID" and ENV_VAR in doc["error"]["message"]
    assert main(["doctor", "--json"]) == 3
    raw = capsys.readouterr().out
    assert TOKEN not in raw and json.loads(raw)["who"]["error"] == "extra headers"
    monkeypatch.setenv(ENV_VAR, f"X-Api-Key={TOKEN}")
    assert main(["webhooks", "ls"]) == 3
    err = capsys.readouterr().err
    assert "FI_EXTRA_HEADERS entry 1: X-Api-Key cannot be set" in err and TOKEN not in err
    assert platform.requests == []  # nothing was sent with a malformed setting


def test_judge_calls_never_get_the_platform_headers_and_journals_hold_no_value(servers, logs, monkeypatch, tmp_path):
    pytest.importorskip("opentelemetry.sdk")
    from fi import experiments
    from fi.experiments.evaluators import judge

    platform, other = servers
    monkeypatch.setenv("OPENAI_API_KEY", "judge-key-for-tests")
    answer = {"choices": [{"message": {"content": "{}"}, "finish_reason": "stop"}],
              "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2}}
    other.route("/v1/chat/completions", 200, answer)
    rows = experiments.dataset([{"input": "2+2", "expected": "4"}], name="xh-judge")
    experiments.run(rows, lambda row: "4", [judge("Is the OUTPUT correct?", base_url=f"{other.url}/v1")],
                    upload=False, trace=False, progress=False)
    calls = other.seen("/v1/chat/completions")
    assert calls and all(carries_none(c) for c in calls)
    assert all(c["headers"].get("authorization") == "Bearer judge-key-for-tests" for c in calls)
    assert platform.requests == []  # a local run sends nothing to the platform
    files = [p for p in Path(tmp_path / "runs").rglob("*") if p.is_file()]
    assert files, "the run wrote no journal"
    for path in files:
        text = path.read_bytes()
        assert TOKEN.encode() not in text and b"team-env-value" not in text, path
