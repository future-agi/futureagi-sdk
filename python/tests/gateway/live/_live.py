"""Helpers of the live wire suite: the running stack as tests see it."""

from __future__ import annotations

import hashlib
import json
import os
import pathlib
import uuid
from typing import Any

import httpx

LIVE_BASE = os.environ.get("FI_GATEWAY_LIVE_BASE_URL", "")


def sha12(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()[:12]


class Live:
    """The running stack, as the tests see it."""

    def __init__(self) -> None:
        self.base = LIVE_BASE.rstrip("/")
        self.tap = os.environ["FI_GATEWAY_LIVE_TAP_URL"].rstrip("/")
        self.mock = os.environ["FI_GATEWAY_LIVE_MOCK_URL"].rstrip("/")
        self.keys: dict[str, Any] = json.loads(pathlib.Path(os.environ["FI_GATEWAY_LIVE_KEYS"]).read_text())
        self.block_word = os.environ["FI_GATEWAY_LIVE_BLOCK_WORD"]
        self.upstream_key_sha12 = os.environ.get("FI_GATEWAY_LIVE_UPSTREAM_KEY_SHA12", "")
        self.evidence = pathlib.Path(os.environ.get("FI_GATEWAY_LIVE_EVIDENCE", "/tmp/gw-live-evidence")) / "py"
        self.evidence.mkdir(parents=True, exist_ok=True)

    @property
    def key(self) -> str:
        return self.keys["plain"]["key"]

    @property
    def override_key(self) -> str:
        return self.keys["override"]["key"]

    @staticmethod
    def marker() -> str:
        """A unique tag a test puts in its prompt, to find its requests in the records."""
        return f"[[id:{uuid.uuid4().hex[:12]}]]"

    def _records(self, base: str, route: str, marker: str | None) -> list[dict]:
        rows = httpx.get(f"{base}{route}", timeout=10).json()
        if marker is None:
            return rows
        return [r for r in rows if marker in json.dumps(r.get("body"))]

    def mock_records(self, marker: str | None = None) -> list[dict]:
        """What the gateway forwarded to the upstream."""
        return self._records(self.mock, "/__mock/requests", marker)

    def tap_records(self, marker: str | None = None) -> list[dict]:
        """What the client put on the wire to the gateway (requests sent through the tap)."""
        return self._records(self.tap, "/__tap/requests", marker)

    def last_tap_seq(self) -> int:
        rows = self.tap_records()
        return rows[-1]["seq"] if rows else 0

    def tap_since(self, seq: int) -> list[dict]:
        return httpx.get(f"{self.tap}/__tap/requests?since={seq}", timeout=10).json()

    def record(self, name: str, data: Any) -> None:
        """Write an observation to the evidence directory (never a key: tokens are hashed)."""
        (self.evidence / f"{name}.json").write_text(json.dumps(data, indent=1, sort_keys=True, default=str))

    def raw(self) -> httpx.Client:
        return httpx.Client(base_url=self.base, timeout=30)

    def auth(self, key: str | None = None) -> dict[str, str]:
        return {"Authorization": f"Bearer {key or self.key}"}

    def sse(self, path: str, body: dict, headers: dict[str, str] | None = None) -> tuple[int, dict, list[str]]:
        """POST a stream request with httpx: (status, response headers, the raw SSE lines)."""
        with httpx.Client(base_url=self.base, timeout=60) as c:
            with c.stream("POST", path, json=body, headers={**self.auth(), **(headers or {})}) as resp:
                text = "".join(resp.iter_text())
                return resp.status_code, dict(resp.headers), text.split("\n")


def data_frames(lines: list[str]) -> list[str]:
    """The data payloads of an SSE body, in order."""
    return [ln[len("data: "):] for ln in lines if ln.startswith("data: ")]


def user(text: str) -> list[dict[str, str]]:
    return [{"role": "user", "content": text}]
