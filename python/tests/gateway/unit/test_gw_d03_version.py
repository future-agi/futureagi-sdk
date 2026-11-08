"""D-03: ``__version__``, User-Agent and x-agentcc-sdk-version carry the futureagi version.

The released ``agentcc-python`` prefix is unchanged. Both header versions now
follow the distribution, including the no-send request inspection helper.
"""

from __future__ import annotations

import importlib.metadata
from pathlib import Path

import httpx

import fi.gateway as gw
from fi.gateway._version import futureagi_version

PYPROJECT = Path(__file__).resolve().parents[3] / "pyproject.toml"
COMPLETION = {
    "id": "c",
    "object": "chat.completion",
    "created": 1,
    "model": "m",
    "choices": [{"index": 0, "message": {"role": "assistant", "content": "hi"}}],
}


def _declared_version() -> str:
    for line in PYPROJECT.read_text(encoding="utf-8").splitlines():
        if line.strip().startswith("version = "):
            return line.split("=", 1)[1].strip().strip('"')
    raise AssertionError("no version in pyproject.toml")


def test_version_is_the_futureagi_distribution_version() -> None:
    try:
        expected = importlib.metadata.version("futureagi")
    except importlib.metadata.PackageNotFoundError:
        expected = _declared_version()
    assert gw.__version__ == expected == futureagi_version()
    assert gw.__version__ != "0.1.0"


def test_a_source_tree_reads_the_declared_version(monkeypatch) -> None:
    def missing(name: str) -> str:
        raise importlib.metadata.PackageNotFoundError(name)

    monkeypatch.setattr("fi.gateway._version.version", missing)
    assert futureagi_version() == _declared_version()


def test_both_headers_carry_it_on_the_wire() -> None:
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(200, json=COMPLETION)

    client = gw.AgentCC(
        api_key="k",
        base_url="http://127.0.0.1:9",
        http_client=httpx.Client(transport=httpx.MockTransport(handler)),
    )
    client.chat.completions.create(model="m", messages=[])
    headers = seen[0].headers
    assert headers["user-agent"] == f"agentcc-python/{gw.__version__}"
    assert headers["x-agentcc-sdk-version"] == gw.__version__
