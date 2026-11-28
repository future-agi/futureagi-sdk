"""Observe generation, language parity and documentation admission gates."""
import inspect
import json
import re
from pathlib import Path

from fi import AsyncFutureAGIClient, FutureAGIClient

ROOT = Path(__file__).resolve().parents[3]
MAP = json.loads((ROOT / 'openapi/tracing/wrapper-map.json').read_text())
SOURCE = json.loads((ROOT / 'openapi/tracing/source.json').read_text())


def test_public_paths_and_arguments_have_language_twins():
    names = []
    endpoints = []
    for row in MAP['operations']:
        names.append(row['public']['py'])
        endpoints.append((row['method'], row['path']))
        assert re.sub(r'(?<!^)(?=[A-Z])', '_', row['ts']).lower() == row['py']
        assert row['public']['py'] == 'client.tracing.' + row['py']
        assert row['public']['ts'] == 'client.tracing.' + row['ts']
        op = SOURCE['paths'][row['path']][row['method'].lower()]
        assert op['operationId'] == row['operation_id']
        for cls, asynchronous in ((FutureAGIClient, False), (AsyncFutureAGIClient, True)):
            client = cls('fixture-api', 'fixture-secret', base_url='http://localhost:9012')
            method = getattr(client.tracing, row['py'])
            assert inspect.iscoroutinefunction(method) is asynchronous
            assert list(inspect.signature(method).parameters)[:len(row['args'])] == list(row['args'].values())
            assert inspect.getdoc(method)
    assert len(names) == len(set(names))
    assert len(endpoints) == len(set(endpoints))
    for row in MAP['derived']:
        assert row['why']
        assert 'client.tracing.' + row['from'] in names


def test_existing_tracing_names_and_error_clusters_are_not_renamed():
    previous = json.loads((ROOT / 'openapi/sdk/wrapper-map.json').read_text())['tracing']
    current = {row['ts']: row for row in MAP['operations']}
    assert set(previous) <= set(current)
    assert {'issues', 'issue', 'issueStats'} <= set(current)
    assert all(not row['py'].startswith('errors.') for row in current.values())


def test_extra_and_docs_point_to_traceai_not_a_new_instrumentor():
    metadata = (ROOT / 'python/pyproject.toml').read_text()
    assert 'tracing = ["fi-instrumentation-otel", "opentelemetry-exporter-otlp-proto-http"]' in metadata
    doc = (ROOT / 'python/fi/tracing/README.md').read_text()
    assert 'futureagi[tracing]' in doc
    assert 'fi-instrumentation-otel' in doc
    assert '@traceai/*' in doc
    assert 'one bounded page' in doc
    assert 'person-owned' in doc
    assert 'does **not** supply a tracing' in doc
    assert 'Online evaluation task management is not offered' in doc
    assert not (ROOT / 'python/fi/tracing/instrumentation.py').exists()
