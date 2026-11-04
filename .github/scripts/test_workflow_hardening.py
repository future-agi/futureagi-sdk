"""Static release workflow tests: python -m unittest discover -s .github/scripts.

The release guard tests use the standard library, not PyYAML. Keep that contract:
read exact, indentation-bounded blocks in these four checked-in workflows. This
is deliberately not a general YAML parser; a layout change must update the
assertions, rather than silently accepting an unrecognized security setting.
"""
import re
import unittest
from pathlib import Path


WORKFLOWS = Path(__file__).resolve().parents[1] / 'workflows'
WORKFLOW_NAMES = ('publish.yml', 'promote.yml', 'release-please.yml', 'pr-title-lint.yml')


class WorkflowHardeningTests(unittest.TestCase):
    def workflow(self, name):
        path = WORKFLOWS / name
        self.assertTrue(path.is_file(), f'Missing workflow: {name}')
        self.assertLessEqual(path.stat().st_size, 64 * 1024, f'Oversized workflow: {name}')
        text = path.read_text(encoding='utf-8')
        self.assertNotIn('\t', text, 'Exact-line checks require space indentation')
        return text.splitlines()

    def block(self, lines, header):
        """Require one exact key and return its indentation-bounded body."""
        matches = [i for i, line in enumerate(lines) if line == header]
        self.assertEqual(len(matches), 1, f'Expected one {header!r}')
        start = matches[0]  # Guarded above: missing/duplicate keys fail assertions.
        indent = len(header) - len(header.lstrip())
        body = []
        for line in lines[start + 1:]:
            if not line.strip() or line.lstrip().startswith('#'):
                continue
            if len(line) - len(line.lstrip()) <= indent:
                break
            body.append(line)
        return body

    def jobs(self, lines):
        body = self.block(lines, 'jobs:')
        names = [line[2:-1] for line in body if re.fullmatch(r'  [a-z][a-z0-9_-]*:', line)]
        self.assertTrue(names, 'Expected explicit job mappings')
        return {name: self.block(body, f'  {name}:') for name in names}

    def job(self, lines, name):
        jobs = self.jobs(lines)
        self.assertIn(name, jobs, f'Missing job: {name}')
        return jobs.get(name, [])

    def steps(self, job):
        body = self.block(job, '    steps:')
        starts = [i for i, line in enumerate(body) if line.startswith('      - ')]
        self.assertTrue(starts, 'Expected explicit workflow steps')
        self.assertEqual(starts[0], 0, 'Unexpected step layout')
        ends = starts[1:] + [len(body)]
        return [body[start:end] for start, end in zip(starts, ends)]

    def uses(self, lines):
        return [line.strip().removeprefix('- ') for line in lines
                if re.match(r'^\s*(?:- )?uses:', line)]

    def assert_action_pin(self, action, sha, version, expected_counts):
        self.assertRegex(sha, r'^[0-9a-f]{40}$')
        for name in WORKFLOW_NAMES:
            with self.subTest(workflow=name, action=action):
                matches = [line for line in self.uses(self.workflow(name)) if action in line]
                self.assertEqual(len(matches), expected_counts.get(name, 0))
                for line in matches:
                    self.assertEqual(line, f'uses: {action}@{sha}  # {version}')

    def test_pypi_publish_sha_pin(self):
        self.assert_action_pin(
            'pypa/gh-action-pypi-publish',
            '7245906fb61fa33a13554f9d5fb856fe61758086', 'v1.14.3',
            {'publish.yml': 1},
        )

    def test_app_token_sha_pins(self):
        self.assert_action_pin(
            'actions/create-github-app-token',
            'fee1f7d63c2ff003460e3d139729b119787bc349', 'v2.2.2',
            {'promote.yml': 1, 'release-please.yml': 1},
        )

    def test_release_please_sha_pin(self):
        self.assert_action_pin(
            'googleapis/release-please-action',
            '5c625bfb5d1ff62eadeeb3772007f7f66fdcf071', 'v4.4.1',
            {'release-please.yml': 1},
        )

    def test_every_action_is_pinned_to_a_full_commit_sha(self):
        pinned = re.compile(r'^uses: [A-Za-z0-9_.-]+/[A-Za-z0-9_./-]+@[0-9a-f]{40}(?:\s+#\s*\S.*)?$')
        for name in WORKFLOW_NAMES:
            uses = self.uses(self.workflow(name))
            self.assertTrue(uses, f'Expected action references in {name}')
            for line in uses:
                with self.subTest(workflow=name, line=line):
                    self.assertRegex(line, pinned)

    def test_common_action_sha_pins(self):
        self.assert_action_pin(
            'actions/checkout',
            '11d5960a326750d5838078e36cf38b85af677262', 'v4.4.0',
            {'publish.yml': 3, 'release-please.yml': 1},
        )
        self.assert_action_pin(
            'actions/setup-python',
            'a26af69be951a213d495a4c3e4e4022e16d87065', 'v5.6.0',
            {'publish.yml': 2, 'release-please.yml': 1},
        )
        self.assert_action_pin(
            'pnpm/action-setup',
            'b906affcce14559ad1aafd4ab0e942779e9f58b1', 'v4.3.0',
            {'publish.yml': 1},
        )
        self.assert_action_pin(
            'actions/setup-node',
            '49933ea5288caeca8642d1e84afbd3f7d6820020', 'v4.4.0',
            {'publish.yml': 1},
        )

    def test_publish_accepts_only_workflow_dispatch_on_main(self):
        lines = self.workflow('publish.yml')
        text = '\n'.join(lines)
        self.assertNotIn('repository_dispatch', text)
        self.assertNotIn('client_payload', text)
        self.assertEqual(self.block(lines, 'on:'), [
            '  workflow_dispatch:',
            '    inputs:',
            '      tag:',
            '        description: Release tag to publish (python-vX.Y.Z or typescript-vX.Y.Z)',
            '        required: true',
            '        type: string',
        ])
        self.assertEqual(self.block(lines, 'env:'), ['  TAG: ${{ inputs.tag }}'])
        self.assertEqual(self.block(lines, 'concurrency:'), [
            '  group: sdk-publish-${{ inputs.tag }}',
            '  cancel-in-progress: false',
        ])
        verify = self.job(lines, 'verify')
        self.assertIn("    if: github.ref == 'refs/heads/main'", verify)
        for name, environment, prefix in [('python', 'pypi', 'python-v'),
                                           ('typescript', 'npm', 'typescript-v')]:
            with self.subTest(job=name):
                job = self.job(lines, name)
                self.assertIn('    needs: verify', job)
                self.assertIn(f'    environment: {environment}', job)
                self.assertIn(f"    if: startsWith(inputs.tag, '{prefix}')", job)

    def test_release_dispatches_publish_on_main_with_app_token(self):
        lines = self.workflow('release-please.yml')
        text = '\n'.join(lines)
        self.assertNotIn('/dispatches', text)
        self.assertNotIn('repository_dispatch', text)
        self.assertNotIn('client_payload', text)
        steps = self.steps(self.job(lines, 'release'))
        dispatches = [step for step in steps if any('gh workflow run' in line for line in step)]
        self.assertEqual(len(dispatches), 1, 'Expected one publication dispatch step')
        dispatch = dispatches[0]
        self.assertIn("        if: steps.release.outputs.releases_created == 'true'", dispatch)
        self.assertEqual(self.block(dispatch, '        env:'), [
            '          GH_TOKEN: ${{ steps.app-token.outputs.token }}',
            '          GH_REPO: ${{ github.repository }}',
            "          PYTHON_TAG: ${{ steps.release.outputs['python--tag_name'] }}",
            "          TYPESCRIPT_TAG: ${{ steps.release.outputs['typescript/futureagi--tag_name'] }}",
        ])
        self.assertEqual(self.block(dispatch, '        run: |'), [
            '          for tag in "$PYTHON_TAG" "$TYPESCRIPT_TAG"; do',
            '            [ -n "$tag" ] || continue',
            '            gh workflow run publish.yml --ref main -f tag="$tag"',
            '          done',
        ])

    def test_credential_jobs_are_protected_and_checkout_only_main(self):
        expected = {('promote.yml', 'promote'): 'release-promote',
                    ('release-please.yml', 'release'): 'release-please'}
        credentials = set()
        protected = {}
        for name in WORKFLOW_NAMES:
            for job_name, job in self.jobs(self.workflow(name)).items():
                key = (name, job_name)
                if any('secrets.RELEASE_BOT_' in line or
                       'actions/create-github-app-token@' in line for line in job):
                    credentials.add(key)
                environments = [line.removeprefix('    environment: ') for line in job
                                if line.startswith('    environment: ')]
                self.assertLessEqual(len(environments), 1, f'Duplicate environment: {key}')
                for environment in environments:
                    if environment in expected.values():
                        protected[key] = environment
        self.assertEqual(credentials, set(expected))
        self.assertEqual(protected, expected)

        # The base already checks out main. Preserve that boundary while adding
        # environment-scoped credentials: the triggering SHA is guard data only.
        lines = self.workflow('release-please.yml')
        release = self.job(lines, 'release')
        self.assertIn("    if: github.ref == 'refs/heads/main'", release)
        self.assertEqual(self.block(self.block(lines, 'on:'), '  workflow_run:'), [
            '    workflows: [CI, E2E]', '    branches: [main]', '    types: [completed]',
        ])
        checkouts = [step for step in self.steps(release)
                     if any('actions/checkout@' in line for line in self.uses(step))]
        self.assertEqual(len(checkouts), 1, 'Expected one trusted checkout')
        self.assertEqual(self.block(checkouts[0], '        with:'), [
            '          ref: main', '          persist-credentials: false',
        ])
        self.assertEqual([line for line in lines if 'github.event.workflow_run' in line], [
            '          TRIGGER_SHA: ${{ github.event.workflow_run.head_sha }}',
        ])
        self.assertEqual([line for line in lines if 'TRIGGER_SHA' in line], [
            '          TRIGGER_SHA: ${{ github.event.workflow_run.head_sha }}',
            '        run: python .github/scripts/release_guard.py check-main --sha "$TRIGGER_SHA"',
        ])

    def test_pr_title_lint_has_only_read_job_permissions(self):
        lines = self.workflow('pr-title-lint.yml')
        lint = self.job(lines, 'lint')
        self.assertEqual(self.block(lint, '    permissions:'), [
            '      pull-requests: read', '      contents: read',
        ])
        self.assertEqual(self.block(lines, 'permissions:'), ['  pull-requests: read'])
        self.assertEqual(self.block(lines, 'on:'), [
            '  pull_request:',
            '    types: [opened, edited, synchronize, reopened]',
            '    branches: [dev, main]',
        ])
        self.assertEqual(self.uses(lint), [
            'uses: amannn/action-semantic-pull-request@e32d7e603df1aa1ba07e981f2a23455dee596825 # v5',
        ])
        self.assertFalse(any(re.match(r'^\s*(?:- )?run:', line) for line in lint))
        self.assertEqual([line for line in lines if 'secrets.' in line], [
            '          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}',
        ])


if __name__ == '__main__':
    unittest.main()
