"""Release authorization tests. Run in cloud CI: python -m unittest discover -s .github/scripts."""
import copy
import json
import unittest
from unittest.mock import patch

from release_guard import GitHub, GuardError, MANIFEST, PACKAGES, RELEASE_BRANCH, validate_version_changes


def fixture():
    old = {'python': '0.6.14', 'typescript/futureagi': '0.1.2'}
    new = {'python': '0.7.0', 'typescript/futureagi': '0.2.0'}
    before = {
        MANIFEST: json.dumps(old),
        'python/pyproject.toml': '[tool.poetry]\nname = "futureagi"\nversion = "0.6.14"\n',
        'python/fi/__init__.py': '__version__ = "0.6.14"  # x-release-please-version\nfrom pkgutil import extend_path\n',
        'python/CHANGELOG.md': None,
        'typescript/futureagi/package.json': json.dumps({'name': '@future-agi/sdk', 'version': '0.1.2', 'scripts': {'build': 'tsc'}}),
        'typescript/futureagi/package-lock.json': json.dumps({
            'name': '@future-agi/sdk', 'version': '0.1.2', 'lockfileVersion': 3,
            'packages': {
                '': {'name': '@future-agi/sdk', 'version': '0.1.2', 'dependencies': {'fixture': '^9.9.9'}},
                'node_modules/fixture': {'version': '9.9.9', 'resolved': 'https://registry.npmjs.org/fixture/-/fixture-9.9.9.tgz', 'integrity': 'sha512-synthetic'},
            },
        }),
        'typescript/futureagi/CHANGELOG.md': None,
    }
    after = {key: (value.replace('0.6.14', '0.7.0').replace('0.1.2', '0.2.0') if value else '# Changelog\n\nNew version.') for key, value in before.items()}
    after[MANIFEST] = json.dumps(new)
    return before, after


