"""Offline contracts for exact, independently cleared release artifacts."""

import contextlib
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock
from urllib.error import HTTPError, URLError


ROOT = Path(__file__).resolve().parents[3]
CHECKER = ROOT / ".github/scripts/verify_cleared_artifacts.py"
MANIFEST = ROOT / ".github/cleared-release-artifacts.json"
WORKFLOW = ROOT / ".github/workflows/publish.yml"
PAYLOADS = {
    "python-v0.8.0": {
        "futureagi-0.8.0-py3-none-any.whl": b"reviewed wheel",
        "futureagi-0.8.0.tar.gz": b"reviewed sdist",
    },
    "typescript-v0.3.0": {"future-agi-sdk-0.3.0.tgz": b"reviewed npm tarball"},
}


class CheckerTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.script = self.root / ".github/scripts/verify_cleared_artifacts.py"
        self.script.parent.mkdir(parents=True)
        self.manifest = self.root / ".github/cleared-release-artifacts.json"
        self.directory = self.root / "dist"
        self.directory.mkdir()
        self.document = {
            "schema_version": 1,
            "releases": {
                tag: {name: hashlib.sha256(data).hexdigest() for name, data in files.items()}
                for tag, files in PAYLOADS.items()
            },
        }
        self.write_manifest()

    def write_manifest(self):
        self.manifest.write_text(json.dumps(self.document), encoding="utf-8")

    def populate(self, tag="python-v0.8.0"):
        for name, data in PAYLOADS[tag].items():
            (self.directory / name).write_bytes(data)

    def run_checker(self, tag="python-v0.8.0", extra=()):
        # Tests must collect before the implementation exists. Its absence is
        # an ordinary assertion failure, never an import/collection error.
        self.assertTrue(CHECKER.is_file(), "missing cleared-artifact checker")
        shutil.copyfile(CHECKER, self.script)
        return subprocess.run(
            [sys.executable, "-I", str(self.script), "--tag", tag,
             "--directory", str(self.directory), *extra],
            cwd=self.root, capture_output=True, text=True, timeout=10,
        )

    def assert_rejected(self, result):
        self.assertNotEqual(result.returncode, 0, result.stdout)
        self.assertNotIn("Verified", result.stdout)

    def test_exact_python_pair(self):
        self.populate()
        result = self.run_checker()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Verified", result.stdout)

    def test_exact_npm_tarball(self):
        self.populate("typescript-v0.3.0")
        result = self.run_checker("typescript-v0.3.0")
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_different_bytes_require_new_clearance(self):
        self.populate()
        (self.directory / "futureagi-0.8.0.tar.gz").write_bytes(b"rebuilt sdist")
        result = self.run_checker()
        self.assert_rejected(result)
        self.assertIn("independent security clearance", result.stderr)
        self.assertIn("do not update the manifest automatically", result.stderr)

    def test_each_python_artifact_is_required(self):
        for name in PAYLOADS["python-v0.8.0"]:
            with self.subTest(name=name):
                self.populate()
                (self.directory / name).unlink()
                self.assert_rejected(self.run_checker())

    def test_absent_npm_tarball(self):
        self.assert_rejected(self.run_checker("typescript-v0.3.0"))

    def test_extra_file_is_rejected(self):
        self.populate()
        (self.directory / "pack.json").write_text("{}", encoding="utf-8")
        self.assert_rejected(self.run_checker())

    def test_wrong_or_unreviewed_tag(self):
        self.populate()
        for tag in ("python-v0.8.1", "typescript-v0.3.0", "python-v../0.8.0", "v0.8.0"):
            with self.subTest(tag=tag):
                self.assert_rejected(self.run_checker(tag))

    def test_missing_manifest(self):
        self.populate()
        self.manifest.unlink()
        self.assert_rejected(self.run_checker())

    def test_malformed_or_incomplete_manifest(self):
        self.populate()
        original = json.dumps(self.document)
        malformed = ["{", "[]", "null", "{}"]
        for field, value in (("schema_version", True), ("schema_version", 2),
                             ("releases", {}), ("releases", [])):
            changed = json.loads(original)
            changed[field] = value
            malformed.append(json.dumps(changed))
        changed = json.loads(original)
        changed["unreviewed_metadata"] = True
        malformed.append(json.dumps(changed))
        for digest in (None, "", "a" * 63, "G" * 64, "A" * 64, 123):
            changed = json.loads(original)
            changed["releases"]["python-v0.8.0"]["futureagi-0.8.0.tar.gz"] = digest
            malformed.append(json.dumps(changed))
        changed = json.loads(original)
        del changed["releases"]["python-v0.8.0"]["futureagi-0.8.0.tar.gz"]
        malformed.append(json.dumps(changed))
        changed = json.loads(original)
        changed["releases"]["typescript-v0.3.0"] = {"other.tgz": "a" * 64}
        malformed.append(json.dumps(changed))
        for document in malformed:
            with self.subTest(document=document):
                self.manifest.write_text(document, encoding="utf-8")
                self.assert_rejected(self.run_checker())

    def test_duplicate_manifest_keys_at_every_level(self):
        self.populate()
        releases = json.dumps(self.document["releases"])
        python_files = json.dumps(self.document["releases"]["python-v0.8.0"])
        documents = [
            '{"schema_version":1,"schema_version":1,"releases":' + releases + '}',
            '{"schema_version":1,"releases":' + releases + ',"releases":' + releases + '}',
            '{"schema_version":1,"releases":{"python-v0.8.0":' + python_files
            + ',"python-v0.8.0":' + python_files + '}}',
            json.dumps(self.document).replace(
                '"futureagi-0.8.0.tar.gz":',
                '"futureagi-0.8.0.tar.gz":"' + 'a' * 64 + '","futureagi-0.8.0.tar.gz":',
            ),
        ]
        for document in documents:
            with self.subTest(document=document):
                self.manifest.write_text(document, encoding="utf-8")
                self.assert_rejected(self.run_checker())

    def test_manifest_filenames_cannot_escape_directory(self):
        self.populate()
        for name in ("../futureagi-0.8.0.tar.gz", "/tmp/outside.tar.gz",
                     "sub/futureagi-0.8.0.tar.gz", "..\\futureagi-0.8.0.tar.gz"):
            with self.subTest(name=name):
                files = self.document["releases"]["python-v0.8.0"]
                digest = files.pop("futureagi-0.8.0.tar.gz")
                files[name] = digest
                self.write_manifest()
                self.assert_rejected(self.run_checker())
                files["futureagi-0.8.0.tar.gz"] = files.pop(name)

    def test_artifact_symlink_is_rejected_even_with_matching_bytes(self):
        self.populate()
        artifact = self.directory / "futureagi-0.8.0.tar.gz"
        target = self.root / "matching-sdist"
        artifact.rename(target)
        artifact.symlink_to(target)
        self.assert_rejected(self.run_checker())

    def test_nonregular_artifacts_are_rejected(self):
        self.populate()
        artifact = self.directory / "futureagi-0.8.0.tar.gz"
        artifact.unlink()
        artifact.mkdir()
        self.assert_rejected(self.run_checker())
        artifact.rmdir()
        os.mkfifo(artifact)
        self.assert_rejected(self.run_checker())

    def test_symlink_distribution_directory_is_rejected(self):
        self.populate()
        original = self.root / "original-dist"
        self.directory.rename(original)
        self.directory.symlink_to(original, target_is_directory=True)
        self.assert_rejected(self.run_checker())

    def test_no_external_manifest_override(self):
        self.populate()
        result = self.run_checker(extra=("--manifest", str(self.manifest)))
        self.assert_rejected(result)
        self.assertIn("unrecognized arguments", result.stderr)


