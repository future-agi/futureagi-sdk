"""Fail-closed guards for releases and bot-only version PR approval. Standard library only."""
from __future__ import annotations

import argparse
import base64
import json
import os
import re
import time
import urllib.error
import urllib.parse
import urllib.request

PACKAGES = {
    "python": ("python/pyproject.toml", "python/fi/__init__.py", "python/CHANGELOG.md"),
    "typescript/futureagi": ("typescript/futureagi/package.json", "typescript/futureagi/CHANGELOG.md"),
}
# Unlike PACKAGES, these are required only when they exist at the PR base.
BASE_VERSION_FILES = {
    "typescript/futureagi": (
        "typescript/futureagi/package-lock.json",
        "typescript/futureagi/gateway-client/src/constants.ts",
    ),
}
MANIFEST = ".release-please-manifest.json"
RELEASE_BRANCH = "release-please--branches--main"
REQUIRED_WORKFLOWS = {".github/workflows/ci.yml", ".github/workflows/e2e.yml"}


class GuardError(RuntimeError):
    pass


def require(condition, message):
    if not condition:
        raise GuardError(message)


def version(value):
    require(isinstance(value, str) and re.fullmatch(r"\d+\.\d+\.\d+", value), "Only stable semantic versions may release automatically")
    return tuple(map(int, value.split(".")))


def valid_bump(old, new):
    major, minor, patch = version(old)
    return version(new) in {(major, minor, patch + 1), (major, minor + 1, 0), (major + 1, 0, 0)}


def validate_lockfile(before, after, old, new):
    def unique_object(pairs):
        result = {}
        for key, value in pairs:
            require(key not in result, 'Invalid package-lock.json: duplicate key')
            result[key] = value
        return result

    normalized = []
    try:
        for content, expected in [(before, old), (after, new)]:
            lock = json.loads(content, object_pairs_hook=unique_object)
            require(isinstance(lock, dict) and isinstance(lock.get('packages'), dict)
                    and isinstance(lock['packages'].get(''), dict), 'Invalid package-lock.json structure')
            root = lock['packages']['']
            require(lock.get('version') == root.get('version') == expected, 'Lockfile version disagrees with manifest')
            del lock['version']; del root['version']
            # Canonical JSON also distinguishes booleans from numbers (True == 1 in Python).
            normalized.append(json.dumps(lock, sort_keys=True, allow_nan=False))
    except ValueError:
        raise GuardError('Invalid package-lock.json') from None
    require(normalized[0] == normalized[1], 'package-lock.json changes more than its root versions')


def validate_version_changes(before, after, existing_paths=()):
    """Validate a diff, with base-existing conditional paths supplied by validate_pr."""
    old, new = json.loads(before[MANIFEST]), json.loads(after[MANIFEST])
    require(set(old) == set(new) == set(PACKAGES), "Manifest package set changed")
    changed = {name for name in PACKAGES if old[name] != new[name]}
    require(changed, "No package version changed")
    allowed = {MANIFEST}
    for name in changed:
        require(valid_bump(old[name], new[name]), f"Unexpected version bump for {name}")
        allowed.update(PACKAGES[name])
        allowed.update(BASE_VERSION_FILES.get(name, ()))
    paths = set(before) | set(after)
    require(paths <= allowed, "Release PR changes files outside the version/changelog allowlist")
    require(all(after.get(path) is not None for path in paths), "Release PR deletes a file")
    require(all(before.get(path) is not None or path.endswith('/CHANGELOG.md') for path in paths), "Release PR adds a non-changelog file")
    for name in changed:
        conditional = tuple(path for path in BASE_VERSION_FILES.get(name, ()) if path in existing_paths or path in paths)
        for path in PACKAGES[name] + conditional:
            require(path in after, f"Version bump missing {path}")
            if path.endswith('/CHANGELOG.md'):
                require(after[path].strip(), "Empty changelog")
                continue
            a, b = before[path], after[path]
            if path.endswith('package-lock.json'):
                validate_lockfile(a, b, old[name], new[name])
            elif path.endswith('/constants.ts'):
                pattern = r'(?m)^export const VERSION: string = "([^"\r\n]+)"; // x-release-please-version$'
                old_matches, new_matches = list(re.finditer(pattern, a)), list(re.finditer(pattern, b))
                require(len(old_matches) == len(new_matches) == 1, f"Ambiguous version declaration: {path}")
                old_match, new_match = old_matches[0], new_matches[0]
                require(old_match.group(1) == old[name] and new_match.group(1) == new[name], f"Version disagreement: {path}")
                normalized_a = a[:old_match.start(1)] + a[old_match.end(1):]
                normalized_b = b[:new_match.start(1)] + b[new_match.end(1):]
                require(normalized_a == normalized_b, f"Non-version source edit in {path}")
            elif path.endswith('package.json'):
                a, b = json.loads(a), json.loads(b)
                require(a.get('version') == old[name] and b.get('version') == new[name], "Package version disagrees with manifest")
                a.pop('version'); b.pop('version')
                require(a == b, "package.json changes more than its version")
            else:
                field = '__version__' if path.endswith('__init__.py') else 'version'
                pattern = rf'(?m)^({field}\s*=\s*")[^"]+("[^\n]*)$'
                old_matches = list(re.finditer(pattern, a))
                new_matches = list(re.finditer(pattern, b))
                require(len(old_matches) == len(new_matches) == 1, f"Ambiguous version declaration: {path}")
                require(f'"{old[name]}"' in old_matches[0].group() and f'"{new[name]}"' in new_matches[0].group(), f"Version disagreement: {path}")
                normalized_a = re.sub(pattern, r'\1VERSION\2', a)
                normalized_b = re.sub(pattern, r'\1VERSION\2', b)
                require(normalized_a == normalized_b, f"Non-version source edit in {path}")


