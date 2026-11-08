"""Client-owned secrets stay opaque to traceback-local repr collectors."""
from __future__ import annotations

import copy
import inspect
import json
import pickle

import httpx
import pytest

from fi.gateway import AgentCC, AsyncAgentCC
from fi.gateway._exceptions import APIConnectionError, APIStatusError
from fi.gateway._gateway_config import GatewayConfig, LoadBalanceConfig, LoadBalanceTarget
from fi.gateway._transport._request import RequestBuilder

ORIGIN = "https://gateway.example.test"
KEY = "synthetic-frame-api-key"
VIRTUAL_KEY = "synthetic-frame-virtual-key"
HEADER_KEY = "synthetic-frame-header-key"
MASK = "[REDACTED]"


async def resolve(value):
    return await value if inspect.isawaitable(value) else value


def assert_safe_frames(error):
    """Capture every SDK local, including stored fields on SDK client locals.

    This models repr-based error trackers, not arbitrary interpreter/slot walks.
    The extra client-field projection catches secrets hidden by a client's own
    repr, without calling public accessors that deliberately return raw data.
    """
    captured = {}
    clients = 0
    seen = set()
    pending = [error]
    while pending:
        exc = pending.pop()
        if exc is None or id(exc) in seen:
            continue
        seen.add(id(exc))
        pending.extend((exc.__cause__, exc.__context__))
        tb = exc.__traceback__
        while tb is not None:
            frame = tb.tb_frame
            if frame.f_globals.get("__name__", "").startswith("fi.gateway."):
                for name, value in frame.f_locals.items():
                    location = (frame.f_code.co_name, tb.tb_lineno, name)
                    captured[location] = repr(value)
                    if isinstance(value, (AgentCC, AsyncAgentCC, RequestBuilder)):
                        clients += 1
                        captured[(*location, "stored_fields")] = repr(vars(value))
            tb = tb.tb_next
    assert captured and clients, "The failure must retain actual SDK client frames"
    leaks = [location for location, text in captured.items()
             if any(secret in text for secret in (KEY, VIRTUAL_KEY, HEADER_KEY))]
    assert not leaks, f"Client secrets appeared in SDK locals: {leaks}"


def config_with_virtual_key():
    with pytest.warns(DeprecationWarning):
        target = LoadBalanceTarget(model="test", virtual_key=VIRTUAL_KEY)
        config = GatewayConfig(load_balance=LoadBalanceConfig(targets=[target]))
    return target, config


@pytest.mark.parametrize("async_mode", [False, True])
@pytest.mark.parametrize("outcome", ["status", "connection"])
@pytest.mark.parametrize("resource", ["json", "form", "binary", "stream"])
async def test_failing_call_frame_locals_redact_client_secrets(async_mode, outcome, resource):
    target, config = config_with_virtual_key()
    defaults = {"X-Api-Key": HEADER_KEY}
    wire = []

    def serve(request):
        wire.append(dict(request.headers))
        if outcome == "connection":
            raise httpx.ConnectError("synthetic connection failure", request=request)
        return httpx.Response(400, json={"error": {"message": "synthetic refusal"}})

    http = (httpx.AsyncClient if async_mode else httpx.Client)(
        transport=httpx.MockTransport(serve), trust_env=False,
    )
    client = (AsyncAgentCC if async_mode else AgentCC)(
        api_key=KEY, base_url=ORIGIN, config=config, default_headers=defaults,
        http_client=http, max_retries=0,
    )
    error_type = APIConnectionError if outcome == "connection" else APIStatusError
    try:
        with pytest.warns(DeprecationWarning, match="Deprecated gateway config adapter"):
            with pytest.raises(error_type) as caught:
                if resource == "form":
                    await resolve(client.audio.transcriptions.create(
                        model="test", file=("sample.wav", b"sample"),
                    ))
                elif resource == "binary":
                    await resolve(client.audio.speech.create(model="test", input="hi", voice="alloy"))
                else:
                    await resolve(client.chat.completions.create(
                        model="test", messages=[], stream=resource == "stream",
                    ))
        assert len(wire) == 1
        assert wire[0]["authorization"] == "Bearer " + KEY
        assert wire[0]["x-api-key"] == HEADER_KEY
        assert json.loads(wire[0]["x-agentcc-config"])["load_balance"]["targets"][0]["virtual_key"] == VIRTUAL_KEY
        # Public config inspection and caller-owned objects retain released values.
        assert target.virtual_key == VIRTUAL_KEY
        assert isinstance(target.virtual_key, str)
        assert config.to_dict()["load_balance"]["targets"][0]["virtual_key"] == VIRTUAL_KEY
        assert defaults == {"X-Api-Key": HEADER_KEY}
        assert_safe_frames(caught.value)
    finally:
        await resolve(http.aclose() if async_mode else http.close())


