"""D-15: a ``with_options()`` copy sends its own options, whenever it is made.

agentcc 1.x gave a copy the parent's transport once the parent had sent a request.
That transport had frozen the parent's timeout, retries, headers, session and
metadata, so the copy's own were dropped, and a copy of a used copy sent the first
copy's session id (one tenant's id on another tenant's requests). A copy made before
the parent's first request built its own transport and httpx client, so the two
shared no connections and the copy's pool was never closed. Now every client builds
its own transport and all of them send through one shared httpx client.
"""

from __future__ import annotations

import httpx
import pytest

from fi.gateway import AgentCC, AsyncAgentCC, InternalServerError

GW = "http://127.0.0.1:8090"
COMPLETION = {
    "id": "c",
    "object": "chat.completion",
    "created": 1,
    "model": "m",
    "choices": [{"index": 0, "message": {"role": "assistant", "content": "hi"}}],
}
HEADERS = (
    "x-agentcc-trace-id",
    "x-extra",
    "x-agentcc-session-id",
    "x-agentcc-metadata",
)


def _wire(request: httpx.Request) -> dict[str, object]:
    out: dict[str, object] = {h: request.headers.get(h) for h in HEADERS}
    out["read_timeout"] = request.extensions["timeout"]["read"]
    return out


def _client(seen: list[httpx.Request], status: list[int] | None = None) -> AgentCC:
    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        code = status.pop(0) if status else 200
        if code != 200:
            return httpx.Response(code, json={"error": {"message": "boom"}})
        return httpx.Response(200, json=COMPLETION)

    return AgentCC(
        api_key="k",
        base_url=GW,
        timeout=600,
        http_client=httpx.Client(transport=httpx.MockTransport(handler)),
    )


def _send(client: AgentCC) -> None:
    client.chat.completions.create(model="m", messages=[])


COPY_OPTIONS = {
    "trace_id": "T1",
    "extra_headers": {"x-extra": "E"},
    "session_id": "S2",
    "metadata": {"tenant": "B"},
    "timeout": 99,
}
COPY_WIRE = {
    "x-agentcc-trace-id": "T1",
    "x-extra": "E",
    "x-agentcc-session-id": "S2",
    "x-agentcc-metadata": '{"tenant":"B"}',
    "read_timeout": 99.0,
}
PARENT_WIRE = dict.fromkeys(HEADERS) | {"read_timeout": 600.0}


@pytest.mark.filterwarnings('default:^Deprecated\\ gateway\\ compatibility\\ options:DeprecationWarning')
@pytest.mark.parametrize("parent_sent_first", [False, True])
def test_a_copy_sends_its_own_options_before_and_after_the_parent_has_sent(
    parent_sent_first: bool,
) -> None:
    seen: list[httpx.Request] = []
    client = _client(seen)
    if parent_sent_first:
        _send(client)
    copy = client.with_options(**COPY_OPTIONS)
    _send(copy)
    _send(client)
    wire = [_wire(r) for r in seen]
    expected = [COPY_WIRE, PARENT_WIRE]
    assert wire == ([PARENT_WIRE] + expected if parent_sent_first else expected)


@pytest.mark.filterwarnings('default:^Deprecated\\ gateway\\ compatibility\\ options:DeprecationWarning')
def test_a_copy_of_a_used_client_keeps_its_own_max_retries() -> None:
    seen: list[httpx.Request] = []
    client = _client(seen, status=[200, 500, 500, 500, 500])
    _send(client)
    copy = client.with_options(max_retries=0)
    with pytest.raises(InternalServerError):
        _send(copy)
    assert len(seen) == 2  # one try, no retry
    client._get_base_client()._calculate_delay = lambda attempt, headers=None: 0.0
    with pytest.raises(InternalServerError):
        _send(client)
    assert len(seen) == 5  # the parent still retries twice


@pytest.mark.filterwarnings('default:^Deprecated\\ gateway\\ compatibility\\ options:DeprecationWarning')
def test_chained_copies_never_send_another_tenants_session() -> None:
    seen: list[httpx.Request] = []
    client = _client(seen)
    _send(client)
    tenant_a = client.with_options(session_id="tenant-A", metadata={"tenant": "A"})
    _send(tenant_a)
    tenant_b = tenant_a.with_options(session_id="tenant-B", metadata={"tenant": "B"})
    _send(tenant_b)
    _send(tenant_a)
    _send(client)
    sessions = [r.headers.get("x-agentcc-session-id") for r in seen]
    metadata = [r.headers.get("x-agentcc-metadata") for r in seen]
    assert sessions == [None, "tenant-A", "tenant-B", "tenant-A", None]
    assert metadata == [
        None,
        '{"tenant":"A"}',
        '{"tenant":"B"}',
        '{"tenant":"A"}',
        None,
    ]


