"""The alk import guard must not change what later tests in the same process can see.

The first test to import ``fi.evals.metrics`` loads the evals dependencies inside the guard. One
of them, the importlib_metadata backport, appends its own finder to ``sys.meta_path`` and disables
the stdlib PathFinder's distribution lookup. If the guard then restores a different list, every
later ``importlib.metadata`` lookup in the process raises PackageNotFoundError.
"""

import os
from pathlib import Path
import subprocess
import sys

PYTHON = Path(__file__).resolve().parents[2]
GUARDED = "tests/evals/test_alk_compat_errors.py::test_report_module_points_to_its_alk_replacement"
LATER = "tests/test_version.py::test_public_version_matches_package_metadata"
# Only what the interpreter needs to start; nothing that could carry credentials, preload a module
# (PYTEST_PLUGINS) or add options (PYTEST_ADDOPTS). The evals conftest sets its own fake keys.
_KEEP = ("PATH", "TMPDIR", "TEMP", "TMP", "LANG", "LC_ALL", "LC_CTYPE", "SYSTEMROOT")


def test_package_metadata_still_resolves_after_the_guarded_first_evals_import(tmp_path):
    env = {key: os.environ[key] for key in _KEEP if key in os.environ}
    env.update(HOME=str(tmp_path), PYTHONDONTWRITEBYTECODE="1", PYTEST_DISABLE_PLUGIN_AUTOLOAD="1")
    # One interpreter, in this order, with the backport first imported inside the guard.
    run = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", "-o", "addopts=", GUARDED, LATER],
        cwd=PYTHON, env=env, capture_output=True, text=True, timeout=600,
    )
    assert run.returncode == 0, run.stdout[-3000:] + run.stderr[-2000:]
    assert "3 passed" in run.stdout, run.stdout[-3000:]
