"""``health_check()`` asks ``GET /healthz``, the gateway's liveness route.

The client falls back to ``/health`` only after a 404 from ``/healthz``.
Other HTTP errors and connection failures do not trigger fallback.
"""

from __future__ import annotations

import httpx
import pytest

from fi.gateway import health_check


@pytest.fixture
def calls(monkeypatch: pytest.MonkeyPatch) -> list[tuple[str, dict]]:
    seen: list[tuple[str, dict]] = []

    def fake_get(url: str, **kwargs: object) -> httpx.Response:
        seen.append((url, dict(kwargs)))
        if url.endswith("/healthz"):
            return httpx.Response(200, json={"status": "ok"})
        return httpx.Response(404)

    monkeypatch.setattr("fi.gateway._utils.httpx.get", fake_get)
    return seen


def test_the_liveness_route_is_asked(calls) -> None:
    result = health_check(base_url="https://gateway.example.test", api_key="k")
    assert result["status"] == "ok"
    assert [url for url, _ in calls] == ["https://gateway.example.test/healthz"]
    assert calls[0][1]["headers"] == {"Authorization": "Bearer k"}


def test_a_v1_base_url_asks_the_origin(calls) -> None:
    assert health_check(base_url="https://gateway.example.test/v1/")["status"] == "ok"
    assert calls[0][0] == "https://gateway.example.test/healthz"


def test_a_gateway_without_healthz_is_an_error_naming_the_status(monkeypatch) -> None:
    calls = []

    def get(url, **kwargs):
        calls.append(url)
        return httpx.Response(404)

    monkeypatch.setattr("fi.gateway._utils.httpx.get", get)
    result = health_check(base_url="https://gateway.example.test")
    assert result["status"] == "error" and result["error"] == "HTTP 404"
    assert calls == ["https://gateway.example.test/healthz", "https://gateway.example.test/health"]


def test_only_a_404_uses_the_released_health_fallback(monkeypatch) -> None:
    calls = []

    def get(url, **kwargs):
        calls.append((url, kwargs))
        return httpx.Response(404 if url.endswith("/healthz") else 200)

    monkeypatch.setattr("fi.gateway._utils.httpx.get", get)
    result = health_check(base_url="https://gateway.example.test", api_key="k", timeout=3)
    assert result["status"] == "ok"
    assert [url for url, _ in calls] == [
        "https://gateway.example.test/healthz", "https://gateway.example.test/health",
    ]
    # A remote gateway's health request keeps the environment (proxy and NO_PROXY): nothing is switched off.
    assert calls[0][1] == calls[1][1] == {
        "headers": {"Authorization": "Bearer k"}, "timeout": 3, "follow_redirects": False,
    }


@pytest.mark.parametrize("failure", [500, "connection"])
def test_other_failures_never_try_health(monkeypatch, failure) -> None:
    calls = []

    def get(url, **kwargs):
        calls.append(url)
        if failure == "connection":
            raise httpx.ConnectError("connection refused")
        return httpx.Response(failure)

    monkeypatch.setattr("fi.gateway._utils.httpx.get", get)
    result = health_check(base_url="https://gateway.example.test")
    assert result["status"] == "error"
    assert result["error"] == ("HTTP 500" if failure == 500 else "connection refused")
    assert calls == ["https://gateway.example.test/healthz"]


def test_with_a_model_it_sends_one_minimal_completion(monkeypatch) -> None:
    posts: list[tuple[str, dict]] = []

    def fake_post(url: str, **kwargs: object) -> httpx.Response:
        posts.append((url, dict(kwargs)))
        return httpx.Response(200, json={})

    monkeypatch.setattr("fi.gateway._utils.httpx.post", fake_post)
    assert health_check(model="m", base_url="https://gateway.example.test")["status"] == "ok"
    assert posts[0][0] == "https://gateway.example.test/v1/chat/completions"
    assert posts[0][1]["json"]["max_tokens"] == 1
