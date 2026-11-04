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
            'changed_files': 6,
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
        contents = self.before if sha == 'base' else self.after
        return contents.get(path) if optional else contents[path]

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


LOCKFILE = 'typescript/futureagi/package-lock.json'
CONSTANTS = 'typescript/futureagi/gateway-client/src/constants.ts'


def extended_fixture(*, lockfile=True, constants=False):
    # PR #40 (e9fd7b0b) has these seven paths and these exact version bumps.
    # Keep representative dependency/integrity data without a full npm lockfile.
    before, after = fixture()
    if lockfile:
        old_lock = {
            'name': '@future-agi/sdk', 'version': '0.1.2',
            'lockfileVersion': 3, 'requires': True,
            'packages': {
                '': {'name': '@future-agi/sdk', 'version': '0.1.2', 'dependencies': {'axios': '^1.6.0'}},
                'node_modules/axios': {'version': '1.6.0', 'integrity': 'sha512-unchanged'},
            },
        }
        new_lock = copy.deepcopy(old_lock)
        new_lock['version'] = new_lock['packages']['']['version'] = '0.2.0'
        before[LOCKFILE], after[LOCKFILE] = json.dumps(old_lock), json.dumps(new_lock)
    if constants:
        before[CONSTANTS] = (
            '// SDK version\n'
            'export const VERSION: string = "0.1.2"; // x-release-please-version\n'
            '\n// Defaults\nexport const DEFAULT_TIMEOUT = 600_000; // 600s in ms\n'
        )
        after[CONSTANTS] = before[CONSTANTS].replace('"0.1.2"', '"0.2.0"')
    return before, after


