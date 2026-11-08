"""Explicit installed-wheel/action verification with a hostile project import.

Run with the trusted installed Python, not PYTHONPATH=python. This probes the
actual composite action's script; it invokes no repository hooks or model calls.
"""

from __future__ import annotations

import hashlib
import importlib.metadata
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import yaml
from fi.context import materialize
from test_materializer import bundle


def main(action_path: Path) -> None:
    distribution = importlib.metadata.distribution("futureagi")
    installed = Path(distribution.locate_file("fi/context/materialize.py"))
    if installed.resolve() != Path(materialize.__file__).resolve():
        raise AssertionError("Probe imported a source checkout instead of the wheel")
    script = yaml.safe_load(action_path.read_text())["runs"]["steps"][0]["run"]
    with tempfile.TemporaryDirectory(prefix="fi-l11-wheel-") as temporary:
        project = Path(temporary) / "project"
        project.mkdir()
        source = bundle()
        prepared = materialize.plan_install(
            source, project=project, profile="codex", allow_preview=True
        )
        materialize.apply_plan(prepared, authorize=lambda auth: None, quiescent=True)
        trap = project / "PROJECT_CODE_EXECUTED"
        (project / "json.py").write_text(
            f"from pathlib import Path\nPath({str(trap)!r}).touch()\n"
            "raise RuntimeError('Project import executed')\n"
        )
        environment = {
            "PATH": os.environ["PATH"],
            "HOME": os.environ["HOME"],
            "PYTHONPATH": str(project),
            "FI_VERIFY_PYTHON": sys.executable,
            "FI_VERIFY_VERSION": distribution.version,
            "FI_VERIFY_MATERIALIZER_SHA256": hashlib.sha256(
                installed.read_bytes()
            ).hexdigest(),
            "FI_VERIFY_PROJECT": str(project),
        }
        result = subprocess.run(
            ["bash", "-c", script],
            cwd=project,
            env=environment,
            text=True,
            capture_output=True,
            timeout=30,
        )
        if result.returncode != 0:
            raise AssertionError(result.stderr)
        if not json.loads(result.stdout)["verified"] or trap.exists():
            raise AssertionError("Installed action ran project code or missed bytes")
        (project / "AGENTS.md").write_bytes(b"Deliberately corrupted instructions")
        negative = subprocess.run(
            ["bash", "-c", script],
            cwd=project,
            env=environment,
            text=True,
            capture_output=True,
            timeout=30,
        )
        if negative.returncode != 6 or json.loads(negative.stdout)["verified"]:
            raise AssertionError("Action missed the independent corruption control")
        environment["FI_VERIFY_MATERIALIZER_SHA256"] = "0" * 64
        wrong_pin = subprocess.run(
            ["bash", "-c", script],
            cwd=project,
            env=environment,
            text=True,
            capture_output=True,
            timeout=30,
        )
        if wrong_pin.returncode == 0 or trap.exists():
            raise AssertionError("Action accepted a wrong pin or ran project code")
        print(
            json.dumps(
                {
                    "schema": 1,
                    "installed_wheel": distribution.version,
                    "action": "passed",
                    "corruption_control": "passed",
                    "pin_control": "passed",
                    "project_code": "not_executed",
                    "scope": "checked_in_bytes_only",
                },
                sort_keys=True,
            )
        )


if __name__ == "__main__":
    main(Path(sys.argv[1]))