class RegistryPreflightTests(unittest.TestCase):
    def setUp(self):
        self.assertTrue(CHECKER.is_file(), "missing cleared-artifact checker")
        spec = importlib.util.spec_from_file_location("cleared_artifacts", CHECKER)
        self.checker = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.checker)

    def test_only_registry_404_allows_a_new_version(self):
        for tag, url in (
            ("python-v0.8.0", "https://pypi.org/pypi/futureagi/0.8.0/json"),
            ("typescript-v0.3.0", "https://registry.npmjs.org/%40future-agi%2Fsdk/0.3.0"),
        ):
            with self.subTest(tag=tag):
                error = HTTPError(url, 404, "Not Found", {}, None)
                with mock.patch.object(self.checker, "urlopen", side_effect=error) as request:
                    self.checker.require_unpublished(tag)
                request.assert_called_once_with(url, timeout=30)

    def test_existing_version_requires_readback(self):
        with mock.patch.object(self.checker, "urlopen"):
            for tag in PAYLOADS:
                with self.subTest(tag=tag), self.assertRaisesRegex(ValueError, "readback"):
                    self.checker.require_unpublished(tag)

    def test_registry_errors_are_not_absence(self):
        for error in (HTTPError("https://example.invalid", 403, "Forbidden", {}, None),
                      HTTPError("https://example.invalid", 500, "Unavailable", {}, None),
                      URLError("offline"), TimeoutError("timed out")):
            with self.subTest(error=type(error).__name__):
                with mock.patch.object(self.checker, "urlopen", side_effect=error):
                    with self.assertRaises(ValueError):
                        self.checker.require_unpublished("python-v0.8.0")

    def test_registry_gate_failure_never_reports_verified_success(self):
        with mock.patch.object(self.checker, "verify_release", return_value=(Path("wheel"),)):
            with mock.patch.object(self.checker, "require_unpublished", side_effect=ValueError("readback required")):
                out, err = io.StringIO(), io.StringIO()
                with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                    result = self.checker.main([
                        "--tag", "python-v0.8.0", "--directory", "dist", "--require-unpublished",
                    ])
        self.assertNotEqual(result, 0)
        self.assertNotIn("Verified", out.getvalue())
        self.assertIn("readback", err.getvalue())


