import hashlib
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import release_stack as stack


class ReleaseStackTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        checksums = {}
        for name in stack.FILES:
            path = self.root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(name.encode())
            checksums[name] = hashlib.sha256(path.read_bytes()).hexdigest()
        for name, value in [("FILES", checksums), ("INDEX", hashlib.sha256(b"published index").hexdigest())]:
            replacement = patch.object(stack, name, value)
            replacement.start()
            self.addCleanup(replacement.stop)
        self.head = stack.COMMIT
        self.registry = b"published index"
        mock = patch.object(subprocess, "check_output", side_effect=self.command)
        self.calls = mock.start()
        self.addCleanup(mock.stop)

    def command(self, args, **kwargs):
        if args == ["git", "rev-parse", "HEAD"] and kwargs["cwd"] == self.root:
            return self.head + "\n"
        self.assertEqual(args, ["docker", "buildx", "imagetools", "inspect", "--raw", "futureagi/standalone:v1.59.0"])
        return self.registry

    def render(self, version=stack.TAG, ref=stack.TAG):
        return stack.overlay(self.root, version, ref)

    def test_exact_overlay_and_immutable_release_ref(self):
        expected = ("services:\n  app:\n    image: futureagi/standalone:v1.59.0@sha256:" + stack.INDEX + "\n"
                    "    volumes:\n      - ./e2e/stack/backend/e2e_legacy_eval.py:/app/backend/sdk/views/e2e_legacy_eval.py:ro\n")
        for ref in (stack.TAG, "refs/tags/" + stack.TAG, stack.COMMIT):
            self.assertEqual(self.render(ref=ref), expected)

    def test_no_compat_for_other_tags_or_refs(self):
        for version, ref in [("latest", "main"), ("v1.58.0", "v1.58.0"), (stack.TAG, "dev"), (stack.TAG, "0" * 40)]:
            with self.subTest(version=version, ref=ref), self.assertRaises(ValueError):
                self.render(version, ref)
        self.calls.assert_not_called()

    def test_moved_tag(self):
        self.head = "1" * 40
        with self.assertRaisesRegex(ValueError, "checkout"):
            self.render()

    def test_replaced_image_index(self):
        self.registry = b"different index"
        with self.assertRaisesRegex(ValueError, "image index"):
            self.render()

    def test_missing_or_changed_fixture(self):
        p = self.root / stack.FIXTURE
        p.unlink()
        with self.assertRaisesRegex(ValueError, "missing or changed"):
            self.render()
        p.write_text("different fixture")
        with self.assertRaisesRegex(ValueError, "missing or changed"):
            self.render()

    def test_never_run_changed_sql_provisioner(self):
        (self.root / "e2e/stack/backend/bootstrap_sql.py").write_text("changed")
        with self.assertRaisesRegex(ValueError, "missing or changed"):
            self.render()

    def test_never_override_existing_mount(self):
        for name in ["docker-compose.yml", "e2e/stack/docker-compose.standalone-e2e.yml"]:
            path = self.root / name
            original = path.read_bytes()
            for suffix in [f"./{stack.FIXTURE}:{stack.TARGET}:ro", f"./other.py:{stack.TARGET}:rw"]:
                with self.subTest(name=name, mount=suffix), self.assertRaisesRegex(ValueError, "changed"):
                    path.write_bytes(original + ("\n      - " + suffix + "\n").encode())
                    self.render()
                path.write_bytes(original)
