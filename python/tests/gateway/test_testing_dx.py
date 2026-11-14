"""Tests for testing DX utilities: RequestRecorder, assertion helpers, mock client factory."""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from fi.gateway.callbacks.base import CallbackHandler, CallbackRequest, CallbackResponse
from fi.gateway.testing import (
    RequestRecorder,
    assert_completion_valid,
    assert_cost_tracked,
    assert_agentcc_metadata,
    assert_stream_valid,
    assert_usage_valid,
    create_mock_client,
)
from fi.gateway.testing.fixtures import make_completion, make_agentcc_metadata, make_usage

# ---------------------------------------------------------------------------
# RequestRecorder tests
# ---------------------------------------------------------------------------


class TestRequestRecorder:
    def test_recorder_captures_request(self) -> None:
        recorder = RequestRecorder("dummy.json")
        req = CallbackRequest(method="POST", url="https://gw.test/v1/chat/completions", headers={}, body={"model": "gpt-4o"})
        resp = CallbackResponse(status_code=200, headers={}, body={"id": "chatcmpl-1"})
        recorder.on_request_end(req, resp)

        assert len(recorder.recordings) == 1
        rec = recorder.recordings[0]
        assert rec["request"]["method"] == "POST"
        assert rec["request"]["url"] == "https://gw.test/v1/chat/completions"
        assert rec["request"]["body"] == {"model": "gpt-4o"}
        assert rec["response"]["status_code"] == 200
        assert rec["response"]["body"] == {"id": "chatcmpl-1"}

    def test_recorder_save_to_file(self, tmp_path: Path) -> None:
        file_path = str(tmp_path / "recordings.json")
        recorder = RequestRecorder(file_path)
        req = CallbackRequest(method="POST", url="https://gw.test/v1/chat/completions", headers={}, body={"model": "gpt-4o"})
        resp = CallbackResponse(status_code=200, headers={}, body={"id": "chatcmpl-1"})
        recorder.on_request_end(req, resp)
        recorder.save()

        data = json.loads(Path(file_path).read_text())
        assert len(data) == 1
        assert data[0]["request"]["method"] == "POST"
        assert data[0]["response"]["status_code"] == 200

    def test_recorder_context_manager(self, tmp_path: Path) -> None:
        file_path = str(tmp_path / "recordings.json")
        with RequestRecorder(file_path) as recorder:
            req = CallbackRequest(method="POST", url="https://gw.test/v1/chat/completions", headers={}, body={"model": "gpt-4o"})
            resp = CallbackResponse(status_code=200, headers={}, body={"id": "chatcmpl-1"})
            recorder.on_request_end(req, resp)

        # File should have been written on __exit__
        data = json.loads(Path(file_path).read_text())
        assert len(data) == 1
        assert data[0]["request"]["url"] == "https://gw.test/v1/chat/completions"

    def test_recorder_is_callback_handler(self) -> None:
        recorder = RequestRecorder("dummy.json")
        assert isinstance(recorder, CallbackHandler)

    def test_recorder_multiple_requests(self, tmp_path: Path) -> None:
        file_path = str(tmp_path / "recordings.json")
        recorder = RequestRecorder(file_path)
        for i in range(3):
            req = CallbackRequest(method="POST", url="https://gw.test/v1/chat/completions", headers={}, body={"model": f"model-{i}"})
            resp = CallbackResponse(status_code=200, headers={}, body={"id": f"chatcmpl-{i}"})
            recorder.on_request_end(req, resp)

        assert len(recorder.recordings) == 3
        recorder.save()
        data = json.loads(Path(file_path).read_text())
        assert len(data) == 3


# ---------------------------------------------------------------------------
# Assertion helpers tests
# ---------------------------------------------------------------------------


class TestAssertCompletionValid:
    def test_assert_completion_valid_passes(self) -> None:
        comp = make_completion(content="Hello!")
        assert_completion_valid(comp)

    def test_assert_completion_valid_fails_none(self) -> None:
        with pytest.raises(AssertionError, match="Response is None"):
            assert_completion_valid(None)

    def test_assert_completion_valid_fails_no_choices(self) -> None:
        comp = make_completion()
        # Manually clear choices to trigger assertion
        comp.choices = []
        with pytest.raises(AssertionError, match="Response has no choices"):
            assert_completion_valid(comp)

    def test_assert_completion_valid_fails_no_content(self) -> None:
        comp = make_completion(content="test")
        comp.choices[0].message.content = None
        with pytest.raises(AssertionError, match="Message content is None"):
            assert_completion_valid(comp)


class TestAssertStreamValid:
    def test_assert_stream_valid_passes(self) -> None:
        chunk = SimpleNamespace(
            choices=[SimpleNamespace(finish_reason="stop")],
        )
        assert_stream_valid([chunk])

    def test_assert_stream_valid_fails_empty(self) -> None:
        with pytest.raises(AssertionError, match="No chunks received"):
            assert_stream_valid([])

    def test_assert_stream_valid_no_finish_reason(self) -> None:
        chunk = SimpleNamespace(
            choices=[SimpleNamespace(finish_reason=None)],
        )
        with pytest.raises(AssertionError, match="Last chunk missing finish_reason"):
            assert_stream_valid([chunk])

    def test_assert_stream_valid_empty_choices(self) -> None:
        # When choices is empty, no assertion on finish_reason
        chunk = SimpleNamespace(choices=[])
        assert_stream_valid([chunk])


