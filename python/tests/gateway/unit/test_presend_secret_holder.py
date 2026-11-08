"""Pre-send failures drop SDK aliases, not caller state or exception identity."""

import json
import warnings

import httpx
import pytest

from fi.gateway import AgentCC, AsyncAgentCC, Gateway, AsyncGateway
from fi.gateway._exceptions import AgentCCError
from fi.gateway._gateway_config import TimeoutConfig, create_headers
from fi.gateway._transport._base import RequestOptions
from fi.gateway._transport._request import RequestBuilder
from ._presend_helpers import (
    ORIGIN, KEY, HEADER, VIRTUAL, resolve, config_with_key,
    assert_safe_sdk_locals, caller_failure, assert_caller_untouched,
)


@pytest.mark.parametrize("client_type", [AgentCC, AsyncAgentCC])
@pytest.mark.parametrize("failure", ["missing-key", "origin", "platform-key", "metadata-mode", "audio-mode", "callback-mode", "warning", "copy-warning"])
def test_constructor_failures(client_type, failure, monkeypatch):
    for name in ("FI_GATEWAY_API_KEY", "AGENTCC_API_KEY", "FI_API_KEY", "FI_SECRET_KEY", "FI_GATEWAY_BASE_URL", "FI_GATEWAY_URL", "AGENTCC_BASE_URL"):
        monkeypatch.delenv(name, raising=False)
    config = config_with_key()
    defaults = {"X-Api-Key": HEADER}
    kwargs = dict(api_key=KEY, base_url=ORIGIN, config=config, default_headers=defaults)
    expected = ValueError
    match = ""
    if failure == "missing-key":
        kwargs["api_key"] = None
        expected, match = AgentCCError, "api_key is required:"
    elif failure == "origin":
        kwargs.pop("base_url")
        expected, match = AgentCCError, "base_url is required:"
    elif failure == "platform-key":
        monkeypatch.setenv("FI_API_KEY", KEY)
        expected, match = AgentCCError, "The gateway key equals FI_API_KEY from the environment."
    elif failure.endswith("-mode"):
        option = {"metadata-mode": "metadata_mode", "audio-mode": "audio_upload_mode", "callback-mode": "callback_mode"}[failure]
        kwargs[option] = "invalid"
        match = option + " must be "
    else:
        expected, match = DeprecationWarning, "Deprecated gateway compatibility options:"
        if failure == "warning":
            kwargs["callbacks"] = []
    if failure == "copy-warning":
        client = client_type(**kwargs)
        call = lambda: client.with_options(timeout=10)
    else:
        call = lambda: client_type(**kwargs)
    with warnings.catch_warnings():
        warnings.simplefilter("error", DeprecationWarning)
        error = caller_failure(call)
    assert type(error) is expected and str(error).startswith(match)
    assert defaults == {"X-Api-Key": HEADER}
    assert config.load_balance.targets[0].virtual_key == VIRTUAL
    assert kwargs["api_key"] == (None if failure == "missing-key" else KEY)
    assert_caller_untouched(error)
    assert_safe_sdk_locals(error)


@pytest.mark.parametrize("client_type", [Gateway, AsyncGateway])
@pytest.mark.parametrize("failure", ["warning", "origin"])
def test_wrapper_failures(client_type, failure):
    kwargs = dict(api_key=KEY, base_url=ORIGIN, default_headers={"X-Api-Key": HEADER})
    if failure == "origin":
        kwargs["base_url"] = "https://user:password@gateway.example.test"
    with warnings.catch_warnings():
        warnings.simplefilter("error" if failure == "warning" else "always", DeprecationWarning)
        error = caller_failure(lambda: client_type(**kwargs))
    assert type(error) is (DeprecationWarning if failure == "warning" else AgentCCError)
    assert_caller_untouched(error)
    assert_safe_sdk_locals(error)


