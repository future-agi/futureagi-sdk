"""Offline exact-archive differential plus installed-package and CI checks.

Dependencies must be provisioned before network access is disabled. Baseline
sources and test assertions are never patched or replaced with head tests.
"""
from __future__ import annotations

import base64
from collections import Counter
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import xml.etree.ElementTree as ET

ROOT = Path(sys.argv[1]).resolve()
EV = ROOT / '.evidence'
EV.mkdir(exist_ok=True)
PY = str(ROOT / '.sdk-python/bin/python')
for key in list(os.environ):
    if key.startswith(('FI_', 'OPENAI_', 'ANTHROPIC_', 'GOOGLE_API_', 'GEMINI_', 'AWS_', 'AZURE_')) or key in {'NPM_TOKEN', 'GITHUB_TOKEN', 'GH_TOKEN'}:
        os.environ.pop(key, None)
os.environ.update(PYTHONDONTWRITEBYTECODE='1', GIT_NO_LAZY_FETCH='1', npm_config_offline='true',
                  npm_config_ignore_scripts='true', npm_config_userconfig='/dev/null', UV_OFFLINE='1')
os.environ['PATH'] = str(ROOT / '.proof-tools/node_modules/.bin') + os.pathsep + os.environ['PATH']
(ROOT / 'baseline/typescript/futureagi/node_modules').symlink_to(ROOT / 'typescript/futureagi/node_modules', target_is_directory=True)
stages = []


def run(name, argv, cwd, timeout=900):
    start = time.monotonic()
    try:
        p = subprocess.run(list(map(str, argv)), cwd=cwd, capture_output=True, text=True, errors='replace', timeout=timeout)
        rc, stdout, stderr = p.returncode, p.stdout, p.stderr
    except subprocess.TimeoutExpired as exc:
        rc = 124
        stdout, stderr = exc.stdout or b'', exc.stderr or b''
        stdout = stdout.decode(errors='replace') if isinstance(stdout, bytes) else stdout
        stderr = stderr.decode(errors='replace') if isinstance(stderr, bytes) else stderr
    (EV / (name + '.stdout.log')).write_text(stdout[-30000:])
    (EV / (name + '.stderr.log')).write_text(stderr[-30000:])
    row = {'name': name, 'exit_code': rc, 'seconds': round(time.monotonic() - start, 3),
           'stdout_chars': len(stdout), 'stderr_chars': len(stderr), 'log_tail_limit': 30000}
    stages.append(row)
    print('INTEGRATION_STAGE ' + json.dumps(row), flush=True)
    return rc


