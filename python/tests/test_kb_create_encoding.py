"""Check the body Requests would send, without opening a connection."""

import json
from email.parser import BytesParser
from email.policy import default

import pytest
import requests

from fi.kb import KnowledgeBase


@pytest.fixture
def kb_http(monkeypatch):
    client = KnowledgeBase(
        fi_api_key="fixture-key", fi_secret_key="fixture-secret", fi_base_url="http://127.0.0.1:9"
    )
    sent = []

    def send(session, request, **kwargs):
        sent.append(request)
        assert request.method == "POST"
        assert request.url == "http://127.0.0.1:9/model-hub/knowledge-base/"
        assert request.headers["Accept"] == "application/json"
        assert request.headers["X-Api-Key"] == "fixture-key"
        assert request.headers["X-Secret-Key"] == "fixture-secret"
        assert kwargs["timeout"] == 300
        response = requests.Response()
        response.request = request
        response.url = request.url
        response.status_code = 200
        response._content = json.dumps({
            "status": True,
            "result": {
                "kb_id": "00000000-0000-4000-8000-000000000003",
                "kb_name": "Fixture KB",
                "detail": "Knowledge base created",
                "file_ids": [],
            },
        }).encode()
        return response

    monkeypatch.setattr(requests.Session, "send", send)
    return client, sent


@pytest.mark.parametrize(("options", "expected_name"), [
    ({"name": "Empty KB"}, "Empty KB"),
    ({"file_paths": []}, "Unnamed KB"),
])
def test_create_without_files_encodes_json(kb_http, options, expected_name):
    client, sent = kb_http
    assert client.create_kb(**options) is client
    (request,) = sent
    assert request.headers["Content-Type"] == "application/json"
    assert json.loads(request.body) == {"name": expected_name}
    assert client.kb.name == "Fixture KB"


def test_create_with_files_encodes_multipart(kb_http, tmp_path):
    client, sent = kb_http
    paths = [tmp_path / "one.txt", tmp_path / "two.txt"]
    for path in paths:
        path.write_bytes(path.stem.encode())

    assert client.create_kb("With files", [str(path) for path in paths]) is client
    (request,) = sent
    content_type = request.headers["Content-Type"]
    assert content_type.startswith("multipart/form-data; boundary=")
    message = BytesParser(policy=default).parsebytes(
        f"Content-Type: {content_type}\r\n\r\n".encode() + request.body
    )
    assert [
        (
            part.get_param("name", header="Content-Disposition"),
            part.get_filename(),
            part.get_content_type(),
            part.get_payload(decode=True),
        )
        for part in message.iter_parts()
    ] == [
        ("name", None, "text/plain", b"With files"),
        ("file", "one.txt", "text/plain", b"one"),
        ("file", "two.txt", "text/plain", b"two"),
    ]
