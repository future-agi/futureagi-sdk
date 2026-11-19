"""Exact release exceptions; blocked credentials are not release authorization."""

from copy import deepcopy
import hashlib
import inspect
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest import mock

import yaml

import workflow_policy as policy

ROOT = Path(__file__).resolve().parents[2]
CONFIG = json.loads(Path(__file__).with_name("workflow-policy.json").read_text())
ACTIONS = CONFIG.get("actions", []) if isinstance(CONFIG, dict) else []
ENTRIES = CONFIG.get("released_workflow_exceptions", []) if isinstance(CONFIG, dict) else []
RECORD = "RL2251m-W1-W6"
REVIEW_RECORD = 'reviewed-release-and-promotion-workflows-2026-11-07'
PINS = {
    # Explicit pnpm run forwards the existing Jest argument; grants unchanged.
    "ci": "5af3ad0dc77532cba22325afa39e6595977b3622",
    "e2e": "cba54bac7b19da39a12e8175dee35cbc05cac28c",
    "publish": "5768525321a738d9b1ccd4f7a7c3761bc767e834",
    "promote": "4dd63903e8404d464e3039fc9e8532dd9b4db079",
    "release-please": "bd03fe5c7d6a48b91b0570acec35a327d78cb2c4",
    "pr-title-lint": "01db2c11caeef450ea14a715c65deb881788735d",
}
# Independent census: changing JSON alone cannot expand authority. Growth must
# name a new record, and update this reviewed list, not just a count or digest.
CASES = [
    ("ci-push", "ci", "trigger", "on.push", {"branches": ["dev", "main"]}),
    ("e2e-push", "e2e", "trigger", "on.push", {"branches": ["dev", "main"]}),
    ("e2e-schedule", "e2e", "trigger", "on.schedule", [{"cron": "17 3 * * *"}]),
    ("e2e-backend-ref", "e2e", "checkout_ref", "workflow.jobs.e2e.steps[2].uses", {
        "repository": "future-agi/future-agi", "ref": "${{ env.BACKEND_REF }}",
        "source": "${{ inputs.backend-ref || 'main' }}",
    }),
    ("publish-dispatch", "publish", "trigger", "on.repository_dispatch", {"types": ["sdk-release-publish"]}),
    ("promote-push", "promote", "trigger", "on.push", {"branches": ["dev"]}),
    ("release-name", "release-please", "workflow_name", "workflow.name", "release-please"),
    ("pr-title-action", "pr-title-lint", "action", "workflow.jobs.lint.steps[0].uses",
     "amannn/action-semantic-pull-request@e32d7e603df1aa1ba07e981f2a23455dee596825"),
]
EXPECTED = [{"id": id_, "record": RECORD if name in ("ci", "e2e") else REVIEW_RECORD,
             "workflow": f".github/workflows/{name}.yml",
             "blob": PINS[name], "kind": kind, "location": location, "value": value}
            for id_, name, kind, location, value in CASES]
# Independent, reviewed census: never derive expected grants from the policy file.
REVIEWED_CASES = json.loads(Path(__file__).with_name("reviewed-workflow-census.json").read_text())
EXPECTED.extend(REVIEWED_CASES)


def blob(raw):
    return hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()


def check(raw, path, entries=ENTRIES, actions=ACTIONS):
    # New tests applied alone to the base must reach assertions, not TypeError.
    kwargs = {"exceptions": entries} if "exceptions" in inspect.signature(policy.check_workflow).parameters else {}
    return policy.check_workflow(raw.decode("utf-8"), path, actions, set(), **kwargs)


def serialize(document):
    return yaml.safe_dump(document, sort_keys=False).encode("utf-8")


def repin(entries, path, raw):
    # Synthetic test copies ONLY. Production always checks the original bytes.
    result = deepcopy(entries)
    for entry in result:
        if entry["workflow"] == path:
            entry["blob"] = blob(raw)
    return result


def violation(errors, entry):
    location = entry["location"]
    if entry["kind"] == "trigger" and location != "on.push":
        return any(f"event {location[3:]!r}" in error for error in errors)
    return any(f":{location}:" in error for error in errors)


