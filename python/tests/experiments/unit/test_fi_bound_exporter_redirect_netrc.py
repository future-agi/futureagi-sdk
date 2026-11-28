# ruff: noqa: F811
"""A Future AGI exporter with no keys follows a redirect, and reads ``.netrc`` on no hop.

The exporter for a Future AGI endpoint sends over a session of the SDK's own whose auth adds nothing, so its first
request gets no netrc credentials. With no keys in its headers it follows a redirect; the request for every later
hop, to another host, another port or the same origin, carries no netrc ``Authorization`` either. A ``.netrc`` in a
scratch home lists every loopback host the test uses, and recording listeners count the encoded credential bytes.
"""

import base64
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest

from tests.experiments.unit.test_fi_bound_exporter_headers import (  # noqa: F401
    AMBIENT_VARS,
    evals_exporter,
    export_spans,
)

LOGIN, PASSWORD = "netrc-login-r4l", "netrc-pass-r4l"
ENCODED = base64.b64encode(f"{LOGIN}:{PASSWORD}".encode()).decode()


class Origin:
    """A loopback HTTP listener. With ``location`` set it answers each POST with ``status`` and that ``Location``
    (a ``{port}`` in it names this listener's own port); otherwise it answers 200. Every request's raw header
    block is kept."""

    def __init__(self, host, status=None, location=None):
        self.raw = []
        outer = self

        class Handler(BaseHTTPRequestHandler):
            def do_POST(self):
                self.rfile.read(int(self.headers.get("Content-Length", "0")))
                outer.raw.append(str(self.headers))
                if outer.location and len(outer.raw) == 1:
                    self.send_response(outer.status)
                    self.send_header("Location", outer.location.format(port=outer.port))
                else:
                    self.send_response(200)
                self.send_header("Content-Length", "0")
                self.end_headers()

            # A 301, 302 or 303 turns the POST into a GET on the next hop.
            do_GET = do_POST

            def log_message(self, *args):
                pass

        self.status, self.location = status, location
        self.server = ThreadingHTTPServer((host, 0), Handler)
        self.host = host
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)

    @property
    def port(self):
        return self.server.server_address[1]

    @property
    def base(self):
        return f"http://{self.host}:{self.port}"

    def credential_bytes(self):
        return sum(block.count(ENCODED) for block in self.raw) * len(ENCODED)

    def __enter__(self):
        self.thread.start()
        return self

    def __exit__(self, *exc):
        self.server.shutdown()
        self.server.server_close()


def scratch_home(tmp_path, monkeypatch):
    """A home whose ``.netrc`` holds credentials for both loopback hosts; nothing else reads a netrc."""
    (tmp_path / ".netrc").write_text(
        "".join(f"machine {host} login {LOGIN} password {PASSWORD}\n" for host in ("127.0.0.1", "127.0.0.2"))
    )
    (tmp_path / ".netrc").chmod(0o600)
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.delenv("NETRC", raising=False)
    for name in (*AMBIENT_VARS, "FI_API_KEY", "FI_SECRET_KEY", "FI_TRACES_URL", "FI_GRPC_URL"):
        monkeypatch.delenv(name, raising=False)


STATUSES = [301, 302, 303, 307, 308]
# Where the redirect goes: another loopback host, another port on the first host, the first origin itself.
HOPS = ["other-host", "other-port", "same-origin"]


def run(kind, status, hop, monkeypatch):
    with Origin("127.0.0.2") as other, Origin("127.0.0.1") as other_port:
        location = {
            "other-host": other.base + "/v1/traces",
            "other-port": other_port.base + "/v1/traces",
            "same-origin": "http://127.0.0.1:{port}/second",
        }[hop]
        with Origin("127.0.0.1", status, location) as first:
            monkeypatch.setenv("FI_BASE_URL", first.base)
            export_spans(evals_exporter(first.base + "/tracer/v1/traces", None, kind=kind))
    return first, other, other_port


@pytest.mark.parametrize("hop", HOPS)
@pytest.mark.parametrize("status", STATUSES)
@pytest.mark.parametrize("kind", ["FUTUREAGI", "OTLP_HTTP"])
def test_the_futureagi_exporter_reads_netrc_on_no_redirect_hop(tmp_path, monkeypatch, kind, status, hop):
    scratch_home(tmp_path, monkeypatch)
    first, other, other_port = run(kind, status, hop, monkeypatch)
    followed = {"other-host": other, "other-port": other_port, "same-origin": first}[hop]
    # The redirect was followed: one request at the first origin, then one at the hop's target.
    assert len(first.raw) + len(other.raw) + len(other_port.raw) == 2
    assert followed.raw, "the redirect was not followed"
    assert [first.credential_bytes(), other.credential_bytes(), other_port.credential_bytes()] == [0, 0, 0]
    assert all("authorization" not in block.lower() for o in (first, other, other_port) for block in o.raw)


def test_the_no_op_auth_is_marked_to_skip_netrc():
    from fi._otlp_headers import futureagi_session

    from fi._core.requests_session import LoopbackDirectSession

    assert futureagi_session().auth.skips_netrc is True
    # A session of the SDK's for another backend has no such auth: requests reads .netrc for it.
    assert LoopbackDirectSession().auth is None


@pytest.mark.parametrize("location", ["bracketed-ipv4", "latin-1-byte"])
@pytest.mark.parametrize("kind", ["FUTUREAGI", "OTLP_HTTP"])
def test_a_keyed_export_answered_with_an_unreadable_location_is_a_failed_export(tmp_path, monkeypatch, kind, location):
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import SimpleSpanProcessor, SpanExportResult

    scratch_home(tmp_path, monkeypatch)
    monkeypatch.setenv("FI_API_KEY", "fi-key-value")
    monkeypatch.setenv("FI_SECRET_KEY", "fi-secret-value")
    with Origin("127.0.0.2") as other:
        written = {"bracketed-ipv4": f"http://[127.0.0.2]:{other.port}/v1/traces", "latin-1-byte": "/\xe9"}[location]
        with Origin("127.0.0.1", 307, written) as first:
            monkeypatch.setenv("FI_BASE_URL", first.base)
            exporter = evals_exporter(first.base + "/tracer/v1/traces", None, kind=kind)
            outcomes = []
            original = exporter.export

            def export(spans):
                try:
                    outcomes.append(original(spans))
                except Exception as error:  # the processors log what an exporter raises
                    outcomes.append(error)
                    raise
                return outcomes[-1]

            exporter.export = export
            provider = TracerProvider()
            provider.add_span_processor(SimpleSpanProcessor(exporter))
            provider.get_tracer("netrc-test").start_span("one").end()
            provider.shutdown()
    assert outcomes == [SpanExportResult.FAILURE]
    assert len(first.raw) == 1 and other.raw == []
