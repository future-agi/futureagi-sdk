"""Tests for session tracking and metadata features (Session, SessionContext, properties, user_id, request_id)."""

from __future__ import annotations

import json

import pytest
import respx

from fi.gateway._client import AsyncAgentCC, AgentCC
from fi.gateway._session import Session, SessionContext

# --- Response fixtures ---

GATEWAY_RESPONSE = {
    "id": "chatcmpl-abc123",
    "object": "chat.completion",
    "created": 1709000000,
    "model": "gpt-4o",
    "choices": [
        {
            "index": 0,
            "message": {"role": "assistant", "content": "Hello!"},
            "finish_reason": "stop",
        }
    ],
    "usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
}

GATEWAY_HEADERS = {
    "x-agentcc-request-id": "req-abc",
    "x-agentcc-trace-id": "trace-xyz",
    "x-agentcc-provider": "openai",
    "x-agentcc-latency-ms": "42",
}


# ===== Session class tests =====


class TestSession:
    def test_session_default_id_generated(self) -> None:
        """Session auto-generates a UUID hex string when no session_id is provided."""
        session = Session()
        assert len(session.session_id) == 32  # uuid4().hex is 32 hex chars
        assert session.session_id.isalnum()

    def test_session_custom_id(self) -> None:
        """Session uses the provided session_id."""
        session = Session(session_id="my-custom-id")
        assert session.session_id == "my-custom-id"

    def test_session_step_builds_path(self) -> None:
        """step() appends to the path correctly."""
        session = Session()
        assert session.path == "/"

        session.step("research")
        assert session.path == "/research"

        session.step("summarize")
        assert session.path == "/research/summarize"

    def test_session_reset_path(self) -> None:
        """reset_path() resets path to / and clears steps."""
        session = Session()
        session.step("a")
        session.step("b")
        assert session.path == "/a/b"

        session.reset_path()
        assert session.path == "/"
        assert session._steps == []

    def test_session_to_headers(self) -> None:
        """to_headers() returns all expected headers."""
        session = Session(
            session_id="sess-123",
            name="my-session",
            metadata={"env": "prod", "version": "2"},
        )
        session.step("search")

        headers = session.to_headers()
        assert headers["x-agentcc-session-id"] == "sess-123"
        assert headers["x-agentcc-session-name"] == "my-session"
        assert headers["x-agentcc-session-path"] == "/search"
        assert headers["x-agentcc-metadata-env"] == "prod"
        assert headers["x-agentcc-metadata-version"] == "2"

    def test_session_to_headers_minimal(self) -> None:
        """to_headers() only includes session_id when name is None and path is /."""
        session = Session(session_id="sess-minimal")
        headers = session.to_headers()

        assert headers == {"x-agentcc-session-id": "sess-minimal"}
        assert "x-agentcc-session-name" not in headers
        assert "x-agentcc-session-path" not in headers

    def test_session_track_request(self) -> None:
        """track_request() updates cost, tokens, and count."""
        session = Session()

        session.track_request(cost=0.01, tokens=100)
        assert session.total_cost == pytest.approx(0.01)
        assert session.total_tokens == 100
        assert session.request_count == 1

        session.track_request(cost=0.02, tokens=200)
        assert session.total_cost == pytest.approx(0.03)
        assert session.total_tokens == 300
        assert session.request_count == 2

    def test_session_metadata_in_headers(self) -> None:
        """Metadata keys are converted to x-agentcc-metadata-{key} headers."""
        session = Session(
            session_id="s1",
            metadata={"team": "backend", "priority": "high"},
        )
        headers = session.to_headers()
        assert headers["x-agentcc-metadata-team"] == "backend"
        assert headers["x-agentcc-metadata-priority"] == "high"


# ===== SessionContext tests =====


class TestSessionContext:
    def test_session_context_manager_sync(self) -> None:
        """Entering sets _active_session, exiting clears it."""
        client = AgentCC(api_key="sk-test", base_url="http://localhost:8080")
        assert client._active_session is None

        ctx = SessionContext(client, session_id="ctx-1", name="test")
        with ctx as session:
            assert client._active_session is session
            assert session.session_id == "ctx-1"
            assert session.name == "test"

        assert client._active_session is None

    def test_session_context_via_client_method(self) -> None:
        """client.session() returns a SessionContext that works as context manager."""
        client = AgentCC(api_key="sk-test", base_url="http://localhost:8080")

        with client.session(session_id="s1", name="my-session", metadata={"k": "v"}) as sess:
            assert client._active_session is sess
            assert sess.session_id == "s1"
            assert sess.name == "my-session"
            assert sess.metadata == {"k": "v"}

        assert client._active_session is None

    @respx.mock
    def test_session_context_auto_headers(self) -> None:
        """Headers from the active session are merged into the request."""
        route = respx.post("http://gateway.test/v1/chat/completions").respond(
            200, json=GATEWAY_RESPONSE, headers=GATEWAY_HEADERS,
        )
        client = AgentCC(api_key="sk-test", base_url="http://gateway.test")

        with client.session(session_id="sess-auto", name="auto-test") as sess:
            sess.step("search")
            client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": "Hello"}],
            )

        request = route.calls[0].request
        assert request.headers["x-agentcc-session-id"] == "sess-auto"
        assert request.headers["x-agentcc-session-name"] == "auto-test"
        assert request.headers["x-agentcc-session-path"] == "/search"

    @respx.mock
    def test_session_context_nested_steps(self) -> None:
        """Multiple steps build the path correctly within a session context."""
        route = respx.post("http://gateway.test/v1/chat/completions").respond(
            200, json=GATEWAY_RESPONSE, headers=GATEWAY_HEADERS,
        )
        client = AgentCC(api_key="sk-test", base_url="http://gateway.test")

        with client.session(session_id="nest") as sess:
            sess.step("research")
            sess.step("summarize")
            client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": "Hi"}],
            )

        request = route.calls[0].request
        assert request.headers["x-agentcc-session-path"] == "/research/summarize"

    @pytest.mark.anyio
    async def test_session_context_async(self) -> None:
        """Async context manager sets/clears _active_session."""
        client = AsyncAgentCC(api_key="sk-test", base_url="http://localhost:8080")
        assert client._active_session is None

        async with client.session(session_id="async-1", name="async-sess") as sess:
            assert client._active_session is sess
            assert sess.session_id == "async-1"

        assert client._active_session is None


