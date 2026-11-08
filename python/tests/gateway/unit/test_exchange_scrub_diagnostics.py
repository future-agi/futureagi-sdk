"""Bounded diagnostic links, fresh per-exchange names, and active sessions."""
import inspect

import httpx
import pytest

from fi.gateway import AgentCC, AsyncAgentCC
from fi.gateway._transport._base import RequestOptions
from fi.gateway._transport._request import RequestBuilder
from fi.gateway._transport._scrub import scrub_sent_request

pytestmark = pytest.mark.filterwarnings('ignore::DeprecationWarning')
ORIGIN = 'https://gateway.example.test'
MASK = '[REDACTED]'


def test_composed_name_inventory_is_exchange_local():
    defaults = {'X-First': 'synthetic-first'}
    class Config:
        calls = 0
        def to_headers(self):
            self.calls += 1
            return {'X-Config-'+str(self.calls): 'synthetic-config'}
    config = Config()
    builder = RequestBuilder(api_key='synthetic-sdk', base_url=ORIGIN, default_headers=defaults, config=config,
                             session_id='synthetic-session', metadata={'private': 'synthetic-metadata'})
    options = RequestOptions('POST', '/v1/test', headers={'X-Caller': 'visible'})
    headers, first = builder._build_headers(options, {'cache_namespace': 'visible'})
    assert first == frozenset({'authorization', 'x-first', 'x-config-1', 'x-agentcc-session-id', 'x-agentcc-metadata'})
    assert headers['X-Caller'] == 'visible'
    defaults.clear()
    defaults['X-Second'] = 'synthetic-second'
    _, second = builder._build_headers(options)
    assert 'x-first' not in second and 'x-config-1' not in second
    assert {'x-second', 'x-config-2'} <= second
    assert first != second and config.calls == 2
    assert options.headers == {'X-Caller': 'visible'}


def test_diagnostic_args_history_groups_and_header_aliases():
    requests = [httpx.Request('GET', ORIGIN, headers={'Authorization': 'synthetic-key', 'X-Private': 'synthetic-default'}) for _ in range(4)]
    response = httpx.Response(200, headers={'Set-Cookie': 'synthetic-cookie'}, request=requests[0])
    response.history = [httpx.Response(401, request=requests[1])]
    response.next_request = requests[2]
    leaf = httpx.ReadError('synthetic failure', request=requests[3])
    error = RuntimeError({'response': response})
    group = ExceptionGroup('synthetic group', [leaf, leaf])
    error.__cause__ = group
    group.__context__ = error
    try:
        raise error
    except RuntimeError:
        traceback = error.__traceback__
    aliases = [request.headers for request in requests]
    scrub_sent_request(None, None, error, frozenset({'x-private'}))
    assert error.__traceback__ is traceback
    assert error.__cause__ is group and group.exceptions[0] is leaf
    assert group.exceptions[0] is group.exceptions[1] and group.__context__ is error
    assert response.headers['set-cookie'] == MASK
    assert all(headers['authorization'] == headers['x-private'] == MASK for headers in aliases)


@pytest.fixture
def anyio_backend():
    return 'asyncio'


@pytest.mark.anyio
@pytest.mark.parametrize('async_mode', [False, True])
@pytest.mark.parametrize('metadata_mode', ['replace', 'merge'])
async def test_active_session_without_client_defaults_is_private(async_mode, metadata_mode):
    sent, wire = [], []
    def serve(request):
        sent.append(request)
        wire.append(dict(request.headers))
        return httpx.Response(200, json={'id': 'reply', 'object': 'chat.completion', 'created': 0, 'model': 'fixture', 'choices': []})
    http = (httpx.AsyncClient if async_mode else httpx.Client)(transport=httpx.MockTransport(serve), trust_env=False)
    client = (AsyncAgentCC if async_mode else AgentCC)(api_key='synthetic-sdk', base_url=ORIGIN, http_client=http, metadata_mode=metadata_mode)
    try:
        with client.session(session_id='synthetic-session', name='synthetic-name', metadata={'private': 'synthetic-metadata'}):
            result = client.chat.completions.create(model='fixture', messages=[])
            if inspect.isawaitable(result):
                await result
        assert wire[0]['x-agentcc-session-id'] == 'synthetic-session'
        assert 'synthetic-metadata' in repr(wire[0])
        assert all('synthetic-' not in value for value in sent[0].headers.values())
    finally:
        result = http.aclose() if async_mode else http.close()
        if inspect.isawaitable(result):
            await result