for label, root in [('base', ROOT / 'baseline'), ('head', ROOT)]:
    editable = run(label + '-editable', ['uv', 'pip', 'install', '--python', PY, '--no-deps', '--no-build-isolation', '--offline', '-e', root / 'python'], root)
    if editable:
        stages.append({'name': label + '-suites', 'exit_code': None, 'status': 'NOT_RUN_EDITABLE_FAILED'})
        continue
    top = [str(p) for p in sorted((root / 'python/tests').glob('test*.py')) if p.name != 'test_live_smoke.py']
    run(label + '-python', [PY, '-I', '-B', '-m', 'pytest', '-q', '-p', 'no:cacheprovider', *top, '--junitxml=' + str(EV / (label + '-python.xml'))], root / 'python')
    run(label + '-gateway', [PY, '-I', '-B', '-m', 'pytest', '-q', '-p', 'no:cacheprovider', '-o', 'pythonpath=tests/gateway', 'tests/gateway', '--ignore=tests/gateway/live', '--junitxml=' + str(EV / (label + '-gateway.xml'))], root / 'python')
    run(label + '-typescript', ['node', 'node_modules/jest/bin/jest.js', '--runInBand', '--ci', '--json', '--outputFile=' + str(EV / (label + '-typescript.json')), '--testPathIgnorePatterns', '/src/datasets/__tests__/', '/src/platform/__tests__/live'], root / 'typescript/futureagi', timeout=1200)
    run(label + '-release-guards', [PY, '-I', '-B', '-m', 'unittest', 'discover', '-s', '.github/scripts', '-p', 'test_*.py', '-v'], root)
    run(label + '-generator-drift', [PY, '-I', '-B', 'sdkgen/generate.py', '--check'], root)
    run(label + '-reference-python', [PY, '-I', '-B', 'python/consumer/docs_examples.py', root / 'docs/sdk-reference'], root)
    run(label + '-reference-tests', [PY, '-I', '-B', '-m', 'pytest', '-q', '-p', 'no:cacheprovider', 'tests/platform/test_docs_examples.py', '--junitxml=' + str(EV / (label + '-reference.xml'))], root / 'python')
    run(label + '-consumer-python', [PY, '-I', '-B', 'python/consumer/consumer.py'], root)
    ts = root / 'typescript/futureagi'
    if label == 'base':
        build = run(label + '-consumer-typescript-build', ['node', 'node_modules/typescript/bin/tsc', '--build', 'tsconfig.json', 'tsconfig.esm.json', 'tsconfig.esnext.json'], ts)
        if build == 0:
            run(label + '-consumer-typescript-alias', ['node', 'node_modules/tsc-alias/dist/bin/index.js', '-p', 'tsconfig.esm.json'], ts)
            for folder, kind in [('esm', 'module'), ('src', 'commonjs')]:
                (ts / 'dist' / folder / 'package.json').write_text(json.dumps({'type': kind}))
            run(label + '-consumer-typescript', ['bash', 'scripts/check-consumer.sh'], ts, timeout=180)
        else:
            stages.append({'name': label + '-consumer-typescript', 'exit_code': None, 'status': 'NOT_RUN_BUILD_FAILED'})
    else:
        run('head-frozen-install', ['pnpm', 'install', '--offline', '--ignore-workspace', '--frozen-lockfile', '--ignore-scripts'], ts)
        build = run('head-build', ['pnpm', 'run', 'build'], ts)
        run('head-wheel-consumer-reference', [PY, '-I', '-B', ROOT / 'scripts/testing/package-proof.py', ROOT, EV, 'python'], ROOT)
        if build == 0:
            run('head-tarball-consumer-reference', [PY, '-I', '-B', ROOT / 'scripts/testing/package-proof.py', ROOT, EV, 'typescript'], ROOT)
        else:
            stages.append({'name': 'head-tarball-consumer-reference', 'exit_code': None, 'status': 'NOT_RUN_BUILD_FAILED'})
        run('head-workflow-tests', [PY, '-I', '-B', '-m', 'unittest', 'discover', '-s', '.github/ci', '-p', 'test_workflow_policy*.py', '-v'], ROOT)
        run('head-workflow-checker', [PY, '-I', '-B', '.github/ci/workflow_policy.py'], ROOT)
        spec = importlib.util.spec_from_file_location("proof_workflow_policy", ROOT / '.github/ci/workflow_policy.py')
        policy = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(policy)
        diagnostics = policy.check_repository(ROOT)
        exception_paths = {'.github/workflows/publish.yml', '.github/workflows/release-please.yml'}
        outside_exception = [line for line in diagnostics if line.split(':', 1)[0] not in exception_paths]
        (EV / 'workflow-diagnostics.json').write_text(json.dumps({
            'all': diagnostics, 'named_exception_paths': sorted(exception_paths),
            'outside_named_exception': outside_exception,
        }, indent=2) + '\n')
        stages.append({'name': 'head-workflow-exception-accounting', 'exit_code': int(bool(outside_exception))})
        gateway = ts / 'gateway-client'
        run('head-gateway-typecheck', ['node', 'node_modules/typescript/bin/tsc', '-p', 'tsconfig.json', '--noEmit'], gateway)
        run('head-gateway-test-typecheck', ['node', 'node_modules/typescript/bin/tsc', '-p', 'tsconfig.typecheck.json'], gateway)
        run('head-gateway-jest', ['node', 'node_modules/jest/bin/jest.js', '-c', 'jest.config.cjs', '--runInBand', '--ci', '--json', '--outputFile=' + str(EV / 'head-gateway-jest.json')], gateway, timeout=1200)
        run('head-gateway-original-names', ['node', 'scripts/check-test-names.cjs', EV / 'head-gateway-jest.json'], gateway)
        run('head-gateway-parity', ['node', '--test', 'tests/parity/compare.test.mjs', 'tests/parity/hygiene.test.mjs'], gateway)


def xml_tests(file):
    cases, seen = {}, Counter()
    for test in ET.parse(file).getroot().iter('testcase'):
        status = 'failed' if test.find('failure') is not None or test.find('error') is not None else 'skipped' if test.find('skipped') is not None else 'passed'
        key = test.get('classname', '') + '::' + test.get('name', '')
        seen[key] += 1
        cases[key if seen[key] == 1 else key + '::occurrence=' + str(seen[key])] = status
    return cases


