"""Observe generation, language parity and documentation admission gates."""
import importlib.util
import inspect
import json
import re
import subprocess
import sys
from pathlib import Path

from fi import AsyncFutureAGIClient, FutureAGIClient

ROOT = Path(__file__).resolve().parents[3]
MAP = json.loads((ROOT / 'openapi/tracing/wrapper-map.json').read_text())
SOURCE = json.loads((ROOT / 'openapi/tracing/source.json').read_text())


def test_generated_files_are_reproducible_and_detect_drift(tmp_path):
    command = [sys.executable, str(ROOT / 'scripts/generate-tracing.py'), '--out', str(tmp_path)]
    subprocess.run(command, check=True, capture_output=True)
    files = list(tmp_path.rglob('*'))
    for path in (p for p in files if p.is_file()):
        assert path.read_bytes() == (ROOT / path.relative_to(tmp_path)).read_bytes()
        assert len(path.read_text().splitlines()) <= 400
    subprocess.run([*command, '--check'], check=True, capture_output=True)
    victim = next(p for p in files if p.is_file())
    victim.write_text(victim.read_text() + '# changed\n')
    drift = subprocess.run([*command, '--check'], capture_output=True)
    assert drift.returncode != 0
    assert b'generated output differs' in drift.stderr


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
    assert 'tracing = ["fi-instrumentation-otel"]' in metadata
    doc = (ROOT / 'python/fi/tracing/README.md').read_text()
    assert 'futureagi[tracing]' in doc
    assert 'fi-instrumentation-otel' in doc
    assert '@traceai/*' in doc
    assert 'one bounded page' in doc
    assert 'person-owned' in doc
    assert 'does **not** supply a tracing' in doc
    assert 'Online evaluation task management is not offered' in doc
    assert not (ROOT / 'python/fi/tracing/instrumentation.py').exists()