def mutate(test, document, entry, move=False):
    kind = entry["kind"]
    if kind == "trigger":
        event = entry["location"][3:]
        settings = test.value(document, "on", event)
        if move:
            document["on"]["pull_request_target"] = document["on"].pop(event)
        elif event == "schedule":
            test.value(settings, 0, "cron")
            settings[0]["cron"] = "* * * * *"
        else:
            key = "types" if event == "repository_dispatch" else "branches"
            values = test.value(settings, key)
            test.assertIsInstance(values, list)
            values.append("*")
    elif kind == "workflow_name":
        name = test.value(document, "name")
        test.assertIsInstance(name, str)
        if move:
            document["env"] = {"LABEL": document.pop("name")}
        else:
            document["name"] = name + " widened"
    else:
        job = "e2e" if kind == "checkout_ref" else "lint"
        test.value(document, "jobs", job)
        if move:
            document["jobs"][job + "-moved"] = document["jobs"].pop(job)
        elif kind == "checkout_ref":
            test.value(document, "jobs", job, "steps", 2, "with", "repository")
            document["jobs"][job]["steps"][2]["with"]["repository"] = "other/source"
        else:
            test.value(document, "jobs", job, "steps", 0, "uses")
            document["jobs"][job]["steps"][0]["uses"] = "other/action@v1"


