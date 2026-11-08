"""Header, URL, timeout and lifecycle configuration."""
from __future__ import annotations

import httpx
import pytest
import respx
from typing import Any
from fi.gateway._base_client import RequestOptions, RetryConfig, Timeout
from ._base_client_fixtures import _MockResponse, _make_sync_client
import json
from fi.gateway._constants import NOT_GIVEN


class TestBuildHeaders:
    def test_sdk_auto_headers_present(self) -> None:
        client = _make_sync_client(base_url="https://gateway.test")
        opts = RequestOptions(method="POST", url="/v1/chat/completions")
        headers, _ = client._build_headers(opts)
        assert headers["User-Agent"].startswith("agentcc-python/")
        assert headers["Content-Type"] == "application/json"
        assert "x-agentcc-sdk-version" in headers

    def test_auth_header_present(self) -> None:
        client = _make_sync_client(base_url="https://gateway.test")
        opts = RequestOptions(method="POST", url="/v1/chat/completions")
        headers, _ = client._build_headers(opts)
        assert headers["Authorization"] == "Bearer sk-test-key-12345"

    def test_agentcc_params_session_id_and_cache_ttl(self) -> None:
        client = _make_sync_client(base_url="https://gateway.test")
        opts = RequestOptions(method="POST", url="/v1/chat/completions")
        headers, _ = client._build_headers(
            opts, agentcc_params={"session_id": "abc", "cache_ttl": "10m"}
        )
        assert headers["x-agentcc-session-id"] == "abc"
        assert headers["x-agentcc-cache-ttl"] == "10m"

    def test_per_request_headers_override_defaults(self) -> None:
        client = _make_sync_client(base_url="https://gateway.test", default_headers={"x-custom": "default"})
        opts = RequestOptions(
            method="POST", url="/v1/test", headers={"x-custom": "override"}
        )
        headers, _ = client._build_headers(opts)
        assert headers["x-custom"] == "override"

    def test_request_metadata_serialized_as_json(self) -> None:
        client = _make_sync_client(base_url="https://gateway.test")
        opts = RequestOptions(method="POST", url="/v1/test")
        meta = {"user": "test", "session": 123}
        headers, _ = client._build_headers(opts, agentcc_params={"request_metadata": meta})
        parsed = json.loads(headers["x-agentcc-metadata"])
        assert parsed == meta

    def test_client_level_session_id(self) -> None:
        client = _make_sync_client(base_url="https://gateway.test", session_id="client-session")
        opts = RequestOptions(method="POST", url="/v1/test")
        headers, _ = client._build_headers(opts)
        assert headers["x-agentcc-session-id"] == "client-session"

    def test_per_request_overrides_client_session_id(self) -> None:
        client = _make_sync_client(base_url="https://gateway.test", session_id="client-session")
        opts = RequestOptions(method="POST", url="/v1/test")
        headers, _ = client._build_headers(
            opts, agentcc_params={"session_id": "request-session"}
        )
        assert headers["x-agentcc-session-id"] == "request-session"

    def test_not_given_params_skipped(self) -> None:
        client = _make_sync_client(base_url="https://gateway.test")
        opts = RequestOptions(method="POST", url="/v1/test")
        headers, _ = client._build_headers(
            opts, agentcc_params={"session_id": NOT_GIVEN, "cache_ttl": None}
        )
        assert "x-agentcc-session-id" not in headers
        assert "x-agentcc-cache-ttl" not in headers

    def test_client_level_metadata(self) -> None:
        client = _make_sync_client(base_url="https://gateway.test", metadata={"user": "global"})
        opts = RequestOptions(method="POST", url="/v1/test")
        headers, _ = client._build_headers(opts)
        parsed = json.loads(headers["x-agentcc-metadata"])
        assert parsed == {"user": "global"}


class TestBuildUrl:
    def test_basic_join(self) -> None:
        client = _make_sync_client(base_url="https://gateway.example.com")
        assert (
            client._build_url("/v1/chat/completions")
            == "https://gateway.example.com/v1/chat/completions"
        )

    def test_trailing_slash_on_base(self) -> None:
        client = _make_sync_client(base_url="https://gateway.example.com/")
        assert (
            client._build_url("/v1/chat/completions")
            == "https://gateway.example.com/v1/chat/completions"
        )

    def test_no_leading_slash_on_path(self) -> None:
        client = _make_sync_client(base_url="https://gateway.example.com")
        assert (
            client._build_url("v1/chat/completions")
            == "https://gateway.example.com/v1/chat/completions"
        )

    def test_absolute_url_returned_as_is(self) -> None:
        from fi.gateway import AgentCCError

        client = _make_sync_client(base_url="https://other.com")
        assert client._build_url("https://other.com/api") == "https://other.com/api"
        with pytest.raises(AgentCCError, match="explicitly configured origin"):
            client._build_url("https://unconfigured.test/api")


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


class TestClientLifecycle:
    def test_lazy_client_creation(self) -> None:
        client = _make_sync_client(base_url="https://gateway.test")
        assert client._client is None
        http = client._ensure_client()
        assert isinstance(http, httpx.Client)
        assert client._client is http

    def test_close(self) -> None:
        client = _make_sync_client(base_url="https://gateway.test")
        client._ensure_client()
        assert client._client is not None
        client.close()
        assert client._client is None

    def test_custom_http_client_not_closed(self) -> None:
        custom = httpx.Client()
        client = _make_sync_client(base_url="https://gateway.test", http_client=custom)
        assert client._client is custom
        assert client._owns_client is False
        client.close()
        # Custom client should still be there (not None'd, not closed by us)
        assert client._client is custom
        custom.close()