def jest_tests(file):
    result, cases = json.loads(file.read_text()), {}
    for suite in result['testResults']:
        name = suite['name'].split('/typescript/futureagi/', 1)[-1]
        seen = Counter()
        for test in suite['assertionResults']:
            key = name + '::' + test['fullName']
            seen[key] += 1
            cases[key if seen[key] == 1 else key + '::occurrence=' + str(seen[key])] = test['status']
        if not suite['assertionResults'] and suite.get('status') == 'failed':
            cases['COLLECTION::' + name] = 'failed'
    return cases


comparison, all_cases = {}, {}
for name, reader, ext in [('python', xml_tests, 'xml'), ('gateway', xml_tests, 'xml'), ('typescript', jest_tests, 'json')]:
    try:
        before = reader(EV / ('base-' + name + '.' + ext))
        after = reader(EV / ('head-' + name + '.' + ext))
    except (OSError, ValueError, ET.ParseError) as exc:
        comparison[name] = {'status': 'MISSING_EVIDENCE', 'reason': str(exc)}
        continue
    all_cases[name] = {'base': before, 'head': after}
    comparison[name] = {'base': dict(Counter(before.values())), 'head': dict(Counter(after.values())),
        'new_failures': [k for k, v in after.items() if v == 'failed' and before.get(k) != 'failed'],
        'fixed_failures': [k for k, v in before.items() if v == 'failed' and after.get(k) == 'passed'],
        'head_failures': [k for k, v in after.items() if v == 'failed'],
        'removed_cases': [k for k in before if k not in after], 'added_cases': [k for k in after if k not in before],
        'new_skips': [k for k, v in after.items() if v in ('skipped', 'pending', 'todo') and before.get(k) == 'passed']}
result = {'stages': stages, 'comparison': comparison,
          'case_identity': 'Python classname::name; Jest suite-relative-path::fullName; duplicate occurrences retained',
          'baseline_tests_modified': False, 'policy_exception': ['publish.yml', 'release-please.yml']}
(EV / 'comparison.json').write_text(json.dumps(result, indent=2) + '\n')
(EV / 'all-cases.json').write_text(json.dumps(all_cases, indent=2) + '\n')
# Keep complete case identities, not Jest's large duplicated source/stack dumps.
for path in [EV / 'base-typescript.json', EV / 'head-typescript.json', EV / 'head-gateway-jest.json']:
    if path.exists():
        original = json.loads(path.read_text())
        reduced = {k: original[k] for k in ('success', 'numTotalTests', 'numFailedTests', 'numPassedTests', 'numPendingTests') if k in original}
        reduced['testResults'] = []
        for suite in original.get('testResults', []):
            tests = [{**{k: test[k] for k in ('fullName', 'status', 'title', 'ancestorTitles') if k in test},
                      'failureMessages': [message[-8000:] for message in test.get('failureMessages', [])]}
                     for test in suite.get('assertionResults', [])]
            reduced['testResults'].append({'name': suite['name'], 'status': suite.get('status'),
                                           'message': suite.get('message', '')[-8000:], 'assertionResults': tests})
        path.write_text(json.dumps(reduced, indent=2) + '\n')
for path in sorted(EV.iterdir()):
    if path.is_file() and path.stat().st_size < 16 * 1024 * 1024:
        data = path.read_bytes()
        print('SDK_ARTIFACT ' + json.dumps({'name': path.name, 'sha256': hashlib.sha256(data).hexdigest(), 'bytes': len(data), 'data_base64': base64.b64encode(data).decode()}, separators=(',', ':')), flush=True)
print('INTEGRATION_SUMMARY ' + json.dumps({name: {k: len(v) if isinstance(v, list) else v for k, v in row.items()} for name, row in comparison.items()}), flush=True)
failed_comparison = any(v.get('new_failures') or v.get('new_skips') or v.get('status') == 'MISSING_EVIDENCE' for v in comparison.values())
required = {'head-build', 'head-frozen-install', 'head-wheel-consumer-reference', 'head-tarball-consumer-reference',
            'head-release-guards', 'head-generator-drift', 'head-gateway-typecheck', 'head-gateway-test-typecheck',
            'head-gateway-jest', 'head-gateway-original-names', 'head-gateway-parity',
            'head-workflow-exception-accounting'}
stage_by_name = {stage['name']: stage for stage in stages}
failed_checks = any(stage_by_name.get(name, {}).get('exit_code') != 0 for name in required)
raise SystemExit(1 if failed_comparison or failed_checks else 0)