@pytest.mark.parametrize("async_mode", [False, True])
@pytest.mark.parametrize("failure", ["guard", "override-guard", "metadata", "config-warning", "config-json", "config-timeout", "header", "url", "json", "form", "stream-url", "pool", "stream-pool"])
async def test_send_preparation_failures(async_mode, failure, monkeypatch):
    defaults = {"X-Api-Key": HEADER}
    config = config_with_key()
    sent = []

    def serve(request):
        sent.append(dict(request.headers))
        return httpx.Response(200, json={})

    http = (httpx.AsyncClient if async_mode else httpx.Client)(transport=httpx.MockTransport(serve), trust_env=False)
    client = (AsyncAgentCC if async_mode else AgentCC)(api_key=KEY, base_url=ORIGIN, default_headers=defaults, config=config, http_client=http)
    base = client._get_base_client()
    options = RequestOptions(method="POST", url="/v1/test", body={})
    expected, match = ValueError, ""
    sentinel = RuntimeError("synthetic pre-send failure")
    if failure == "guard":
        monkeypatch.setenv("FI_API_KEY", KEY)
        expected, match = AgentCCError, "The gateway key equals FI_API_KEY"
    elif failure == "override-guard":
        monkeypatch.setenv("FI_API_KEY", HEADER)
        expected, match = AgentCCError, "The gateway key equals FI_API_KEY"
    elif failure in {"metadata", "json", "form", "config-json"}:
        cycle = {}
        cycle["cycle"] = cycle
        if failure == "metadata":
            base._metadata = cycle
        elif failure == "config-json":
            config.load_balance.targets[0].weight = object()
            expected, match = TypeError, "Object of type object is not JSON serializable"
        else:
            options.body = cycle
            if failure == "form":
                options.files = {"file": ("test.txt", b"test")}
        if failure != "config-json":
            match = "Circular reference detected"
    elif failure == "config-warning":
        expected, match = DeprecationWarning, "Deprecated gateway config adapter:"
    elif failure == "config-timeout":
        config.timeout = TimeoutConfig(total=float("nan"))
        match = "cannot convert float NaN to integer"
    elif failure == "header":
        defaults["X-Invalid"] = object()
        expected, match = AgentCCError, "Invalid HTTP header value for x-invalid."
    elif failure in {"url", "stream-url"}:
        options.url = "https://other.example.test/v1/test"
        expected, match = AgentCCError, "Gateway requests must use the explicitly configured origin."
    else:
        def fail():
            raise sentinel
        monkeypatch.setattr(base, "_ensure_client", fail)
        expected, match = RuntimeError, str(sentinel)
    try:
        caller_key = KEY
        with warnings.catch_warnings():
            warnings.simplefilter("error" if failure == "config-warning" else "always", DeprecationWarning)
            try:
                await resolve(base._send_response(options, None, streaming=failure.startswith("stream-")))
            except BaseException as error:
                caught = error
            else:
                raise AssertionError("Expected a pre-send failure")
        assert type(caught) is expected and str(caught).startswith(match)
        if failure == "header":
            assert str(caught) == match
        if failure in {"pool", "stream-pool"}:
            assert caught is sentinel
        assert not sent
        assert caller_key == KEY and defaults["X-Api-Key"] == HEADER
        assert config.load_balance.targets[0].virtual_key == VIRTUAL
        assert_safe_sdk_locals(caught)
    finally:
        await resolve(http.aclose() if async_mode else http.close())


@pytest.mark.parametrize("failure", ["builder-origin", "builder-mode", "raw-header", "raw-url", "create-guard", "create-config", "create-metadata"])
def test_direct_request_helpers(failure, monkeypatch):
    defaults = {"X-Api-Key": HEADER}
    config = config_with_key()
    if failure.startswith("builder-"):
        kwargs = dict(api_key=KEY, base_url=ORIGIN, default_headers=defaults, config=config)
        if failure == "builder-origin":
            kwargs["base_url"] = "https://user:password@gateway.example.test"
        else:
            kwargs["metadata_mode"] = "invalid"
        call = lambda: RequestBuilder(**kwargs)
    elif failure.startswith("raw-"):
        builder = RequestBuilder(api_key=KEY, base_url=ORIGIN, default_headers=defaults, config=config)
        options = RequestOptions(method="GET", url="/v1/test")
        if failure == "raw-header":
            defaults["X-Invalid"] = object()
        else:
            options.url = "https://other.example.test/v1/test"
        call = lambda: builder._build_request(options)
    else:
        kwargs = dict(api_key=KEY, config=config)
        if failure == "create-guard":
            monkeypatch.setenv("FI_API_KEY", KEY)
        elif failure == "create-metadata":
            cycle = {}
            cycle["cycle"] = cycle
            kwargs["metadata"] = cycle
        call = lambda: create_headers(**kwargs)
    with warnings.catch_warnings():
        warnings.simplefilter("error" if failure == "create-config" else "always", DeprecationWarning)
        error = caller_failure(call)
    expected = AgentCCError if failure in {"create-guard", "builder-origin", "raw-url", "raw-header"} else DeprecationWarning if failure == "create-config" else ValueError
    assert type(error) is expected
    if failure == "raw-header":
        assert str(error) == "Invalid HTTP header value for x-invalid."
    assert defaults["X-Api-Key"] == HEADER and config.load_balance.targets[0].virtual_key == VIRTUAL
    assert_caller_untouched(error)
    assert_safe_sdk_locals(error)


