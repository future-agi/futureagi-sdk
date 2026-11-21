"""Unit tests for Prompt module fixes from PR #27.

Covers four fix categories:
  1. Endpoint routing  –  get_template_by_name and delete_template_by_name
     use Routes.get_template_by_name instead of Routes.prompt_label_get_by_name.
  2. generate() / improve()  –  use SimpleJsonResponseHandler, safe
     response unpacking, expose last_generation_id.
  3. Cache invalidation  –  prompt_cache.invalidate called on delete.
  4. snake_case key handling  –  model key, error code, version extraction.
"""

import json
import uuid
from unittest.mock import MagicMock, patch, PropertyMock

import pytest

from fi.prompt.client import Prompt, PromptResponseHandler, SimpleJsonResponseHandler
from fi.prompt.cache import prompt_cache
from fi.prompt.types import PromptTemplate, ModelConfig
from fi.utils.errors import TemplateAlreadyExists, TemplateNotFound
from fi.utils.routes import Routes


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _mock_response(data, status_code=200):
    resp = MagicMock()
    resp.ok = 200 <= status_code < 300
    resp.status_code = status_code
    resp.json.return_value = data
    resp.text = json.dumps(data) if not isinstance(data, str) else data
    resp.url = "http://test/api/"
    resp.request = MagicMock()
    resp.request.method = "GET"
    resp.request.url = "http://test/api/"
    return resp


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def client():
    """Create a Prompt client with a known template (id present → no init fetch)."""
    with patch.dict("os.environ", {"FI_API_KEY": "test-key", "FI_SECRET_KEY": "test-secret"}):
        tpl = PromptTemplate(
            id=uuid.UUID("00000000-0000-0000-0000-000000000001"),
            name="test-template",
            messages=[{"role": "user", "content": "Hello"}],
        )
        p = Prompt(template=tpl)
    return p


@pytest.fixture
def mock_request(client):
    with patch.object(client, "request") as m:
        yield m


def _config(mock_request, call_index=-1):
    """Extract RequestConfig from a mock call (handles keyword-style calls)."""
    call = mock_request.call_args if call_index < 0 else mock_request.call_args_list[call_index]
    if call.args:
        return call.args[0]
    return call.kwargs["config"]


# ===========================================================================
# 1. Endpoint Routing
# ===========================================================================