class VersionDiffTests(unittest.TestCase):
    def test_both_packages(self):
        validate_version_changes(*fixture())

    def test_single_package(self):
        before, after = fixture()
        for path in PACKAGES['typescript/futureagi']:
            del before[path]; del after[path]
        after[MANIFEST] = json.dumps({'python': '0.7.0', 'typescript/futureagi': '0.1.2'})
        validate_version_changes(before, after)

    def test_rejects_code_edit_even_in_version_file(self):
        before, after = fixture()
        after['python/fi/__init__.py'] += 'print("unexpected side effect")\n'
        with self.assertRaises(GuardError):
            validate_version_changes(before, after)

    def test_rejects_package_script_change(self):
        before, after = fixture()
        package = json.loads(after['typescript/futureagi/package.json'])
        package['scripts']['prepare'] = 'unexpected-command'
        after['typescript/futureagi/package.json'] = json.dumps(package)
        with self.assertRaises(GuardError):
            validate_version_changes(before, after)

    def test_lockfile_matches_real_release_please_diff(self):
        before, after = fixture()
        self.assertEqual(len(after), 7)
        path = 'typescript/futureagi/package-lock.json'
        old, new = json.loads(before[path]), json.loads(after[path])
        self.assertEqual(old['packages']['node_modules/fixture'], new['packages']['node_modules/fixture'])
        self.assertEqual(new['version'], '0.2.0')
        self.assertEqual(new['packages']['']['version'], '0.2.0')
        validate_version_changes(before, after)

    def test_rejects_lockfile_dependency_or_metadata_changes(self):
        for change in ['dependency_version', 'integrity', 'resolved', 'constraint', 'removed_package', 'added_package', 'lock_format', 'root_name']:
            with self.subTest(change=change):
                before, after = fixture()
                path = 'typescript/futureagi/package-lock.json'
                lock = json.loads(after[path])
                dependency = lock['packages']['node_modules/fixture']
                if change == 'dependency_version': dependency['version'] = '10.0.0'
                if change == 'integrity': dependency['integrity'] = 'sha512-different'
                if change == 'resolved': dependency['resolved'] = 'https://different.test/package.tgz'
                if change == 'constraint': lock['packages']['']['dependencies']['fixture'] = '^10.0.0'
                if change == 'removed_package': del lock['packages']['node_modules/fixture']
                if change == 'added_package': lock['packages']['node_modules/extra'] = {'version': '1.0.0'}
                if change == 'lock_format': lock['lockfileVersion'] = 2
                if change == 'root_name': lock['packages']['']['name'] = 'different-package'
                after[path] = json.dumps(lock)
                with self.assertRaises(GuardError): validate_version_changes(before, after)

    def test_rejects_missing_or_mismatched_lockfile_version(self):
        for change in ['no_file', 'no_root', 'root_null', 'no_root_version', 'wrong_root_version', 'wrong_top_version']:
            with self.subTest(change=change):
                before, after = fixture()
                path = 'typescript/futureagi/package-lock.json'
                lock = json.loads(after[path])
                if change == 'no_file': del after[path]
                if change == 'no_root': del lock['packages']['']
                if change == 'root_null': lock['packages'][''] = None
                if change == 'no_root_version': del lock['packages']['']['version']
                if change == 'wrong_root_version': lock['packages']['']['version'] = '0.1.2'
                if change == 'wrong_top_version': lock['version'] = '0.1.2'
                if change != 'no_file': after[path] = json.dumps(lock)
                with self.assertRaises(GuardError): validate_version_changes(before, after)

    def test_lockfile_change_requires_typescript_version_bump(self):
        before, after = fixture()
        after[MANIFEST] = json.dumps({'python': '0.7.0', 'typescript/futureagi': '0.1.2'})
        with self.assertRaises(GuardError): validate_version_changes(before, after)

    def test_rejects_workflow_changes(self):
        before, after = fixture()
        after['.github/workflows/publish.yml'] = 'changed'
        with self.assertRaises(GuardError):
            validate_version_changes(before, after)

    def test_rejects_bad_versions(self):
        for bad in ['0.6.14', '0.6.13', '0.9.0', '0.7.0-rc.1', '1.2.3.4']:
            with self.subTest(version=bad):
                before, after = fixture()
                after[MANIFEST] = json.dumps({'python': bad, 'typescript/futureagi': '0.1.2'})
                with self.assertRaises(GuardError):
                    validate_version_changes(before, after)

    def test_rejects_missing_version_update(self):
        before, after = fixture()
        del after['python/fi/__init__.py']
        with self.assertRaises(GuardError):
            validate_version_changes(before, after)

    def test_rejects_file_deletion(self):
        before, after = fixture()
        after['python/CHANGELOG.md'] = None
        with self.assertRaises(GuardError):
            validate_version_changes(before, after)

    def test_rejects_new_manifest_package(self):
        before, after = fixture()
        manifest = json.loads(after[MANIFEST]); manifest['extra'] = '1.0.0'
        after[MANIFEST] = json.dumps(manifest)
        with self.assertRaises(GuardError):
            validate_version_changes(before, after)