@pytest.mark.filterwarnings('default:^Deprecated\\ gateway\\ compatibility\\ options:DeprecationWarning')
def test_parent_and_copies_share_one_pooled_client_and_only_the_parent_closes_it() -> None:
    client = AgentCC(api_key="k", base_url=GW)
    early = client.with_options(timeout=5)  # made before anything was built
    independent = early._get_base_client()._ensure_client()
    pooled = client._get_base_client()._ensure_client()
    assert independent is not pooled
    late = client.with_options(max_retries=0)
    assert client._get_base_client()._ensure_client() is pooled
    assert late._get_base_client()._ensure_client() is pooled
    assert late.with_options()._get_base_client()._ensure_client() is pooled
    early.close()
    assert independent.is_closed
    late.close()
    assert not pooled.is_closed
    client.close()
    assert pooled.is_closed


@pytest.mark.filterwarnings('default:^Deprecated\\ gateway\\ compatibility\\ options:DeprecationWarning')
def test_a_passed_http_client_is_shared_and_never_closed() -> None:
    http = httpx.Client(transport=httpx.MockTransport(lambda r: httpx.Response(200)))
    client = AgentCC(api_key="k", base_url=GW, http_client=http)
    copy = client.with_options(timeout=5)
    assert copy._get_base_client()._ensure_client() is http
    assert client._get_base_client()._ensure_client() is http
    client.close()
    assert not http.is_closed
    http.close()


@pytest.mark.filterwarnings('default:^Deprecated\\ gateway\\ compatibility\\ options:DeprecationWarning')
def test_the_client_that_builds_the_pool_does_not_set_the_others_timeout() -> None:
    """A shared pool's defaults never replace each client's explicit send timeout."""
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(200, json=COMPLETION)

    client = AgentCC(api_key="k", base_url=GW, timeout=600)
    builder = client._get_base_client()
    builder._new_http_client = lambda: httpx.Client(
        transport=httpx.MockTransport(handler), timeout=builder._timeout
    )
    pooled = builder._ensure_client()
    copy = client.with_options(timeout=5)
    _send(copy)
    _send(client)
    assert pooled is copy._get_base_client()._ensure_client()
    assert pooled.timeout.read == 600.0
    assert [r.extensions["timeout"]["read"] for r in seen] == [5.0, 600.0]
    client.close()
    assert pooled.is_closed


def _async_client(seen: list[httpx.Request]) -> AsyncAgentCC:
    async def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(200, json=COMPLETION)

    return AsyncAgentCC(
        api_key="k",
        base_url=GW,
        timeout=600,
        http_client=httpx.AsyncClient(transport=httpx.MockTransport(handler)),
    )


@pytest.mark.filterwarnings('default:^Deprecated\\ gateway\\ compatibility\\ options:DeprecationWarning')
async def test_the_async_copy_of_a_used_client_sends_its_own_options() -> None:
    seen: list[httpx.Request] = []
    client = _async_client(seen)
    await client.chat.completions.create(model="m", messages=[])
    copy = client.with_options(**COPY_OPTIONS)
    await copy.chat.completions.create(model="m", messages=[])
    tenant_a = copy.with_options(session_id="tenant-A")
    await tenant_a.chat.completions.create(model="m", messages=[])
    tenant_b = tenant_a.with_options(session_id="tenant-B")
    await tenant_b.chat.completions.create(model="m", messages=[])
    await client.chat.completions.create(model="m", messages=[])
    wire = [_wire(r) for r in seen]
    assert wire[:2] == [PARENT_WIRE, COPY_WIRE]
    assert [w["x-agentcc-session-id"] for w in wire[2:]] == [
        "tenant-A",
        "tenant-B",
        None,
    ]
    assert wire[4] == PARENT_WIRE


@pytest.mark.filterwarnings('default:^Deprecated\\ gateway\\ compatibility\\ options:DeprecationWarning')
async def test_the_async_pool_is_shared_and_only_the_parent_closes_it() -> None:
    client = AsyncAgentCC(api_key="k", base_url=GW)
    early = client.with_options(timeout=5)
    independent = early._get_base_client()._ensure_client()
    pooled = client._get_base_client()._ensure_client()
    assert independent is not pooled
    late = client.with_options(timeout=5)
    assert late._get_base_client()._ensure_client() is pooled
    await early.aclose()
    assert independent.is_closed
    await late.aclose()
    assert not pooled.is_closed
    await client.aclose()
    assert pooled.is_closed
