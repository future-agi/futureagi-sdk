"""Retained graph aliases observe transport-boundary credential scrubbing."""
from __future__ import annotations

import asyncio
from dataclasses import dataclass
import inspect

import httpx
import pytest
from pydantic import BaseModel, ValidationError

from fi.gateway import AgentCC, AsyncAgentCC


class SlottedFailure(Exception):
    __slots__ = ('request', 'response')

    def __init__(self, request, response):
        super().__init__('synthetic diagnostic', request, response)
        self.request, self.response = request, response


@dataclass(slots=True)
class Diagnostic:
    request: object
    label: str


class InputModel(BaseModel):
    value: int


@pytest.mark.parametrize('asynchronous', [False, True])
@pytest.mark.parametrize('redact', [False, True])
@pytest.mark.parametrize('state', ['slots', 'containers', 'pydantic', 'group_slots', 'dataclass_slots'])
def test_original_diagnostic_aliases_are_scrubbed_without_graph_reconstruction(asynchronous, redact, state):
    async def exercise():
        sent, retained, callbacks, wire = [], [], [], []

        class Observer:
            def on_error(self, request, error):
                callbacks.append(error)

        def handler(request):
            sent.append(request)
            wire.append(dict(request.headers))
            response = httpx.Response(418, request=request, json={'error': 'fixture'})
            error = httpx.ConnectError('fixture failure', request=request)
            leaf = httpx.HTTPStatusError('fixture status', request=request, response=response)
            if state == 'slots':
                error.diagnostic = SlottedFailure(request, response)
            elif state == 'containers':
                error.diagnostic = {'headers': request.headers, 'keys': {request: 'safe'},
                                    'set': {leaf}, 'frozenset': frozenset([leaf])}
            elif state == 'pydantic':
                try:
                    InputModel.model_validate({'value': request})
                except ValidationError as diagnostic:
                    error.diagnostic = diagnostic
            elif state == 'group_slots':
                # Exception groups are available on the Python 3.11 proof runner.
                # On the supported floor, retain the same slotted-state invariant.
                import builtins
                base = getattr(builtins, 'ExceptionGroup', Exception)
                class GroupWithSlot(base):
                    __slots__ = ('label',)
                    def __init__(self, *args):
                        super().__init__(*args)
                        self.label = 'safe-label'
                error.diagnostic = GroupWithSlot('fixture group', [leaf])
            else:
                error.diagnostic = Diagnostic(request, 'safe-label')
            retained.append(error)
            raise error

        http = (httpx.AsyncClient if asynchronous else httpx.Client)(transport=httpx.MockTransport(handler), trust_env=False)
        with pytest.warns(DeprecationWarning, match='^Deprecated gateway compatibility options: redact_messages, callbacks$'):
            client = (AsyncAgentCC if asynchronous else AgentCC)(
                api_key='synthetic-graph-key', base_url='https://gateway.test', http_client=http,
                callbacks=[Observer()], max_retries=0, redact_messages=redact,
            )
        try:
            with pytest.raises(Exception) as raised:
                result = client.chat.completions.create(model='fixture', messages=[])
                if inspect.isawaitable(result):
                    await result
            assert len(wire) == len(callbacks) == 1
            assert callbacks[0] is raised.value
            assert type(raised.value).__name__ != 'TypeError'
            assert wire[0]['authorization'] == 'Bearer synthetic-graph-key'
            original = retained[0]
            assert original.request is sent[0]
            assert sent[0].headers['authorization'] == '[REDACTED]'
            diagnostic = original.diagnostic
            if state == 'slots':
                assert diagnostic.request is diagnostic.response.request is sent[0]
                assert diagnostic.request.headers['authorization'] == '[REDACTED]'
            elif state == 'containers':
                assert diagnostic['headers']['authorization'] == '[REDACTED]'
                assert next(iter(diagnostic['keys'])).headers['authorization'] == '[REDACTED]'
                for name in ('set', 'frozenset'):
                    item = next(iter(diagnostic[name]))
                    assert item.request.headers['authorization'] == '[REDACTED]'
                    assert item.response.request is item.request
            elif state == 'pydantic':
                assert diagnostic.errors(include_url=False)[0]['input'] is sent[0]
                assert diagnostic.errors(include_url=False)[0]['input'].headers['authorization'] == '[REDACTED]'
            elif state == 'group_slots':
                assert diagnostic.label == 'safe-label'
                if hasattr(diagnostic, 'exceptions'):
                    assert diagnostic.exceptions[0].request.headers['authorization'] == '[REDACTED]'
            else:
                assert diagnostic.label == 'safe-label'
                assert diagnostic.request.headers['authorization'] == '[REDACTED]'
        finally:
            if asynchronous:
                await client.aclose()
                await http.aclose()
            else:
                client.close()
                http.close()

    asyncio.run(exercise())
