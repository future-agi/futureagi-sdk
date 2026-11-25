"""Offline contracts for resolve_product_ref.py; Git's ref validator is local, never networked."""

import io
import subprocess
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

import resolve_product_ref as resolver

SHA = "a" * 40
OTHER_SHA = "b" * 40
THIRD_SHA = "c" * 40


class FakeGit(resolver.GitProbe):
    """The probe's real logic over a scripted repository. Arguments are matched by content."""

    def __init__(self, refs=None, *, missing=(), modes=None, fetchable=None):
        self.refs = refs or {}
        self.missing = set(missing)
        self.modes = modes or {}
        self.fetchable = fetchable
        self.calls = []
        self.fetched_sha = None
        super().__init__(Path("."))

    def _git(self, *args, allow_missing=False):
        self.calls.append(args)
        code, output = 0, ""
        if args[0] == "ls-remote":
            names = [arg for arg in args if arg.startswith("refs/")]
            matches = [name for name in names if name in self.refs]
            code = 0 if matches else 2
            output = "".join(f"{self.refs[name]}\t{name}\n" for name in matches)
        elif args[0] == "fetch":
            ref = args[-1]
            self.fetched_sha = self.refs.get(ref) or (ref if self.fetchable is None or ref in self.fetchable else None)
            if self.fetched_sha is None:
                code = 128
        elif args[0] == "rev-parse":
            output = self.fetched_sha + "\n"
        elif args[0] == "ls-tree":
            paths = args[args.index("--") + 1:]
            output = "".join(
                f"{self.modes.get(path, '100644 blob')} {'0' * 40}\t{path}\0"
                for path in paths if path not in self.missing
            )
        elif args[0] not in ("init", "remote"):
            raise AssertionError(args)
        if code and not allow_missing:
            raise resolver.ResolutionError("product repository operation failed")
        return subprocess.CompletedProcess(args, code, output, "not-for-output")

    def fetches(self):
        return [call[-1] for call in self.calls if call[0] == "fetch"]


def scripted(results):
    seen = []

    def lookup(ref, explicit):
        seen.append(ref)
        value = results.get(ref)
        if isinstance(value, Exception):
            raise value
        return value

    return lookup, seen