class FakeGitHub(GitHub):
    def __init__(self):
        super().__init__('future-agi/futureagi-sdk')
        self.before, self.after = fixture()
        self.pr = {
            'state': 'open', 'draft': False, 'user': {'login': 'futureagi-release-bot[bot]', 'type': 'Bot'},
            'base': {'ref': 'main', 'sha': 'base'},
            'head': {'ref': RELEASE_BRANCH, 'sha': 'head', 'repo': {'full_name': self.repo}},
            'changed_files': len(self.after),
        }
        self.behind = 0
        self.posts = []
        self.head_reads = 0
        self.race = False
        self.already_approved = False
        self.runs = [
            {'id': 1, 'path': '.github/workflows/ci.yml', 'head_sha': 'base', 'head_branch': 'main', 'event': 'push', 'status': 'completed', 'conclusion': 'success'},
            {'id': 2, 'path': '.github/workflows/e2e.yml', 'head_sha': 'base', 'head_branch': 'main', 'event': 'push', 'status': 'completed', 'conclusion': 'success'},
        ]
        self.tag_sha = 'base'
        self.ancestor = True
        self.tag_exists = True
        self.annotated = False

    def main_sha(self):
        return 'base'

    def content(self, path, sha, optional=False):
        return (self.before if sha == 'base' else self.after)[path]

    def api(self, suffix, method='GET', data=None):
        if method == 'POST':
            self.posts.append((suffix, data)); return {'id': 123}
        if suffix == 'pulls/1':
            self.head_reads += 1
            pr = copy.deepcopy(self.pr)
            if self.race and self.head_reads > 1:
                pr['head']['sha'] = 'different'
            return pr
        if suffix == 'compare/base...head':
            return {'behind_by': self.behind}
        if suffix.startswith('pulls/1/files'):
            return [{'filename': path, 'status': 'added' if self.before.get(path) is None else 'modified'} for path in self.after]
        if suffix.startswith('pulls/1/reviews'):
            return [{'user': {'login': 'github-actions[bot]'}, 'commit_id': 'head', 'state': 'APPROVED'}] if self.already_approved else []
        if suffix.startswith('actions/runs?'):
            return {'workflow_runs': self.runs}
        if suffix.startswith('git/ref/tags/'):
            if not self.tag_exists:
                raise GuardError('GitHub API returned HTTP 404 for GET ' + suffix)
            return {'object': {'sha': 'annotation' if self.annotated else self.tag_sha, 'type': 'tag' if self.annotated else 'commit'}}
        if suffix == 'git/tags/annotation':
            return {'object': {'sha': self.tag_sha, 'type': 'commit'}}
        if suffix.startswith('commits/'):
            raise AssertionError('Commit names are not proof a release tag exists')
        if suffix.endswith('...main'):
            return {'merge_base_commit': {'sha': self.tag_sha if self.ancestor else 'other'}}
        raise AssertionError(suffix)


class ReconcileGitHub(FakeGitHub):
    def __init__(self):
        super().__init__()
        self.candidates = [{'number': 1}]
        self.current_main = 'newbase'
        self.puts = []
        self.updated = False
        self.complete_update = True
        self.main_passes = True
        self.conflict = False
        self.mutate_after_update = False
        self.main_advances = False
        self.main_before = dict(self.before)
        self.main_added_import = ''

    def main_sha(self):
        return 'another-main' if self.main_advances and self.updated else self.current_main

    def checks_passed(self, sha):
        return self.main_passes

    def content(self, path, sha, optional=False):
        if sha == 'newbase':
            return self.main_before[path]
        return (self.before if sha == 'base' else self.after)[path]

    def api(self, suffix, method='GET', data=None):
        if suffix.startswith('pulls?state=open'):
            return self.candidates
        if suffix == 'pulls/1/update-branch':
            if self.conflict:
                raise GuardError('GitHub API returned HTTP 409 for PUT update-branch')
            assert method == 'PUT'
            assert data == {'expected_head_sha': 'head'}
            self.puts.append(data)
            if self.complete_update:
                self.updated = True
                self.pr['base']['sha'] = self.current_main
                self.pr['head']['sha'] = 'updated'
                self.after['python/fi/__init__.py'] += self.main_added_import
                if self.mutate_after_update:
                    self.after['python/fi/__init__.py'] += '\nprint("unexpected")\n'
            return {'message': 'Updating pull request branch.'}
        if suffix.startswith('compare/'):
            return {'behind_by': 0 if self.updated or self.current_main == 'base' else 1,
                    'merge_base_commit': {'sha': self.current_main if self.updated else 'base'}}
        return super().api(suffix, method, data)


