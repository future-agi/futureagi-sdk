import subprocess
import sys
from importlib.metadata import version
from pathlib import Path

import fi


def _declared_package_version() -> str:
    pyproject = Path(__file__).resolve().parents[1] / "pyproject.toml"
    for line in pyproject.read_text().splitlines():
        stripped = line.strip()
        if stripped.startswith("version = "):
            return stripped.split("=", 1)[1].strip().strip('"').strip("'")
    raise AssertionError("python/pyproject.toml has no version")


def test_source_fallback_matches_declared_package_version():
    python_root = Path(__file__).resolve().parents[1]
    script = (
        "import fi; "
        "print(fi.__version__); "
        "print(fi.__versions__)"
    )
    completed = subprocess.run(
        [sys.executable, "-c", script],
        cwd=python_root,
        env={"PYTHONPATH": str(python_root), "PYTHONDONTWRITEBYTECODE": "1"},
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    declared = _declared_package_version()
    lines = [line for line in completed.stdout.splitlines() if line.strip()]
    assert lines[-2:] == [declared, declared]


def test_public_version_matches_package_metadata():
    assert fi.__version__ == version("futureagi")


def test_public_versions_alias_matches_package_metadata():
    assert fi.__versions__ == version("futureagi")
