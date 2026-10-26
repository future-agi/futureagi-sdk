"""Tests for agentcc._base_client — header building, URL building, retry logic, callbacks."""

from __future__ import annotations

import json
from typing import Any

import httpx
import pytest
import respx
from pydantic import BaseModel, ConfigDict

from fi.gateway._base_client import (
    RequestOptions,
    RetryConfig,
    SyncBaseClient,
    Timeout,
)
from fi.gateway._constants import NOT_GIVEN

# --- Test helpers ---


class _MockResponse(BaseModel):
    """Simple Pydantic model for testing _process_response_body."""

    model_config = ConfigDict(extra="allow")
    id: str
    content: str


def _make_sync_client(**kwargs: Any) -> SyncBaseClient:
    defaults: dict[str, Any] = {"api_key": "sk-test-key-12345"}
    defaults.update(kwargs)
    return SyncBaseClient(**defaults)


# --- Header building tests ---


class TestBuildHeaders:
    def test_sdk_auto_headers_present(self) -> None:
        client = _make_sync_client()
        opts = RequestOptions(method="POST", url="/v1/chat/completions")
        headers = client._build_headers(opts)
        assert headers["User-Agent"].startswith("agentcc-python/")
        assert headers["Content-Type"] == "application/json"
        assert "x-agentcc-sdk-version" in headers

    def test_auth_header_present(self) -> None:
        client = _make_sync_client()
        opts = RequestOptions(method="POST", url="/v1/chat/completions")
        headers = client._build_headers(opts)
        assert headers["Authorization"] == "Bearer sk-test-key-12345"

    def test_agentcc_params_session_id_and_cache_ttl(self) -> None:
        client = _make_sync_client()
        opts = RequestOptions(method="POST", url="/v1/chat/completions")
        headers = client._build_headers(opts, agentcc_params={"session_id": "abc", "cache_ttl": "10m"})
        assert headers["x-agentcc-session-id"] == "abc"
        assert headers["x-agentcc-cache-ttl"] == "10m"

    def test_per_request_headers_override_defaults(self) -> None:
        client = _make_sync_client(default_headers={"x-custom": "default"})
        opts = RequestOptions(method="POST", url="/v1/test", headers={"x-custom": "override"})
        headers = client._build_headers(opts)
        assert headers["x-custom"] == "override"

    def test_request_metadata_serialized_as_json(self) -> None:
        client = _make_sync_client()
        opts = RequestOptions(method="POST", url="/v1/test")
        meta = {"user": "test", "session": 123}
        headers = client._build_headers(opts, agentcc_params={"request_metadata": meta})
        parsed = json.loads(headers["x-agentcc-metadata"])
        assert parsed == meta

    def test_client_level_session_id(self) -> None:
        client = _make_sync_client(session_id="client-session")
        opts = RequestOptions(method="POST", url="/v1/test")
        headers = client._build_headers(opts)
        assert headers["x-agentcc-session-id"] == "client-session"

    def test_per_request_overrides_client_session_id(self) -> None:
        client = _make_sync_client(session_id="client-session")
        opts = RequestOptions(method="POST", url="/v1/test")
        headers = client._build_headers(opts, agentcc_params={"session_id": "request-session"})
        assert headers["x-agentcc-session-id"] == "request-session"

    def test_not_given_params_skipped(self) -> None:
        client = _make_sync_client()
        opts = RequestOptions(method="POST", url="/v1/test")
        headers = client._build_headers(opts, agentcc_params={"session_id": NOT_GIVEN, "cache_ttl": None})
        assert "x-agentcc-session-id" not in headers
        assert "x-agentcc-cache-ttl" not in headers

    def test_client_level_metadata(self) -> None:
        client = _make_sync_client(metadata={"user": "global"})
        opts = RequestOptions(method="POST", url="/v1/test")
        headers = client._build_headers(opts)
        parsed = json.loads(headers["x-agentcc-metadata"])
        assert parsed == {"user": "global"}


# --- URL building tests ---


class TestBuildUrl:
    def test_basic_join(self) -> None:
        client = _make_sync_client(base_url="https://gateway.example.com")
        assert client._build_url("/v1/chat/completions") == "https://gateway.example.com/v1/chat/completions"

    def test_trailing_slash_on_base(self) -> None:
        client = _make_sync_client(base_url="https://gateway.example.com/")
        assert client._build_url("/v1/chat/completions") == "https://gateway.example.com/v1/chat/completions"

    def test_no_leading_slash_on_path(self) -> None:
        client = _make_sync_client(base_url="https://gateway.example.com")
        assert client._build_url("v1/chat/completions") == "https://gateway.example.com/v1/chat/completions"

    def test_absolute_url_returned_as_is(self) -> None:
        client = _make_sync_client()
        assert client._build_url("https://other.com/api") == "https://other.com/api"


