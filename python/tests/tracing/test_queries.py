"""Observe operation contracts against an in-memory transport, never a service."""
import asyncio
import copy
import json
from pathlib import Path

import httpx
import pytest

from fi import AsyncFutureAGIClient, FutureAGIClient
from fi.errors import ConfigurationError, FutureAGIAPIError, UnexpectedRedirectError

ROOT = Path(__file__).resolve().parents[3]
ROWS = json.loads((ROOT / 'openapi/tracing/wrapper-map.json').read_text())['operations']
SOURCE = json.loads((ROOT / 'openapi/tracing/source.json').read_text())


def make(handler, asynchronous):
    cls = AsyncFutureAGIClient if asynchronous else FutureAGIClient
    client = cls('fixture-api', 'fixture-secret', base_url='http://localhost:9012',
                 workspace_id='workspace', organization_id='organization', retries=0)
    transport = httpx.MockTransport(handler)
    if asynchronous:
        client.generated_client.set_async_httpx_client(httpx.AsyncClient(
            base_url=client.base_url, transport=transport, auth=client._auth))
    else:
        client.generated_client.set_httpx_client(httpx.Client(
            base_url=client.base_url, transport=transport, auth=client._auth))
    return client


def call(client, operation_name, asynchronous, *args, **kwargs):
    result = getattr(client.tracing, operation_name)(*args, **kwargs)
    return asyncio.run(result) if asynchronous else result


@pytest.mark.parametrize('asynchronous', [True, False])
@pytest.mark.parametrize('row', ROWS, ids=lambda row: row['py'])
def test_operation_contract(row, asynchronous):
    seen = []
    payload = {'status': True, 'result': {'id': 'child', 'parent_span_id': 'parent'},
               'query_complete': False, 'next_cursor': 'next'}
    def handler(request):
        seen.append(request)
        assert request.headers['x-api-key'] == 'fixture-api'
        assert request.headers['x-secret-key'] == 'fixture-secret'
        assert request.headers['x-workspace-id'] == 'workspace'
        assert request.headers['x-organization-id'] == 'organization'
        assert 'idempotency-key' not in request.headers
        assert request.url.host == 'localhost'
        return httpx.Response(200, json=payload)
    args = ['identifier'] * len(row['args'])
    body = row['method'] in ('POST', 'PUT', 'PATCH')
    if body:
        args.append({'tags': ['tag'], 'optional': None})
    client = make(handler, asynchronous)
    assert call(client, row['py'], asynchronous, *args) == payload
    assert len(seen) == 1
    request = seen[0]
    assert request.method == row['method']
    path = row['path']
    for arg in row['args']:
        path = path.replace('{' + arg + '}', 'identifier')
    assert request.url.path == path
    if body:
        assert json.loads(request.content) == args[-1]
    assert row['operation_id'] == SOURCE['paths'][row['path']][row['method'].lower()]['operationId']


@pytest.mark.parametrize('asynchronous', [True, False])
def test_trace_scope_is_required_and_additive(asynchronous):
    seen = []
    def handler(request):
        seen.append(request)
        return httpx.Response(200, json={'status': True, 'result': {'table': [
            {'span_id': 'child', 'trace_id': 'trace', 'parent_span_id': 'parent'}],
            'metadata': {'has_more': True, 'next_cursor': 'cursor', 'query_complete': False}}})
    client = make(handler, asynchronous)
    extra = [{'column_id': 'created_at', 'filter_config': {'filter_type': 'datetime',
             'filter_op': 'between', 'filter_value': ['2026-01-01', '2026-01-02']}}]
    before = copy.deepcopy(extra)
    result = call(client, 'spans_by_trace', asynchronous, 'trace', project_id='project', filters=extra, cursor='resume', cursor_mode=True)
    assert extra == before
    query = seen[0].url.params
    assert query['project_id'] == 'project'
    assert query['cursor'] == 'resume'
    assert query['cursor_mode'] == 'true'
    filters = json.loads(query['filters'])
    assert filters[:-1] == before
    assert filters[-1] == {'column_id': 'trace_id', 'filter_config': {
        'col_type': 'SYSTEM_METRIC', 'filter_type': 'text', 'filter_op': 'in', 'filter_value': ['trace']}}
    assert result['result']['metadata']['has_more'] is True
    assert result['result']['table'][0]['parent_span_id'] == 'parent'
    assert len(seen) == 1


@pytest.mark.parametrize('asynchronous', [True, False])
@pytest.mark.parametrize('kwargs', [{'trace_id': ''}, {'project_id': ''}, {'filters': 'not-a-list'}, {'filters': [None]}])
def test_bad_trace_selectors_never_send(asynchronous, kwargs):
    client = make(lambda r: pytest.fail('must not send'), asynchronous)
    with pytest.raises(ConfigurationError):
        call(client, 'spans_by_trace', asynchronous, **{'trace_id': 'trace', 'project_id': 'project', **kwargs})


@pytest.mark.parametrize('asynchronous', [True, False])
@pytest.mark.parametrize('status', [400, 401, 403, 404, 429, 500, 503])
def test_typed_errors_and_no_success_fallback(asynchronous, status):
    client = make(lambda r: httpx.Response(status, json={'detail': 'denied'}), asynchronous)
    with pytest.raises(FutureAGIAPIError) as error:
        call(client, 'spans', asynchronous, project_id='foreign-project')
    assert error.value.status_code == status


@pytest.mark.parametrize('asynchronous', [True, False])
def test_redirects_and_path_traversal_never_escape(asynchronous):
    seen = []
    client = make(lambda r: (seen.append(r), httpx.Response(302, headers={'location': 'https://untrusted.invalid'}))[1], asynchronous)
    with pytest.raises(UnexpectedRedirectError):
        call(client, 'get_span', asynchronous, 'span')
    with pytest.raises(ConfigurationError):
        call(client, 'get_span', asynchronous, '..')
    assert len(seen) == 1


@pytest.mark.parametrize('asynchronous', [True, False])
def test_copy_binds_own_namespaces(asynchronous):
    client = make(lambda r: httpx.Response(200, json={}), asynchronous)
    clone = client.with_options(timeout=2)
    assert clone.tracing._client is clone
    assert clone.tracing.dashboards._client is clone
    assert client.tracing._client is client


@pytest.mark.parametrize('asynchronous', [True, False])
def test_query_contract_and_identifier_escaping(asynchronous):
    seen = []
    client = make(lambda r: (seen.append(r), httpx.Response(200, json={}))[1], asynchronous)
    call(client, 'projects', asynchronous, name='my project', page_size=10)
    assert seen[-1].url.params['name'] == 'my project'
    call(client, 'issue', asynchronous, 'cluster/one', project_id='project')
    assert b'cluster%2Fone' in seen[-1].url.raw_path
    assert seen[-1].url.params['project_id'] == 'project'
    with pytest.raises(ConfigurationError):
        call(client, 'spans', asynchronous, undeclared=True)
    assert len(seen) == 2
