import pytest
from unittest.mock import MagicMock, patch

from fi.kb.client import KnowledgeBase
from fi.kb.types import KnowledgeBaseConfig


@pytest.fixture(autouse=True)
def _opt_in_to_plain_http(monkeypatch):
    """The tests send to ``http://example.test``, a host that is not loopback."""
    monkeypatch.setenv("FI_ALLOW_INSECURE_HTTP", "1")


def _response(method: str, url: str, result: dict):
    response = MagicMock()
    response.status_code = 200
    response.url = url
    response.request.method = method
    response.json.return_value = {"status": True, "result": result}
    return response


def test_create_kb_without_files_uses_json_body():
    client = KnowledgeBase(
        fi_api_key="api-key",
        fi_secret_key="secret-key",
        fi_base_url="https://example.test",
    )

    with patch("fi._core.requests_session.LoopbackDirectSession.request") as post:
        post.return_value = _response(
            "POST",
            "https://example.test/model-hub/knowledge-base/",
            {
                "kb_id": "00000000-0000-0000-0000-000000000001",
                "kb_name": "Empty KB",
                "file_ids": [],
            },
        )

        client.create_kb("Empty KB")

    kwargs = post.call_args.kwargs
    assert kwargs["json"] == {"name": "Empty KB"}
    assert "data" not in kwargs
    assert "files" not in kwargs


def test_update_kb_without_files_uses_json_body():
    client = KnowledgeBase(
        fi_api_key="api-key",
        fi_secret_key="secret-key",
        fi_base_url="https://example.test",
    )
    client.kb = KnowledgeBaseConfig(
        id="00000000-0000-0000-0000-000000000001",
        name="Old KB",
        files=[],
    )

    with patch("fi._core.requests_session.LoopbackDirectSession.request") as patch_request:
        patch_request.return_value = _response(
            "PATCH",
            "https://example.test/model-hub/knowledge-base/",
            {"id": "00000000-0000-0000-0000-000000000001", "name": "New KB", "files": []},
        )

        client.update_kb("Old KB", new_name="New KB")

    kwargs = patch_request.call_args.kwargs
    assert kwargs["json"] == {
        "kb_id": "00000000-0000-0000-0000-000000000001",
        "name": "New KB",
    }
    assert "data" not in kwargs
    assert "files" not in kwargs


def test_list_kbs_returns_configs():
    client = KnowledgeBase(
        fi_api_key="api-key",
        fi_secret_key="secret-key",
        fi_base_url="https://example.test",
    )
    response = MagicMock()
    response.status_code = 200
    response.url = "https://example.test/model-hub/knowledge-base/list/"
    response.request.method = "GET"
    response.json.return_value = {
        "status": True,
        "result": {
            "table_data": [
                {
                    "id": "00000000-0000-0000-0000-000000000001",
                    "name": "KB",
                    "status": "Completed",
                    "files": [],
                }
            ]
        },
    }

    with patch.object(client, "request", return_value=response.json.return_value) as request:
        result = client.list_kbs("KB")

    config = request.call_args.kwargs["config"]
    assert config.params == {"search": "KB"}
    assert result[0].name == "KB"
    assert result[0].status == "Completed"
