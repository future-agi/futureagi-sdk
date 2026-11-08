"""A loopback-only HTTP bridge to the SDK's MockAgentCC for real framework calls."""

import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest
from fi.gateway.testing import MockAgentCC, mock_completion


@pytest.fixture
def gateway(monkeypatch):
    """Capture the wire request, then serve an SDK mock completion."""
    mock = MockAgentCC()
    mock.chat.completions.respond_with(mock_completion("Hello from the mock gateway."))
    requests = []

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_args):
            pass

        def do_POST(self):
            body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            requests.append((self.path, dict(self.headers), body))
            if self.path != "/v1/chat/completions":
                self.send_error(404)
                return
            if self.headers.get("Authorization") != "Bearer mock-personal-gateway-key":
                self.send_error(401)
                return
            answer = mock.chat.completions.create(**body).model_dump(mode="json")
            encoded = json.dumps(answer).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(encoded)))
            self.end_headers()
            self.wfile.write(encoded)

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    worker = threading.Thread(target=server.serve_forever, daemon=True)
    worker.start()
    for name in (
        "FI_API_KEY", "FI_SECRET_KEY", "AGENTCC_API_KEY", "AGENTCC_BASE_URL",
        "OPENAI_ORG_ID", "OPENAI_PROJECT_ID", "LANGCHAIN_API_KEY", "LANGSMITH_API_KEY",
    ):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("FI_GATEWAY_API_KEY", "mock-personal-gateway-key")
    monkeypatch.setenv("FI_GATEWAY_BASE_URL", f"http://127.0.0.1:{server.server_port}/v1/")
    monkeypatch.setenv("FI_GATEWAY_MODEL", "example-model")
    monkeypatch.setenv("OPENAI_API_KEY", "unused-provider-key")
    monkeypatch.setenv("OPENAI_BASE_URL", "https://provider.invalid/v1")
    monkeypatch.setenv("LANGCHAIN_TRACING_V2", "false")
    monkeypatch.setenv("LANGSMITH_TRACING", "false")
    monkeypatch.setenv("NO_PROXY", "127.0.0.1,localhost")
    try:
        yield mock, requests
    finally:
        server.shutdown()
        server.server_close()
        worker.join(timeout=5)