class ModeTests(unittest.TestCase):
    def mode(self, **env):
        return resolver.select_mode(env)

    def test_release_runs_stay_pinned(self):
        cases = [
            {"GITHUB_EVENT_NAME": "push", "GITHUB_REF": "refs/heads/main", "GITHUB_REF_NAME": "main"},
            {"GITHUB_EVENT_NAME": "pull_request", "GITHUB_BASE_REF": "main", "GITHUB_HEAD_REF": "dev"},
            {"GITHUB_EVENT_NAME": "pull_request", "GITHUB_BASE_REF": "main",
             "GITHUB_HEAD_REF": "release-please--branches--main"},
            {"GITHUB_EVENT_NAME": "workflow_dispatch", "BACKEND_VERSION_INPUT": "v1.59.0", "GITHUB_REF_NAME": "dev"},
            # A dispatched stack ref alone keeps today's meaning: the pinned release's stack.
            {"GITHUB_EVENT_NAME": "workflow_dispatch", "BACKEND_REF_INPUT": "v1.59.0", "GITHUB_REF_NAME": "dev"},
            {"GITHUB_EVENT_NAME": "merge_group", "QUEUE_BASE_REF": "refs/heads/main"},
        ]
        for env in cases:
            with self.subTest(env=env):
                self.assertEqual(resolver.select_mode(env), ("pinned", "", "", ""))

    def test_nightly_uses_latest(self):
        self.assertEqual(self.mode(GITHUB_EVENT_NAME="schedule", GITHUB_REF="refs/heads/main"), ("latest", "", "", ""))

    def test_dev_and_feature_work_is_paired(self):
        self.assertEqual(
            self.mode(GITHUB_EVENT_NAME="pull_request", GITHUB_BASE_REF="dev", GITHUB_HEAD_REF="feat/x"),
            ("paired", "", "feat/x", "dev"))
        self.assertEqual(
            self.mode(GITHUB_EVENT_NAME="pull_request", GITHUB_BASE_REF="feat/base", GITHUB_HEAD_REF="feat/x"),
            ("paired", "", "feat/x", "feat/base"))
        self.assertEqual(
            self.mode(GITHUB_EVENT_NAME="push", GITHUB_REF="refs/heads/dev", GITHUB_REF_NAME="dev"),
            ("paired", "", "", "dev"))
        self.assertEqual(
            self.mode(GITHUB_EVENT_NAME="workflow_dispatch", GITHUB_REF_NAME="feat/x"),
            ("paired", "", "", "feat/x"))
        self.assertEqual(
            self.mode(GITHUB_EVENT_NAME="workflow_dispatch", GITHUB_REF_NAME="dev", PRODUCT_REF_INPUT=SHA),
            ("paired", SHA, "", "dev"))
        self.assertEqual(
            self.mode(GITHUB_EVENT_NAME="merge_group", QUEUE_BASE_REF="refs/heads/dev",
                      GITHUB_HEAD_REF="gh-readonly-queue/dev/pr-1"),
            ("paired", "", "", "dev"))

    def test_conflicting_or_misplaced_inputs_fail(self):
        for env in [
            {"GITHUB_EVENT_NAME": "workflow_dispatch", "PRODUCT_REF_INPUT": "dev", "BACKEND_VERSION_INPUT": "v1.59.0"},
            {"GITHUB_EVENT_NAME": "workflow_dispatch", "PRODUCT_REF_INPUT": "dev", "BACKEND_REF_INPUT": "main"},
            {"GITHUB_EVENT_NAME": "push", "GITHUB_REF": "refs/heads/dev", "PRODUCT_REF_INPUT": "dev"},
        ]:
            with self.subTest(env=env), self.assertRaises(resolver.ResolutionError):
                resolver.select_mode(env)

    def test_unknown_or_malformed_events_fail(self):
        for env in [
            {},
            {"GITHUB_EVENT_NAME": "release"},
            {"GITHUB_EVENT_NAME": "push", "GITHUB_REF": "refs/tags/v1.0.0"},
            {"GITHUB_EVENT_NAME": "pull_request", "GITHUB_HEAD_REF": "feat/x"},
        ]:
            with self.subTest(env=env), self.assertRaises(resolver.ResolutionError):
                resolver.select_mode(env)

    def test_malformed_queue_base_fails(self):
        for ref in ("", "main", "refs/tags/main", "refs/heads/", "refs/heads/bad..name"):
            with self.subTest(ref=ref), self.assertRaises(resolver.InvalidRefError):
                resolver.select_mode({"GITHUB_EVENT_NAME": "merge_group", "QUEUE_BASE_REF": ref})

    def test_pinned_and_latest_never_probe(self):
        def factory(_directory):
            raise AssertionError("pinned and latest runs must not query the product")

        for env in [{"GITHUB_EVENT_NAME": "push", "GITHUB_REF": "refs/heads/main"},
                    {"GITHUB_EVENT_NAME": "schedule"}]:
            with self.subTest(env=env):
                self.assertEqual(resolver.resolve(env, factory)[1:], ("", ""))


