"""Recorded resource payload fixtures."""
GATEWAY = "http://test-gateway:8080"


AGENTCC_HEADERS = {
    "x-agentcc-request-id": "req-1",
    "x-agentcc-trace-id": "t-1",
    "x-agentcc-provider": "openai",
    "x-agentcc-latency-ms": "10",
}


COMPLETIONS_RESPONSE = {
    "id": "cmpl-abc",
    "object": "text_completion",
    "created": 1700000000,
    "model": "gpt-3.5-turbo-instruct",
    "choices": [{"text": "Hello world!", "index": 0, "finish_reason": "stop"}],
    "usage": {"prompt_tokens": 3, "completion_tokens": 2, "total_tokens": 5},
}


SPEECH_AUDIO_BYTES = b"\xff\xfb\x90\x00\x00\x00\x00" * 100  # fake MP3 bytes
