# SDK release automation

## Release boundary

Only changes merged to `main` are eligible for a public SDK release. A push to `dev` prepares a promotion PR but never approves or auto-merges it. Merge promotions with a merge commit to preserve Conventional Commit history. After a release, bring main's version commits back to dev before the next promotion; the existing up-to-date protection remains enabled.

Once both **CI** and **E2E** succeed on the current `main` push:

1. `release-please.yml` uses the release app to create or update a version/changelog PR.
2. `release_guard.py` verifies the app author, same-repository release branch, up-to-date main base, exact head, complete diff, and version-only changes. GitHub Actions approves that machine-generated PR, not ordinary code PRs.
3. The release app enables normal auto-merge. Required **CI Pass** and **E2E Tests Pass** still gate merging; no admin bypass is used.
4. After the version commit lands on main and its own main-push checks succeed, release-please creates the package tags and GitHub releases.
5. The workflow sends a `repository_dispatch` event to `publish.yml` on main for each new tag. This avoids reusable-workflow identity differences between PyPI and npm. Publication independently resolves a real tag, verifies main ancestry, and waits up to 65 minutes for its exact commit's main-push checks if main advanced during release preparation. Failed checks stop publication; passing checks allow building that immutable commit.
6. PyPI and npm exchange the GitHub Actions OIDC identity for short-lived publisher credentials. The published version is reinstalled from its registry and smoke-tested.

`feat`, `fix`, `perf`, and breaking conventional commits drive version changes according to release-please's package strategy. Documentation-only or CI-only changes need not create a package version. Python and TypeScript version independently.

## One-time setup

Configuration does not publish a version. Do not dispatch publication merely to test credentials.

### GitHub

- Install the existing `futureagi-release-bot` app on **future-agi/futureagi-sdk**, with Contents and Pull requests write access. Do not create a broad personal access token.
- Set repository variable `RELEASE_BOT_APP_ID` to the app ID. A secret of the same name is also supported for compatibility.
- Set repository secret `RELEASE_BOT_PRIVATE_KEY` from the app's private-key file. Never commit it or paste it into a PR/log. An existing selected-repository organization secret may be shared instead.
- Enable repository **Allow auto-merge**.
- Enable **Allow GitHub Actions to create and approve pull requests**. Keep default workflow permissions read-only. Only the release job requests `pull-requests: write`; its script refuses human PRs, forks, dev promotions, code/workflow edits, unexpected paths, file deletions, inconsistent version bumps, stale bases, and changed heads.
- Keep `CI Pass` and `E2E Tests Pass` required on dev/main. Keep the organization's review rule and stale-review dismissal. Do not exempt the release app from required checks.
- Create environments **pypi** and **npm**, allowing deployments only from branch **main**. No per-release environment approval is needed because main is the reviewed boundary and the publish guard verifies the tagged commit. Do not allow arbitrary branches or tags to use these environments.

GitHub Actions approvals must also be allowed by the organization's Actions policy. If the repository setting is denied, an organization administrator must permit it; the workflow must not use a PAT/admin bypass to work around that denial.

### PyPI — `futureagi`

In the existing project's Publishing settings, add this GitHub trusted publisher:

| Field | Value |
|---|---|
| Owner | `future-agi` |
| Repository | `futureagi-sdk` |
| Workflow filename | `publish.yml` |
| Environment | `pypi` |

No PyPI API token is used. See [PyPI trusted-publisher setup](https://docs.pypi.org/trusted-publishers/adding-a-publisher/).

### npm — `@future-agi/sdk`

In the existing package's trusted-publisher settings:

| Field | Value |
|---|---|
| Owner | `future-agi` |
| Repository | `futureagi-sdk` |
| Workflow filename | `publish.yml` |
| Environment | `npm` |
| Allowed action | Direct `npm publish` |

The workflow uses Node 24 and npm 11.6.2 (trusted publishing requires npm >=11.5.1). It does not use `NPM_TOKEN`. Package ownership, repository metadata, and publisher identity must agree with the repository publishing the package. See [npm trusted publishing](https://docs.npmjs.com/trusted-publishers).

## Guarded approval scope

Only this same-repository branch is eligible: `release-please--branches--main`, opened by the configured release app and targeting `main`.

Allowed changes:

- `.release-please-manifest.json`: the existing two package entries, stable one-step semantic version bumps only.
- `python/pyproject.toml`: only its package-version declaration.
- `python/fi/__init__.py`: only its `__version__` declaration.
- `typescript/futureagi/package.json`: only its `version` property.
- The corresponding package `CHANGELOG.md` files.

No application code, dependency updates, scripts, workflow edits, renamed/deleted files, or new packages are automatically approved. A changed version must match all of that package's version files and include its changelog. Approval is bound to the validated head SHA; organization stale-review dismissal invalidates it on subsequent pushes.

The generator/transport SDK tests are separate from these release-authorization tests. `CI Pass` depends on both.

## Recovery

- **No release PR:** inspect `release-please` and the main CI/E2E runs. Missing bot credentials fail clearly. An old workflow event, a failing/running main suite, or a newer main commit skips release preparation until the relevant successful completion event.
- **Version PR rejected by the guard:** read the failure; do not override it. A release requiring a source or dependency change belongs in a normally reviewed PR.
- **Required check pending:** fix the check/ref alignment. Do not disable required checks or add a bypass.
- **Registry upload fails:** fix the registry trusted publisher and dispatch **Publish** on **main**, supplying the existing exact tag (`python-vX.Y.Z` or `typescript-vX.Y.Z`). The guard still verifies ancestry and checks. Existing registry versions are not overwritten.
- **Release creation succeeded but the caller was interrupted:** retry **Publish** with that tag; release-please may correctly report no new release on its own rerun.
- **Post-publish smoke fails:** the version may already be public. Do not delete/reuse it; investigate and ship a normally versioned fix.

## Validation without publishing

Run authorization unit tests and workflow lint in GitHub Actions, GCP staging, or E2B. No local app/test stack and no live registry writes are required.

```sh
python -m unittest discover -s .github/scripts -p 'test_*.py' -v
actionlint .github/workflows/*.yml
```

The tests use synthetic API responses and assert that invalid author/branch/diff/version/check states cannot create an approval. Actual registry OIDC authorization can be confirmed only once the owner has configured the publishers and a real release is intentionally made. A dry run is not a claim of successful publication.