@pytest.mark.parametrize("client_type", [AgentCC, AsyncAgentCC])
@pytest.mark.parametrize("failure", ["env-key-log", "env-origin-log", "transport-timeout", "config-cancel"])
async def test_original_presend_exception_is_untouched(client_type, failure, monkeypatch):
    from fi.gateway import _env

    class Cancelled(BaseException):
        pass

    sentinel = Cancelled("synthetic cancellation") if failure == "config-cancel" else RuntimeError("synthetic preparation failure")
    cause = LookupError("synthetic cause")
    sentinel.__cause__ = cause
    config = config_with_key()
    defaults = {"X-Api-Key": HEADER}
    kwargs = dict(api_key=KEY, base_url=ORIGIN, default_headers=defaults, config=config)

    def fail(*args, **kwargs):
        caller_key = KEY
        raise sentinel

    if failure.startswith("env-"):
        monkeypatch.setattr(_env.logger, "warning", fail)
        if failure == "env-key-log":
            kwargs["api_key"] = None
            monkeypatch.setenv("FI_GATEWAY_API_KEY", KEY)
            monkeypatch.setenv("AGENTCC_API_KEY", "synthetic-other")
        else:
            kwargs["base_url"] = None
            monkeypatch.setenv("FI_GATEWAY_BASE_URL", ORIGIN)
            monkeypatch.setenv("AGENTCC_BASE_URL", ORIGIN + "/different")
        call = lambda: client_type(**kwargs)
    else:
        client = client_type(**kwargs)
        if failure == "transport-timeout":
            from fi.gateway._transport import _base
            monkeypatch.setattr(_base, "parse_timeout", fail)
            call = client._get_base_client
        else:
            monkeypatch.setattr(config, "to_headers", fail)
            base = client._get_base_client()
            call = lambda: base._build_headers(RequestOptions(method="GET", url="/v1/test"))
    error = caller_failure(call)
    assert error is sentinel and error.__cause__ is cause
    assert str(error) == ("synthetic cancellation" if failure == "config-cancel" else "synthetic preparation failure")
    assert_caller_untouched(error)
    assert defaults == {"X-Api-Key": HEADER}
    tb = error.__traceback__
    while tb.tb_next is not None:
        tb = tb.tb_next
    assert tb.tb_frame.f_locals["caller_key"] == KEY
    assert_safe_sdk_locals(error)


@pytest.mark.parametrize("async_mode", [False, True])
@pytest.mark.parametrize("failure", ["header-name", "header-ascii", "cleartext-warning", "capture", "form-url", "stream-header", "stream-json", "parameter"])
async def test_additional_preparation_boundaries(async_mode, failure, monkeypatch):
    from fi.gateway._deprecation import AgentCCDeprecationWarning
    from fi.gateway._transport import _async, _sync

    sentinel = RuntimeError("synthetic preparation boundary")

    class Parameter:
        def __str__(self):
            raise sentinel

    defaults = {"X-Api-Key": HEADER}
    config = config_with_key()
    origin = "http://gateway.example.test" if failure == "cleartext-warning" else ORIGIN
    sent = []

    def serve(request):
        sent.append(request)
        raise AssertionError("No exchange expected")

    http = (httpx.AsyncClient if async_mode else httpx.Client)(transport=httpx.MockTransport(serve), trust_env=False)
    client = (AsyncAgentCC if async_mode else AgentCC)(api_key=KEY, base_url=origin, default_headers=defaults, config=config, http_client=http)
    base = client._get_base_client()
    options = RequestOptions(method="POST", url="/v1/test", body={})
    params = None
    expected, message = RuntimeError, str(sentinel)
    if failure == "header-name":
        defaults[1] = "invalid"
        expected, message = AttributeError, "'int' object has no attribute 'lower'"
    elif failure == "header-ascii":
        defaults["X-Invalid"] = "☃"
        expected, message = AgentCCError, "Invalid HTTP header value for x-invalid."
    elif failure == "cleartext-warning":
        expected, message = AgentCCDeprecationWarning, "futureagi: sending gateway credentials in cleartext over HTTP"
    elif failure == "capture":
        def fail():
            raise sentinel
        monkeypatch.setattr(_async if async_mode else _sync, "ResponseCapture", fail)
    elif failure == "form-url":
        options.files = {"file": ("test.txt", b"test")}
        options.url = "https://other.example.test/v1/test"
        expected, message = AgentCCError, "Gateway requests must use the explicitly configured origin."
    elif failure == "stream-header":
        defaults["X-Invalid"] = object()
        expected, message = AgentCCError, "Invalid HTTP header value for x-invalid."
    elif failure == "stream-json":
        options.body = {}
        options.body["cycle"] = options.body
        expected, message = ValueError, "Circular reference detected"
    else:
        params = {"trace_id": Parameter()}
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("always", DeprecationWarning)
            warnings.simplefilter("error", AgentCCDeprecationWarning)
            try:
                await resolve(base._send_response(options, params, streaming=failure.startswith("stream-")))
            except BaseException as error:
                caught = error
            else:
                raise AssertionError("Expected a pre-send failure")
        assert type(caught) is expected and str(caught).startswith(message)
        if failure in {"header-ascii", "stream-header"}:
            assert str(caught) == message
        if failure in {"capture", "parameter"}:
            assert caught is sentinel
        assert not sent and defaults["X-Api-Key"] == HEADER
        assert config.load_balance.targets[0].virtual_key == VIRTUAL
        assert_safe_sdk_locals(caught)
    finally:
        await resolve(http.aclose() if async_mode else http.close())


