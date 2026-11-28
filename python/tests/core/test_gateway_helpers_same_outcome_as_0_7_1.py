"""The gateway helpers and clients give a caller of 0.7.1 the outcome 0.7.1 gave, for the URLs below.

``check_valid_key`` reports a refused or unreadable destination as ``False`` and ``health_check`` as an ``error`` status; a
gateway client called with a URL the HTTP library cannot read raises the library's ``httpx.InvalidURL``; a user-info URL
for a Future AGI host over plain http raises ``InsecureHttpRefusedError`` (code ``INSECURE_HTTP_REFUSED``). Every refusal
happens before a name is looked up or a socket is opened, so none of these needs a listener: the egress guard of this
package fails a test that tried to leave the machine."""

from __future__ import annotations

import asyncio

import httpx
import pytest

from fi.gateway import AgentCC, AsyncAgentCC
from fi.gateway._utils import check_valid_key, health_check
from fi.utils.errors import InsecureHttpRefusedError

KEY = "FIMARKERKEY-0b7e41d9"
FUTURE_AGI_PLAIN = [
    "http://api.futureagi.com",
    "http://a.b.futureagi.com:8080",
    "HTTP://API.FutureAGI.com/",
    "http://api.futureagi.com./",
    "http://user:pw@api.futureagi.com",
]
UNREADABLE = ["http://0177.0.0.1:1", "http://ａpi.futureagi.com:1"]


@pytest.mark.parametrize("flag", [None, "1"])
@pytest.mark.parametrize("base", FUTURE_AGI_PLAIN)
def test_check_valid_key_reports_false_for_plain_http_to_a_future_agi_host(monkeypatch, flag, base):
    if flag is not None:
        monkeypatch.setenv("FI_ALLOW_INSECURE_HTTP", flag)
    assert check_valid_key(KEY, base) is False


@pytest.mark.parametrize("base", ["http://gw.selfhosted.example", "http://user:pw@127.0.0.1:1", *UNREADABLE])
def test_check_valid_key_reports_false_for_a_destination_it_refuses(monkeypatch, base):
    monkeypatch.delenv("FI_ALLOW_INSECURE_HTTP", raising=False)
    assert check_valid_key(KEY, base) is False


@pytest.mark.parametrize("base", UNREADABLE)
def test_health_check_reports_an_error_status_for_a_url_the_library_cannot_read(monkeypatch, base):
    monkeypatch.setenv("FI_ALLOW_INSECURE_HTTP", "1")
    assert health_check(api_key=KEY, base_url=base)["status"] == "error"


@pytest.mark.parametrize("flag", [None, "1"])
@pytest.mark.parametrize("base", UNREADABLE)
def test_the_gateway_clients_raise_the_library_error_for_a_url_it_cannot_read(monkeypatch, flag, base):
    if flag is None:
        monkeypatch.delenv("FI_ALLOW_INSECURE_HTTP", raising=False)
    else:
        monkeypatch.setenv("FI_ALLOW_INSECURE_HTTP", flag)
    client = AgentCC(api_key=KEY, base_url=base, max_retries=0)
    try:
        with pytest.raises(httpx.InvalidURL):
            client.models.list()
    finally:
        client.close()

    async def go():
        async_client = AsyncAgentCC(api_key=KEY, base_url=base, max_retries=0)
        try:
            return await async_client.models.list()
        finally:
            await async_client.aclose()

    with pytest.raises(httpx.InvalidURL):
        asyncio.run(go())


def test_the_gateway_clients_name_a_future_agi_host_given_with_user_info():
    base = "http://user:pw@api.futureagi.com"
    client = AgentCC(api_key=KEY, base_url=base, max_retries=0)
    try:
        with pytest.raises(InsecureHttpRefusedError) as info:
            client.models.list()
    finally:
        client.close()
    assert info.value.get_error_code() == "INSECURE_HTTP_REFUSED"

    async def go():
        async_client = AsyncAgentCC(api_key=KEY, base_url=base, max_retries=0)
        try:
            return await async_client.models.list()
        finally:
            await async_client.aclose()

    with pytest.raises(InsecureHttpRefusedError) as info:
        asyncio.run(go())
    assert info.value.get_error_code() == "INSECURE_HTTP_REFUSED"
