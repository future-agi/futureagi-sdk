"""Positive and negative controls for the test-only workflow policy."""

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import yaml

from workflow_policy import check_repository, check_workflow


ROOT = Path(__file__).resolve().parents[2]
ACTIONS = json.loads(Path(__file__).with_name("workflow-policy.json").read_text())["actions"]


def workflow(command="python -m unittest discover"):
    return {
        "name": "Tests",
        "on": {"pull_request": None},
        "permissions": {"contents": "read"},
        "jobs": {"tests": {"runs-on": "ubuntu-latest", "steps": [{"run": command}]}},
    }


def inspect(document):
    return check_workflow(yaml.safe_dump(document), "control.yml", ACTIONS, set())


def repository_qualified_commands(group, arguments):
    """The CLI accepts repository options before, within or after commands."""
    for option in (
        "--repo example/project", "--repo=example/project",
        "-R example/project", "-Rexample/project", "-R=example/project",
        "--repo 'example/project'", '"--repo" "example/project"',
        "--repo '${{ github.repository }}'", "--repo $GH_REPO",
    ):
        yield f"gh {option} {group} {arguments}"
        yield f"gh {group} {option} {arguments}"
        yield f"gh {group} {arguments} {option}"


def dispatch_workflow(command):
    document = workflow(command)
    document["on"] = {
        "workflow_dispatch": {"inputs": {"repository": {"type": "string", "required": True}}}
    }
    document["jobs"]["tests"]["env"] = {"GH_REPO": "${{ inputs.repository }}"}
    return document


def run_policy(document):
    """Run the real policy entry point on a one-workflow repository."""
    with tempfile.TemporaryDirectory() as temporary:
        folder = Path(temporary) / ".github/workflows"
        folder.mkdir(parents=True)
        (folder / "control.yml").write_text(yaml.safe_dump(document))
        return subprocess.run(
            [sys.executable, str(Path(__file__).with_name("workflow_policy.py")), "--root", temporary],
            capture_output=True, text=True,
        )


SECRET_ACCESS = "explicit token or secret access is forbidden"
CREDENTIAL_FLOW = "credential-named value may not come from an expression"
# Credential contexts reached from anywhere inside an expression body.
SMUGGLED_CREDENTIALS = (
    "${{ toJSON(secrets) }}", "${{ format('{0}', secrets.NPM_TOKEN) }}",
    "${{ (secrets.NPM_TOKEN) }}", "${{ (github.token) }}", "${{ toJSON(github) }}",
    "${{ fromJSON(toJSON(github)).token }}", "${{ github.*.token }}",
    "${{ github[format('{0}', 'token')] }}", "${{ github . token }}", "${{ GITHUB.TOKEN }}",
    "${{ format('}}', secrets.NPM_TOKEN) }}", "${{\n  secrets.NPM_TOKEN }}",
    "v-${{ github.sha }}-${{ toJSON(secrets) }}", "${{ format('{0}', github) }}",
)


