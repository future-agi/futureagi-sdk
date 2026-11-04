"""Regression tests for bugs found by running fi.gateway against a real gateway."""

from __future__ import annotations

import io

import httpx
import respx

from fi.gateway import Gateway

BASE = "http://gw.test"
COMPLETION = {
    "id": "chatcmpl-1",
    "object": "chat.completion",
    "created": 1,
    "model": "gpt-4o-mini",
    "choices": [{"index": 0, "message": {"role": "assistant", "content": "hi"}, "finish_reason": "stop"}],
    "usage": {"prompt_tokens": 3, "completion_tokens": 2, "total_tokens": 5},
}


def _gw() -> Gateway:
    return Gateway(api_key="sk-agentcc-x", base_url=BASE, max_retries=0)


@respx.mock
def test_transcription_uploads_multipart_not_json() -> None:
    route = respx.post(f"{BASE}/v1/audio/transcriptions").mock(return_value=httpx.Response(200, json={"text": "hello"}))
    result = _gw().audio.transcriptions.create(model="whisper-1", file=("a.mp3", io.BytesIO(b"ID3audio")), language="en")

    assert result.text == "hello"
    request = route.calls.last.request
    assert request.headers["content-type"].startswith("multipart/form-data; boundary=")
    body = request.content
    assert b'name="model"' in body and b"whisper-1" in body
    assert b'name="language"' in body
    assert b'name="file"; filename="a.mp3"' in body and b"ID3audio" in body


@respx.mock
def test_translation_uploads_multipart() -> None:
    route = respx.post(f"{BASE}/v1/audio/translations").mock(return_value=httpx.Response(200, json={"text": "hello"}))
    _gw().audio.translations.create(model="whisper-1", file=("a.mp3", io.BytesIO(b"ID3")))
    assert route.calls.last.request.headers["content-type"].startswith("multipart/form-data")


@respx.mock
def test_json_requests_keep_json_content_type() -> None:
    route = respx.post(f"{BASE}/v1/chat/completions").mock(return_value=httpx.Response(200, json=COMPLETION))
    _gw().chat.completions.create(model="gpt-4o-mini", messages=[{"role": "user", "content": "hi"}])
    assert route.calls.last.request.headers["content-type"] == "application/json"


@respx.mock
def test_embedding_usage_without_completion_tokens() -> None:
    # Embedding responses carry only prompt/total tokens.
    respx.post(f"{BASE}/v1/embeddings").mock(
        return_value=httpx.Response(
            200,
            json={
                "object": "list",
                "model": "text-embedding-3-small",
                "data": [{"object": "embedding", "index": 0, "embedding": [0.1, 0.2]}],
                "usage": {"prompt_tokens": 2, "total_tokens": 2},
            },
        )
    )
    result = _gw().embeddings.create(model="text-embedding-3-small", input="hello")
    assert result.usage.total_tokens == 2 and result.usage.completion_tokens == 0


@respx.mock
def test_session_tracks_requests_cost_and_tokens() -> None:
    respx.post(f"{BASE}/v1/chat/completions").mock(
        return_value=httpx.Response(200, json=COMPLETION, headers={"x-agentcc-cost": "0.0025"})
    )
    gw = _gw()
    with gw.session(name="checkout", session_id="s-1") as session:
        session.step("plan")
        gw.chat.completions.create(model="gpt-4o-mini", messages=[{"role": "user", "content": "hi"}])
        session.step("act")
        gw.chat.completions.create(model="gpt-4o-mini", messages=[{"role": "user", "content": "hi"}])
    assert session.request_count == 2
    assert session.total_tokens == 10
    assert abs(session.total_cost - 0.005) < 1e-12

    # Outside the session nothing is tracked.
    gw.chat.completions.create(model="gpt-4o-mini", messages=[{"role": "user", "content": "hi"}])
    assert session.request_count == 2