# --- Retry logic tests ---


class TestShouldRetry:
    def test_retryable_429_first_attempt(self) -> None:
        client = _make_sync_client()
        assert client._should_retry(429, attempt=0, max_retries=2) is True

    def test_retryable_429_exhausted(self) -> None:
        client = _make_sync_client()
        assert client._should_retry(429, attempt=2, max_retries=2) is False

    def test_not_retryable_400(self) -> None:
        client = _make_sync_client()
        assert client._should_retry(400, attempt=0, max_retries=2) is False

    def test_retryable_500(self) -> None:
        client = _make_sync_client()
        assert client._should_retry(500, attempt=0, max_retries=2) is True

    def test_retryable_502(self) -> None:
        client = _make_sync_client()
        assert client._should_retry(502, attempt=1, max_retries=3) is True

    def test_not_retryable_401(self) -> None:
        client = _make_sync_client()
        assert client._should_retry(401, attempt=0, max_retries=5) is False


class TestCalculateDelay:
    def test_respects_retry_after(self) -> None:
        client = _make_sync_client()
        delay = client._calculate_delay(0, {"retry-after": "2.5"})
        assert delay == 2.5

    def test_retry_after_capped(self) -> None:
        client = _make_sync_client(retry_config=RetryConfig(backoff_max=5.0))
        delay = client._calculate_delay(0, {"retry-after": "100"})
        assert delay == 5.0

    def test_exponential_backoff(self) -> None:
        client = _make_sync_client(retry_config=RetryConfig(backoff_factor=0.5, backoff_jitter=0.0))
        d0 = client._calculate_delay(0)
        d1 = client._calculate_delay(1)
        d2 = client._calculate_delay(2)
        assert d0 == 0.5  # 0.5 * 2^0
        assert d1 == 1.0  # 0.5 * 2^1
        assert d2 == 2.0  # 0.5 * 2^2

    def test_backoff_capped(self) -> None:
        client = _make_sync_client(retry_config=RetryConfig(backoff_factor=1.0, backoff_max=3.0, backoff_jitter=0.0))
        delay = client._calculate_delay(5)  # 1.0 * 2^5 = 32 → capped to 3.0
        assert delay == 3.0

    def test_jitter_within_range(self) -> None:
        client = _make_sync_client(retry_config=RetryConfig(backoff_factor=1.0, backoff_jitter=0.5))
        delays = [client._calculate_delay(0) for _ in range(100)]
        # delay = 1.0 ± 0.5, so between 0.5 and 1.5
        assert all(0.5 <= d <= 1.5 for d in delays)


# --- Response processing tests ---


class TestProcessResponse:
    @respx.mock
    def test_parse_json_into_model(self) -> None:
        client = _make_sync_client(base_url="https://gateway.test")
        respx.post("https://gateway.test/v1/test").respond(
            200,
            json={"id": "abc", "content": "hello"},
            headers={
                "x-agentcc-request-id": "req-1",
                "x-agentcc-trace-id": "trace-1",
                "x-agentcc-provider": "openai",
                "x-agentcc-latency-ms": "50",
            },
        )
        opts = RequestOptions(method="POST", url="/v1/test", body={})
        result = client._request(opts, _MockResponse)
        assert isinstance(result, _MockResponse)
        assert result.id == "abc"
        assert result.content == "hello"
        assert hasattr(result, "agentcc")
        assert result.agentcc.request_id == "req-1"  # type: ignore[attr-defined]
        assert result.agentcc.provider == "openai"  # type: ignore[attr-defined]

    @respx.mock
    def test_error_raises_correct_exception(self) -> None:
        from fi.gateway._exceptions import BadRequestError

        client = _make_sync_client(base_url="https://gateway.test")
        respx.post("https://gateway.test/v1/test").respond(
            400,
            json={"error": {"message": "Bad request", "type": "invalid_request_error"}},
        )
        opts = RequestOptions(method="POST", url="/v1/test", body={})
        with pytest.raises(BadRequestError) as exc_info:
            client._request(opts, _MockResponse)
        assert exc_info.value.status_code == 400

    @respx.mock
    def test_429_error_with_ratelimit(self) -> None:
        from fi.gateway._exceptions import RateLimitError

        client = _make_sync_client(base_url="https://gateway.test")
        respx.post("https://gateway.test/v1/test").respond(
            429,
            json={"error": {"message": "Rate limited"}},
            headers={"x-ratelimit-limit-requests": "100"},
        )
        opts = RequestOptions(method="POST", url="/v1/test", body={})
        with pytest.raises(RateLimitError):
            client._request(opts, _MockResponse)


