"""Check the package file rules without needing a TypeScript build or install."""
import fnmatch
import json
from pathlib import Path
import unittest

REPO = Path(__file__).resolve().parents[2]
RULES = json.loads((REPO / "typescript/futureagi/package.json").read_text())["files"]


def included(path):
    # The current positive rules are directory roots; negative rules are globs.
    selected = any(path == rule or path.startswith(rule + "/")
                   for rule in RULES if not rule.startswith("!"))
    return selected and not any(fnmatch.fnmatchcase(path, rule[1:])
                                for rule in RULES if rule.startswith("!"))


class TestOutputBoundaryTests(unittest.TestCase):
    def test_compiled_test_outputs_are_excluded(self):
        for family in ("esm", "src", "esnext", "gateway/esm", "gateway/cjs"):
            for stem in ("_core/__fixtures__/payload", "__fixtures__/payload",
                         "_core/__tests__/helper", "resource.test", "resource.spec"):
                for suffix in (".js", ".js.map", ".d.ts", ".d.ts.map"):
                    path = f"dist/{family}/{stem}{suffix}"
                    with self.subTest(path=path):
                        self.assertFalse(included(path), f"Test output would be packed: {path}")
            self.assertFalse(included(f"dist/{family}/tsconfig.tsbuildinfo"))

    def test_runtime_outputs_and_public_testing_subpath_stay_included(self):
        for family in ("esm", "src", "esnext", "gateway/esm", "gateway/cjs"):
            for stem in ("index", "platform/resources/evals", "testing", "fixtures"):
                for suffix in (".js", ".js.map", ".d.ts", ".d.ts.map"):
                    path = f"dist/{family}/{stem}{suffix}"
                    with self.subTest(path=path):
                        self.assertTrue(included(path), f"Runtime output would be removed: {path}")


if __name__ == "__main__":
    unittest.main()
