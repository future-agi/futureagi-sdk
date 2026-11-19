"""Live wire suite for fi.gateway against a real agentcc-gateway.

Gated: every test here is skipped unless ``FI_GATEWAY_LIVE_BASE_URL`` is set, so the
fixed CI line (``pytest -q python/tests``) collects and skips them. The stack they need
(the gateway built at the recorded source, the mock upstream, the wire tap and minted virtual
keys) is started by ``stack/run-wire-suite.sh`` on a disposable build machine.

Environment, all set by run-wire-suite.sh:
- ``FI_GATEWAY_LIVE_BASE_URL``: the gateway origin.
- ``FI_GATEWAY_LIVE_TAP_URL``: the recording proxy in front of it (stack/wiretap.py).
- ``FI_GATEWAY_LIVE_MOCK_URL``: the mock upstream (stack/mock_upstream.py).
- ``FI_GATEWAY_LIVE_KEYS``: a JSON file of the keys minted for this run.
- ``FI_GATEWAY_LIVE_EVIDENCE``: where tests write what they observed (JSON).
- ``FI_GATEWAY_LIVE_BLOCK_WORD``: the word the gateway's keyword guardrail blocks.
"""

from __future__ import annotations

import pathlib
from typing import Any

import pytest

from ._live import LIVE_BASE, Live

HERE = pathlib.Path(__file__).resolve().parent

# Variables a test may set; cleared around each test so resolution starts empty.
_ENV_NAMES = (
    "FI_GATEWAY_API_KEY", "FI_GATEWAY_BASE_URL", "AGENTCC_API_KEY", "AGENTCC_BASE_URL",
    "FI_API_KEY", "FI_SECRET_KEY", "FI_PLATFORM_TOKEN", "OPENAI_API_KEY", "OPENAI_BASE_URL",
    "OPENAI_ORG_ID", "OPENAI_PROJECT_ID",
)


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    if LIVE_BASE:
        return
    skip = pytest.mark.skip(reason="live gateway suite: set FI_GATEWAY_LIVE_BASE_URL (stack/run-wire-suite.sh)")
    for item in items:
        if HERE in pathlib.Path(str(item.fspath)).resolve().parents:
            item.add_marker(skip)


@pytest.fixture(scope="session")
def live() -> Live:
    return Live()


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in _ENV_NAMES:
        monkeypatch.delenv(name, raising=False)


@pytest.fixture
def client(live: Live) -> Any:
    from fi.gateway import AgentCC

    c = AgentCC(api_key=live.key, base_url=live.base, max_retries=0)
    yield c
    c.close()


@pytest.fixture
def tapped(live: Live) -> Any:
    """A client that sends through the wire tap."""
    from fi.gateway import AgentCC

    c = AgentCC(api_key=live.key, base_url=live.tap, max_retries=0)
    yield c
    c.close()
