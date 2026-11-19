"""Real localhost OTLP requests during uploaded runs; platform CRUD uses the contract stand-in.

The collector is separate from Django: tfc/urls.py:67-69 and tracer/urls.py:245-249
remove trace ingestion routes in favor of fi-collector. No provider or remote service is used.
"""

from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import io
import json
import socket
import threading
from types import SimpleNamespace
import warnings

import httpx
import pytest

from fi import experiments
from fi._cli import doctor
from fi.experiments._cli import routes
from fi.experiments.errors import ExperimentError
from tests.experiments.unit.contract_server import ContractServer, client_for

PATH = "/tracer/v1/traces"
SECRET = "s-test-1234"


@contextmanager
def collector(status):
    """Only bind loopback; a bound, non-listening socket gives deterministic refusal."""
    requests = []
    if status == "refused":
        with socket.socket() as sock:
            sock.bind(("127.0.0.1", 0))
            yield f"http://127.0.0.1:{sock.getsockname()[1]}", requests
        return

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            body = self.rfile.read(int(self.headers.get("Content-Length", "0")))
            requests.append(("POST", self.path, body))
            self.answer()

        def do_GET(self):
            requests.append(("GET", self.path, b""))
            self.answer()

        def answer(self):
            reply = status(len(requests)) if callable(status) else status
            # Even an error body echoing a credential must never appear in logs/warnings.
            payload = b"" if reply == 200 else json.dumps({"detail": SECRET}).encode()
            self.send_response(reply)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)

        def log_message(self, *args):
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}", requests
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


@pytest.fixture(autouse=True)
def bounded_export(monkeypatch):
    monkeypatch.setenv("OTEL_EXPORTER_OTLP_TRACES_TIMEOUT", "0.2")
    monkeypatch.setenv("NO_PROXY", "127.0.0.1,localhost")
    for name in ("FI_EXTRA_HEADERS", "HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY"):
        monkeypatch.delenv(name, raising=False)


def run_on(base, server, **kwargs):
    return experiments.run(
        experiments.dataset([{"q": "one"}, {"q": "two"}], name="collector-test"),
        lambda row: "answer", client=client_for(server, base_url=base),
        instrument=False, progress=False, **kwargs,
    )


@pytest.mark.parametrize("status", [404, 405, 500, 503, "refused"])
def test_uploaded_run_cannot_succeed_after_otlp_failure(status, caplog):
    server = ContractServer()
    with collector(status) as (base, requests), warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        with pytest.raises(ExperimentError, match="trace export") as error:
            run_on(base, server)
    exc = error.value
    assert type(exc).__name__ == "TraceExportError"
    assert exc.get_error_code() == "TRACE_EXPORT_FAILED" and exc.exit_code == 3
    assert exc.endpoint == base + PATH
    assert exc.status_code == (None if status == "refused" else status)
    assert ("connection" if status == "refused" else f"HTTP {status}") in str(exc)
    assert exc.to_json()["endpoint"] == base + PATH
    assert exc.to_json()["status_code"] == exc.status_code
    # A trace-export failure is not a failed task or an item-ingest failure.
    [stored] = server.runs.values()
    assert len(stored["items"]) == 2
    assert all(item["status"] == "completed" for item in stored["items"].values())
    assert exc.run_id in server.runs
    export_warnings = [w for w in caught if type(w.message).__name__ == "TraceExportWarning"]
    assert len(export_warnings) == 1, "exactly one warning per run, even with progress=False"
    assert base + PATH in str(export_warnings[0].message)
    assert ("connection" if status == "refused" else f"HTTP {status}") in str(export_warnings[0].message)
    assert SECRET not in str(exc) + str(export_warnings[0].message) + caplog.text
    if status != "refused":
        assert requests and all(m == "POST" and p == PATH and b for m, p, b in requests)


def test_successful_export_has_no_failure_warning():
    with collector(200) as (base, requests), warnings.catch_warnings(record=True) as caught:
        result = run_on(base, ContractServer())
    assert result.status == "completed"
    assert requests and all(m == "POST" and p == PATH and b for m, p, b in requests)
    assert not [w for w in caught if type(w.message).__name__ == "TraceExportWarning"]


@pytest.mark.parametrize("upload,trace", [(True, False), (False, True)])
def test_disabled_export_does_not_contact_collector(upload, trace):
    with collector(404) as (base, requests):
        result = run_on(base, ContractServer(), upload=upload, trace=trace)
    assert result.status == ("completed" if upload else "no_upload")
    assert requests == []


def route_client(base):
    """Only the collector check goes over a real socket; all other doctor checks are local."""
    transport = httpx.HTTPTransport()

    def handle(request):
        if request.url.path == PATH:
            return transport.handle_request(request)
        return httpx.Response(404, json={"detail": "object not found"})

    client = client_for(ContractServer(), base_url=base)
    client.generated_client.get_httpx_client()._transport = httpx.MockTransport(handle)
    return client, transport


@pytest.mark.parametrize("status", [404, 500, 503, "refused"])
def test_doctor_reports_collector_response_or_inconclusive_transport(status):
    with collector(status) as (base, requests):
        client, transport = route_client(base)
        try:
            lines = routes.route_lines(client)
        finally:
            transport.close()
    matching = [line for line in lines if "collector" in line.lower()]
    assert len(matching) == 1, "doctor must check the collector route used by uploaded runs"
    line = matching[0]
    # No HTTP response is inconclusive, as for the five sibling platform routes.
    assert isinstance(line, doctor.Problem) is (status != "refused")
    assert PATH in line
    assert ("MISSING" if status == 404 else "could not check" if status == "refused" else f"HTTP {status}") in line
    if status != "refused":
        assert requests == [("GET", PATH, b"")], "doctor must not send spans"


def test_doctor_get_405_does_not_claim_post_export_works():
    with collector(405) as (base, requests):
        client, transport = route_client(base)
        try:
            lines = routes.route_lines(client)
        finally:
            transport.close()
    matching = [line for line in lines if "collector" in line.lower()]
    assert len(matching) == 1
    assert "POST not checked" in matching[0] and "HTTP 405" in matching[0]
    assert not isinstance(matching[0], doctor.Problem)
    assert requests == [("GET", PATH, b"")]


def test_doctor_missing_collector_is_setup_exit_and_json_problem(monkeypatch):
    from fi._cli import auth, ownership

    monkeypatch.setattr(auth, "who_info", lambda args: {"line": "local fixture"})
    monkeypatch.setattr(ownership, "section", lambda args: [])
    out = io.StringIO()
    with collector(404) as (base, requests):
        client, transport = route_client(base)
        monkeypatch.setattr(doctor, "_SECTIONS", [("Experiments", lambda args: routes.route_lines(client))])
        try:
            code = doctor.run_doctor(SimpleNamespace(stdout=out, json=True, offline=False))
        finally:
            transport.close()
    assert code == 3, "missing collector must not be a successful doctor diagnosis"
    section = json.loads(out.getvalue())["sections"]["Experiments"]
    assert any(PATH in problem and "MISSING" in problem for problem in section["problems"])
