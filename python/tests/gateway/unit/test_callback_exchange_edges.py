"""Small second-pass edge checks and explicit grouped-exception backreference proof."""
import inspect
import json
import httpx
import pytest
from fi.gateway import AgentCC, AsyncAgentCC
from fi.gateway.callbacks.base import CallbackHandler

pytestmark = [pytest.mark.anyio, pytest.mark.filterwarnings('ignore::DeprecationWarning')]

@pytest.fixture
def anyio_backend():
    return 'asyncio'

async def resolve(value):
    return await value if inspect.isawaitable(value) else value

@pytest.mark.parametrize('async_mode', [False, True])
@pytest.mark.parametrize('redact', [False, True])
async def test_method_url_timeout_and_body_assignment(async_mode, redact):
    seen, completed = [], []
    class Edit(CallbackHandler):
        def on_request_start(self, request):
            request.method = 'PATCH'
            request.url = '/v1/changed'
            request.timeout = httpx.Timeout(23)
            request.body = {'model': 'changed', 'messages': []}
            request.headers = {'X-Changed': 'yes'}
            completed.append(True)
    def serve(request):
        seen.append(request)
        return httpx.Response(200, json={'id': 'reply', 'object': 'chat.completion', 'created': 0,
            'model': 'test', 'choices': []})
    http = (httpx.AsyncClient if async_mode else httpx.Client)(transport=httpx.MockTransport(serve))
    client = (AsyncAgentCC if async_mode else AgentCC)(api_key='synthetic-sdk',
        base_url='https://gateway.example.test', callbacks=[Edit()], redact_messages=redact, http_client=http)
    try:
        await resolve(client.chat.completions.create(model='test', messages=[], timeout=11))
        assert completed == [True]
        wire = seen[0]
        assert wire.method == ('POST' if redact else 'PATCH')
        assert wire.url.path == ('/v1/chat/completions' if redact else '/v1/changed')
        assert json.loads(wire.content)['model'] == ('test' if redact else 'changed')
        assert wire.extensions['timeout']['read'] == (11 if redact else 23)
        assert wire.headers.get('x-changed') == (None if redact else 'yes')
    finally:
        await resolve(http.aclose() if async_mode else http.close())

@pytest.mark.parametrize('async_mode', [False, True])
@pytest.mark.parametrize('redact', [False, True])
async def test_grouped_connection_error_children_have_sanitized_request(async_mode, redact):
    captured, original_errors, wire = [], [], []
    class Capture(CallbackHandler):
        def on_error(self, request, error):
            captured.append(error)
    def serve(request):
        wire.append(dict(request.headers))
        leaf = httpx.ConnectError('offline child', request=request)
        group = ExceptionGroup('offline group', [leaf])
        outer = httpx.ConnectError('offline outer', request=request)
        outer.__cause__ = group
        original_errors.append(outer)
        raise outer
    http = (httpx.AsyncClient if async_mode else httpx.Client)(transport=httpx.MockTransport(serve))
    client = (AsyncAgentCC if async_mode else AgentCC)(api_key='synthetic-sdk',
        base_url='https://gateway.example.test', callbacks=[Capture()], redact_messages=redact,
        http_client=http, max_retries=0, default_headers={'X-Private': 'synthetic-default'})
    try:
        with pytest.raises(Exception) as raised:
            await resolve(client.chat.completions.create(model='test', messages=[]))
        assert len(captured) == 1
        assert raised.value.__cause__ is original_errors[0]
        original_leaf = original_errors[0].__cause__.exceptions[0]
        callback_leaf = captured[0].__cause__.__cause__.exceptions[0]
        assert wire[0]['authorization'] == 'Bearer synthetic-sdk'
        assert original_leaf.request.headers['authorization'] == '[REDACTED]'
        assert callback_leaf.request.headers['authorization'] == '[REDACTED]'
        assert callback_leaf.request.headers['x-private'] == '[REDACTED]'
        assert callback_leaf is original_leaf
        assert original_leaf.__traceback__ is not None or original_errors[0].__traceback__ is not None
    finally:
        await resolve(http.aclose() if async_mode else http.close())