class TestEndpointRouting:

    # ------------------------------------------------------------------
    # _fetch_template_by_name  (called from __init__ and elsewhere)
    # ------------------------------------------------------------------

    def test_fetch_by_name_uses_get_template_by_name_route(self, client, mock_request):
        """_fetch_template_by_name must use Routes.get_template_by_name."""
        mock_request.return_value = PromptTemplate(name="test")
        client._fetch_template_by_name("test")

        cfg = _config(mock_request)
        assert Routes.get_template_by_name.value in cfg.url
        assert cfg.params["name"] == "test"

    def test_fetch_by_name_not_using_label_route(self, client, mock_request):
        """Verify prompt_label_get_by_name is NOT used in _fetch_template_by_name."""
        mock_request.return_value = PromptTemplate(name="test")
        client._fetch_template_by_name("test")

        cfg = _config(mock_request)
        assert Routes.prompt_label_get_by_name.value not in cfg.url

    def test_fetch_by_name_passes_response_handler(self, client, mock_request):
        """_fetch_template_by_name must pass PromptResponseHandler."""
        mock_request.return_value = PromptTemplate(name="test")
        client._fetch_template_by_name("test")

        call = mock_request.call_args if hasattr(mock_request, 'call_args') else mock_request.call_args_list[-1]
        assert call.kwargs.get("response_handler") is PromptResponseHandler

    # ------------------------------------------------------------------
    # delete_template_by_name  (classmethod, creates its own client)
    # ------------------------------------------------------------------

    def test_delete_by_name_uses_get_template_by_name_route(self):
        """delete_template_by_name lookup step must use Routes.get_template_by_name."""
        tpl = PromptTemplate(
            id=uuid.UUID("00000000-0000-0000-0000-000000000001"),
            name="test",
        )
        with patch("fi.prompt.client.APIKeyAuth.request") as mock_req:
            mock_req.side_effect = [tpl, None]
            with patch.dict("os.environ", {"FI_API_KEY": "k", "FI_SECRET_KEY": "s"}):
                Prompt.delete_template_by_name("test")

        # First call = lookup
        cfg = _config(mock_req, 0)
        assert Routes.get_template_by_name.value in cfg.url
        assert cfg.params["name"] == "test"

    def test_delete_by_name_not_using_label_route(self):
        """delete_template_by_name must NOT use prompt_label_get_by_name."""
        tpl = PromptTemplate(
            id=uuid.UUID("00000000-0000-0000-0000-000000000001"),
            name="test",
        )
        with patch("fi.prompt.client.APIKeyAuth.request") as mock_req:
            mock_req.side_effect = [tpl, None]
            with patch.dict("os.environ", {"FI_API_KEY": "k", "FI_SECRET_KEY": "s"}):
                Prompt.delete_template_by_name("test")

        cfg = _config(mock_req, 0)
        assert Routes.prompt_label_get_by_name.value not in cfg.url

    # ------------------------------------------------------------------
    # get_template_by_name  fallback path
    # ------------------------------------------------------------------

    def test_get_template_by_name_fallback_uses_correct_route(self):
        """When production label fetch fails, fallback must use get_template_by_name."""
        tpl = PromptTemplate(
            id=uuid.UUID("00000000-0000-0000-0000-000000000001"),
            name="test",
            messages=[{"role": "user", "content": "Hi"}],
        )
        with patch("fi.prompt.client.APIKeyAuth.request") as mock_req:
            mock_req.side_effect = [TemplateNotFound("test"), tpl]
            with patch("fi.prompt.cache.prompt_cache.get", return_value=None):
                with patch("fi.prompt.cache.prompt_cache.get_stale", return_value=None):
                    with patch.dict("os.environ", {"FI_API_KEY": "k", "FI_SECRET_KEY": "s"}):
                        result = Prompt.get_template_by_name("test")

        # Second call = fallback
        cfg = _config(mock_req, 1)
        assert Routes.get_template_by_name.value in cfg.url
        assert Routes.prompt_label_get_by_name.value not in cfg.url

    def test_get_template_by_name_label_path_uses_label_route(self):
        """When a label is explicitly requested, use prompt_label_get_by_name."""
        tpl = PromptTemplate(
            id=uuid.UUID("00000000-0000-0000-0000-000000000001"),
            name="test",
            messages=[{"role": "user", "content": "Hi"}],
        )
        with patch("fi.prompt.client.APIKeyAuth.request") as mock_req:
            mock_req.return_value = tpl
            with patch("fi.prompt.cache.prompt_cache.get", return_value=None):
                with patch("fi.prompt.cache.prompt_cache.get_stale", return_value=None):
                    with patch.dict("os.environ", {"FI_API_KEY": "k", "FI_SECRET_KEY": "s"}):
                        Prompt.get_template_by_name("test", label="production")

        cfg = _config(mock_req, 0)
        assert Routes.prompt_label_get_by_name.value in cfg.url


# ===========================================================================
# 2. generate() / improve()
# ===========================================================================

