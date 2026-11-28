"""``health_check`` and ``check_valid_key`` skip the environment proxy for a loopback gateway and nothing else: the
trust the environment names (``SSL_CERT_FILE``) still applies, so an ``https://`` gateway on this machine whose
certificate only that file trusts is reachable, and its key reaches it and not the proxy.

The certificate is generated here with the ``openssl`` command line tool, for ``localhost`` and ``127.0.0.1``.
"""

from __future__ import annotations

import shutil
import ssl
import subprocess
import threading
import warnings
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest

from tests.platform.test_env_proxy import _proxy_url, servers_fixture  # noqa: F401  (fixture)

pytestmark = pytest.mark.skipif(shutil.which("openssl") is None, reason="the openssl command line tool is needed")


@pytest.fixture(name="tls_gateway")
def tls_gateway_fixture(tmp_path):
    cert, key = tmp_path / "cert.pem", tmp_path / "key.pem"
    subprocess.run(
        ["openssl", "req", "-x509", "-newkey", "rsa:2048", "-nodes", "-keyout", str(key), "-out", str(cert),
         "-days", "2", "-subj", "/CN=localhost", "-addext", "subjectAltName=DNS:localhost,IP:127.0.0.1"],
        check=True, capture_output=True,
    )
    seen: list[tuple[str, str]] = []

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            seen.append((self.path, self.headers.get("authorization", "")))
            body = b"{}"
            self.send_response(200)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *args):
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain(str(cert), str(key))
    server.socket = context.wrap_socket(server.socket, server_side=True)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    yield server.server_address[1], cert, seen
    server.shutdown()
    server.server_close()


@pytest.mark.parametrize("host", ["127.0.0.1", "localhost"])
def test_an_https_loopback_gateway_trusted_through_ssl_cert_file_is_reached_without_the_proxy(
    servers, tls_gateway, monkeypatch, host,
):
    from fi.gateway import check_valid_key, health_check

    proxy, _sink = servers
    port, cert, seen = tls_gateway
    monkeypatch.delenv("SSL_CERT_DIR", raising=False)
    monkeypatch.setenv("SSL_CERT_FILE", str(cert))
    for name in ("HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY"):
        monkeypatch.setenv(name, _proxy_url(proxy))
    base_url = f"https://{host}:{port}"
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        health = health_check(api_key="sk-test-gateway-key", base_url=base_url)
        valid = check_valid_key("sk-test-gateway-key", base_url)
    assert health["status"] == "ok", health
    assert valid is True
    assert proxy.requests == []
    assert seen == [("/healthz", "Bearer sk-test-gateway-key"), ("/v1/models", "Bearer sk-test-gateway-key")]


def test_without_that_trust_the_https_loopback_gateway_is_refused(servers, tls_gateway, monkeypatch):
    from fi.gateway import check_valid_key, health_check

    proxy, _sink = servers
    port, _cert, seen = tls_gateway
    monkeypatch.delenv("SSL_CERT_FILE", raising=False)
    monkeypatch.delenv("SSL_CERT_DIR", raising=False)
    monkeypatch.setenv("HTTPS_PROXY", _proxy_url(proxy))
    assert health_check(api_key="sk-test-gateway-key", base_url=f"https://127.0.0.1:{port}")["status"] == "error"
    assert check_valid_key("sk-test-gateway-key", f"https://127.0.0.1:{port}") is False
    assert proxy.requests == [] and seen == []
