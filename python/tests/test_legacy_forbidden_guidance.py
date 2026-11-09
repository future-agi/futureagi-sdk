"""Knowledge-base forbidden responses retain guidance without changing catch contracts."""

import json
from unittest.mock import patch

import pytest
import requests

from fi.kb.client import KBResponseHandler, KnowledgeBase
from fi.utils.errors import InvalidAuthError, SDKException
from tests.core import _egress


@pytest.fixture(autouse=True)
def no_egress(monkeypatch, tmp_path):
    _egress.install(monkeypatch, tmp_path)
    yield
    _egress.assert_no_attempts()


@pytest.fixture
def handler():
    return KBResponseHandler


def response_for(status=403, payload=None, raw=None):
    response = requests.Response()
    response.status_code = status
    response.url = "https://example.test/model-hub/knowledge-base/"
    response.request = requests.Request("POST", response.url).prepare()
    response.encoding = "utf-8"
    response._content = raw if raw is not None else json.dumps(payload).encode("utf-8")
    return response


@pytest.mark.parametrize("field", ["detail", "message", "result"])
def test_forbidden_preserves_server_guidance_and_exception_type(handler, field):
    guidance = "Workspace access denied; ask an administrator."
    with pytest.raises(InvalidAuthError) as caught:
        handler.parse(response_for(payload={field: guidance}))

    assert type(caught.value) is InvalidAuthError
    assert guidance in str(caught.value)
    assert "403" in str(caught.value)
    assert "check your API key" not in str(caught.value)
    assert caught.value.get_error_code() == "INVALID_FI_CLIENT_AUTHENTICATION"


@pytest.mark.parametrize(
    "payload",
    [
        {"detail": " ", "message": "Request workspace access."},
        {"detail": {"code": "forbidden"}, "message": "Request workspace access."},
        {"detail": None, "message": False, "result": "Request workspace access."},
        {"detail": "Request workspace access.", "message": "Less specific guidance."},
    ],
)
def test_forbidden_selects_a_nonempty_text_explanation(handler, payload):
    with pytest.raises(InvalidAuthError) as caught:
        handler.parse(response_for(payload=payload))
    assert "Request workspace access." in str(caught.value)
    assert "Less specific guidance." not in str(caught.value)


@pytest.mark.parametrize(
    "raw",
    [
        b"", b"not JSON", b"<html>Forbidden</html>", b"null", b"[]",
        b'"Forbidden"', b"42", b"{}",
        b'{"detail": null, "message": false, "result": []}',
        b'{"detail": "   ", "message": "\\n\\t"}',
    ],
)
def test_forbidden_without_usable_json_has_permission_guidance(handler, raw):
    with pytest.raises(InvalidAuthError) as caught:
        handler.parse(response_for(raw=raw))
    message = str(caught.value)
    assert type(caught.value) is InvalidAuthError
    assert "403" in message
    assert "permissions" in message
    assert "administrator" in message
    assert "check your API key" not in message
    assert "<html>" not in message


def test_forbidden_explanation_is_bounded(handler):
    guidance = "Ask an administrator. " + "x" * 2000
    with pytest.raises(InvalidAuthError) as caught:
        handler.parse(response_for(payload={"detail": guidance}))
    message = caught.value.get_message()
    assert "Ask an administrator." in message
    assert len(message) <= 600
    assert message.endswith("...")
    assert "x" * 600 not in message


def test_forbidden_normalizes_explanation_whitespace(handler):
    with pytest.raises(InvalidAuthError) as caught:
        handler.parse(response_for(payload={"detail": "  Workspace denied.\n Ask\t an administrator.  "}))
    message = caught.value.get_message()
    assert "Workspace denied. Ask an administrator." in message
    assert "\n" not in message
    assert "\t" not in message


@pytest.mark.parametrize("status", [400, 401, 404, 429, 500])
def test_other_error_statuses_keep_their_type_and_guidance(handler, status):
    guidance = "Check the request and retry later."
    with pytest.raises(SDKException) as caught:
        handler.parse(response_for(status=status, payload={"detail": guidance}))
    assert type(caught.value) is SDKException
    assert guidance in str(caught.value)


def test_knowledge_base_create_keeps_forbidden_guidance():
    guidance = "Ask an administrator to enable knowledge-base access."
    client = KnowledgeBase(
        fi_api_key="synthetic-api",
        fi_secret_key="synthetic-secret",
        fi_base_url="https://example.test",
    )
    try:
        with patch("requests.post", return_value=response_for(payload={"detail": guidance})) as post:
            with pytest.raises(InvalidAuthError) as caught:
                client.create_kb("Example knowledge base")
        assert type(caught.value) is InvalidAuthError
        assert guidance in str(caught.value)
        assert post.call_count == 1
    finally:
        client.close()
