from __future__ import annotations

import os
from pathlib import Path

import pytest

ENV_FILE = Path(__file__).resolve().parents[3] / ".env.local"


def _load_env_file() -> None:
    if not ENV_FILE.exists():
        return
    for line in ENV_FILE.read_text().splitlines():
        key, _, value = line.partition("=")
        if key and value:
            os.environ.setdefault(key.strip(), value.strip())


_load_env_file()


def _require_backend() -> None:
    if not (os.environ.get("FI_API_KEY") and os.environ.get("FI_SECRET_KEY") and os.environ.get("FI_BASE_URL")):
        pytest.skip("no backend configured: run sdkgen/local_api_key.py (writes .env.local)")


@pytest.fixture
def client():
    _require_backend()
    from fi.platform import Client

    # strict: a response that does not match the contract fails the test instead of warning
    with Client(strict_responses=True) as client:
        yield client


# --------------------------------------------------------------------------- #
# Coverage: which catalog operations did the live tests actually call?
# --------------------------------------------------------------------------- #

CALLED: dict[str, list[str]] = {}  # op id -> outcomes ("ok" or the HTTP status of an APIError)


@pytest.fixture(scope="session", autouse=True)
def record_calls():
    from fi.platform import APIError
    from fi.platform._transport import AsyncTransport, SyncTransport

    sync_request, async_request = SyncTransport.request, AsyncTransport.request

    def record(op, outcome):
        if not op.id.startswith("raw:"):  # client.request() / resource .raw() calls are not catalog ops
            CALLED.setdefault(op.id, []).append(outcome)

    def request(self, op, **kwargs):
        try:
            result = sync_request(self, op, **kwargs)
        except APIError as exc:
            record(op, str(exc.status_code))
            raise
        record(op, "ok")
        return result

    async def arequest(self, op, **kwargs):
        try:
            result = await async_request(self, op, **kwargs)
        except APIError as exc:
            record(op, str(exc.status_code))
            raise
        record(op, "ok")
        return result

    SyncTransport.request, AsyncTransport.request = request, arequest
    yield CALLED
    SyncTransport.request, AsyncTransport.request = sync_request, async_request