@pytest.mark.parametrize("client_type", [AgentCC, AsyncAgentCC])
def test_client_key_holder_redacts_text_format_and_pickle(client_type):
    client = client_type(api_key=KEY, base_url=ORIGIN)
    holder = client._api_key
    assert repr(holder) == str(holder) == format(holder) == MASK
    assert format(holder, ">40") == MASK
    assert holder.get() == KEY
    for protocol in range(pickle.HIGHEST_PROTOCOL + 1):
        payload = pickle.dumps(holder, protocol=protocol)
        assert KEY.encode() not in payload
        assert str(pickle.loads(payload)) == MASK
    assert copy.copy(holder).get() == copy.deepcopy(holder).get() == KEY
    assert holder == KEY and KEY == holder
    assert holder != KEY + "-different"
    assert holder == client_type(api_key=KEY, base_url=ORIGIN)._api_key
    assert hash(holder) == hash(KEY)
    assert KEY not in repr(vars(client))
    assert KEY not in repr(vars(client._get_base_client()))


@pytest.mark.parametrize("client_type", [AgentCC, AsyncAgentCC])
def test_key_comparison_never_passes_raw_value_to_caller_equality(client_type):
    holder = client_type(api_key=KEY, base_url=ORIGIN)._api_key
    observed = []

    class Comparison:
        def __eq__(self, value):
            observed.append(value)
            return False

    assert not (holder == Comparison())
    assert observed == [holder]
    assert observed[0] is holder
    assert repr(observed[0]) == MASK
    assert KEY not in repr(observed)


@pytest.mark.parametrize("client_type", [AgentCC, AsyncAgentCC])
def test_option_copies_pass_released_values_to_subclass_constructors(client_type):
    _, config = config_with_virtual_key()
    received = []

    class CustomClient(client_type):
        def __init__(self, *, api_key=None, config=None, **kwargs):
            received.append((api_key, config))
            super().__init__(api_key=api_key, config=config, **kwargs)

    client = CustomClient(api_key=KEY, base_url=ORIGIN, config=config)
    with pytest.warns(DeprecationWarning, match="Deprecated gateway compatibility options"):
        client.with_options(timeout=10)
    assert len(received) == 2
    for key, passed_config in received:
        assert isinstance(key, str) and key == KEY
        assert passed_config is config


@pytest.mark.parametrize("async_mode", [False, True])
@pytest.mark.parametrize("initialize_first", [False, True])
async def test_option_copies_keep_real_wire_secrets_and_live_config(async_mode, initialize_first):
    target, config = config_with_virtual_key()
    defaults = {"X-Api-Key": HEADER_KEY}
    wire = []

    def serve(request):
        wire.append(dict(request.headers))
        return httpx.Response(200, json={"data": [], "object": "list"})

    http = (httpx.AsyncClient if async_mode else httpx.Client)(
        transport=httpx.MockTransport(serve), trust_env=False,
    )
    client = (AsyncAgentCC if async_mode else AgentCC)(
        api_key=KEY, base_url=ORIGIN, config=config, default_headers=defaults, http_client=http,
    )
    try:
        if initialize_first:
            client._get_base_client()
        with pytest.warns(DeprecationWarning, match="Deprecated gateway compatibility options"):
            derived = client.with_options(extra_headers={"X-Copy": "copied"})
        target.virtual_key = VIRTUAL_KEY + "-updated"
        defaults["X-Api-Key"] = HEADER_KEY + "-updated"
        with pytest.warns(DeprecationWarning, match="Deprecated gateway config adapter"):
            await resolve(derived.models.list())
            await resolve(client.models.list())
        assert [row["authorization"] for row in wire] == ["Bearer " + KEY] * 2
        assert [row["x-api-key"] for row in wire] == [HEADER_KEY, HEADER_KEY + "-updated"]
        assert wire[0]["x-copy"] == "copied" and "x-copy" not in wire[1]
        assert all(json.loads(row["x-agentcc-config"])["load_balance"]["targets"][0]["virtual_key"]
                   == VIRTUAL_KEY + "-updated" for row in wire)
        assert KEY not in repr(vars(derived))
        assert VIRTUAL_KEY not in repr(vars(derived))
        assert HEADER_KEY not in repr(vars(derived))
    finally:
        await resolve(http.aclose() if async_mode else http.close())