class ReleasedWorkflowPolicyTests(unittest.TestCase):
    def setUp(self):
        self.assertIsInstance(CONFIG, dict)
        self.assertIsInstance(CONFIG.get("actions"), list)
        self.assertIsInstance(ENTRIES, list)
        for entry in ENTRIES:
            self.assertIsInstance(entry, dict)
            self.assertEqual(set(entry), {"id", "record", "workflow", "blob", "kind", "location", "value"})
            for key in set(entry) - {"value"}:
                self.assertIsInstance(entry.get(key), str)

    def value(self, document, *keys):
        # Missing/renamed fixture fields fail by assertion, never KeyError or
        # IndexError. Only literal, locally constructed controls bypass this.
        for key in keys:
            if isinstance(key, int):
                self.assertIsInstance(document, list)
                self.assertGreater(len(document), key)
            else:
                self.assertIsInstance(document, dict)
                self.assertIn(key, document)
            document = document[key]
        return document

    def row(self, id_):
        matches = [entry for entry in ENTRIES if entry.get("id") == id_]
        self.assertEqual(len(matches), 1, "missing/duplicate exact exception")
        expected = [entry for entry in EXPECTED if entry["id"] == id_]
        self.assertEqual(matches, expected, "fixture must use its exact reviewed census row")
        return matches[0]

    def fixture(self, id_):
        entry = self.row(id_)
        path = entry["workflow"]
        document = yaml.load((ROOT / path).read_bytes(), Loader=policy.WorkflowLoader)
        # C disables checkout persistence. Model that hardening in synthetic
        # controls without granting any exception for the historical default.
        if path in (".github/workflows/ci.yml", ".github/workflows/e2e.yml"):
            jobs = self.value(document, "jobs")
            self.assertIsInstance(jobs, dict)
            for job in jobs.values():
                steps = self.value(job, "steps")
                self.assertIsInstance(steps, list)
                for step in steps:
                    self.assertIsInstance(step, dict)
                    if step.get("uses") == "actions/checkout@v4":
                        options = step.setdefault("with", {})
                        self.assertIsInstance(options, dict)
                        options["persist-credentials"] = "false"
        raw = serialize(document)
        return entry, document, raw, repin(ENTRIES, path, raw)

    def current_fixture(self, name):
        # Keep the original refusal controls when the separately reviewed
        # exact-byte admission is absent; credentials are not globally allowed.
        pin = PINS.get(name)
        self.assertIsInstance(pin, str)
        path = f".github/workflows/{name}.yml"
        raw = (ROOT / path).read_bytes()
        self.assertEqual(blob(raw), pin, "current-blob refusal needs renewed review")
        document = yaml.load(raw, Loader=policy.WorkflowLoader)
        self.assertIsInstance(document, dict)
        return path, document, check(raw, path, [e for e in ENTRIES if e["kind"] != "reviewed_workflow"])

    def assert_refused(self, errors, path, location, diagnostic):
        self.assertIn(f"{path}:{location}: {diagnostic}", errors)

    def test_driver_discovers_release_exception_tests(self):
        driver = Path(__file__).with_name("check-workflows.sh").read_text()
        self.assertIn("-p 'test_workflow_policy*.py'", driver)

    def test_census_names_record_and_exact_six_workflows(self):
        self.assertEqual(ENTRIES, EXPECTED, "exception growth needs a reviewed record field")
        self.assertEqual({e["workflow"] for e in ENTRIES}, {e["workflow"] for e in EXPECTED})
        self.assertEqual(len({e["workflow"] for e in ENTRIES}), 6)

    def test_reconciled_ci_and_e2e_pass_with_final_byte_pins(self):
        # Integration dependency: C's files must land first. Historical released
        # files intentionally fail W1 rather than receiving a second valid pin.
        for name in ("ci", "e2e"):
            path = f".github/workflows/{name}.yml"
            with self.subTest(workflow=path):
                self.assertEqual(check((ROOT / path).read_bytes(), path), [])

    def test_blocked_released_workflows_stay_blocked(self):
        for name in ("publish", "promote", "release-please", "pr-title-lint"):
            path = f".github/workflows/{name}.yml"
            with self.subTest(workflow=path):
                self.assertTrue(check((ROOT / path).read_bytes(), path,
                                      [e for e in ENTRIES if e["kind"] != "reviewed_workflow"]))

    def test_item1_requires_explicit_lint_job_permissions_at_current_blob(self):
        path, document, errors = self.current_fixture("pr-title-lint")
        self.assertEqual(self.value(document, "on"), {"pull_request": {
            "types": ["opened", "edited", "synchronize", "reopened"], "branches": ["dev", "main"],
        }})
        self.assertEqual(self.value(document, "permissions"), {"pull-requests": "read"})
        job = self.value(document, "jobs", "lint")
        self.assertIsInstance(job, dict)
        self.assertNotIn("permissions", job, "workflow inheritance does not satisfy the job-level ruling")
        steps = self.value(job, "steps")
        self.assertIsInstance(steps, list)
        self.assertEqual(len(steps), 1)
        self.assertEqual(self.value(steps, 0, "uses"),
                         "amannn/action-semantic-pull-request@e32d7e603df1aa1ba07e981f2a23455dee596825")
        self.assertNotIn("run", steps[0])
        self.assertEqual(self.value(steps, 0, "env"), {"GITHUB_TOKEN": "${{ secrets.GITHUB_TOKEN }}"})
        location = "workflow.jobs.lint.steps[0].env.GITHUB_TOKEN"
        self.assert_refused(errors, path, location, "explicit token or secret access is forbidden")
        self.assert_refused(errors, path, location, "credential-named value may not come from an expression")

    def test_item2_publish_branch_action_remains_refused_at_current_blob(self):
        path, document, errors = self.current_fixture("publish")
        action = "pypa/gh-action-pypi-publish@release/v1"
        self.assertEqual(self.value(document, "jobs", "python", "steps", 4, "uses"), action)
        self.assert_refused(errors, path, "workflow.jobs.python.steps[4].uses",
                            f"unreviewed action or remote reusable workflow: {action}")

    def test_item3_publish_dispatch_oidc_remains_refused_at_current_blob(self):
        path, document, errors = self.current_fixture("publish")
        self.assertEqual(self.value(document, "on", "repository_dispatch"), {"types": ["sdk-release-publish"]})
        for name, environment in (("python", "pypi"), ("typescript", "npm")):
            with self.subTest(job=name):
                self.assertEqual(self.value(document, "jobs", name, "environment"), environment)
                self.assertEqual(self.value(document, "jobs", name, "permissions"),
                                 {"contents": "read", "id-token": "write"})
                self.assert_refused(errors, path, f"workflow.jobs.{name}.permissions",
                                    "write or dynamic permissions are forbidden")

    def assert_app_credentials_refused(self, document, errors, path, job_name, step_index):
        job = self.value(document, "jobs", job_name)
        self.assertIsInstance(job, dict)
        self.assertNotIn("environment", job)
        step = self.value(job, "steps", step_index)
        self.assertEqual(self.value(step, "uses"), "actions/create-github-app-token@v2")
        for name, expression in (("app-id", "${{ vars.RELEASE_BOT_APP_ID || secrets.RELEASE_BOT_APP_ID }}"),
                                 ("private-key", "${{ secrets.RELEASE_BOT_PRIVATE_KEY }}")):
            self.assertEqual(self.value(step, "with", name), expression)
            self.assert_refused(errors, path, f"workflow.jobs.{job_name}.steps[{step_index}].with.{name}",
                                "explicit token or secret access is forbidden")

    def test_item4_promote_credentials_remain_refused_at_current_blob(self):
        path, document, errors = self.current_fixture("promote")
        self.assertEqual(self.value(document, "on", "push"), {"branches": ["dev"]})
        self.assert_app_credentials_refused(document, errors, path, "promote", 0)
        self.assert_refused(errors, path, "workflow.jobs.promote.steps[1].env.GH_TOKEN",
                            "credential-named value may not come from an expression")

    def test_item5_release_credentials_remain_refused_at_current_blob(self):
        path, document, errors = self.current_fixture("release-please")
        self.assertEqual(self.value(document, "on", "workflow_run"), {
            "workflows": ["CI", "E2E"], "branches": ["main"], "types": ["completed"],
        })
        self.assert_app_credentials_refused(document, errors, path, "release", 4)
        self.assertEqual(self.value(document, "jobs", "release", "steps", 5, "uses"),
                         "googleapis/release-please-action@v4")
        self.assert_refused(errors, path, "workflow.jobs.release.steps[5].with.token",
                            "credential-named value may not come from an expression")

    def test_reviewed_workflows_pass_only_with_their_exact_records(self):
        for row in REVIEWED_CASES:
            path = row["workflow"]
            raw = (ROOT / path).read_bytes()
            with self.subTest(workflow=path):
                self.assertEqual(blob(raw), row["blob"])
                self.assertEqual(hashlib.sha256(raw).hexdigest(), row["value"]["source_sha256"])
                self.assertEqual(check(raw, path), [])
                without = [e for e in ENTRIES if e["id"] != row["id"]]
                self.assertTrue(check(raw, path, without))
                changed = raw + b"# changed bytes require review\n"
                self.assertTrue(check(changed, path))
                self.assertTrue(check(changed, path, repin(ENTRIES, path, changed)))
                self.assertTrue(check(raw, ".github/workflows/unlisted.yml"))
                altered = deepcopy(ENTRIES)
                next(e for e in altered if e["id"] == row["id"])["value"]["diagnostics"].append("unexpected")
                self.assertTrue(check(raw, path, altered))

    def test_git_blob_id_hashes_original_bytes(self):
        implementation = getattr(policy, "git_blob_id", None)
        self.assertTrue(callable(implementation), "raw-byte Git blob hashing is required")
        self.assertEqual(implementation(b""), "e69de29bb2d1d6434b8b29ae775ad8c2e48c5391")
        for raw in (b"a\n", b"a\r\n", b"\xef\xbb\xbfa\n"):
            self.assertEqual(implementation(raw), blob(raw))
        self.assertNotEqual(implementation(b"a\n"), implementation(b"a\r\n"))

    def test_pr_controlled_checkout_ref_is_refused_even_after_repin(self):
        entry, document, raw, entries = self.fixture("e2e-backend-ref")
        self.assertFalse(violation(check(raw, entry["workflow"], entries), entry))
        for source in ("${{ github.event.pull_request.head.sha }}", "${{ github.head_ref }}",
                       "${{ github.event.pull_request.title }}", "${{ github.ref_name }}"):
            changed = deepcopy(document)
            self.value(changed, "env", "BACKEND_REF")
            changed["env"]["BACKEND_REF"] = source
            raw = serialize(changed)
            forged = repin(entries, entry["workflow"], raw)
            for row in forged:
                if row["id"] == entry["id"]:
                    row["value"]["source"] = source
            with self.subTest(source=source):
                self.assertTrue(violation(check(raw, entry["workflow"], forged), entry))

    def test_backend_env_cannot_be_shadowed(self):
        entry, document, _, entries = self.fixture("e2e-backend-ref")
        for scope in ("job", "step"):
            changed = deepcopy(document)
            job = self.value(changed, "jobs", "e2e")
            target = job if scope == "job" else self.value(job, "steps", 2)
            self.assertIsInstance(target, dict)
            target["env"] = {"BACKEND_REF": "${{ github.head_ref }}"}
            raw = serialize(changed)
            self.assertTrue(violation(check(raw, entry["workflow"], repin(entries, entry["workflow"], raw)), entry))

    def test_new_construct_in_excepted_workflow_is_refused_after_repin(self):
        entry, document, _, entries = self.fixture("ci-push")
        jobs = self.value(document, "jobs")
        self.assertIsInstance(jobs, dict)
        jobs["extra"] = {"runs-on": "ubuntu-latest", "steps": [{"run": "npm publish"}]}
        raw = serialize(document)
        errors = check(raw, entry["workflow"], repin(entries, entry["workflow"], raw))
        self.assertTrue(any("package publication is forbidden" in error for error in errors))

    def test_branch_action_cannot_enter_global_or_exact_allowlists(self):
        path = ".github/workflows/pr-title-lint.yml"
        for action in ("owner/action@main", "pypa/gh-action-pypi-publish@release/v1"):
            document = {"on": {"workflow_dispatch": None}, "permissions": {"contents": "read"},
                        "jobs": {"lint": {"runs-on": "ubuntu-latest", "steps": [{"uses": action}]}}}
            raw = serialize(document)
            entry = dict(next(e for e in EXPECTED if e["id"] == "pr-title-action"),
                         blob=blob(raw), value=action)
            errors = check(raw, path, [entry], [*ACTIONS, action])
            self.assertTrue(any("W2_BLOCKER" in error for error in errors), errors)

    def test_no_exception_for_w2_events_permissions_or_credentials(self):
        path = ".github/workflows/publish.yml"
        document = {"on": {"workflow_dispatch": None}, "permissions": {"contents": "read"},
                    "jobs": {"test": {"runs-on": "ubuntu-latest", "steps": [{"run": "true"}]}}}
        for event in ("pull_request_target", "workflow_run"):
            changed = deepcopy(document)
            changed["on"] = {event: None}
            raw = serialize(changed)
            entry = dict(EXPECTED[4], blob=blob(raw), location=f"on.{event}", value="")
            self.assertTrue(any(f"event {event!r}" in e for e in check(raw, path, [entry])))
        for event in ("pull_request", "push", "repository_dispatch", "workflow_dispatch"):
            changed = deepcopy(document)
            changed["on"] = {event: None}
            job = changed["jobs"]["test"]
            job["environment"] = "pypi"
            job["permissions"] = {"id-token": "write"}
            job["env"] = {"TOKEN": "${{ secrets.PUBLISH_TOKEN }}"}
            raw = serialize(changed)
            errors = check(raw, path, [])
            self.assertTrue(any("write or dynamic permissions" in e for e in errors))
            self.assertTrue(any("explicit token or secret access" in e for e in errors))
        document["permissions"] = "write-all"
        self.assertTrue(check(serialize(document), path, []))

    def test_repository_preserves_crlf_bytes_when_enforcing_pins(self):
        path = ".github/workflows/promote.yml"
        raw = (ROOT / path).read_bytes().replace(b"\n", b"\r\n")
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary) / path
            target.parent.mkdir(parents=True)
            target.write_bytes(raw)
            errors = policy.check_repository(temporary)
        self.assertTrue(any("blob mismatch" in error for error in errors), errors)

    def path_fixture(self, temporary):
        # Independent synthetic bytes/pin; no C integration or repository writes.
        # Keep the checker/config tree separate to pin configuration provenance.
        base = Path(temporary).resolve()
        root, checker = base / "candidate", base / "checker/.github/ci/workflow_policy.py"
        target = root / ".github/workflows/ci.yml"
        target.parent.mkdir(parents=True)
        checker.parent.mkdir(parents=True)
        raw = (b"name: Path control\non: {push: {branches: [dev, main]}}\n"
               b"permissions: {contents: read}\njobs:\n"
               b"  test: {runs-on: ubuntu-latest, steps: [{run: 'true'}]}\n")
        target.write_bytes(raw)
        matches = [entry for entry in EXPECTED if entry["id"] == "ci-push"]
        self.assertEqual(len(matches), 1)
        config = {"actions": [], "released_workflow_exceptions": [dict(matches[0], blob=blob(raw))]}
        checker.with_name("workflow-policy.json").write_text(json.dumps(config))
        return root, checker

    def assert_symlink_refused(self, component, policy_input=False):
        # Cover both an in-tree relocation and an external target; root aliases
        # necessarily target a sibling. All symlinks exist only in this temp dir.
        for in_tree in ((False, True) if component else (False,)):
            with self.subTest(component=component, policy_input=policy_input, in_tree=in_tree):
                with tempfile.TemporaryDirectory() as temporary:
                    root, checker = self.path_fixture(temporary)
                    with mock.patch.object(policy, "__file__", str(checker)):
                        self.assertEqual(policy.check_repository(root), [])
                    boundary = checker.parents[2] if policy_input else root
                    selected = boundary / component
                    target = (boundary if in_tree else Path(temporary).resolve()) / "relocated"
                    selected.rename(target)
                    os.symlink(target, selected, target_is_directory=target.is_dir())
                    with mock.patch.object(policy, "__file__", str(checker)), \
                            mock.patch.object(policy, "check_workflow", wraps=policy.check_workflow) as inspect_workflow, \
                            mock.patch.object(Path, "read_bytes", side_effect=AssertionError("aliased workflow read")):
                        if policy_input:
                            with mock.patch.object(Path, "read_text", side_effect=AssertionError("aliased policy read")):
                                errors = policy.check_repository(root)
                        else:
                            errors = policy.check_repository(root)
                    self.assertTrue(any("symlink path component is forbidden" in error for error in errors), errors)
                    inspect_workflow.assert_not_called()

    def test_symlinked_workflows_directory_refused(self):
        self.assert_symlink_refused(".github/workflows")

    def test_symlinked_github_ancestor_refused(self):
        self.assert_symlink_refused(".github")

    def test_symlinked_workflow_file_refused(self):
        self.assert_symlink_refused(".github/workflows/ci.yml")

    def test_symlinked_repository_root_refused(self):
        self.assert_symlink_refused("")

    def test_symlinked_policy_file_refused(self):
        self.assert_symlink_refused(".github/ci/workflow-policy.json", policy_input=True)

    def test_symlinked_policy_ci_directory_refused(self):
        self.assert_symlink_refused(".github/ci", policy_input=True)

    def test_symlinked_policy_github_ancestor_refused(self):
        self.assert_symlink_refused(".github", policy_input=True)

    def test_symlinked_policy_repository_root_refused(self):
        self.assert_symlink_refused("", policy_input=True)

    def test_parent_relative_repository_root_is_accepted(self):
        # `--root ..` from .github must work; only lexical '..' in the root
        # selection is normalized, never symlinks below the root.
        with tempfile.TemporaryDirectory() as temporary:
            root, checker = self.path_fixture(temporary)
            parent_relative = str(root / ".github" / "..")
            with mock.patch.object(policy, "__file__", str(checker)):
                self.assertEqual(policy.check_repository(parent_relative), [])
                selected = root / ".github" / "workflows"
                target = Path(temporary).resolve() / "relocated"
                selected.rename(target)
                os.symlink(target, selected, target_is_directory=True)
                errors = policy.check_repository(parent_relative)
            self.assertTrue(any("symlink path component is forbidden" in error for error in errors), errors)

    def test_normal_tree_applies_only_byte_bound_exception(self):
        with tempfile.TemporaryDirectory() as temporary:
            root, checker = self.path_fixture(temporary)
            with mock.patch.object(policy, "__file__", str(checker)):
                self.assertEqual(policy.check_repository(root), [])
                config_path = checker.with_name("workflow-policy.json")
                config_path.write_text(json.dumps({"actions": [], "released_workflow_exceptions": []}))
                errors = policy.check_repository(root)
                self.assertTrue(any(":on.push:" in error for error in errors), errors)
        # Pair acceptance with alias refusal so removing the guard fails this
        # control by assertion, not merely the separate negative controls.
        self.assert_symlink_refused(".github/workflows")

    def assert_resolved_alias_refused(self, policy_input=False):
        with tempfile.TemporaryDirectory() as temporary:
            root, checker = self.path_fixture(temporary)
            selected = checker.with_name("workflow-policy.json") if policy_input else root / ".github/workflows/ci.yml"
            resolve = Path.resolve

            def aliased(path, *args, **kwargs):
                resolved = resolve(path, *args, **kwargs)
                return resolved.with_name("relocated") if path == selected else resolved

            with mock.patch.object(policy, "__file__", str(checker)), \
                    mock.patch.object(policy, "check_workflow", wraps=policy.check_workflow) as inspect_workflow, \
                    mock.patch.object(Path, "resolve", autospec=True, side_effect=aliased), \
                    mock.patch.object(Path, "read_bytes", side_effect=AssertionError("aliased workflow read")):
                if policy_input:
                    with mock.patch.object(Path, "read_text", side_effect=AssertionError("aliased policy read")):
                        errors = policy.check_repository(root)
                else:
                    errors = policy.check_repository(root)
            self.assertTrue(any("resolved path differs from lexical repository path" in error for error in errors), errors)
            inspect_workflow.assert_not_called()

    def test_resolved_workflow_alias_refused(self):
        self.assert_resolved_alias_refused()

    def test_resolved_policy_alias_refused(self):
        self.assert_resolved_alias_refused(policy_input=True)

    def test_invalid_duplicate_and_glob_entries_fail_closed(self):
        entry, _, raw, entries = self.fixture("ci-push")
        matches = [e for e in entries if e["id"] == entry["id"]]
        self.assertEqual(len(matches), 1)
        row = matches[0]
        for broken in ([row, row], [dict(row, workflow=".github/workflows/*.yml")],
                       [dict(row, kind="credential")], [dict(row, blob="*")],
                       [dict(row, record="")], {"allow": "any"}):
            errors = check(raw, entry["workflow"], broken)
            self.assertTrue(any(":exceptions:" in e for e in errors), errors)


