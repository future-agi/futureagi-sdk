"""Independent callback graph and caller-original fidelity checks; synthetic data only."""
import sys
import inspect
import json
from contextlib import asynccontextmanager
from types import SimpleNamespace

import httpx
import pytest
from fi.gateway import AgentCC, AsyncAgentCC
from fi.gateway.callbacks.base import CallbackHandler
from fi.gateway._gateway_config import GatewayConfig, LoadBalanceConfig, LoadBalanceTarget

REQUIRES_EXCEPTION_GROUP = pytest.mark.skipif(
    sys.version_info < (3, 11), reason='ExceptionGroup is a Python 3.11+ builtin')

pytestmark = [pytest.mark.anyio, pytest.mark.filterwarnings('ignore::DeprecationWarning')]

@pytest.fixture
def anyio_backend():
    return 'asyncio'

async def resolve(value):
    return await value if inspect.isawaitable(value) else value

MARKERS = ['synthetic-api-key', 'synthetic-default-header', 'synthetic-config-key',
           'synthetic-client-session', 'synthetic-client-metadata', 'synthetic-active-session',
           'synthetic-active-metadata']

def graph(value, seen=None):
    seen = set() if seen is None else seen
    if id(value) in seen:
        return ''
    seen.add(id(value))
    if isinstance(value, (str, bytes, int, float, bool, type(None))):
        return repr(value)
    if isinstance(value, dict):
        children = list(value) + list(value.values())
    elif isinstance(value, (list, tuple, set, frozenset)):
        children = list(value)
    else:
        children = list(vars(value).values()) if hasattr(value, '__dict__') else []
        if isinstance(value, BaseException):
            children += [value.args, value.__cause__, value.__context__]
            if hasattr(value, 'exceptions'):
                children.append(value.exceptions)
            # Interpreter frames are outside the bounded data-attribute contract.
        for name in ('request', 'response', 'http_response', 'next_request', 'history'):
            try:
                item = getattr(value, name, None)
            except (RuntimeError, AttributeError):
                continue
            if item is not None and not callable(item):
                children.append(item)
    return ' '.join(graph(child, seen) for child in children)

class Capture(CallbackHandler):
    def __init__(self):
        self.calls = []
    def capture(self, name, request, *args):
        self.calls.append((name, request, args))
    def on_request_start(self, request):
        self.capture('start', request)
    def on_request_end(self, request, response):
        self.capture('end', request, response)
    def on_retry(self, request, error, attempt, delay):
        self.capture('retry', request, error, attempt, delay)
    def on_error(self, request, error):
        self.capture('error', request, error)
    def on_stream_start(self, request, info):
        self.capture('stream-start', request, info)
    def on_stream_chunk(self, request, chunk):
        self.capture('chunk', request, chunk)
    def on_stream_end(self, request, info, completion):
        self.capture('stream-end', request, info, completion)

@pytest.mark.parametrize('async_mode', [False, True])
@pytest.mark.parametrize('redact', [False, True])
@pytest.mark.parametrize('mode', ['success', 'retry', 'status_error', 'connection',
    pytest.param('exception_group', marks=REQUIRES_EXCEPTION_GROUP), 'stream', 'stream_error'])