class ExtendedVersionDiffTests(unittest.TestCase):
    def test_accepts_lockfile_and_constants_with_existing_two_argument_api(self):
        validate_version_changes(*extended_fixture(constants=True))

    def test_rejects_lockfile_dependency_integrity_and_nested_version_edits(self):
        for location, field, value in [
            ('', 'dependencies', {'axios': '^2.0.0'}),
            ('node_modules/axios', 'integrity', 'sha512-changed'),
            ('node_modules/axios', 'version', '1.6.1'),
        ]:
            with self.subTest(location=location, field=field):
                before, after = extended_fixture()
                lock = json.loads(after[LOCKFILE])
                lock['packages'][location][field] = value
                after[LOCKFILE] = json.dumps(lock)
                with self.assertRaisesRegex(GuardError, 'package-lock.json changes more than'):
                    validate_version_changes(before, after)

    def test_rejects_lockfile_metadata_edits(self):
        for field, value in [('lockfileVersion', 2), ('requires', False), ('requires', 1), ('name', 'other')]:
            with self.subTest(field=field, value=value):
                before, after = extended_fixture()
                lock = json.loads(after[LOCKFILE]); lock[field] = value
                after[LOCKFILE] = json.dumps(lock)
                with self.assertRaisesRegex(GuardError, 'package-lock.json changes more than'):
                    validate_version_changes(before, after)

    def test_requires_both_lockfile_versions_to_match_each_manifest(self):
        for side in ['before', 'after']:
            for root in [True, False]:
                for bad in ['9.9.9', None]:
                    with self.subTest(side=side, root=root, version=bad):
                        before, after = extended_fixture()
                        contents = before if side == 'before' else after
                        lock = json.loads(contents[LOCKFILE])
                        target = lock if root else lock['packages']['']
                        if bad is None:
                            del target['version']
                        else:
                            target['version'] = bad
                        contents[LOCKFILE] = json.dumps(lock)
                        with self.assertRaisesRegex(GuardError, 'Lockfile version disagrees with manifest'):
                            validate_version_changes(before, after)

    def test_rejects_invalid_lockfile_json_or_structure(self):
        for bad in ['{', '[]', '{"version":"0.2.0"}', '{"packages":{"":[]}}']:
            with self.subTest(lock=bad):
                before, after = extended_fixture(); after[LOCKFILE] = bad
                with self.assertRaisesRegex(GuardError, 'Invalid package-lock.json'):
                    validate_version_changes(before, after)

    def test_rejects_duplicate_lockfile_keys_and_non_json_numbers(self):
        before, after = extended_fixture()
        duplicate = after[LOCKFILE].replace('"lockfileVersion": 3', '"lockfileVersion": 2, "lockfileVersion": 3')
        non_json = after[LOCKFILE].replace('"requires": true', '"requires": NaN')
        for bad in [duplicate, non_json]:
            with self.subTest(lock=bad):
                changed = {**after, LOCKFILE: bad}
                with self.assertRaisesRegex(GuardError, 'Invalid package-lock.json'):
                    validate_version_changes(before, changed)

    def test_rejects_constants_non_version_edits(self):
        for change in ['source', 'comment', 'newline']:
            with self.subTest(change=change):
                before, after = extended_fixture(constants=True)
                if change == 'source': after[CONSTANTS] = after[CONSTANTS].replace('600_000', '1')
                if change == 'comment': after[CONSTANTS] = after[CONSTANTS].replace('// Defaults', '// Changed defaults')
                if change == 'newline': after[CONSTANTS] = after[CONSTANTS].rstrip('\n')
                with self.assertRaisesRegex(GuardError, 'Non-version source edit in ' + CONSTANTS):
                    validate_version_changes(before, after)

    def test_rejects_constants_version_disagreement(self):
        for side, expected in [('before', '0.1.2'), ('after', '0.2.0')]:
            with self.subTest(side=side):
                before, after = extended_fixture(constants=True)
                contents = before if side == 'before' else after
                contents[CONSTANTS] = contents[CONSTANTS].replace(expected, '9.9.9')
                with self.assertRaisesRegex(GuardError, 'Version disagreement: ' + CONSTANTS):
                    validate_version_changes(before, after)

    def test_requires_one_exact_constants_declaration_in_each_revision(self):
        for side in ['before', 'after']:
            for change in ['duplicate', 'missing', 'type', 'marker', 'suffix']:
                with self.subTest(side=side, change=change):
                    before, after = extended_fixture(constants=True)
                    contents = before if side == 'before' else after
                    declaration = contents[CONSTANTS].splitlines(keepends=True)[1]
                    if change == 'duplicate': contents[CONSTANTS] += declaration
                    if change == 'missing': contents[CONSTANTS] = contents[CONSTANTS].replace(declaration, '')
                    if change == 'type': contents[CONSTANTS] = contents[CONSTANTS].replace(': string', '')
                    if change == 'marker': contents[CONSTANTS] = contents[CONSTANTS].replace('x-release-please-version', 'other')
                    if change == 'suffix': contents[CONSTANTS] = contents[CONSTANTS].replace(declaration, declaration.rstrip('\n') + ' extra\n')
                    with self.assertRaisesRegex(GuardError, 'Ambiguous version declaration: ' + CONSTANTS):
                        validate_version_changes(before, after)

    def test_rejects_optional_file_deletions_in_content_validation(self):
        for path in [LOCKFILE, CONSTANTS]:
            for missing_key in [False, True]:
                with self.subTest(path=path, missing_key=missing_key):
                    before, after = extended_fixture(constants=True)
                    if missing_key:
                        del after[path]
                    else:
                        after[path] = None
                    with self.assertRaisesRegex(GuardError, 'Release PR deletes a file'):
                        validate_version_changes(before, after)


