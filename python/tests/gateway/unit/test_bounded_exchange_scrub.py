"""Client-composed headers are private; per-call data and wire values stay live."""
import inspect
import json

import httpx
import pytest

from fi.gateway import AgentCC, AsyncAgentCC
from fi.gateway._gateway_config import GatewayConfig
from fi.gateway.callbacks.base import CallbackResponse

pytestmark = [pytest.mark.anyio, pytest.mark.filterwarnings('ignore::DeprecationWarning')]
ORIGIN = 'https://gateway.example.test'
KEY = 'synthetic-bounded-client-key'
MASK = '[REDACTED]'
CHAT = {'id': 'reply', 'object': 'chat.completion', 'created': 0, 'model': 'fixture', 'choices': []}


@pytest.fixture
def anyio_backend():
    return 'asyncio'


async def resolve(value):
    return await value if inspect.isawaitable(value) else value


@pytest.mark.parametrize('async_mode', [False, True])
@pytest.mark.parametrize('redact', [False, True])
@pytest.mark.parametrize('outcome', ['success', 'status', 'timeout', 'connect', 'retry', 'stream'])
async def test_composed_names_are_private_per_exchange(async_mode, redact, outcome):
    sent, wire, events = [], [], []
    defaults = {'X-Arbitrary-Default': 'synthetic-default'}
    extra = {'X-Caller': 'caller-data', 'Cookie': 'synthetic-caller-cookie'}
    metadata = {'private': 'synthetic-metadata'}

    class Config(GatewayConfig):
        def to_headers(self):
            return {'X-Arbitrary-Config': 'synthetic-config'}

    class Capture:
        def on_request_end(self, request, response):
            events.append(response)
        def on_error(self, request, error):
            events.append(error)

    def serve(request):
        sent.append(request)
        wire.append(dict(request.headers))
        if outcome in {'timeout', 'connect'}:
            raise (httpx.ReadTimeout if outcome == 'timeout' else httpx.ConnectError)('synthetic failure', request=request)
        if outcome == 'status' or outcome == 'retry' and len(sent) == 1:
            return httpx.Response(400 if outcome == 'status' else 503, headers={'retry-after': '0'}, json={'error': {'message': 'synthetic'}})
        if outcome == 'stream':
            return httpx.Response(200, headers={'content-type': 'text/event-stream'}, content=b'data: [DONE]\n\n')
        return httpx.Response(200, json=CHAT)

    http = (httpx.AsyncClient if async_mode else httpx.Client)(transport=httpx.MockTransport(serve), trust_env=False)
    client = (AsyncAgentCC if async_mode else AgentCC)(api_key=KEY, base_url=ORIGIN, http_client=http,
        default_headers=defaults, config=Config(), session_id='synthetic-session', metadata=metadata,
        callbacks=[Capture()], redact_messages=redact, max_retries=1 if outcome == 'retry' else 0)
    try:
        caught = None
        try:
            result = await resolve(client.chat.completions.create(model='fixture', messages=[], extra_headers=extra,
                cache_namespace='caller-namespace', stream=outcome == 'stream'))
            if outcome == 'stream':
                if async_mode:
                    async for _ in result:
                        pass
                else:
                    list(result)
        except Exception as exc:
            caught = exc
        assert (caught is not None) == (outcome in {'status', 'timeout', 'connect'})
        assert len(wire) == (2 if outcome == 'retry' else 1)
        for headers in wire:
            assert headers['authorization'] == 'Bearer '+KEY
            assert headers['x-arbitrary-default'] == 'synthetic-default'
            assert headers['x-arbitrary-config'] == 'synthetic-config'
            assert headers['x-agentcc-session-id'] == 'synthetic-session'
            assert json.loads(headers['x-agentcc-metadata']) == metadata
        for request in sent:
            for name in ('authorization', 'x-arbitrary-default', 'x-arbitrary-config', 'x-agentcc-session-id', 'x-agentcc-metadata', 'cookie'):
                assert request.headers[name] == MASK, name
            assert request.headers['x-caller'] == 'caller-data'
            assert request.headers['x-agentcc-cache-namespace'] == 'caller-namespace'
        assert defaults == {'X-Arbitrary-Default': 'synthetic-default'}
        assert extra == {'X-Caller': 'caller-data', 'Cookie': 'synthetic-caller-cookie'}
        assert metadata == {'private': 'synthetic-metadata'}
    finally:
        await resolve(http.aclose() if async_mode else http.close())


@pytest.mark.parametrize('async_mode', [False, True])
async def test_per_call_metadata_is_not_a_client_default(async_mode):
    sent = []
    def serve(request):
        sent.append(request)
        return httpx.Response(200, json=CHAT)
    http = (httpx.AsyncClient if async_mode else httpx.Client)(transport=httpx.MockTransport(serve), trust_env=False)
    client = (AsyncAgentCC if async_mode else AgentCC)(api_key=KEY, base_url=ORIGIN, http_client=http)
    try:
        await resolve(client.chat.completions.create(model='fixture', messages=[], request_metadata={'caller': 'kept'}, session_id='caller-session'))
        assert json.loads(sent[0].headers['x-agentcc-metadata']) == {'caller': 'kept'}
        assert sent[0].headers['x-agentcc-session-id'] == 'caller-session'
        assert sent[0].headers['authorization'] == MASK
    finally:
        await resolve(http.aclose() if async_mode else http.close())