def exception_test(id_, operation):
    def test(self):
        entry, document, raw, entries = self.fixture(id_)
        path = entry["workflow"]
        baseline = check(raw, path, entries)
        self.assertFalse(violation(baseline, entry), baseline)
        if operation == "necessary":
            without = [row for row in entries if row["id"] != id_]
            self.assertTrue(violation(check(raw, path, without), entry))
        elif operation == "byte_bound":
            for changed in (raw + b"# comment\n", raw.replace(b"\n", b"\r\n")):
                errors = check(changed, path, entries)
                self.assertTrue(any("blob mismatch" in e and id_ in e for e in errors))
        elif operation == "unlisted_workflow":
            self.assertTrue(violation(check(raw, ".github/workflows/unlisted.yml", entries), entry))
        else:
            for move in (False, True):
                changed = deepcopy(document)
                mutate(self, changed, entry, move=move)
                raw = serialize(changed)
                # A blob-only re-pin cannot turn a changed construct into a grant.
                errors = check(raw, path, repin(entries, path, raw))
                self.assertTrue(any(f"unused exact exception {id_}" in e for e in errors), errors)
    return test


for case in CASES:
    for operation in ("necessary", "byte_bound", "unlisted_workflow", "widened_or_moved"):
        name = f"test_exception_{case[0].replace('-', '_')}_{operation}"
        setattr(ReleasedWorkflowPolicyTests, name, exception_test(case[0], operation))


if __name__ == "__main__":
    unittest.main()