class GitHub:
    def __init__(self, repo):
        require(re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+', repo), "Invalid repository")
        self.repo = repo

    def api(self, suffix, method='GET', data=None):
        headers = {'Accept': 'application/vnd.github+json', 'X-GitHub-Api-Version': '2022-11-28', 'User-Agent': 'sdk-release-guard'}
        if os.environ.get('GH_TOKEN'):
            headers['Authorization'] = 'Bearer ' + os.environ['GH_TOKEN']
        raw = None if data is None else json.dumps(data).encode()
        request = urllib.request.Request(f'https://api.github.com/repos/{self.repo}/{suffix}', data=raw, headers=headers, method=method)
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                return json.load(response)
        except urllib.error.HTTPError as error:
            raise GuardError(f'GitHub API returned HTTP {error.code} for {method} {suffix}') from None

    def content(self, path, sha, optional=False):
        # Read JSON/base64, never execute or import code from the candidate PR.
        try:
            result = self.api('contents/' + urllib.parse.quote(path, safe='/') + '?ref=' + sha)
        except GuardError as error:
            if optional and 'HTTP 404 ' in str(error):
                return None
            raise
        require(result.get('type') == 'file' and result.get('encoding') == 'base64', f'Not an ordinary file: {path}')
        require(result.get('size', 0) <= 2_000_000, f'File too large: {path}')
        return base64.b64decode(result['content']).decode('utf-8')

    def main_sha(self):
        return self.api('git/ref/heads/main')['object']['sha']

    def check_state(self, sha):
        runs = self.api(f'actions/runs?head_sha={sha}&event=push&branch=main&per_page=100')['workflow_runs']
        pending = False
        for path in REQUIRED_WORKFLOWS:
            matches = [r for r in runs if r['head_sha'] == sha and r['head_branch'] == 'main' and r['event'] == 'push' and r['path'] == path]
            if not matches:
                pending = True
                continue
            latest = max(matches, key=lambda r: r['id'])
            if latest['status'] != 'completed':
                pending = True
            elif latest['conclusion'] != 'success':
                return 'failed'
        return 'pending' if pending else 'success'

    def checks_passed(self, sha):
        return self.check_state(sha) == 'success'

    def validate_pr(self, number, bot):
        pr = self.api(f'pulls/{number}')
        require(pr['state'] == 'open' and not pr['draft'], 'Release PR is not open and ready')
        require(pr['user']['login'] == bot and pr['user']['type'] == 'Bot', 'PR was not opened by the configured release bot')
        require(pr['base']['ref'] == 'main' and pr['head']['ref'] == RELEASE_BRANCH, 'Not the release-please version PR')
        require(pr['head']['repo']['full_name'] == self.repo, 'Release PR is from a fork')
        base, head = pr['base']['sha'], pr['head']['sha']
        require(base == self.main_sha(), 'Main changed; wait for the next release run')
        comparison = self.api(f'compare/{base}...{head}')
        require(comparison['behind_by'] == 0, 'Release PR must be up to date with main')
        files = self.api(f'pulls/{number}/files?per_page=100')
        require(len(files) == pr['changed_files'] and 0 < len(files) <= 8, 'Unexpected or truncated release diff')
        require(all(f['status'] in ('modified', 'added') for f in files), 'Release PR renames or deletes files')
        paths = {f['filename'] for f in files}
        require(MANIFEST in paths, 'Release manifest is missing from the diff')
        conditional = {path for package in BASE_VERSION_FILES.values() for path in package}
        allowed = {MANIFEST} | {path for package in PACKAGES.values() for path in package} | conditional
        require(paths <= allowed, 'Release PR includes code or workflow changes')
        # Probe the base even for files absent from the diff; never infer existence
        # from the head or the changed-file list. Only an optional 404 means absent.
        base_contents = {path: self.content(path, base, optional=True) for path in conditional}
        before = {path: (base_contents[path] if path in base_contents else
                         self.content(path, base, optional=path.endswith('/CHANGELOG.md'))) for path in paths}
        after = {path: self.content(path, head) for path in paths}
        existing_paths = {path for path, content in base_contents.items() if content is not None}
        validate_version_changes(before, after, existing_paths=existing_paths)
        # Bind approval to the validated commit; stale reviews are dismissed by the org rule.
        require(self.api(f'pulls/{number}')['head']['sha'] == head, 'Release PR changed during validation')
        return head

    def approve(self, number, bot):
        head = self.validate_pr(number, bot)
        reviews = self.api(f'pulls/{number}/reviews?per_page=100')
        if any(r['user']['login'] == 'github-actions[bot]' and r['commit_id'] == head and r['state'] == 'APPROVED' for r in reviews):
            return head
        self.api(f'pulls/{number}/reviews', method='POST', data={
            'event': 'APPROVE', 'commit_id': head,
            'body': 'Automated release-only approval: verified release-bot identity, same-repository main target, exact head, version/changelog-only diff, and consistent one-step version bumps. Required CI/E2E checks still govern merging.',
        })
        return head

    def validate_tag(self, tag, wait_seconds=0):
        require(re.fullmatch(r'(python|typescript)-v\d+\.\d+\.\d+', tag), 'Invalid release tag')
        obj = self.api('git/ref/tags/' + tag)['object']
        # A branch with a tag-shaped name is not a release. Support annotated
        # tags, but bound peeling to avoid malformed/cyclic remote references.
        for _ in range(5):
            if obj['type'] == 'commit':
                break
            require(obj['type'] == 'tag', 'Release tag does not point to a commit')
            obj = self.api('git/tags/' + obj['sha'])['object']
        require(obj['type'] == 'commit', 'Too many nested annotated tags')
        sha = obj['sha']
        comparison = self.api(f'compare/{sha}...main')
        require(comparison['merge_base_commit']['sha'] == sha, 'Release tag is not on main')
        deadline = time.monotonic() + wait_seconds
        while True:
            state = self.check_state(sha)
            if state == 'success':
                return sha
            require(state != 'failed', 'Release tag commit failed main-push CI or E2E')
            require(time.monotonic() < deadline, 'Release tag commit lacks passing main-push CI and E2E')
            print('Waiting for the exact release commit CI/E2E; no package has been published.', flush=True)
            time.sleep(min(15, max(0, deadline - time.monotonic())))


def output(name, value):
    print(f'{name}={value}')
    if os.environ.get('GITHUB_OUTPUT'):
        with open(os.environ['GITHUB_OUTPUT'], 'a') as handle:
            handle.write(f'{name}={value}\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['check-main', 'approve', 'validate-tag'])
    parser.add_argument('--repo', default=os.environ.get('GITHUB_REPOSITORY', 'future-agi/futureagi-sdk'))
    parser.add_argument('--sha', default='')
    parser.add_argument('--number', type=int)
    parser.add_argument('--bot', default='futureagi-release-bot[bot]')
    parser.add_argument('--tag')
    parser.add_argument('--wait-seconds', type=int, default=0)
    args = parser.parse_args()
    github = GitHub(args.repo)
    if args.action == 'check-main':
        sha = github.main_sha()
        ready = (not args.sha or args.sha == sha) and github.checks_passed(sha)
        output('ready', 'true' if ready else 'false')
    elif args.action == 'approve':
        require(args.number is not None, '--number is required')
        output('head', github.approve(args.number, args.bot))
    else:
        require(args.tag is not None, '--tag is required')
        require(0 <= args.wait_seconds <= 3900, '--wait-seconds must be between 0 and 3900')
        output('sha', github.validate_tag(args.tag, args.wait_seconds))


if __name__ == '__main__':
    try:
        main()
    except GuardError as error:
        raise SystemExit(str(error)) from None