@pytest.mark.parametrize('async_mode', [False, True])
@pytest.mark.parametrize('redact', [False, True])
async def test_snapshot_response_has_no_caller_aliases(async_mode, redact):
    seen = []
    class Mutate:
        def on_request_end(self, request, response):
            seen.append(response)
            response.body['model'] = 'callback-body'
            if response._parsed is not None:
                response._parsed.model = 'callback-model'
            if response.agentcc.http_response is not None:
                response.agentcc.http_response.headers['x-callback'] = 'changed'
            response.agentcc.model_used = 'callback-metadata'
    http = (httpx.AsyncClient if async_mode else httpx.Client)(transport=httpx.MockTransport(lambda request: httpx.Response(200, headers={'x-agentcc-model-used': 'fixture'}, json=CHAT)), trust_env=False)
    client = (AsyncAgentCC if async_mode else AgentCC)(api_key=KEY, base_url=ORIGIN, http_client=http, callbacks=[Mutate()], callback_mode='snapshot', redact_messages=redact)
    try:
        result = await resolve(client.chat.completions.create(model='fixture', messages=[]))
        assert len(seen) == 1 and isinstance(seen[0], CallbackResponse)
        assert result.model == 'fixture'
        assert result.agentcc.model_used != 'callback-metadata'
        assert 'x-callback' not in result.agentcc.http_response.headers
        assert seen[0]._parsed is not result
        assert seen[0].agentcc is not result.agentcc
        assert seen[0].agentcc.http_response is not result.agentcc.http_response
    finally:
        await resolve(http.aclose() if async_mode else http.close())


@pytest.mark.parametrize('async_mode', [False, True])
@pytest.mark.parametrize('resource', ['json', 'form', 'binary', 'list'])
@pytest.mark.parametrize('fails', [False, True])
async def test_supplied_request_override_and_finally(async_mode, resource, fails):
    calls, wire, retained = [], [], []
    def serve(request):
        wire.append(dict(request.headers))
        retained.append(request)
        if fails:
            raise httpx.ConnectError('synthetic failure', request=request)
        if resource == 'binary':
            return httpx.Response(200, content=b'audio')
        return httpx.Response(200, json={'text': 'ok'} if resource == 'form' else {'object': 'list', 'data': []} if resource == 'list' else CHAT)
    if async_mode:
        class Custom(httpx.AsyncClient):
            async def request(self, *args, **kwargs):
                calls.append(True)
                kwargs['headers'] = {**kwargs.get('headers', {}), 'X-Client-Policy': 'applied'}
                return await super().request(*args, **kwargs)
    else:
        class Custom(httpx.Client):
            def request(self, *args, **kwargs):
                calls.append(True)
                kwargs['headers'] = {**kwargs.get('headers', {}), 'X-Client-Policy': 'applied'}
                return super().request(*args, **kwargs)
    http = Custom(transport=httpx.MockTransport(serve), trust_env=False)
    client = (AsyncAgentCC if async_mode else AgentCC)(api_key=KEY, base_url=ORIGIN, http_client=http, max_retries=0)
    try:
        caught = None
        try:
            if resource == 'form':
                await resolve(client.audio.transcriptions.create(model='fixture', file=('sample.wav', b'audio')))
            elif resource == 'binary':
                await resolve(client.audio.speech.create(model='fixture', input='hi', voice='alloy'))
            elif resource == 'list':
                await resolve(client.models.list())
            else:
                await resolve(client.chat.completions.create(model='fixture', messages=[]))
        except Exception as exc:
            caught = exc
        assert (caught is not None) == fails
        assert calls == [True]
        assert wire[0]['x-client-policy'] == 'applied'
        assert wire[0]['authorization'] == 'Bearer '+KEY
        assert retained[0].headers['authorization'] == MASK
    finally:
        await resolve(http.aclose() if async_mode else http.close())


@pytest.mark.parametrize('utility', ['healthz', 'fallback', 'model', 'valid-key'])
@pytest.mark.parametrize('failure_at', [0, 1, 2])
def test_each_utility_exchange_is_scrubbed(utility, failure_at, monkeypatch):
    from fi.gateway._utils import health_check, check_valid_key
    import httpx._api as api
    retained, wire = [], []
    original = httpx.Client
    def serve(request):
        retained.append(request)
        wire.append(request.headers['authorization'])
        if len(retained) == failure_at:
            raise httpx.ReadTimeout('synthetic utility timeout', request=request)
        return httpx.Response(404 if utility == 'fallback' and len(retained) == 1 else 200)
    monkeypatch.setattr(api, 'Client', lambda *args, **kwargs: original(*args, **{**kwargs, 'transport': httpx.MockTransport(serve), 'trust_env': False}))
    if utility == 'valid-key':
        result = check_valid_key(KEY, ORIGIN)
        assert result is (failure_at != 1)
    else:
        result = health_check(api_key=KEY, base_url=ORIGIN, model='fixture' if utility == 'model' else None)
        assert result['status'] == ('error' if failure_at == 1 or utility == 'fallback' and failure_at == 2 else 'ok')
    assert len(wire) == (2 if utility == 'fallback' and failure_at != 1 else 1)
    assert all(value == 'Bearer '+KEY for value in wire)
    assert all(request.headers['authorization'] == MASK for request in retained)