class ReconciliationTests(unittest.TestCase):
    def test_unchanged_pr_recovers_from_failed_prior_run(self):
        github = ReconcileGitHub()
        self.assertEqual(github.reconcile('futureagi-release-bot[bot]'), 1)
        self.assertEqual(github.puts, [{'expected_head_sha': 'head'}])
        self.assertEqual(github.pr['head']['sha'], 'updated')
        self.assertEqual(github.posts, [], 'The app reconciles; it does not submit reviews')
        self.assertEqual(github.approve(1, 'futureagi-release-bot[bot]'), 'updated')
        self.assertEqual(github.posts[0][1]['commit_id'], 'updated')

    def test_stale_pr_uses_merge_base_then_preserves_new_main_code(self):
        github = ReconcileGitHub()
        github.pr['base']['sha'] = 'newbase'  # API may already report current main
        github.main_added_import = '\nfrom typing import TYPE_CHECKING\n'
        github.main_before['python/fi/__init__.py'] += github.main_added_import
        self.assertEqual(github.reconcile('futureagi-release-bot[bot]'), 1)
        self.assertIn('from typing import TYPE_CHECKING', github.after['python/fi/__init__.py'])
        self.assertEqual(github.approve(1, 'futureagi-release-bot[bot]'), 'updated')

    def test_current_version_pr_needs_no_update(self):
        github = ReconcileGitHub(); github.current_main = 'base'
        self.assertEqual(github.reconcile('futureagi-release-bot[bot]'), 1)
        self.assertEqual(github.puts, [])

    def test_no_outstanding_pr_is_noop(self):
        github = ReconcileGitHub(); github.candidates = []
        self.assertIsNone(github.reconcile('futureagi-release-bot[bot]'))
        self.assertEqual(github.puts, [])

    def test_multiple_candidates_fail_closed(self):
        github = ReconcileGitHub(); github.candidates.append({'number': 2})
        with self.assertRaises(GuardError): github.reconcile('futureagi-release-bot[bot]')
        self.assertEqual(github.puts, [])

    def test_human_or_code_pr_is_never_updated(self):
        for defect in ['human', 'code', 'fork', 'dev']:
            with self.subTest(defect=defect):
                github = ReconcileGitHub()
                if defect == 'human': github.pr['user']['type'] = 'User'
                if defect == 'code': github.after['python/fi/__init__.py'] += '\nprint(1)\n'
                if defect == 'fork': github.pr['head']['repo']['full_name'] = 'other/repo'
                if defect == 'dev': github.pr['head']['ref'] = 'dev'
                with self.assertRaises(GuardError): github.reconcile('futureagi-release-bot[bot]')
                self.assertEqual(github.puts, [])

    def test_failed_main_cannot_update_candidate(self):
        github = ReconcileGitHub(); github.main_passes = False
        with self.assertRaises(GuardError): github.reconcile('futureagi-release-bot[bot]')
        self.assertEqual(github.puts, [])

    def test_update_conflict_does_not_approve(self):
        github = ReconcileGitHub(); github.conflict = True
        with self.assertRaises(GuardError): github.reconcile('futureagi-release-bot[bot]')
        self.assertEqual(github.posts, [])

    def test_update_is_revalidated_for_unexpected_code(self):
        github = ReconcileGitHub(); github.mutate_after_update = True
        with self.assertRaises(GuardError): github.reconcile('futureagi-release-bot[bot]')
        self.assertEqual(github.posts, [])

    def test_main_advancing_during_update_stops_approval(self):
        github = ReconcileGitHub(); github.main_advances = True
        with self.assertRaises(GuardError): github.reconcile('futureagi-release-bot[bot]')
        self.assertEqual(github.posts, [])

    def test_update_timeout_is_bounded(self):
        github = ReconcileGitHub(); github.complete_update = False
        with self.assertRaises(GuardError): github.reconcile('futureagi-release-bot[bot]', wait_seconds=0)
        self.assertEqual(github.posts, [])


