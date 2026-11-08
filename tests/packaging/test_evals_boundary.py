"""The deferred evaluation runner and the platform resource are different modules."""
import importlib.util
from pathlib import Path
import unittest

REPO = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location(
    "check_artifacts", REPO / "scripts/packaging/check_artifacts.py"
)
guard = importlib.util.module_from_spec(spec)
spec.loader.exec_module(guard)


class EvalsBoundaryTests(unittest.TestCase):
    def test_deferred_runner_directory_and_sibling_outputs_stay_excluded(self):
        for output in ("esm", "src", "esnext"):
            for suffix in ("evals/index.js", "evals/nested/runner.d.ts", "evals.js",
                           "evals.js.map", "evals.d.ts", "evals.d.ts.map"):
                with self.subTest(output=output, suffix=suffix):
                    self.assertTrue(guard.is_deferred_evals(f"{output}/{suffix}"))

    def test_platform_resource_and_other_nested_modules_are_not_the_runner(self):
        for output in ("esm", "src", "esnext"):
            for suffix in ("platform/resources/evals.js", "platform/resources/evals.d.ts",
                           "platform/resources/evals.js.map", "platform/resources/evals.d.ts.map",
                           "platform/resources/evals/index.js", "evaluations.js"):
                with self.subTest(output=output, suffix=suffix):
                    self.assertFalse(guard.is_deferred_evals(f"{output}/{suffix}"))
        self.assertFalse(guard.is_deferred_evals("gateway/esm/evals.js"))


if __name__ == "__main__":
    unittest.main()