class ExtendedAuthorizationTests(unittest.TestCase):
    def github(self, **kwargs):
        github = FakeGitHub()
        github.before, github.after = extended_fixture(**kwargs)
        github.pr['changed_files'] = len(github.after)
        return github

    def assert_rejected(self, github, message):
        with self.assertRaisesRegex(GuardError, message):
            github.approve(1, 'futureagi-release-bot[bot]')
        self.assertEqual(github.posts, [])

    def test_approves_pr40_seven_file_shape_without_base_constants(self):
        github = self.github()
        self.assertEqual(set(github.after), {
            MANIFEST, 'python/pyproject.toml', 'python/fi/__init__.py', 'python/CHANGELOG.md',
            'typescript/futureagi/package.json', 'typescript/futureagi/CHANGELOG.md', LOCKFILE,
        })
        with patch.object(github, 'content', wraps=github.content) as content:
            self.assertEqual(github.approve(1, 'futureagi-release-bot[bot]'), 'head')
            content.assert_any_call(LOCKFILE, 'base', optional=True)
            content.assert_any_call(CONSTANTS, 'base', optional=True)
        self.assertEqual(github.posts[0][1]['commit_id'], 'head')

    def test_approves_eight_file_shape_with_base_constants(self):
        github = self.github(constants=True)
        self.assertEqual(len(github.after), 8)
        self.assertEqual(github.approve(1, 'futureagi-release-bot[bot]'), 'head')
        self.assertEqual(github.posts[0][1]['event'], 'APPROVE')

    def test_does_not_require_either_optional_file_when_absent_at_base(self):
        github = self.github(lockfile=False)
        with patch.object(github, 'content', wraps=github.content) as content:
            self.assertEqual(github.validate_pr(1, 'futureagi-release-bot[bot]'), 'head')
            content.assert_any_call(LOCKFILE, 'base', optional=True)
            content.assert_any_call(CONSTANTS, 'base', optional=True)

    def test_requires_each_optional_file_when_present_at_base(self):
        for path in [LOCKFILE, CONSTANTS]:
            with self.subTest(path=path):
                github = self.github(lockfile=path == LOCKFILE, constants=path == CONSTANTS)
                # The base snapshot retains the file, but the PR diff omits it.
                del github.after[path]
                github.pr['changed_files'] = len(github.after)
                self.assert_rejected(github, 'Version bump missing ' + path)

    def test_python_only_bump_does_not_require_existing_ts_files(self):
        github = self.github(constants=True)
        for path in [*PACKAGES['typescript/futureagi'], LOCKFILE, CONSTANTS]:
            del github.after[path]
        github.after[MANIFEST] = json.dumps({'python': '0.7.0', 'typescript/futureagi': '0.1.2'})
        github.pr['changed_files'] = len(github.after)
        self.assertEqual(github.validate_pr(1, 'futureagi-release-bot[bot]'), 'head')

    def test_rejects_newly_added_lockfile_or_constants(self):
        for path in [LOCKFILE, CONSTANTS]:
            with self.subTest(path=path):
                github = self.github(constants=True)
                del github.before[path]
                self.assert_rejected(github, 'Release PR adds a non-changelog file')

    def test_rejects_deleted_or_renamed_lockfile_and_constants(self):
        for path in [LOCKFILE, CONSTANTS]:
            for status in ['removed', 'renamed']:
                with self.subTest(path=path, status=status):
                    github = self.github(constants=True)
                    original_api = github.api
                    files = original_api('pulls/1/files?per_page=100')
                    for item in files:
                        if item['filename'] == path: item['status'] = status
                    def api(suffix, method='GET', data=None):
                        if suffix == 'pulls/1/files?per_page=100': return files
                        return original_api(suffix, method, data)
                    with patch.object(github, 'api', side_effect=api):
                        self.assert_rejected(github, 'Release PR renames or deletes files')

    def test_rejects_ninth_file(self):
        github = self.github(constants=True)
        github.before['README.md'] = 'old'; github.after['README.md'] = 'new'
        github.pr['changed_files'] = 9
        self.assert_rejected(github, 'Unexpected or truncated release diff')

    def test_rejects_workflow_change_within_eight_file_bound(self):
        github = self.github()
        path = '.github/workflows/publish.yml'
        github.before[path] = 'old'; github.after[path] = 'new'
        github.pr['changed_files'] = 8
        self.assert_rejected(github, 'Release PR includes code or workflow changes')

    def test_rejects_truncated_eight_file_shape(self):
        github = self.github(constants=True)
        github.pr['changed_files'] = 9
        self.assert_rejected(github, 'Unexpected or truncated release diff')

    def test_does_not_treat_base_fetch_failure_as_absence(self):
        for path in [LOCKFILE, CONSTANTS]:
            with self.subTest(path=path):
                github = self.github()
                original_content = github.content
                def content(name, sha, optional=False):
                    if name == path and sha == 'base':
                        raise GuardError('GitHub API returned HTTP 403 for GET contents/' + name)
                    return original_content(name, sha, optional)
                with patch.object(github, 'content', side_effect=content):
                    self.assert_rejected(github, 'HTTP 403')


if __name__ == '__main__':
    unittest.main()
