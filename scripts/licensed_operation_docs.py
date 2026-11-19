#!/usr/bin/env python3
"""Apply source-reviewed licensing doc overrides to generated SDK methods.

Run after generate-oss-sdk.sh's generators, or with --check to detect drift.
Only documentation changes: raw generated clients keep their native error
contracts; typed exceptions apply through FutureAGIClient's transport.
The tracing generator consumes licensing_note() from this same source.
"""
from __future__ import annotations

import argparse
import ast
import json
from pathlib import Path
import re
import textwrap

ROOT = Path(__file__).resolve().parents[1]
INVENTORY = ROOT / 'openapi/sdk/licensed-operations.json'
MARKER = 'Licensing: '


def licensing_note(path: str) -> str:
    for gate in json.loads(INVENTORY.read_text())['gates']:
        if path in gate.get('paths', []) or (
            gate.get('path_prefix') and path.startswith(gate['path_prefix'])
        ):
            return gate['documentation']
    return ''


def snake(name: str) -> str:
    return re.sub(r'(?<!^)(?=[A-Z])', '_', name).replace('-', '_').lower()


def camel(name: str) -> str:
    first, *rest = re.split('[-_]', name)
    return first + ''.join(part.title() for part in rest)


def python_docs(text: str, note: str) -> str:
    lines = text.splitlines(keepends=True)
    changes = []
    for node in ast.parse(text).body:
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) or node.name not in (
            'sync', 'sync_detailed', 'asyncio', 'asyncio_detailed'
        ):
            continue
        if not ast.get_docstring(node):
            raise ValueError(f'generated function has no docstring: {node.name}')
        value = node.body[0].value
        start = sum(map(len, lines[:value.lineno - 1])) + value.col_offset
        end = sum(map(len, lines[:value.end_lineno - 1])) + value.end_col_offset
        original = text[start:end]
        # The override is always the final paragraph, before the closing triple quote.
        original = re.sub(r'\n\n    Licensing: .*?(?=\n    """$)', '', original, flags=re.S)
        if not original.endswith('\n    """'):
            raise ValueError(f'unexpected generated docstring layout: {node.name}')
        paragraph = textwrap.fill(MARKER + note, width=100, initial_indent='    ', subsequent_indent='    ')
        changes.append((start, end, original[:-8] + '\n\n' + paragraph + '\n    """'))
    if not changes:
        raise ValueError('no generated Python methods found')
    for start, end, replacement in reversed(changes):
        text = text[:start] + replacement + text[end:]
    return text


def typescript_docs(text: str, operation: str, note: str) -> str:
    marker = f'export const {camel(operation)} ='
    at = text.index(marker)
    prefix = text[:at]
    comment = prefix.rfind('/**')
    if comment >= 0 and re.fullmatch(r'/\*\*(?:(?!\*/).)*\*/\s*', prefix[comment:], re.S):
        original = prefix[comment:]
        original = re.sub(r' \*\n \* Licensing: .*?(?= \*/)', '', original, flags=re.S)
        end = original.rindex(' */')
        before = original[:end]
        after = original[end:]
    else:
        comment = at
        before, after = '/**\n', ' */\n'
    paragraph = textwrap.fill(MARKER + note, width=100, initial_indent=' * ', subsequent_indent=' * ')
    return text[:comment] + before + ' *\n' + paragraph + '\n' + after + text[at:]


def outputs() -> dict[Path, str]:
    spec = json.loads((ROOT / 'openapi/sdk/generated/futureagi-sdk.openapi.json').read_text())
    py_root = ROOT / 'python/fi/generated/openapi_client/api'
    ts_path = ROOT / 'typescript/futureagi/src/generated/openapi/sdk.gen.ts'
    ts = ts_path.read_text()
    out = {}
    for path, methods in spec['paths'].items():
        note = licensing_note(path)
        if not note:
            continue
        note += ' Direct generated calls retain their native response/error contract.'
        for method, operation in methods.items():
            if method not in ('get', 'post', 'put', 'patch', 'delete'):
                continue
            name = operation['operationId']
            matches = list(py_root.glob(f'*/{snake(name)}.py'))
            if len(matches) != 1:
                raise ValueError(f'expected one Python module for {name}: {matches}')
            py_path = matches[0]
            out[py_path] = python_docs(py_path.read_text(), note)
            ts = typescript_docs(ts, name, note)
    out[ts_path] = ts
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    for path, text in outputs().items():
        if args.check:
            if path.read_text() != text:
                raise SystemExit(f'licensing documentation differs: {path.relative_to(ROOT)}')
        else:
            path.write_text(text)


if __name__ == '__main__':
    main()