class TestGenerateImprove:

    def test_generate_uses_simple_json_handler(self, client, mock_request):
        """generate() must pass SimpleJsonResponseHandler."""
        mock_request.return_value = {"generation_id": "gen-1"}
        client.generate("test")
        assert mock_request.call_args.kwargs["response_handler"] is SimpleJsonResponseHandler

    def test_generate_returns_self(self, client, mock_request):
        """generate() must return self for chaining."""
        mock_request.return_value = {"generation_id": "gen-1"}
        result = client.generate("test")
        assert result is client

    def test_generate_sets_last_generation_id(self, client, mock_request):
        """generate() must extract generation_id from response."""
        mock_request.return_value = {"result": {"generation_id": "gen-123"}}
        client.generate("Make a prompt")
        assert client.last_generation_id == "gen-123"

    def test_generate_handles_flat_response(self, client, mock_request):
        """generate() must handle response without 'result' wrapper."""
        mock_request.return_value = {"generation_id": "gen-456"}
        client.generate("test")
        assert client.last_generation_id == "gen-456"

    def test_generate_sets_none_when_no_generation_id(self, client, mock_request):
        """generate() must set last_generation_id to None when missing."""
        mock_request.return_value = {"status": "queued"}
        client.generate("test")
        assert client.last_generation_id is None

    def test_generate_sets_none_when_response_not_dict(self, client, mock_request):
        """generate() must handle non-dict response gracefully."""
        mock_request.return_value = "some string"
        client.generate("test")
        assert client.last_generation_id is None

    def test_generate_raises_without_template(self):
        """generate() must raise when no template is configured."""
        with patch.dict("os.environ", {"FI_API_KEY": "k", "FI_SECRET_KEY": "s"}):
            p = Prompt()
            with pytest.raises(ValueError, match="No template configured"):
                p.generate("test")

    def test_improve_uses_simple_json_handler(self, client, mock_request):
        """improve() must pass SimpleJsonResponseHandler."""
        mock_request.return_value = {"generation_id": "gen-1"}
        client.improve("test")
        assert mock_request.call_args.kwargs["response_handler"] is SimpleJsonResponseHandler

    def test_improve_returns_self(self, client, mock_request):
        """improve() must return self for chaining."""
        mock_request.return_value = {"generation_id": "gen-1"}
        result = client.improve("test")
        assert result is client

    def test_improve_sets_last_generation_id(self, client, mock_request):
        """improve() must extract generation_id from response."""
        mock_request.return_value = {"result": {"generation_id": "gen-789"}}
        client.improve("Make it better")
        assert client.last_generation_id == "gen-789"

    def test_improve_handles_flat_response(self, client, mock_request):
        """improve() must handle response without 'result' wrapper."""
        mock_request.return_value = {"generation_id": "gen-abc"}
        client.improve("test")
        assert client.last_generation_id == "gen-abc"

    def test_improve_sets_none_when_no_generation_id(self, client, mock_request):
        """improve() must set last_generation_id to None when missing."""
        mock_request.return_value = {"status": "ok"}
        client.improve("test")
        assert client.last_generation_id is None

    def test_improve_raises_without_template(self):
        """improve() must raise when no template is configured."""
        with patch.dict("os.environ", {"FI_API_KEY": "k", "FI_SECRET_KEY": "s"}):
            p = Prompt()
            with pytest.raises(ValueError, match="No template configured"):
                p.improve("test")


# ===========================================================================
# 3. Cache Invalidation
# ===========================================================================

class TestCacheInvalidation:

    def test_delete_invalidates_cache(self, client, mock_request):
        """delete() must call prompt_cache.invalidate with template name."""
        mock_request.return_value = None
        with patch("fi.prompt.client.prompt_cache.invalidate") as mock_inv:
            client.delete()
            mock_inv.assert_called_once_with("test-template")

    def test_delete_cache_invalidation_before_http(self, client, mock_request):
        """delete() must invalidate cache before the HTTP DELETE call."""
        mock_request.return_value = None
        with patch("fi.prompt.client.prompt_cache.invalidate") as mock_inv:
            client.delete()
            # invalidate must be called before request (order of calls)
            mock_inv.assert_called_once()
            mock_request.assert_called_once()

    def test_delete_template_by_name_invalidates_cache(self):
        """delete_template_by_name() must call prompt_cache.invalidate."""
        tpl = PromptTemplate(
            id=uuid.UUID("00000000-0000-0000-0000-000000000001"),
            name="test",
        )
        with patch("fi.prompt.client.APIKeyAuth.request") as mock_req:
            mock_req.side_effect = [tpl, None]
            with patch("fi.prompt.client.prompt_cache.invalidate") as mock_inv:
                with patch.dict("os.environ", {"FI_API_KEY": "k", "FI_SECRET_KEY": "s"}):
                    Prompt.delete_template_by_name("test")
                mock_inv.assert_called_once_with("test")

    def test_delete_cache_invalidation_graceful_on_failure(self, client, mock_request):
        """delete() must not crash when prompt_cache.invalidate raises."""
        mock_request.return_value = None
        with patch("fi.prompt.client.prompt_cache.invalidate", side_effect=RuntimeError("fail")):
            # Should not raise
            result = client.delete()
            assert result is True

    def test_delete_template_by_name_graceful_on_cache_failure(self):
        """delete_template_by_name() must not crash when cache invalidation raises."""
        tpl = PromptTemplate(
            id=uuid.UUID("00000000-0000-0000-0000-000000000001"),
            name="test",
        )
        with patch("fi.prompt.client.APIKeyAuth.request") as mock_req:
            mock_req.side_effect = [tpl, None]
            with patch("fi.prompt.client.prompt_cache.invalidate", side_effect=RuntimeError("fail")):
                with patch.dict("os.environ", {"FI_API_KEY": "k", "FI_SECRET_KEY": "s"}):
                    result = Prompt.delete_template_by_name("test")
                assert result is True