# ===== Custom properties tests =====


class TestProperties:
    @respx.mock
    def test_properties_sent_as_headers(self) -> None:
        """Each property is sent as x-agentcc-property-{key}: {value}."""
        route = respx.post("http://gateway.test/v1/chat/completions").respond(
            200, json=GATEWAY_RESPONSE, headers=GATEWAY_HEADERS,
        )
        client = AgentCC(api_key="sk-test", base_url="http://gateway.test")
        client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": "Hello"}],
            properties={"environment": "staging"},
        )

        request = route.calls[0].request
        assert request.headers["x-agentcc-property-environment"] == "staging"

    @respx.mock
    def test_properties_multiple_keys(self) -> None:
        """Multiple properties are all sent as separate headers."""
        route = respx.post("http://gateway.test/v1/chat/completions").respond(
            200, json=GATEWAY_RESPONSE, headers=GATEWAY_HEADERS,
        )
        client = AgentCC(api_key="sk-test", base_url="http://gateway.test")
        client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": "Hello"}],
            properties={"env": "prod", "team": "backend", "version": "v2"},
        )

        request = route.calls[0].request
        assert request.headers["x-agentcc-property-env"] == "prod"
        assert request.headers["x-agentcc-property-team"] == "backend"
        assert request.headers["x-agentcc-property-version"] == "v2"

    @respx.mock
    def test_properties_none_skipped(self) -> None:
        """When properties is None, no x-agentcc-property-* headers are sent."""
        route = respx.post("http://gateway.test/v1/chat/completions").respond(
            200, json=GATEWAY_RESPONSE, headers=GATEWAY_HEADERS,
        )
        client = AgentCC(api_key="sk-test", base_url="http://gateway.test")
        client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": "Hello"}],
        )

        request = route.calls[0].request
        prop_headers = [k for k in request.headers if k.startswith("x-agentcc-property-")]
        assert prop_headers == []


# ===== User ID tests =====


class TestUserId:
    @respx.mock
    def test_user_id_sent_as_header(self) -> None:
        """user_id is sent as x-agentcc-user-id header."""
        route = respx.post("http://gateway.test/v1/chat/completions").respond(
            200, json=GATEWAY_RESPONSE, headers=GATEWAY_HEADERS,
        )
        client = AgentCC(api_key="sk-test", base_url="http://gateway.test")
        client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": "Hello"}],
            user_id="user-42",
        )

        request = route.calls[0].request
        assert request.headers["x-agentcc-user-id"] == "user-42"

    @respx.mock
    def test_user_id_separate_from_openai_user(self) -> None:
        """user_id goes in headers, OpenAI's user goes in the body."""
        route = respx.post("http://gateway.test/v1/chat/completions").respond(
            200, json=GATEWAY_RESPONSE, headers=GATEWAY_HEADERS,
        )
        client = AgentCC(api_key="sk-test", base_url="http://gateway.test")
        client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": "Hello"}],
            user="openai-user-abc",
            user_id="agentcc-user-xyz",
        )

        request = route.calls[0].request
        # user_id goes as header
        assert request.headers["x-agentcc-user-id"] == "agentcc-user-xyz"
        # OpenAI user goes in body
        body = json.loads(request.content)
        assert body["user"] == "openai-user-abc"


# ===== Request ID tests =====


class TestRequestId:
    @respx.mock
    def test_request_id_sent_as_header(self) -> None:
        """request_id is sent as x-agentcc-request-id header."""
        route = respx.post("http://gateway.test/v1/chat/completions").respond(
            200, json=GATEWAY_RESPONSE, headers=GATEWAY_HEADERS,
        )
        client = AgentCC(api_key="sk-test", base_url="http://gateway.test")
        client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": "Hello"}],
            request_id="req-custom-123",
        )

        request = route.calls[0].request
        assert request.headers["x-agentcc-request-id"] == "req-custom-123"

    @respx.mock
    def test_request_id_none_not_sent(self) -> None:
        """When request_id is None, x-agentcc-request-id is not set in request headers."""
        route = respx.post("http://gateway.test/v1/chat/completions").respond(
            200, json=GATEWAY_RESPONSE, headers=GATEWAY_HEADERS,
        )
        client = AgentCC(api_key="sk-test", base_url="http://gateway.test")
        client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": "Hello"}],
        )

        request = route.calls[0].request
        # The key should not be present in the request headers
        # (the response may have it, but we check the request)
        req_headers = dict(request.headers)
        assert "x-agentcc-request-id" not in req_headers


# ===== Lazy import tests =====


class TestLazyImport:
    def test_session_importable(self) -> None:
        """Session can be imported from the agentcc package."""
        from fi.gateway import Session

        session = Session(session_id="test-import")
        assert session.session_id == "test-import"

    def test_session_context_importable(self) -> None:
        """SessionContext can be imported from the agentcc package."""
        from fi.gateway import SessionContext

        assert SessionContext is not None