@pytest.mark.parametrize("client_type", [AgentCC, AsyncAgentCC])
def test_option_copy_formatting_failure(client_type):
    sentinel = RuntimeError("synthetic trace formatting failure")

    class Trace:
        def __str__(self):
            raise sentinel

    defaults = {"X-Api-Key": HEADER}
    client = client_type(api_key=KEY, base_url=ORIGIN, default_headers=defaults)
    error = caller_failure(lambda: client.with_options(trace_id=Trace()))
    assert error is sentinel and str(error) == "synthetic trace formatting failure"
    assert defaults == {"X-Api-Key": HEADER}
    assert_caller_untouched(error)
    assert_safe_sdk_locals(error)


@pytest.mark.parametrize("client_type", [AgentCC, AsyncAgentCC])
def test_config_traversal_failure(client_type):
    sentinel = RuntimeError("synthetic config traversal failure")
    config = config_with_key()

    class BrokenMapping(dict):
        def items(self):
            raise sentinel

    config.load_balance.targets[0].provider = BrokenMapping(value=VIRTUAL)
    client = client_type(api_key=KEY, base_url=ORIGIN, config=config)
    with pytest.warns(DeprecationWarning, match="Deprecated gateway config adapter"):
        error = caller_failure(lambda: client._get_base_client()._build_headers(RequestOptions(method="GET", url="/v1/test")))
    assert error is sentinel
    assert config.load_balance.targets[0].provider == {"value": VIRTUAL}
    assert_caller_untouched(error)
    assert_safe_sdk_locals(error)


@pytest.mark.parametrize("failure", ["origin", "json"])
def test_public_raw_request_failure(failure):
    from fi.gateway._utils import return_raw_request

    kwargs = dict(api_key=KEY, base_url=ORIGIN, model="test", messages=[])
    if failure == "origin":
        kwargs["base_url"] = "https://user:password@gateway.example.test"
    else:
        kwargs["messages"] = object()
    with pytest.warns(DeprecationWarning, match="return_raw_request"):
        error = caller_failure(lambda: return_raw_request(**kwargs))
    assert type(error) is (AgentCCError if failure == "origin" else TypeError)
    assert kwargs["api_key"] == KEY
    assert_caller_untouched(error)
    assert_safe_sdk_locals(error)


@pytest.mark.parametrize("async_mode", [False, True])
@pytest.mark.parametrize("mode", ["json", "form", "stream"])
async def test_success_keeps_wire_and_public_values(async_mode, mode):
    config = config_with_key()
    defaults = {"X-Api-Key": HEADER}
    wire = []

    def serve(request):
        wire.append(dict(request.headers))
        return httpx.Response(200, json={})

    http = (httpx.AsyncClient if async_mode else httpx.Client)(transport=httpx.MockTransport(serve), trust_env=False)
    client = (AsyncAgentCC if async_mode else AgentCC)(api_key=KEY, base_url=ORIGIN, config=config, default_headers=defaults, http_client=http)
    options = RequestOptions(method="POST", url="/v1/test", body={})
    if mode == "form":
        options.files = {"file": ("test.txt", b"test")}
    try:
        with pytest.warns(DeprecationWarning, match="Deprecated gateway config adapter"):
            response = await resolve(client._get_base_client()._send_response(options, None, streaming=mode == "stream"))
        assert wire[0]["authorization"] == "Bearer " + KEY
        assert wire[0]["x-api-key"] == HEADER
        assert json.loads(wire[0]["x-agentcc-config"])["load_balance"]["targets"][0]["virtual_key"] == VIRTUAL
        assert client._api_key.get() == KEY
        assert defaults == {"X-Api-Key": HEADER}
        assert config.to_dict()["load_balance"]["targets"][0]["virtual_key"] == VIRTUAL
        assert repr(client) == f"{type(client).__name__}(base_url={ORIGIN!r}, api_key={(KEY[:10] + '...' + KEY[-4:])!r})"
        await resolve(response.aclose() if async_mode else response.close())
    finally:
        await resolve(http.aclose() if async_mode else http.close())