async def test_composed_credentials_absent_from_graph(async_mode, redact, mode):
    capture = Capture()
    originals, sent, wire = [], [], []
    def serve(request):
        sent.append(request)
        wire.append(dict(request.headers))
        if mode in ('connection', 'exception_group'):
            inner = httpx.ConnectError('offline inner', request=request)
            if mode == 'exception_group':
                group = ExceptionGroup('offline attempts', [inner])
                outer = httpx.ConnectError('offline outer', request=request)
                outer.__cause__ = group
            else:
                outer = inner
            originals.append(outer)
            raise outer
        if mode == 'status_error' or (mode == 'retry' and len(sent) == 1):
            response = httpx.Response(400 if mode == 'status_error' else 500, headers={'retry-after': '0'},
                                      json={'error': {'message': 'offline status'}})
        elif mode.startswith('stream'):
            chunk = {'id': 'reply', 'object': 'chat.completion.chunk', 'created': 0, 'model': 'test',
                     'choices': [{'index': 0, 'delta': {'content': 'ok'}, 'finish_reason': 'stop'}]}
            payload = 'data: ' + json.dumps(chunk) + '\n\n'
            if mode == 'stream_error':
                payload += 'data: {"error":{"message":"offline stream"}}\n\n'
            else:
                payload += 'data: [DONE]\n\n'
            response = httpx.Response(200, headers={'content-type': 'text/event-stream', 'x-visible': 'yes'}, text=payload)
        else:
            response = httpx.Response(200, headers={'x-visible': 'yes'}, json={'id': 'reply',
                'object': 'chat.completion', 'created': 0, 'model': 'test', 'choices': []})
        originals.append(response)
        return response
    http = (httpx.AsyncClient if async_mode else httpx.Client)(transport=httpx.MockTransport(serve))
    client = (AsyncAgentCC if async_mode else AgentCC)(
        api_key=MARKERS[0], base_url='https://gateway.example.test', http_client=http,
        default_headers={'X-Custom': MARKERS[1], 'X-Api-Key': 'synthetic-secondary-key'},
        config=GatewayConfig(load_balance=LoadBalanceConfig(targets=[LoadBalanceTarget(model='test', virtual_key=MARKERS[2])])),
        session_id=MARKERS[3], metadata={'password': MARKERS[4]}, callbacks=[capture], redact_messages=redact,
        max_retries=1 if mode == 'retry' else 0)
    result = error = None
    try:
        with client.session(session_id=MARKERS[5], metadata={'label': MARKERS[6]}):
            try:
                result = await resolve(client.chat.completions.create(model='test', messages=[],
                    stream=mode.startswith('stream'), metadata={'password': 'synthetic-per-request'},
                    extra_headers={'X-Caller': 'synthetic-caller-header'}))
                if mode.startswith('stream'):
                    if async_mode:
                        async for chunk in result:
                            pass
                    else:
                        list(result)
            except Exception as exc:
                error = exc
        assert capture.calls
        requests = [call[1] for call in capture.calls]
        assert all(req is requests[0] for req in requests)
        assert requests[0].body['metadata']['password'] == 'synthetic-per-request'
        assert requests[0].headers['X-Caller'] == 'synthetic-caller-header'
        if mode in ('connection', 'exception_group'):
            assert error is not None and error.__cause__ is originals[0]
        elif mode == 'status_error':
            assert error.response is originals[0]
        elif mode.startswith('stream'):
            assert result.agentcc.http_response is originals[-1]
        else:
            assert result.agentcc.http_response is originals[-1]
        assert all(headers['authorization'] == 'Bearer ' + MARKERS[0] for headers in wire)
        assert all(request.headers['authorization'] == '[REDACTED]' for request in sent)
        assert wire[0]['x-custom'] == MARKERS[1]
        assert sent[0].headers['x-custom'] == '[REDACTED]'
        assert MARKERS[2] in wire[0]['x-agentcc-config']
        assert sent[0].headers['x-agentcc-config'] == '[REDACTED]'
        assert wire[0]['x-agentcc-session-id'] == MARKERS[5]
        assert sent[0].headers['x-agentcc-session-id'] == '[REDACTED]'
        text = graph(capture.calls)
        assert all(marker not in text for marker in MARKERS + ['synthetic-secondary-key']), {'composed_value_reachable': True, 'mode': mode}
    finally:
        await resolve(http.aclose() if async_mode else http.close())

@pytest.mark.parametrize('sink', ['recorder', 'json', 'logging', 'otel'])
def test_writing_sink_masks_credential_named_values(sink, tmp_path):
    import logging
    from fi.gateway.callbacks.base import CallbackRequest, CallbackResponse
    output = tmp_path / 'sink-output.txt'
    headers = {'Authorization': 'synthetic-auth', 'Cookie': 'synthetic-cookie',
               'Api-Key': 'synthetic-api', 'X-Goog-Api-Key': 'synthetic-google'}
    body = {'metadata': {'password': 'synthetic-password', 'api_key': 'synthetic-body-key'}, 'model': 'test'}
    request = CallbackRequest('POST', '/v1/test', headers, body, files={'api_key': 'synthetic-file'})
    response = CallbackResponse(200, {}, body={'model': 'test'})
    if sink == 'recorder':
        from fi.gateway.testing.recorder import RequestRecorder
        callback = RequestRecorder(str(output))
        callback.on_request_end(request, response)
        callback.save()
    elif sink == 'json':
        from fi.gateway.callbacks.json_logger import JSONLoggingCallbackHandler
        callback = JSONLoggingCallbackHandler(str(output))
        callback.on_request_end(request, response)
    elif sink == 'logging':
        from fi.gateway.callbacks.logging import LoggingCallback
        logger = logging.getLogger('independent-sink')
        handler = logging.FileHandler(output)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        try:
            LoggingCallback(logger_name=logger.name).on_request_start(request)
        finally:
            logger.removeHandler(handler)
            handler.close()
    else:
        from fi.gateway.callbacks.opentelemetry import OpenTelemetryCallback
        class Span:
            def __init__(self):
                self.values = {}
            def set_attribute(self, key, value):
                self.values[key] = value
            def end(self):
                output.write_text(json.dumps(self.values))
        callback = OpenTelemetryCallback(tracer=SimpleNamespace(start_span=lambda name: Span()))
        callback.on_request_start(request)
        callback.on_request_end(request, response)
    text = output.read_text()
    assert text.strip()
    assert not any(marker in text for marker in list(headers.values()) + ['synthetic-password', 'synthetic-body-key', 'synthetic-file'])
    assert body['metadata']['password'] == 'synthetic-password'
