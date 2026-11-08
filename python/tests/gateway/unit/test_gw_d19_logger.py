"""D-19: the client logs on ``fi.gateway`` (agentcc 1.0 used ``agentcc``).

The opt-in ``LoggingCallback`` keeps its published ``agentcc`` default logger.
"""

from __future__ import annotations

import pytest

import logging
import re
from pathlib import Path

import httpx

from fi.gateway import AgentCC
from fi.gateway.callbacks.logging import LoggingCallback

PACKAGE = Path(__file__).resolve().parents[3] / "fi" / "gateway"
COMPLETION = {
    "id": "c",
    "object": "chat.completion",
    "created": 1,
    "model": "m",
    "choices": [{"index": 0, "message": {"role": "assistant", "content": "hi"}}],
}


class _Broken:
    def on_request_start(self, request: object) -> None:
        raise RuntimeError("callback bug")


@pytest.mark.filterwarnings('default:^Deprecated\\ gateway\\ compatibility\\ options:DeprecationWarning')
def test_a_failing_callback_is_logged_on_fi_gateway(caplog) -> None:
    transport = httpx.MockTransport(
        lambda request: httpx.Response(200, json=COMPLETION)
    )
    client = AgentCC(
        api_key="k",
        base_url="http://127.0.0.1:9",
        callbacks=[_Broken()],
        http_client=httpx.Client(transport=transport),
    )
    with caplog.at_level(logging.DEBUG):
        client.chat.completions.create(model="m", messages=[])
    names = {r.name for r in caplog.records if "raised an exception" in r.getMessage()}
    assert names == {"fi.gateway"}
    assert not [r for r in caplog.records if r.name.startswith("agentcc")]


def test_the_logging_callback_keeps_its_published_default_logger() -> None:
    # LoggingCallback writes where 0.7.0 did; the fi.gateway namespace is an explicit choice.
    assert LoggingCallback()._logger.name == "agentcc"
    assert LoggingCallback(logger_name="fi.gateway")._logger.name == "fi.gateway"
    assert LoggingCallback(logger_name="mine")._logger.name == "mine"


def test_no_module_asks_for_an_agentcc_logger() -> None:
    pattern = re.compile(r"getLogger\(\s*[\"']agentcc")
    hits = [
        str(p.relative_to(PACKAGE))
        for p in PACKAGE.rglob("*.py")
        if pattern.search(p.read_text(encoding="utf-8"))
    ]
    assert hits == ["callbacks/json_logger.py"]
    from fi.gateway.callbacks.json_logger import JSONLoggingCallbackHandler

    with pytest.warns(DeprecationWarning, match="JSONLoggingCallbackHandler"):
        legacy = JSONLoggingCallbackHandler()
    assert legacy._logger.name == "agentcc.json_logger"