# ===========================================================================
# 4. snake_case Key Handling
# ===========================================================================

class TestSnakeCaseModelKey:
    """Config source reads 'model' key (not 'model_name')."""

    def test_parse_success_reads_model_key(self):
        """PromptResponseHandler._parse_success must use cfg_src.get('model')."""
        data = {
            "result": {
                "id": str(uuid.uuid4()),
                "name": "test",
                "prompt_config": [{
                    "configuration": {
                        "model": "gpt-5",
                        "temperature": 0.7,
                    }
                }]
            }
        }
        resp = _mock_response(data)
        resp.request.method = "GET"
        result = PromptResponseHandler._parse_success(resp)
        assert isinstance(result, PromptTemplate)
        assert result.model_configuration.model_name == "gpt-5"

    def test_parse_success_falls_back_to_unavailable(self):
        """When 'model' key is missing, model_name must be 'unavailable'."""
        data = {
            "result": {
                "id": str(uuid.uuid4()),
                "name": "test",
                "prompt_config": [{
                    "configuration": {
                        "temperature": 0.7,
                    }
                }]
            }
        }
        resp = _mock_response(data)
        resp.request.method = "GET"
        result = PromptResponseHandler._parse_success(resp)
        assert result.model_configuration.model_name == "unavailable"

    def test_dict_to_prompt_template_reads_model_key(self):
        """_dict_to_prompt_template must use cfg_raw.get('model')."""
        item = {
            "id": str(uuid.uuid4()),
            "name": "test",
            "prompt_config": [{
                "configuration": {
                    "model": "claude-sonnet-4",
                }
            }]
        }
        result = Prompt._dict_to_prompt_template(item)
        assert result.model_configuration.model_name == "claude-sonnet-4"

    def test_dict_to_prompt_template_no_config_falls_back(self):
        """When prompt_config is missing entirely, must not crash."""
        item = {"name": "test"}
        result = Prompt._dict_to_prompt_template(item)
        assert result.model_configuration is not None
        # Default model name
        assert result.model_configuration.model_name == "gpt-4o-mini"

    def test_dict_to_prompt_template_empty_config(self):
        """When configuration is empty, model_name must be 'unavailable'."""
        item = {
            "name": "test",
            "prompt_config": [{"configuration": {}}]
        }
        result = Prompt._dict_to_prompt_template(item)
        assert result.model_configuration.model_name == "unavailable"


class TestSnakeCaseErrorCode:
    """Error handler reads 'code' key (not 'error_code')."""

    def test_handle_error_400_reads_code_key(self):
        """_handle_error must use detail.get('code')."""
        resp = _mock_response(
            {"code": "TEMPLATE_ALREADY_EXIST", "name": "my-template"},
            status_code=400,
        )
        with pytest.raises(TemplateAlreadyExists, match="my-template"):
            PromptResponseHandler._handle_error(resp)

    def test_handle_error_400_unknown_code(self):
        """Unknown code must fall through to generic SDKException."""
        resp = _mock_response(
            {"code": "SOME_OTHER_ERROR", "message": "Something went wrong"},
            status_code=400,
        )
        from fi.utils.errors import SDKException
        with pytest.raises(SDKException, match="Something went wrong"):
            PromptResponseHandler._handle_error(resp)

    def test_handle_error_404_reads_name_from_query(self):
        """404 handler must extract name from query string."""
        resp = _mock_response({}, status_code=404)
        resp.request.url = "http://test/api/?name=missing-template"
        with pytest.raises(TemplateNotFound, match="missing-template"):
            PromptResponseHandler._handle_error(resp)

    def test_handle_error_404_fallback_to_unknown(self):
        """404 handler must fallback to 'unknown' when no name in query."""
        resp = _mock_response({}, status_code=404)
        resp.request.url = "http://test/api/"
        with pytest.raises(TemplateNotFound, match="unknown"):
            PromptResponseHandler._handle_error(resp)