# --- Retry integration tests ---


class TestRetryIntegration:
    @respx.mock
    def test_retries_429_then_succeeds(self) -> None:
        client = _make_sync_client(
            base_url="https://gateway.test",
            max_retries=2,
            retry_config=RetryConfig(max_retries=2, backoff_factor=0.01, backoff_jitter=0.0),
        )
        route = respx.post("https://gateway.test/v1/test")
        route.side_effect = [
            httpx.Response(429, json={"error": {"message": "Rate limited"}}),
            httpx.Response(200, json={"id": "abc", "content": "hello"}, headers={
                "x-agentcc-request-id": "req-1",
                "x-agentcc-trace-id": "trace-1",
                "x-agentcc-provider": "openai",
                "x-agentcc-latency-ms": "50",
            }),
        ]
        opts = RequestOptions(method="POST", url="/v1/test", body={})
        result = client._request_with_retry(opts, _MockResponse)
        assert result.id == "abc"
        assert route.call_count == 2

    @respx.mock
    def test_retries_exhausted_raises(self) -> None:
        from fi.gateway._exceptions import RateLimitError

        client = _make_sync_client(
            base_url="https://gateway.test",
            max_retries=1,
            retry_config=RetryConfig(max_retries=1, backoff_factor=0.01, backoff_jitter=0.0),
        )
        respx.post("https://gateway.test/v1/test").respond(
            429, json={"error": {"message": "Rate limited"}},
        )
        opts = RequestOptions(method="POST", url="/v1/test", body={})
        with pytest.raises(RateLimitError):
            client._request_with_retry(opts, _MockResponse)

    @respx.mock
    def test_non_retryable_error_raises_immediately(self) -> None:
        from fi.gateway._exceptions import BadRequestError

        client = _make_sync_client(
            base_url="https://gateway.test",
            max_retries=3,
        )
        route = respx.post("https://gateway.test/v1/test")
        route.respond(400, json={"error": {"message": "Bad request"}})
        opts = RequestOptions(method="POST", url="/v1/test", body={})
        with pytest.raises(BadRequestError):
            client._request_with_retry(opts, _MockResponse)
        assert route.call_count == 1


# --- Callback tests ---


class TestCallbackDispatch:
    def test_callbacks_called_in_order(self) -> None:
        order: list[str] = []

        class CB1:
            def on_request_start(self, *args: Any) -> None:
                order.append("cb1")

        class CB2:
            def on_request_start(self, *args: Any) -> None:
                order.append("cb2")

        client = _make_sync_client(callbacks=[CB1(), CB2()])
        client._dispatch_callback("on_request_start", "test")
        assert order == ["cb1", "cb2"]

    def test_callback_exception_does_not_propagate(self) -> None:
        class BadCallback:
            def on_request_start(self, *args: Any) -> None:
                raise RuntimeError("callback bug")

        class GoodCallback:
            def on_request_start(self, *args: Any) -> None:
                self.called = True

        good = GoodCallback()
        client = _make_sync_client(callbacks=[BadCallback(), good])
        # Should not raise
        client._dispatch_callback("on_request_start", "test")
        assert good.called is True

    def test_missing_callback_method_ignored(self) -> None:
        class PartialCallback:
            pass

        client = _make_sync_client(callbacks=[PartialCallback()])
        # Should not raise
        client._dispatch_callback("on_request_start", "test")


# --- Timeout dataclass tests ---


class TestTimeoutDataclass:
    def test_default_timeout(self) -> None:
        t = Timeout()
        assert t.connect is None
        assert t.read is None
        assert t.write is None
        assert t.pool is None

    def test_custom_timeout(self) -> None:
        t = Timeout(connect=5.0, read=30.0, write=10.0, pool=2.0)
        assert t.connect == 5.0
        assert t.read == 30.0
        assert t.write == 10.0
        assert t.pool == 2.0


# --- Client lifecycle tests ---


class TestClientLifecycle:
    def test_lazy_client_creation(self) -> None:
        client = _make_sync_client()
        assert client._client is None
        http = client._ensure_client()
        assert isinstance(http, httpx.Client)
        assert client._client is http

    def test_close(self) -> None:
        client = _make_sync_client()
        client._ensure_client()
        assert client._client is not None
        client.close()
        assert client._client is None

    def test_custom_http_client_not_closed(self) -> None:
        custom = httpx.Client()
        client = _make_sync_client(http_client=custom)
        assert client._client is custom
        assert client._owns_client is False
        client.close()
        # Custom client should still be there (not None'd, not closed by us)
        assert client._client is custom
        custom.close()
