"""D-19: the client logs on ``fi.gateway`` (agentcc 1.0 used ``agentcc``)."""

from __future__ import annotations

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


def test_the_logging_callback_defaults_to_fi_gateway() -> None:
    assert LoggingCallback()._logger.name == "fi.gateway"
    assert LoggingCallback(logger_name="mine")._logger.name == "mine"


def test_no_module_asks_for_an_agentcc_logger() -> None:
    pattern = re.compile(r"getLogger\(\s*[\"']agentcc")
    hits = [
        str(p.relative_to(PACKAGE))
        for p in PACKAGE.rglob("*.py")
        if pattern.search(p.read_text(encoding="utf-8"))
    ]
    assert hits == []