class TestAssertAgentCCMetadata:
    def test_assert_agentcc_metadata_passes(self) -> None:
        meta = make_agentcc_metadata(provider="openai")
        comp = make_completion(agentcc=meta)
        assert_agentcc_metadata(comp, provider="openai")

    def test_assert_agentcc_metadata_fails_no_agentcc(self) -> None:
        comp = make_completion()  # agentcc=None by default
        with pytest.raises(AssertionError, match=r"no \.agentcc metadata"):
            assert_agentcc_metadata(comp)


class TestAssertUsageValid:
    def test_assert_usage_valid_passes(self) -> None:
        comp = make_completion()
        assert_usage_valid(comp)

    def test_assert_usage_valid_fails_none(self) -> None:
        comp = make_completion()
        comp.usage = None
        with pytest.raises(AssertionError, match="Usage is None"):
            assert_usage_valid(comp)

    def test_assert_usage_valid_fails_zero_tokens(self) -> None:
        comp = make_completion(usage=make_usage(prompt_tokens=0, completion_tokens=0, total_tokens=0))
        with pytest.raises(AssertionError, match="total_tokens is 0"):
            assert_usage_valid(comp)


class TestAssertCostTracked:
    def test_assert_cost_tracked_passes(self) -> None:
        meta = make_agentcc_metadata(cost=0.05)
        comp = make_completion(agentcc=meta)
        assert_cost_tracked(comp)

    def test_assert_cost_tracked_fails_no_agentcc(self) -> None:
        comp = SimpleNamespace()  # no agentcc attr
        with pytest.raises(AssertionError, match="missing 'agentcc' metadata"):
            assert_cost_tracked(comp)

    def test_assert_cost_tracked_fails_no_cost(self) -> None:
        meta = make_agentcc_metadata(cost=None)
        comp = make_completion(agentcc=meta)
        with pytest.raises(AssertionError, match="Cost not tracked"):
            assert_cost_tracked(comp)


# ---------------------------------------------------------------------------
# Mock client factory tests
# ---------------------------------------------------------------------------


class TestCreateMockClient:
    def test_create_mock_client_returns_agentcc(self) -> None:
        from fi.gateway._client import AgentCC

        client = create_mock_client()
        assert isinstance(client, AgentCC)

    def test_create_mock_client_custom_params(self) -> None:
        client = create_mock_client(
            api_key="sk-custom-key",
            base_url="https://custom.test",
        )
        assert client._api_key == "sk-custom-key"
        assert client._base_url == "https://custom.test"

    def test_create_mock_client_stores_responses(self) -> None:
        responses = {"/v1/chat/completions": {"id": "chatcmpl-test"}}
        client = create_mock_client(responses=responses)
        assert client._mock_responses == responses  # type: ignore[attr-defined]

    def test_create_mock_client_default_responses_empty(self) -> None:
        client = create_mock_client()
        assert client._mock_responses == {}  # type: ignore[attr-defined]


# ---------------------------------------------------------------------------
# pip extras test
# ---------------------------------------------------------------------------


class TestPyprojectExtras:
    def test_pyproject_has_gateway_extras(self) -> None:
        """futureagi's pyproject keeps agentcc's optional features installable."""
        import re

        pyproject_path = Path(__file__).resolve().parents[2] / "pyproject.toml"
        text = pyproject_path.read_text()
        extras = text.split("[tool.poetry.extras]", 1)[1].split("\n[", 1)[0]
        assert re.search(r"^gateway-tokens = \[.*tiktoken", extras, re.M)
        assert re.search(r"^gateway-otel = \[.*opentelemetry-sdk", extras, re.M)



# ---------------------------------------------------------------------------
# Testing module import tests
# ---------------------------------------------------------------------------


class TestTestingImports:
    def test_testing_module_importable(self) -> None:
        import fi.gateway.testing as agentcc_testing
        assert hasattr(agentcc_testing, "RequestRecorder")
        assert hasattr(agentcc_testing, "assert_completion_valid")
        assert hasattr(agentcc_testing, "create_mock_client")

    def test_recorder_importable(self) -> None:
        from fi.gateway.testing.recorder import RequestRecorder
        assert RequestRecorder is not None

    def test_assertions_importable(self) -> None:
        from fi.gateway.testing.assertions import (
            assert_completion_valid,
            assert_cost_tracked,
            assert_stream_valid,
            assert_usage_valid,
        )
        assert all(callable(fn) for fn in [
            assert_completion_valid,
            assert_cost_tracked,
            assert_stream_valid,
            assert_usage_valid,
        ])

    def test_mock_importable(self) -> None:
        from fi.gateway.testing.mock import create_mock_client
        assert callable(create_mock_client)

    def test_create_mock_client_from_main_package(self) -> None:
        from fi.gateway import create_mock_client
        assert callable(create_mock_client)
