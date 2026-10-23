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


@pytest.fixture
def client():
    if not (os.environ.get("FI_API_KEY") and os.environ.get("FI_SECRET_KEY") and os.environ.get("FI_BASE_URL")):
        pytest.skip("no backend configured: run sdkgen/local_api_key.py (writes .env.local)")
    from fi.platform import Client

    with Client() as client:
        yield client