class WorkflowTests(unittest.TestCase):
    def setUp(self):
        self.workflow = WORKFLOW.read_text(encoding="utf-8")
        self.python = self.workflow.split("\n  python:\n", 1)[1].split("\n  typescript:\n", 1)[0]
        self.npm = self.workflow.split("\n  typescript:\n", 1)[1].split("\n  docs:\n", 1)[0]

    def test_committed_manifest_contains_only_cleared_bytes(self):
        self.assertTrue(MANIFEST.is_file(), "missing committed clearance manifest")
        self.assertEqual(json.loads(MANIFEST.read_text(encoding="utf-8")), {
            "schema_version": 1,
            "releases": {
                "python-v0.8.0": {
                    "futureagi-0.8.0-py3-none-any.whl": "3278af3145d7d40cedd826a7aa7d6ddda20b8d1f5cac4a1fb81700cf050b6e30",
                    "futureagi-0.8.0.tar.gz": "a1209e122e83c6e66993bd0a6175d18337002dd39216fb70a45fbd12d3de2d8f",
                },
                "typescript-v0.3.0": {
                    "future-agi-sdk-0.3.0.tgz": "3f17452cd578c1f978013bec2dded0fc89cdf00e9de4fd25e92682e8f4649fc5",
                },
            },
        })

    def test_python_checks_both_artifacts_before_publish(self):
        verify = 'python .github/scripts/verify_cleared_artifacts.py --tag "$TAG" --directory python/dist --require-unpublished'
        self.assertIn(verify, self.python)
        self.assertLess(self.python.index("python -m build python"), self.python.index(verify))
        self.assertLess(self.python.index(verify), self.python.index("pypa/gh-action-pypi-publish"))
        self.assertIn("packages-dir: python/dist", self.python)
        self.assertIn("skip-existing: false", self.python)
        self.assertNotIn("skip-existing: true", self.python)

    def test_npm_stages_then_verifies_then_publishes_explicit_tarball(self):
        stage = 'node gateway-client/scripts/stage-package.cjs "$candidate/staged"'
        verify = 'python "$GITHUB_WORKSPACE/.github/scripts/verify_cleared_artifacts.py" --tag "$TAG" --directory "$DIST_DIR" --require-unpublished'
        publish = 'npm publish "$DIST_DIR/future-agi-sdk-${TAG#typescript-v}.tgz" --access public --provenance --ignore-scripts'
        self.assertIn('mktemp -d "$RUNNER_TEMP/npm-cleared.XXXXXX"', self.npm)
        for command in (stage, verify, publish):
            self.assertIn(command, self.npm)
        self.assertIn('mv "$candidate"/staged/*.tgz "$candidate/dist/"', self.npm)
        self.assertIn('echo "directory=$candidate/dist" >> "$GITHUB_OUTPUT"', self.npm)
        self.assertEqual(self.npm.count("DIST_DIR: ${{ steps.package.outputs.directory }}"), 2)
        self.assertLess(self.npm.index("pnpm run build"), self.npm.index(stage))
        self.assertLess(self.npm.index(stage), self.npm.index(verify))
        self.assertLess(self.npm.index(verify), self.npm.index(publish))
        self.assertEqual(self.npm.count("npm publish "), 1)
        self.assertNotIn("npm view", self.npm)
        self.assertNotIn("exit 0", self.npm)

    def test_source_identity_and_postpublication_guards_are_preserved(self):
        self.assertIn("if: github.ref == 'refs/heads/main'", self.workflow)
        self.assertIn('release_guard.py validate-tag --tag "$TAG" --wait-seconds 3900', self.workflow)
        for job, environment in ((self.python, "pypi"), (self.npm, "npm")):
            self.assertIn("ref: ${{ needs.verify.outputs.sha }}", job)
            self.assertIn("environment: " + environment, job)
            self.assertIn("id-token: write", job)
            self.assertIn("persist-credentials: false", job)
            self.assertNotIn("--manifest", job)
            self.assertNotIn("secrets.", job)
        self.assertIn("unset NODE_AUTH_TOKEN NPM_TOKEN", self.npm)
        self.assertIn("Install the published package from PyPI and run the quickstart", self.python)
        self.assertIn("Install the published package from npm and run the quickstart", self.npm)
        self.assertIn("needs: [verify, python, typescript]", self.workflow)
        self.assertIn("repos/future-agi/docs/dispatches", self.workflow)


if __name__ == "__main__":
    unittest.main()
