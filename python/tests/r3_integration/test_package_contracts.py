"""Release wiring regressions: optional runtime coverage cannot silently vanish."""

import os
import subprocess
from importlib.metadata import requires
from pathlib import Path

import pytest
import yaml
from packaging.requirements import Requirement

ROOT = Path(__file__).resolve().parents[3]


def workflow():
    return yaml.safe_load((ROOT / ".github/workflows/ci.yml").read_text())


def commands(job):
    return "\n".join(step.get("run", "") for step in job["steps"])


def test_optional_backend_is_pinned_and_scoped_to_qualified_interpreter():
    requirements = [Requirement(raw) for raw in requires("futureagi") or []]
    backend = next(item for item in requirements if item.name == "deepagents")
    assert str(backend.specifier) == "==0.4.11"
    assert backend.marker is not None
    assert backend.marker.evaluate(
        {"extra": "context-deepagents", "python_version": "3.11"}
    )
    assert not backend.marker.evaluate({"extra": "", "python_version": "3.11"})
    for version in ("3.9", "3.10", "3.12", "3.13"):
        assert not backend.marker.evaluate(
            {"extra": "context-deepagents", "python_version": version}
        )


def test_backend_suite_is_a_required_job_not_a_silent_collection_skip():
    jobs = workflow()["jobs"]
    assert "context-backend" in jobs["ci-pass"]["needs"]
    backend = jobs["context-backend"]
    assert not backend.get("continue-on-error", False)
    assert "if" not in backend
    setup = next(
        step
        for step in backend["steps"]
        if step.get("uses", "").startswith("actions/setup-python@")
    )
    assert setup["with"]["python-version"] == "3.11"
    code = commands(backend)
    assert "./python[context-deepagents]" in code
    assert "python/tests/r3_l10" in code
    assert "--ignore" not in code
    assert "integration_snapshot_probe.py" in code
    assert "flock /tmp/ctxhub-pytest.lock" in code


def test_changed_modules_and_tests_are_in_the_lint_and_typescript_gates():
    jobs = workflow()["jobs"]
    lint = commands(jobs["generated"])
    for path in (
        "python/fi/context",
        "python/fi/skills",
        "python/tests/r3_l10",
        "python/tests/r3_l11",
        "python/tests/r3_integration",
        "python/consumer/context_consumer.py",
    ):
        assert path in lint
    assert "src/__tests__/r3_l10" in commands(jobs["typescript"])


def test_installed_package_gate_exercises_cli_action_and_public_types():
    code = commands(workflow()["jobs"]["packages"])
    assert "unset PYTHONPATH" in code
    assert "context_consumer.py" in code
    assert "integration_snapshot_probe.py" in code
    assert "package_action_probe.py" in code
    assert "mypy --strict" in code
    assert "pnpm run check:consumer" in code


def test_checks_cannot_fall_back_to_a_hosted_or_local_runner():
    for name, job in workflow()["jobs"].items():
        assert job["runs-on"] == ["self-hosted", "linux", "x64", "context-sdk-gcp"]
        if name != "ci-pass":
            assert job["steps"][1]["uses"] == "./.github/actions/require-sdk-test-vm"


@pytest.mark.parametrize(
    ("project", "transport_status", "allowed"),
    [("fagi-omega-staging", 0, True), ("other-project", 0, False), ("", 7, False)],
)
def test_cloud_guard_checks_metadata_and_fails_closed(
    tmp_path, project, transport_status, allowed
):
    action = yaml.safe_load(
        (ROOT / ".github/actions/require-sdk-test-vm/action.yml").read_text()
    )
    script = action["runs"]["steps"][0]["run"]
    fake_curl = tmp_path / "curl"
    fake_curl.write_text(
        '#!/bin/sh\nprintf "%s" "$SYNTHETIC_PROJECT"\nexit "$SYNTHETIC_STATUS"\n'
    )
    fake_curl.chmod(0o700)
    result = subprocess.run(
        ["bash", "-c", script],
        env={
            **os.environ,
            "PATH": f"{tmp_path}:{os.environ['PATH']}",
            "SYNTHETIC_PROJECT": project,
            "SYNTHETIC_STATUS": str(transport_status),
        },
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert (result.returncode == 0) is allowed