class WorkflowPolicyTests(unittest.TestCase):
    def test_repository_workflows_are_test_only(self):
        self.assertEqual(check_repository(ROOT), [])

    def test_required_checks_survive(self):
        folder = ROOT / ".github/workflows"
        package = yaml.safe_load((folder / "release-sdks.yml").read_text())
        self.assertEqual(set(package["jobs"]), {"package-checks"})
        commands = "\n".join(s.get("run", "") for s in package["jobs"]["package-checks"]["steps"])
        for required in ("pytest", "python -m build", "pnpm run typecheck", "pnpm test", "pnpm run build", "go test", "-DskipTests package"):
            with self.subTest(required=required):
                self.assertIn(required, commands)
        compliance = yaml.safe_load((folder / "sdk-compliance.yml").read_text())
        self.assertEqual(set(compliance["jobs"]), {"python-tests", "typescript-tests", "python-compliance", "typescript-compliance", "generated-sdk-builds"})
        for job in ("python-compliance", "typescript-compliance"):
            self.assertEqual(compliance["jobs"][job]["uses"], "./.github/workflows/sdk-contract-check.yml")

    def test_safe_builds_and_tests(self):
        for command in (
            "python -m build python", "twine check dist/*", "npm pack --ignore-scripts",
            "pnpm install --frozen-lockfile --ignore-scripts", "npm ci --ignore-scripts",
            "mvn -B -f java/pom.xml -DskipTests package", "git diff --exit-code",
            "go test ./...", "docker build -t adapter:test .", "pnpm run typecheck",
        ):
            with self.subTest(command=command):
                self.assertEqual(inspect(workflow(command)), [])

    def test_publication_commands_are_rejected(self):
        for command in (
            "twine upload dist/*", "python -m twine upload dist/*",
            "npm publish", "npm --workspace sdk publish", "pnpm publish --provenance",
            "yarn npm publish", "bun publish", "poetry publish", "uv publish",
            "npx semantic-release", "npx changeset publish", "goreleaser release",
            "mvn -B -f pom.xml -DskipTests deploy", "./mvnw deploy",
            "mvn org.apache.maven.plugins:maven-deploy-plugin:3.1.2:deploy-file",
            "./gradlew publishToMavenCentral", "gh release create v1",
            "gh release new v1 dist/*", "gh alias set rc 'release create'",
            "gh alias import aliases.yml",
            "gh release upload v1 dist/*", "gh api -X POST repos/o/r/git/refs",
            "git push origin --tags", 'git push origin "$TAG"',
            "git -c user.name=ci push origin HEAD:refs/tags/v1", "git tag v1",
            "docker push image:v1", "docker buildx build --push .",
            "vercel deploy --prod", "npx wrangler deploy", "kubectl apply -f app.yml",
            "helm upgrade app chart", "gcloud run deploy app", "terraform apply",
            "npm \\\n publish", '"npm" "publish"', "n'p'm pu'bl'ish",
        ):
            with self.subTest(command=command):
                self.assertTrue(inspect(workflow(command)), command)

    def test_repository_qualified_github_mutations_are_rejected(self):
        for group, arguments, diagnostic in (
            ("release", "create v1", "GitHub release"),
            ("release", "new v1 dist/*", "GitHub release"),
            ("release", "upload v1 dist/*", "GitHub release"),
            ("release", "edit v1 --draft=false", "GitHub release"),
            ("release", "delete v1 --yes", "GitHub release"),
            ("release", "delete-asset v1 sdk.whl --yes", "GitHub release"),
            ("api", "--method POST repos/example/project/releases", "GitHub API mutation"),
            ("api", "-X POST repos/example/project/releases", "GitHub API mutation"),
            ("api", "-XPOST repos/example/project/releases", "GitHub API mutation"),
            ("api", "-iX POST repos/example/project/releases", "GitHub API mutation"),
            ("api", "repos/example/project/releases -f tag_name=v1", "GitHub API mutation"),
            ("api", "repos/example/project/releases -ftag_name=v1", "GitHub API mutation"),
            ("api", "repos/example/project/releases --raw-field tag_name=v1", "GitHub API mutation"),
            ("api", "repos/example/project/releases --raw-field=tag_name=v1", "GitHub API mutation"),
            ("api", "repos/example/project/git/refs --input ref.json", "GitHub API mutation"),
            ("api", "repos/example/project/git/refs --input=ref.json", "GitHub API mutation"),
        ):
            for command in repository_qualified_commands(group, arguments):
                with self.subTest(command=command):
                    self.assertTrue(any(diagnostic in error for error in inspect(workflow(command))))

    def test_repository_qualified_github_reads_remain_allowed(self):
        for group, arguments in (
            ("release", "download v1 --pattern '*.whl'"),
            ("release", "download v1 --pattern create"),
            ("release", "download v1 --pattern new"),
            ("release", "view v1 --json tagName"),
            ("release", "list --limit 5"),
            ("api", "repos/example/project/releases/latest"),
            ("api", "repos/example/project/releases/latest --jq .tag_name --include"),
            ("api", "repos/example/project/contents/git-files -H Accept:application/json"),
        ):
            for command in repository_qualified_commands(group, arguments):
                with self.subTest(command=command):
                    self.assertEqual(inspect(workflow(command)), [])

    def test_qualified_github_cli_controls_with_dispatch_inputs(self):
        # These are workflow data, never commands executed by the test. Exercise
        # the real policy entry point with a manual-input, non-credential value.
        controls = (
            ("gh --repo example/project release create v1", "GitHub release"),
            ("gh -R example/project release create v1", "GitHub release"),
            ("gh release --repo example/project create v1", "GitHub release"),
            ("gh release new v1 dist/*", "GitHub release"),
            ("gh --repo=example/project api -X POST repos/example/project/releases", "GitHub API mutation"),
            ("gh -Rexample/project api repos/example/project/releases -f tag_name=v1", "GitHub API mutation"),
            ("gh api repos/o/r/releases --raw-field tag_name=v1", "GitHub API mutation"),
            ("gh api repos/o/r/git/refs --input ref.json", "GitHub API mutation"),
            ("gh --repo example/project release download v1 --pattern '*.whl'", None),
            ("gh release -R example/project download v1 --pattern create", None),
            ("gh --repo example/project api repos/example/project/releases/latest", None),
        )
        for command, diagnostic in controls:
            with self.subTest(command=command):
                result = run_policy(dispatch_workflow(command))
                self.assertEqual(result.returncode, 1 if diagnostic else 0, result.stdout + result.stderr)
                if diagnostic:
                    self.assertIn(diagnostic + " is forbidden", result.stderr)
                    self.assertIn("control.yml", result.stderr)
                else:
                    self.assertIn("all workflows are test-only", result.stdout)

    def test_qualified_github_commands_with_shell_quotes_and_continuations(self):
        for command in (
            '"gh" --repo "example/project" "release" "create" v1',
            "gh --repo example/project \\\n release \\\n create v1",
            "gh release --repo=example/project \\\n create v1",
        ):
            with self.subTest(command=command):
                self.assertTrue(any("GitHub release" in error for error in inspect(workflow(command))))

    def test_disabled_and_manual_jobs_are_still_checked(self):
        document = workflow("npm publish")
        document["on"] = {"workflow_dispatch": None}
        document["jobs"]["tests"]["if"] = "${{ false }}"
        self.assertTrue(inspect(document))

    def test_permissions_at_every_scope(self):
        for permission in ("contents", "id-token", "packages", "deployments", "pull-requests"):
            for scope in ("workflow", "job"):
                with self.subTest(permission=permission, scope=scope):
                    document = workflow()
                    target = document if scope == "workflow" else document["jobs"]["tests"]
                    target["permissions"] = {permission: "write"}
                    self.assertTrue(inspect(document))
        for permissions in ("write-all", "${{ inputs.permissions }}", None):
            document = workflow()
            document["permissions"] = permissions
            self.assertTrue(inspect(document))

    def test_secrets_and_explicit_tokens_are_rejected(self):
        direct = ("${{ secrets.NPM_TOKEN }}", "${{ secrets['PYPI_TOKEN'] }}", "${{ github.token }}", "${{ github['token'] }}")
        # A non-credential name proves the expression rule alone rejects them.
        for expression in direct + SMUGGLED_CREDENTIALS:
            for name in ("TOKEN", "VALUE"):
                with self.subTest(expression=expression, name=name):
                    document = workflow(f"echo {expression}")
                    document["env"] = {name: expression}
                    errors = inspect(document)
                    self.assertTrue(any(SECRET_ACCESS in error for error in errors), errors)
                    self.assertTrue(any("workflow.env." + name in error for error in errors), errors)
                    self.assertTrue(any("workflow.jobs.tests.steps[0].run" in error for error in errors), errors)
        document = workflow()
        document["jobs"]["tests"]["secrets"] = "inherit"
        self.assertTrue(inspect(document))

    def test_smuggled_credentials_are_rejected_by_the_cli(self):
        for expression in SMUGGLED_CREDENTIALS[:5]:
            with self.subTest(expression=expression):
                document = workflow()
                document["env"] = {"TOKEN": expression}
                result = run_policy(document)
                self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
                self.assertIn(SECRET_ACCESS, result.stderr)
                self.assertNotIn("all workflows are test-only", result.stdout)

    def test_ordinary_expressions_remain_allowed(self):
        for expression in (
            "${{ github.ref }}", "${{ github.repository }}", "${{ github.event.pull_request.head.sha }}",
            "${{ inputs.adapter-dockerfile }}", "${{ steps.github.outputs.version }}",
            "${{ contains(github.event.head_commit.message, 'secrets') }}",
            "${{ format('{0}-token', github.sha) }}", "${{ format('it''s {0}', github.run_id) }}",
            "${{ github.event_name == 'push' && 'github.token' || 'none' }}",
            "${{ hashFiles('**/secrets.lock') }}", "${{ matrix.github }}",
        ):
            with self.subTest(expression=expression):
                document = workflow(f"echo {expression}")
                document["env"] = {"VALUE": expression, "GIT_AUTHOR_NAME": "${{ github.actor }}"}
                self.assertEqual(inspect(document), [])

    def test_credentials_cannot_flow_from_inputs_or_other_expressions(self):
        sources = ("${{ inputs.token }}", "${{ github.event.inputs.token }}", "${{ vars.NPM_TOKEN }}", "${{ needs.setup.outputs.value }}")
        names = ("GH_TOKEN", "GITHUB_TOKEN", "NODE_AUTH_TOKEN", "NPM_CONFIG__AUTH", "TWINE_PASSWORD", "TWINE_USERNAME", "UV_PUBLISH_TOKEN", "MAVEN_PASSWORD")
        for source in sources:
            for name in names:
                for scope in ("workflow", "job", "step"):
                    with self.subTest(source=source, name=name, scope=scope):
                        document = dispatch_workflow("pnpm test")
                        target = {"workflow": document, "job": document["jobs"]["tests"], "step": document["jobs"]["tests"]["steps"][0]}[scope]
                        target["env"] = {name: source}
                        self.assertTrue(any(CREDENTIAL_FLOW in error for error in inspect(document)))
        for command in (
            "export GH_TOKEN=${{ inputs.repository }}",
            'echo "NODE_AUTH_TOKEN=${{ inputs.repository }}" >> "$GITHUB_ENV"',
            "npm config set //registry.npmjs.org/:_authToken=${{ inputs.repository }}",
        ):
            with self.subTest(command=command):
                self.assertTrue(any(CREDENTIAL_FLOW in error for error in inspect(dispatch_workflow(command))))
        document = dispatch_workflow("pnpm test")
        document["jobs"]["tests"]["steps"] = [{"uses": "actions/checkout@v4", "with": {"persist-credentials": False, "token": "${{ inputs.repository }}"}}]
        self.assertTrue(any(CREDENTIAL_FLOW in error for error in inspect(document)))
        document = dispatch_workflow("pnpm test")
        document["jobs"]["tests"]["env"] = "${{ fromJSON(inputs.repository) }}"
        self.assertTrue(any("dynamic env or with mapping is forbidden" in error for error in inspect(document)))
        for event in ("workflow_dispatch", "workflow_call"):
            for name in ("token", "npm-token", "pypi_password", "registry-auth"):
                with self.subTest(event=event, name=name):
                    document = workflow()
                    document["on"] = {event: {"inputs": {name: {"type": "string"}}}}
                    self.assertTrue(any("credential-named workflow input is forbidden" in error for error in inspect(document)))
        document = dispatch_workflow("pnpm test")
        document["jobs"]["tests"]["env"] = {"GH_TOKEN": "${{ inputs.repository }}"}
        result = run_policy(document)
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn(CREDENTIAL_FLOW, result.stderr)

    def test_unreviewed_actions_and_remote_workflows_are_rejected(self):
        for action in (
            "pypa/gh-action-pypi-publish@release/v1", "softprops/action-gh-release@v2",
            "googleapis/release-please-action@v4", "docker/build-push-action@v6",
            "org/innocent-looking-action@v1", "./.github/actions/release",
            "org/repo/.github/workflows/tests.yml@main", "${{ matrix.action }}",
        ):
            with self.subTest(action=action):
                document = workflow()
                document["jobs"]["tests"]["steps"] = [{"uses": action}]
                self.assertTrue(inspect(document))

    def test_checkout_cannot_keep_credentials_or_use_mutable_external_source(self):
        for options in ({}, {"persist-credentials": True}, {"persist-credentials": False, "repository": "org/harness", "ref": "main"}):
            document = workflow()
            document["jobs"]["tests"]["steps"] = [{"uses": "actions/checkout@v4", "with": options}]
            self.assertTrue(inspect(document))
        document["jobs"]["tests"]["steps"][0]["with"] = {"persist-credentials": False}
        self.assertEqual(inspect(document), [])

    def test_trigger_boundaries(self):
        for event in ("release", "pull_request_target", "workflow_run", "push"):
            document = workflow()
            document["on"] = {event: None}
            self.assertTrue(inspect(document))
        document["on"] = {"push": {"branches-ignore": ["main", "master", "release/**", "releases/**"], "tags-ignore": ["**"]}}
        self.assertEqual(inspect(document), [])

    def test_folded_flow_alias_and_encoded_commands(self):
        header = "on: pull_request\npermissions: {contents: read}\njobs:\n  test:\n    runs-on: ubuntu-latest\n    steps:\n"
        for steps in (
            "      - run: >\n          npm\n          publish\n",
            "      - {run: 'pnpm publish'}\n",
            '      - run: "npm \\x70ublish"\n',
            "      - run: &command npm publish\n      - run: *command\n",
        ):
            with self.subTest(steps=steps):
                self.assertTrue(check_workflow(header + steps, "test.yml", ACTIONS, set()))

    def test_matrix_and_action_input_commands_are_checked(self):
        for field in ("env", "with", "strategy"):
            document = workflow()
            document["jobs"]["tests"][field] = {"command": "npm publish"}
            self.assertTrue(inspect(document))

    def test_invalid_and_ambiguous_yaml_fails_closed(self):
        for text in ("", "[]", "[", "on: push\non: pull_request", "x: &x [*x]", "x: &x {a: b}\ny: {<<: *x}", "---\n{}\n---\n{}"):
            with self.subTest(text=text):
                self.assertTrue(check_workflow(text, "test.yml", ACTIONS, set()))

    def test_every_yaml_file_is_scanned_and_cli_fails(self):
        with tempfile.TemporaryDirectory() as temporary:
            folder = Path(temporary) / ".github/workflows"
            folder.mkdir(parents=True)
            (folder / "safe.yml").write_text(yaml.safe_dump(workflow()))
            self.assertEqual(check_repository(temporary), [])
            (folder / "new.yaml").write_text(yaml.safe_dump(workflow("npm publish")))
            self.assertTrue(check_repository(temporary))
            result = subprocess.run([sys.executable, str(Path(__file__).with_name("workflow_policy.py")), "--root", temporary], capture_output=True, text=True)
            self.assertEqual(result.returncode, 1)
            self.assertIn("new.yaml", result.stderr)

    def test_missing_directory_and_symlink_fail_closed(self):
        with tempfile.TemporaryDirectory() as temporary:
            self.assertTrue(check_repository(temporary))
            folder = Path(temporary) / ".github/workflows"
            folder.mkdir(parents=True)
            target = Path(temporary) / "target.yml"
            target.write_text(yaml.safe_dump(workflow()))
            (folder / "linked.yml").symlink_to(target)
            self.assertTrue(check_repository(temporary))

    def test_local_reusable_workflow_must_exist_and_is_scanned(self):
        document = workflow()
        document["jobs"] = {"test": {"uses": "./.github/workflows/reusable.yml"}}
        text = yaml.safe_dump(document)
        self.assertTrue(check_workflow(text, "caller.yml", ACTIONS, set()))
        self.assertEqual(check_workflow(text, "caller.yml", ACTIONS, {"./.github/workflows/reusable.yml"}), [])
        with tempfile.TemporaryDirectory() as temporary:
            folder = Path(temporary) / ".github/workflows"
            folder.mkdir(parents=True)
            (folder / "caller.yml").write_text(text)
            (folder / "reusable.yml").write_text(yaml.safe_dump(workflow("mvn deploy")))
            self.assertTrue(check_repository(temporary))


if __name__ == "__main__":
    unittest.main()