class AuthorizationTests(unittest.TestCase):
    def test_approves_valid_exact_commit(self):
        github = FakeGitHub()
        self.assertEqual(github.approve(1, 'futureagi-release-bot[bot]'), 'head')
        self.assertEqual(github.posts[0][1]['commit_id'], 'head')
        self.assertEqual(github.posts[0][1]['event'], 'APPROVE')

    def test_existing_approval_is_not_duplicated(self):
        github = FakeGitHub(); github.already_approved = True
        github.approve(1, 'futureagi-release-bot[bot]')
        self.assertEqual(github.posts, [])

    def test_never_approves_human_fork_dev_or_code_pr(self):
        for change in ['human', 'fork', 'dev', 'branch', 'draft', 'behind', 'truncated', 'code', 'race']:
            with self.subTest(change=change):
                github = FakeGitHub()
                if change == 'human': github.pr['user']['type'] = 'User'
                if change == 'fork': github.pr['head']['repo']['full_name'] = 'other/repo'
                if change == 'dev': github.pr['base']['ref'] = 'dev'
                if change == 'branch': github.pr['head']['ref'] = 'dev'
                if change == 'draft': github.pr['draft'] = True
                if change == 'behind': github.behind = 1
                if change == 'truncated': github.pr['changed_files'] = 101
                if change == 'code': github.after['python/fi/__init__.py'] += '\nprint(1)\n'
                if change == 'race': github.race = True
                with self.assertRaises(GuardError): github.approve(1, 'futureagi-release-bot[bot]')
                self.assertEqual(github.posts, [])

    def test_both_main_workflows_required(self):
        github = FakeGitHub()
        self.assertTrue(github.checks_passed('base'))
        github.runs.pop()
        self.assertFalse(github.checks_passed('base'))

    def test_newer_failure_cannot_reuse_old_success(self):
        github = FakeGitHub()
        failed = {**github.runs[0], 'id': 3, 'conclusion': 'failure'}
        github.runs.append(failed)
        self.assertFalse(github.checks_passed('base'))

    def test_pr_runs_and_other_shas_do_not_authorize_release(self):
        for field, value in [('event', 'pull_request'), ('head_sha', 'other'), ('head_branch', 'dev'), ('status', 'in_progress')]:
            with self.subTest(field=field):
                github = FakeGitHub(); github.runs[0][field] = value
                self.assertFalse(github.checks_passed('base'))

    def test_release_tag_requires_main_ancestry_and_checks(self):
        github = FakeGitHub()
        self.assertEqual(github.validate_tag('python-v0.7.0'), 'base')
        github.ancestor = False
        with self.assertRaises(GuardError): github.validate_tag('python-v0.7.0')
        github.ancestor = True; github.runs = []
        with self.assertRaises(GuardError): github.validate_tag('python-v0.7.0')

    def test_branch_name_cannot_substitute_for_tag(self):
        github = FakeGitHub(); github.tag_exists = False
        with self.assertRaises(GuardError):
            github.validate_tag('python-v0.7.0')

    def test_annotated_release_tag(self):
        github = FakeGitHub(); github.annotated = True
        self.assertEqual(github.validate_tag('python-v0.7.0'), 'base')

    def test_main_advance_race_waits_for_exact_tag_checks(self):
        github = FakeGitHub()
        with patch.object(github, 'check_state', side_effect=['pending', 'success']), patch('release_guard.time.sleep') as sleep:
            self.assertEqual(github.validate_tag('python-v0.7.0', wait_seconds=60), 'base')
            sleep.assert_called_once()

    def test_failed_checks_do_not_wait_or_publish(self):
        github = FakeGitHub()
        with patch.object(github, 'check_state', return_value='failed'), patch('release_guard.time.sleep') as sleep:
            with self.assertRaises(GuardError):
                github.validate_tag('python-v0.7.0', wait_seconds=60)
            sleep.assert_not_called()

    def test_rejects_nonrelease_tags(self):
        for tag in ['dev', 'main', 'v0.7.0', 'python-v0.7.0-rc.1', '../main']:
            with self.subTest(tag=tag), self.assertRaises(GuardError):
                FakeGitHub().validate_tag(tag)


if __name__ == '__main__':
    unittest.main()
