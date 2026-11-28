"""``Guardrails`` with a ``turing`` model raises ``fi.errors.MissingAuthError`` for a missing key pair.

The turing backend takes the API key and secret key as one pair. One key given without the other,
an empty key, or no pair in the arguments, the environment or the saved login raises
``MissingAuthError`` (an ``fi.errors.AuthError``) from the ``Guardrails`` constructor, before any
request. ``FI_BASE_URL`` points at a raw loopback sink that counts each connection and the marker
bytes it reads; the keys are planted markers generated here.
"""

from __future__ import annotations

import secrets
import socket
import socketserver
import threading
from typing import Dict, Iterator, List

import pytest

import fi.errors
from fi.evals.guardrails.base import Guardrails
from fi.evals.guardrails.config import GuardrailModel, GuardrailsConfig

TURING_MODELS = (GuardrailModel.TURING_FLASH, GuardrailModel.TURING_SAFETY)


class _Sink:
    """A raw loopback HTTP sink: keeps the bytes of every connection and answers ``{}``."""

    def __init__(self) -> None:
        self.raw: List[bytes] = []
        outer = self

        class Handler(socketserver.BaseRequestHandler):
            def handle(self) -> None:
                data = b""
                self.request.settimeout(5)
                try:
                    while b"\r\n\r\n" not in data:
                        chunk = self.request.recv(65536)
                        if not chunk:
                            break
                        data += chunk
                finally:
                    outer.raw.append(data)
                self.request.sendall(
                    b"HTTP/1.1 200 OK\r\nContent-Type: application/json\r\n"
                    b"Connection: close\r\nContent-Length: 2\r\n\r\n{}"
                )

        server_class = type("Server", (socketserver.ThreadingTCPServer,), {"daemon_threads": True})
        self._server = server_class(("127.0.0.1", 0), Handler)
        self.url = f"http://127.0.0.1:{self._server.server_address[1]}"
        threading.Thread(target=self._server.serve_forever, args=(0.05,), daemon=True).start()

    def marker_bytes(self, keys: Dict[str, str]) -> int:
        blob = b"".join(self.raw)
        return sum(blob.count(value.encode()) * len(value.encode()) for value in keys.values())

    def close(self) -> None:
        self._server.shutdown()
        self._server.server_close()


@pytest.fixture(name="keys")
def keys_fixture() -> Dict[str, str]:
    return {
        "api": f"MARKERKEY-A-{secrets.token_hex(12)}",
        "secret": f"MARKERSECRET-A-{secrets.token_hex(12)}",
    }


@pytest.fixture(name="sink")
def sink_fixture(monkeypatch: pytest.MonkeyPatch) -> Iterator[_Sink]:
    sink = _Sink()
    monkeypatch.setenv("FI_BASE_URL", sink.url)
    try:
        yield sink
    finally:
        sink.close()


def _guardrails(model: GuardrailModel, **kwargs: str) -> Guardrails:
    return Guardrails(config=GuardrailsConfig(models=[model]), **kwargs)


@pytest.mark.parametrize("model", TURING_MODELS, ids=lambda m: m.value)
@pytest.mark.parametrize(
    "given",
    [
        pytest.param({"fi_api_key": "api"}, id="api-key-only"),
        pytest.param({"fi_secret_key": "secret"}, id="secret-key-only"),
        pytest.param({"fi_api_key": "api", "fi_secret_key": ""}, id="empty-secret-key"),
    ],
)
def test_a_partial_pair_raises_missing_auth_error(model, given, keys, sink, monkeypatch) -> None:
    # A complete pair in the environment does not complete a pair the caller started.
    monkeypatch.setenv("FI_API_KEY", f"MARKERKEY-B-{secrets.token_hex(12)}")
    monkeypatch.setenv("FI_SECRET_KEY", f"MARKERSECRET-B-{secrets.token_hex(12)}")
    kwargs = {name: keys.get(value, value) for name, value in given.items()}

    with pytest.raises(fi.errors.MissingAuthError) as raised:
        _guardrails(model, **kwargs)

    assert isinstance(raised.value, fi.errors.AuthError)
    assert type(raised.value) is fi.errors.MissingAuthError
    assert raised.value.get_error_code() == "MISSING_FI_CLIENT_AUTHENTICATION"
    assert sink.raw == []
    assert sink.marker_bytes(keys) == 0


@pytest.mark.parametrize("model", TURING_MODELS, ids=lambda m: m.value)
def test_no_keys_anywhere_raises_missing_auth_error(model, keys, sink, monkeypatch) -> None:
    monkeypatch.delenv("FI_API_KEY", raising=False)
    monkeypatch.delenv("FI_SECRET_KEY", raising=False)

    with pytest.raises(fi.errors.MissingAuthError) as raised:
        _guardrails(model)

    assert raised.value.missing_api_key and raised.value.missing_secret_key
    assert sink.raw == []


def test_except_auth_error_catches_the_constructor_error(keys, sink) -> None:
    caught = None
    try:
        _guardrails(GuardrailModel.TURING_FLASH, fi_api_key=keys["api"])
    except fi.errors.AuthError as error:
        caught = error
    assert isinstance(caught, fi.errors.MissingAuthError)
    assert caught.missing_secret_key and not caught.missing_api_key
    assert sink.raw == []


def test_a_complete_pair_reaches_the_sink(keys, sink) -> None:
    """The control: with both keys given, screening sends a request to the sink."""
    guardrails = _guardrails(GuardrailModel.TURING_FLASH, fi_api_key=keys["api"], fi_secret_key=keys["secret"])
    try:
        guardrails.screen_input("a short message")
    except Exception:  # the sink answers an empty object; only the request matters here
        pass
    assert len(sink.raw) >= 1
    assert sink.marker_bytes(keys) > 0


def test_other_backend_construction_errors_keep_the_runtime_error(monkeypatch) -> None:
    """A backend that fails for a reason other than missing keys raises RuntimeError as documented."""
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    with pytest.raises(RuntimeError, match="Failed to create backend for openai-moderation"):
        _guardrails(GuardrailModel.OPENAI_MODERATION)


def test_missing_auth_error_resolves_without_a_socket(monkeypatch) -> None:
    """Building the turing backend with a partial pair opens no socket."""
    opened: List[object] = []
    real_connect = socket.socket.connect

    def counting_connect(self, address):
        opened.append(address)
        return real_connect(self, address)

    monkeypatch.setattr(socket.socket, "connect", counting_connect)
    with pytest.raises(fi.errors.AuthError):
        _guardrails(GuardrailModel.TURING_SAFETY, fi_secret_key="MARKERSECRET-C-" + secrets.token_hex(8))
    assert opened == []
