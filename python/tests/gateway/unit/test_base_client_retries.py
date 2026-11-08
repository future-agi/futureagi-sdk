"""Retry policy and HTTP response handling."""
from __future__ import annotations

import httpx
import pytest
import respx
from typing import Any
from fi.gateway._base_client import RequestOptions, RetryConfig, Timeout
from ._base_client_fixtures import _MockResponse, _make_sync_client


class TestShouldRetry:
    def test_retryable_429_first_attempt(self) -> None:
        client = _make_sync_client(base_url="https://gateway.test")
        assert client._should_retry(429, attempt=0, max_retries=2) is True

    def test_retryable_429_exhausted(self) -> None:
        client = _make_sync_client(base_url="https://gateway.test")
        assert client._should_retry(429, attempt=2, max_retries=2) is False

    def test_not_retryable_400(self) -> None:
        client = _make_sync_client(base_url="https://gateway.test")
        assert client._should_retry(400, attempt=0, max_retries=2) is False

    def test_retryable_500(self) -> None:
        client = _make_sync_client(base_url="https://gateway.test")
        assert client._should_retry(500, attempt=0, max_retries=2) is True

    def test_retryable_502(self) -> None:
        client = _make_sync_client(base_url="https://gateway.test")
        assert client._should_retry(502, attempt=1, max_retries=3) is True

    def test_not_retryable_401(self) -> None:
        client = _make_sync_client(base_url="https://gateway.test")
        assert client._should_retry(401, attempt=0, max_retries=5) is False


class TestCalculateDelay:
    def test_respects_retry_after(self) -> None:
        client = _make_sync_client(base_url="https://gateway.test")
        delay = client._calculate_delay(0, {"retry-after": "2.5"})
        assert delay == 2.5

    def test_retry_after_capped(self) -> None:
        client = _make_sync_client(base_url="https://gateway.test", retry_config=RetryConfig(backoff_max=5.0))
        delay = client._calculate_delay(0, {"retry-after": "100"})
        assert delay == 5.0

    def test_exponential_backoff(self) -> None:
        client = _make_sync_client(
            base_url="https://gateway.test",
            retry_config=RetryConfig(backoff_factor=0.5, backoff_jitter=0.0)
        )
        d0 = client._calculate_delay(0)
        d1 = client._calculate_delay(1)
        d2 = client._calculate_delay(2)
        assert d0 == 0.5  # 0.5 * 2^0
        assert d1 == 1.0  # 0.5 * 2^1
        assert d2 == 2.0  # 0.5 * 2^2

    def test_backoff_capped(self) -> None:
        client = _make_sync_client(
            base_url="https://gateway.test",
            retry_config=RetryConfig(
                backoff_factor=1.0, backoff_max=3.0, backoff_jitter=0.0
            )
        )
        delay = client._calculate_delay(5)  # 1.0 * 2^5 = 32 → capped to 3.0
        assert delay == 3.0

    def test_jitter_within_range(self) -> None:
        client = _make_sync_client(
            base_url="https://gateway.test",
            retry_config=RetryConfig(backoff_factor=1.0, backoff_jitter=0.5)
        )
        delays = [client._calculate_delay(0) for _ in range(100)]
        # delay = 1.0 ± 0.5, so between 0.5 and 1.5
        assert all(0.5 <= d <= 1.5 for d in delays)


class TestProcessResponse:
    @respx.mock
    def test_parse_json_into_model(self) -> None:
        client = _make_sync_client(base_url="https://gateway.test")
        respx.post("https://gateway.test/v1/test").respond(
            200,
            json={"id": "abc", "content": "hello"},
            headers={
                "x-agentcc-request-id": "01ARZ3NDEKTSV4RRFFQ69G5FAV",
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
        assert result.agentcc.request_id == "01ARZ3NDEKTSV4RRFFQ69G5FAV"  # type: ignore[attr-defined]
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


class TestRetryIntegration:
    @respx.mock
    def test_retries_429_then_succeeds(self) -> None:
        client = _make_sync_client(
            base_url="https://gateway.test",
            max_retries=2,
            retry_config=RetryConfig(
                max_retries=2, backoff_factor=0.01, backoff_jitter=0.0
            ),
        )
        route = respx.post("https://gateway.test/v1/test")
        route.side_effect = [
            httpx.Response(429, json={"error": {"message": "Rate limited"}}),
            httpx.Response(
                200,
                json={"id": "abc", "content": "hello"},
                headers={
                    "x-agentcc-request-id": "01ARZ3NDEKTSV4RRFFQ69G5FAV",
                    "x-agentcc-trace-id": "trace-1",
                    "x-agentcc-provider": "openai",
                    "x-agentcc-latency-ms": "50",
                },
            ),
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
            retry_config=RetryConfig(
                max_retries=1, backoff_factor=0.01, backoff_jitter=0.0
            ),
        )
        respx.post("https://gateway.test/v1/test").respond(
            429,
            json={"error": {"message": "Rate limited"}},
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


def test_cleartext_origin_warns_and_still_sends(wire_snapshot) -> None:
    from fi.gateway._deprecation import AgentCCDeprecationWarning

    seen = []

    def handler(request):
        seen.append(wire_snapshot(request))
        return httpx.Response(200, json={"id": "reply", "content": "ok"})

    with httpx.Client(transport=httpx.MockTransport(handler)) as http:
        client = _make_sync_client(base_url="http://gateway.test", http_client=http)
        opts = RequestOptions(method="POST", url="/v1/test", body={"test": True})
        with pytest.warns(
            AgentCCDeprecationWarning,
            match=r"^futureagi: sending gateway credentials in cleartext over HTTP to http://gateway\.test\.",
        ) as caught:
            result = client._request(opts, _MockResponse)
        assert len(caught) == 1
        assert result.id == "reply" and result.content == "ok"
        assert len(seen) == 1
        assert seen[0].method == "POST"
        assert str(seen[0].url) == "http://gateway.test/v1/test"
        assert seen[0].headers["authorization"] == "Bearer sk-test-key-12345"
        assert seen[0].content == b'{"test":true}'
        # Warning deduplication is per client; under warnings-as-errors the
        # next successful send must not warn again.
        assert client._request(opts, _MockResponse).id == "reply"
        assert len(seen) == 2
