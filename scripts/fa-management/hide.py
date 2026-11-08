"""Prepare an artifact-level hide of gateway management in an isolated release tree.

The generator and shared FA executor stay for other management namespaces. The
implementation and its contract tests remain preserved in the parent commit.
"""
import argparse
import json
import runpy
import shutil
from pathlib import Path


def replace(text, old, new):
    if text.count(old) != 1:
        raise ValueError("registration context changed; refusing an ambiguous hide")
    return text.replace(old, new)


def hide(root):
    for async_ in (False, True):
        path = root / 'python/fi' / ('futureagi_async_client.py' if async_ else 'futureagi_client.py')
        text = path.read_text()
        text = replace(text, '\nimport threading\n', '\n')
        text = replace(text, '        self._management_lock = threading.Lock()\n', '')
        start = text.index('    @property\n    def gateway(self)')
        end = text.index('    @functools.cached_property\n    def _platform', start)
        text = text[:start] + text[end:]
        text = replace(text, '        clone.__dict__["_management"] = self._management.with_settings(\n            timeout=timeout, retries=retries\n        )\n', '')
        text = text.replace('for name in ("_platform", "_management"):', 'for name in ("_platform",):')
        path.write_text(text)
    path = root / 'typescript/futureagi/src/futureagi-client.ts'
    text = path.read_text()
    for line in ('import { managementOrigin, scrubManagementValue } from "./_core/fa-management";\n',
                 'import { Gateway as ManagementGateway } from "./generated/fa-management/gateway";\n',
                 'import { MANAGEMENT_OPERATIONS } from "./generated/fa-management/policy";\n'):
        text = replace(text, line, '')
    start = text.index('  private managementShared: PlatformShared;')
    end = text.index('\n  /**\n   * Never throws', start)
    text = text[:start] + text[end:]
    start = text.index('    this.managementShared = {')
    end = text.index('    this.generatedClient = createClient', start)
    text = text[:start] + text[end:]
    text = replace(text, '    copy.managementShared = this.managementShared;\n', '')
    path.write_text(text)
    for folder in ('python/fi/generated/platform/fa_management', 'typescript/futureagi/src/generated/fa-management'):
        shutil.rmtree(root / folder)
    for file in ('python/fi/_core/fa_registration.py', 'python/tests/test_fa_management.py',
                 'python/tests/test_fa_management_redaction.py',
                 'python/tests/test_fa_management_metadata.py',
                 'python/tests/test_fa_management_header_secrets.py',
                 'python/tests/test_fa_management_lifecycle.py',
                 'python/tests/test_fa_management_concurrency.py',
                 'typescript/futureagi/src/_core/__tests__/fa-management.test.ts',
                 'typescript/futureagi/src/_core/__tests__/fa-management-redaction.test.ts',
                 'typescript/futureagi/src/_core/__tests__/fa-management-metadata.test.ts',
                 'typescript/futureagi/src/_core/__tests__/fa-management-header-secrets.test.ts',
                 'typescript/futureagi/src/_core/__tests__/fa-management-lifecycle.test.ts'):
        (root / file).unlink()
    (root / 'openapi/fa-mgmt/admission.json').write_text(json.dumps({
        'state': 'HIDDEN', 'reason': 'Backend and installed-artifact journey qualification are pending.',
        'absent': ['client.gateway', 'fi.generated.platform.fa_management', 'generated/fa-management']
    }, indent=2) + '\n')
    generator = runpy.run_path(str(root / 'scripts/fa-management/generate.py'))
    for path, text in generator['generate'](root).items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    hide(parser.parse_args().root)