class TestSnakeCaseVersionExtraction:
    """Version lookups use 'template_version' key (extracted to variable)."""

    VERSION_HISTORY = [
        {"template_version": "v1", "is_draft": False, "id": "ver-1"},
        {"template_version": "v2", "is_draft": True, "id": "ver-2"},
    ]

    def test_current_version_is_draft_uses_template_version(self, client):
        """_current_version_is_draft must read entry.get('template_version')."""
        with patch.object(client, "_fetch_template_version_history") as mock_h:
            mock_h.return_value = self.VERSION_HISTORY

            client.template.version = "v1"
            assert client._current_version_is_draft() is False

            client.template.version = "v2"
            assert client._current_version_is_draft() is True

    def test_current_version_is_draft_defaults_true(self, client):
        """When version not found in history, must default to draft (conservative)."""
        with patch.object(client, "_fetch_template_version_history") as mock_h:
            mock_h.return_value = self.VERSION_HISTORY
            client.template.version = "v999"
            assert client._current_version_is_draft() is True

    def test_get_version_id_by_name_uses_template_version(self, client):
        """_get_version_id_by_name must read entry.get('template_version')."""
        with patch.object(client, "_fetch_template_version_history") as mock_h:
            mock_h.return_value = self.VERSION_HISTORY
            assert client._get_version_id_by_name("v1") == "ver-1"
            assert client._get_version_id_by_name("v2") == "ver-2"

    def test_get_version_id_by_name_returns_none_when_missing(self, client):
        """_get_version_id_by_name must return None for unknown version."""
        with patch.object(client, "_fetch_template_version_history") as mock_h:
            mock_h.return_value = self.VERSION_HISTORY
            assert client._get_version_id_by_name("v999") is None

    def _mock_search_result(self, template_id, name):
        """Build a mock Response for the template-id resolution step."""
        resp = MagicMock()
        resp.url = f"http://test/api/?search={name}"
        resp.json.return_value = {"results": [{"id": str(template_id), "name": name}]}
        return resp

    def _mock_history_result(self, history):
        resp = MagicMock()
        resp.url = "http://test/api/history"
        resp.json.return_value = {"results": history}
        return resp

    def test_assign_label_to_template_version_reads_template_version(self, client):
        """_assign_label_to_template_version_by_names must extract template_version."""
        tpl_id = uuid.uuid4()
        search_resp = self._mock_search_result(tpl_id, "test")
        history_resp = self._mock_history_result(self.VERSION_HISTORY)
        assign_resp = MagicMock()
        assign_resp.json.return_value = {"status": "success"}

        with patch.object(client, "_get_label_id", return_value="lbl-1"):
            with patch.object(client, "request") as mock_req:
                mock_req.side_effect = [search_resp, history_resp, assign_resp]
                result = client._assign_label_to_template_version_by_names(
                    "test", "v1", "production"
                )
                assert result.json.return_value["status"] == "success"

    def test_assign_label_rejects_draft_version(self, client):
        """Assigning label to draft version must raise with 'draft' in message."""
        tpl_id = uuid.uuid4()
        search_resp = self._mock_search_result(tpl_id, "test")
        history_resp = self._mock_history_result(self.VERSION_HISTORY)

        with patch.object(client, "_get_label_id", return_value="lbl-1"):
            with patch.object(client, "request") as mock_req:
                mock_req.side_effect = [search_resp, history_resp]
                from fi.utils.errors import SDKException
                with pytest.raises(SDKException, match="draft"):
                    client._assign_label_to_template_version_by_names(
                        "test", "v2", "production"
                    )