class ChooseTests(unittest.TestCase):
    def test_same_named_head_branch_wins(self):
        probe, seen = scripted({"feat/x": (SHA, []), "dev": (OTHER_SHA, [])})
        self.assertEqual(resolver.choose_ref("", "feat/x", "dev", probe), (SHA, "feat/x"))
        self.assertEqual(seen, ["feat/x"])

    def test_candidates_run_head_base_dev_main(self):
        probe, seen = scripted({
            "feat/x": (SHA, ["bin/e2e"]),
            "feat/base": None,
            "dev": (OTHER_SHA, ["futureagi/mcp_server/catalog/tools.yaml"]),
            "main": (THIRD_SHA, []),
        })
        self.assertEqual(resolver.choose_ref("", "feat/x", "feat/base", probe), (THIRD_SHA, "main"))
        self.assertEqual(seen, ["feat/x", "feat/base", "dev", "main"])

    def test_duplicate_candidates_are_probed_once(self):
        probe, seen = scripted({"dev": (SHA, [])})
        self.assertEqual(resolver.choose_ref("", "", "dev", probe), (SHA, "dev"))
        self.assertEqual(seen, ["dev"])

    def test_no_complete_candidate_is_failure(self):
        probe, _ = scripted({"dev": (SHA, ["bin/e2e"]), "main": (OTHER_SHA, ["bin/e2e"])})
        with self.assertRaisesRegex(resolver.ResolutionError, "no product branch"):
            resolver.choose_ref("", "feat/x", "dev", probe)

    def test_explicit_incomplete_ref_does_not_fall_back(self):
        probe, seen = scripted({"chosen": (SHA, ["bin/e2e"]), "dev": (OTHER_SHA, [])})
        with self.assertRaisesRegex(resolver.ResolutionError, "lacks required"):
            resolver.choose_ref("chosen", "head", "dev", probe)
        self.assertEqual(seen, ["chosen"])

    def test_explicit_missing_ref_fails(self):
        probe, seen = scripted({"dev": (OTHER_SHA, [])})
        with self.assertRaisesRegex(resolver.ResolutionError, "does not exist"):
            resolver.choose_ref("chosen", "head", "dev", probe)
        self.assertEqual(seen, ["chosen"])

    def test_transport_failure_does_not_fall_back(self):
        probe, seen = scripted({"feat/x": resolver.ResolutionError("network unavailable"), "dev": (SHA, [])})
        with self.assertRaisesRegex(resolver.ResolutionError, "network unavailable"):
            resolver.choose_ref("", "feat/x", "dev", probe)
        self.assertEqual(seen, ["feat/x"])

    def test_returned_revision_must_be_immutable(self):
        for sha in ["main", "a" * 7, "a" * 39, "A" * 40, "a" * 40 + "\nsha=main"]:
            with self.subTest(sha=sha):
                probe, _ = scripted({"dev": (sha, [])})
                with self.assertRaisesRegex(resolver.ResolutionError, "full commit"):
                    resolver.choose_ref("", "", "dev", probe)

    def test_explicit_sha_must_resolve_to_itself(self):
        probe, _ = scripted({SHA: (OTHER_SHA, [])})
        with self.assertRaisesRegex(resolver.ResolutionError, "identity mismatch"):
            resolver.choose_ref(SHA, "", "dev", probe)

    def test_invalid_explicit_refs_never_reach_transport(self):
        for value in ["--upload-pack=bad", "dev\nsha=" + SHA, "x..y", "x//y", "x/", "bad name", "refs/pull/1/head"]:
            with self.subTest(value=value):
                probe, seen = scripted({})
                with self.assertRaises(resolver.ResolutionError):
                    resolver.choose_ref(value, "head", "dev", probe)
                self.assertEqual(seen, [])

    def test_unsupported_automatic_ref_does_not_block_defaults(self):
        for head in ["not a branch", "refs/tags/v1", "x..y"]:
            with self.subTest(head=head):
                probe, seen = scripted({"dev": (SHA, [])})
                self.assertEqual(resolver.choose_ref("", head, "dev", probe), (SHA, "dev"))
                self.assertEqual(seen, ["dev"])

    def test_local_validator_failure_is_not_a_candidate_miss(self):
        probe, seen = scripted({"dev": (SHA, [])})
        with patch.object(resolver, "validate_ref", side_effect=resolver.ResolutionError("validation timed out")):
            with self.assertRaisesRegex(resolver.ResolutionError, "timed out"):
                resolver.choose_ref("", "head", "dev", probe)
        self.assertEqual(seen, [])


