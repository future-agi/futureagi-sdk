"""Shared fixture data (tests/fixtures/gateway/*.json) and reply builders."""

from __future__ import annotations

import copy
import json
from functools import lru_cache
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[4]
FIXTURES = REPO / "tests" / "fixtures" / "gateway"
GOLDEN = FIXTURES / "golden"
MSG = [{"role": "user", "content": "Say hello"}]


@lru_cache(maxsize=None)
def _load(name: str) -> Any:
    return json.loads((FIXTURES / name).read_text())


def load(name: str) -> Any:
    return copy.deepcopy(_load(name))


def body(key: str) -> Any:
    return load("responses.json")["bodies"][key]


def chunks(key: str) -> list[str]:
    return load("responses.json")["chunks"][key]


def response_headers(key: str) -> dict[str, str]:
    return load("responses.json")["response_headers"][key]


def envelope(key: str) -> Any:
    return load("responses.json")["error_envelopes"][key]


def statuses() -> list[int]:
    return load("responses.json")["statuses"]


def ok(
    key: str, *, status: int = 200, headers: dict[str, str] | None = None
) -> dict[str, Any]:
    value = body(key)
    if isinstance(value, str):
        return {
            "status": status,
            "headers": {"content-type": "application/octet-stream", **(headers or {})},
            "text": value,
        }
    return {"status": status, "headers": headers or {}, "json": value}


def sse(
    frames: list[str], *, headers: dict[str, str] | None = None, status: int = 200
) -> dict[str, Any]:
    return {"status": status, "headers": headers or {}, "sse": frames}


def error_reply(
    status: int, kind: str, headers: dict[str, str] | None = None
) -> dict[str, Any]:
    value = envelope(kind)
    if isinstance(value, str):
        return {"status": status, "headers": headers or {}, "text": value}
    return {"status": status, "headers": headers or {}, "json": value}


def stream_error_cases() -> list[dict[str, Any]]:
    return load("stream-error-frames.json")["cases"]


def stream_extra_cases() -> list[dict[str, Any]]:
    return load("stream-cases-extra.json")["cases"]