class ProbeTests(unittest.TestCase):
    def test_automatic_candidates_are_branches_only(self):
        probe = FakeGit({"refs/tags/feat-x": OTHER_SHA, "refs/heads/dev": SHA})
        self.assertEqual(resolver.choose_ref("", "feat-x", "dev", probe), (SHA, "dev"))
        lookups = [[a for a in call if a.startswith("refs/")] for call in probe.calls if call[0] == "ls-remote"]
        self.assertEqual(lookups, [["refs/heads/feat-x"], ["refs/heads/dev"]])
        self.assertEqual(probe.fetches(), ["refs/heads/dev"])

    def test_explicit_names_may_be_branches_or_tags(self):
        probe = FakeGit({"refs/tags/v1.60.0": SHA})
        self.assertEqual(resolver.choose_ref("v1.60.0", "", "dev", probe), (SHA, "v1.60.0"))
        self.assertEqual(probe.fetches(), ["refs/tags/v1.60.0"])

    def test_fetch_is_shallow_and_tree_only(self):
        probe = FakeGit({"refs/heads/dev": SHA})
        resolver.choose_ref("", "", "dev", probe)
        fetch = next(call for call in probe.calls if call[0] == "fetch")
        self.assertIn("--depth=1", fetch)
        self.assertIn("--filter=blob:none", fetch)
        self.assertIn("--no-tags", fetch)

    def test_missing_hex_automatic_branch_falls_back_without_fetch(self):
        for ref in ["abcdef0", "a" * 40]:
            with self.subTest(ref=ref):
                probe = FakeGit({"refs/heads/dev": OTHER_SHA})
                self.assertEqual(resolver.choose_ref("", ref, "dev", probe), (OTHER_SHA, "dev"))
                self.assertEqual(probe.fetches(), ["refs/heads/dev"])

    def test_explicit_short_or_uppercase_sha_fails_without_fetch(self):
        for value in ["855f2ad", "A" * 40]:
            with self.subTest(value=value):
                probe = FakeGit()
                with self.assertRaisesRegex(resolver.ResolutionError, "full 40-character"):
                    resolver.choose_ref(value, "head", "dev", probe)
                self.assertEqual(probe.fetches(), [])

    def test_explicit_full_sha_fetches_only_that_object(self):
        probe = FakeGit()
        self.assertEqual(resolver.choose_ref(SHA, "head", "dev", probe), (SHA, SHA))
        self.assertFalse(any(call[0] == "ls-remote" for call in probe.calls))
        self.assertEqual(probe.fetches(), [SHA])

    def test_unfetchable_explicit_sha_fails_closed(self):
        probe = FakeGit(fetchable=set())
        with self.assertRaisesRegex(resolver.ResolutionError, "operation failed"):
            resolver.choose_ref(SHA, "head", "dev", probe)

    def test_every_required_path_is_mandatory(self):
        for path in resolver.REQUIRED_PATHS:
            with self.subTest(path=path):
                probe = FakeGit({"refs/heads/selected": SHA}, missing=[path])
                with self.assertRaisesRegex(resolver.ResolutionError, "lacks required"):
                    resolver.choose_ref("selected", "head", "dev", probe)

    def test_symlinks_and_trees_do_not_count(self):
        path = "e2e/stack/backend/bootstrap_sql.py"
        for mode in ["120000 blob", "040000 tree", "160000 commit"]:
            with self.subTest(mode=mode):
                probe = FakeGit({"refs/heads/selected": SHA}, modes={path: mode})
                with self.assertRaisesRegex(resolver.ResolutionError, "lacks required"):
                    resolver.choose_ref("selected", "head", "dev", probe)
        probe = FakeGit({"refs/heads/selected": SHA}, modes={"bin/e2e": "100755 blob"})
        self.assertEqual(resolver.choose_ref("selected", "head", "dev", probe), (SHA, "selected"))

    def test_incomplete_head_falls_back_through_the_real_probe(self):
        probe = FakeGit({"refs/heads/feat/x": SHA, "refs/heads/dev": OTHER_SHA})
        original = probe._git

        def partial(*args, **kwargs):
            if args[0] == "ls-tree" and probe.fetched_sha == SHA:
                probe.missing = {"futureagi/mcp_server/catalog/tools.yaml"}
            elif args[0] == "ls-tree":
                probe.missing = set()
            return original(*args, **kwargs)

        probe._git = partial
        with redirect_stdout(io.StringIO()):
            self.assertEqual(resolver.choose_ref("", "feat/x", "dev", probe), (OTHER_SHA, "dev"))
        self.assertEqual(probe.fetches(), ["refs/heads/feat/x", "refs/heads/dev"])

    def test_transport_diagnostics_are_not_exposed(self):
        probe = resolver.GitProbe.__new__(resolver.GitProbe)
        probe.directory = Path(".")
        secret = "SYNTHETIC_DO_NOT_PRINT"
        with patch.object(resolver.subprocess, "run", return_value=subprocess.CompletedProcess([], 128, secret, secret)):
            with self.assertRaises(resolver.ResolutionError) as error:
                probe("dev", False)
        self.assertNotIn(secret, str(error.exception))


class MainTests(unittest.TestCase):
    def run_main(self, env, factory=None):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "out"
            output.write_text("")
            # Only what git needs from the real environment; the runner's own GITHUB_* must not leak in.
            full = {"PATH": resolver.os.environ.get("PATH", ""), "GITHUB_OUTPUT": str(output), **env}
            with patch.dict(resolver.os.environ, full, clear=True), redirect_stdout(io.StringIO()) as log:
                if factory is not None:
                    with patch.object(resolver, "GitProbe", factory):
                        code = resolver.main()
                else:
                    code = resolver.main()
            return code, output.read_text(), log.getvalue()

    def test_paired_outputs(self):
        code, output, _ = self.run_main(
            {"GITHUB_EVENT_NAME": "pull_request", "GITHUB_BASE_REF": "dev", "GITHUB_HEAD_REF": "feat/x"},
            lambda _directory: FakeGit({"refs/heads/dev": SHA}),
        )
        self.assertEqual(code, 0)
        self.assertEqual(output, f"mode=paired\nsha={SHA}\nbranch=dev\n")

    def test_pinned_outputs(self):
        code, output, _ = self.run_main({"GITHUB_EVENT_NAME": "push", "GITHUB_REF": "refs/heads/main"})
        self.assertEqual((code, output), (0, "mode=pinned\nsha=\nbranch=\n"))

    def test_failure_writes_no_outputs(self):
        code, output, log = self.run_main({"GITHUB_EVENT_NAME": "release"})
        self.assertEqual((code, output), (1, ""))
        self.assertIn("::error::", log)


if __name__ == "__main__":
    unittest.main()
