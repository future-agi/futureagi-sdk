"""Exercise the real workflow shell. These are selection/ordering tests, not live SQL proof."""
import os
import subprocess
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]
JOB = yaml.safe_load((ROOT / ".github/workflows/e2e.yml").read_text())["jobs"]["e2e"]
STEPS = JOB["steps"]
SELECT = next(s for s in STEPS if s.get("name", "").startswith("Pick the backend"))
BOOT = next(s for s in STEPS if s.get("id") == "boot")
BOOT_PAIRED = next(s for s in STEPS if s.get("id") == "boot_paired")
SQL = next(s for s in STEPS if s.get("name") == "Provision the standalone SQL fixture")
PIN = (ROOT / "sdkgen/contracts/BACKEND_VERSION").read_text().strip()


def shell(script, cwd, **env):
    return subprocess.run(["bash", "-eo", "pipefail", "-c", script], cwd=cwd, env={**os.environ, **env},
                          text=True, capture_output=True)


@pytest.mark.parametrize(("event", "version", "ref", "expected"), [
    ("pull_request", "", "", (PIN, PIN, "refs/tags/" + PIN)),
    ("schedule", "", "", ("latest", "main", "refs/heads/main")),
    ("workflow_dispatch", "latest", "refs/heads/main", ("latest", "refs/heads/main", "refs/heads/main")),
    ("workflow_dispatch", "v1.60.0", "", ("v1.60.0", "v1.60.0", "refs/tags/v1.60.0")),
    ("workflow_dispatch", PIN, "1" * 40, (PIN, "1" * 40, "refs/tags/" + PIN)),
    ("workflow_dispatch", PIN, "main", None), ("workflow_dispatch", "latest", PIN, None),
    ("workflow_dispatch", "latest\nOTHER=value", "main", None),
])
def test_selection(tmp_path, event, version, ref, expected):
    out = tmp_path / "env"
    proc = shell(SELECT["run"].replace("${{ github.event_name }}", event), ROOT,
                 DISPATCHED=version, DISPATCHED_REF=ref, GITHUB_ENV=str(out))
    if expected is None:
        assert proc.returncode != 0 and not out.exists()
        return
    assert proc.returncode == 0, proc.stderr
    values = dict(line.split("=", 1) for line in out.read_text().splitlines())
    assert tuple(values[k] for k in ("BACKEND_VERSION", "BACKEND_REF", "STACK_SOURCE")) == expected
    checkout = next(s["with"] for s in STEPS if s.get("with", {}).get("path") == "future-agi")
    assert (checkout["repository"], checkout["ref"]) == ("future-agi/future-agi", "${{ env.STACK_SOURCE }}")


@pytest.mark.parametrize("ref", ["main", "0" * 40])
def test_refuses_unapproved_helper_or_wrong_explicit_commit(tmp_path, ref):
    helper = tmp_path / "e2e/stack/backend/bootstrap_sql.py"
    helper.parent.mkdir(parents=True)
    helper.write_text("# unapproved helper\n")
    for args in (["init", "-q"], ["add", "."], ["-c", "user.name=CI", "-c", "user.email=ci@example.invalid",
                                               "commit", "-qm", "fixture"]):
        subprocess.run(["git", *args], cwd=tmp_path, check=True)
    proc = shell(BOOT["run"], tmp_path, BACKEND_REF=ref, STACK_SOURCE="refs/heads/main", RUNNER_TEMP=str(tmp_path))
    assert proc.returncode != 0
    assert ("FAILED" if ref == "main" else "explicit commit does not match") in proc.stdout


@pytest.mark.parametrize("version", [PIN, "latest", "v1.60.0"])
def test_provision_is_unconditional_and_ordered(tmp_path, version):
    live = next(s for s in STEPS if s.get("name", "").startswith("Python live suite"))
    # Exactly one boot runs, chosen by the pairing mode alone; provisioning and the live suite
    # always run after it, whichever it was.
    assert not any("if" in s for s in (JOB, SQL, live))
    assert BOOT["if"] == "steps.product.outputs.mode == 'pinned' || steps.product.outputs.mode == 'latest'"
    assert BOOT_PAIRED["if"] == "steps.product.outputs.mode == 'paired'"
    assert STEPS.index(BOOT) < STEPS.index(BOOT_PAIRED) < STEPS.index(SQL) < STEPS.index(live)
    for boot in (BOOT, BOOT_PAIRED):
        assert 'curl -fsS "$FI_BASE_URL/health/"' in boot["run"]
        assert "FUTURE_AGI_E2E_FIXTURE=" not in boot["run"]
    # Capture argv only. Never emulate the helper, account, SDK or backend.
    (tmp_path / "sdk-bootstrap-sql.py").touch()
    proc = shell('docker() { printf "%s\\n" "$*"; };\n' + SQL["run"], tmp_path,
                 RUNNER_TEMP=str(tmp_path), FUTURE_AGI_VERSION=version, BACKEND_VERSION=version)
    assert proc.returncode == 0
    commands = proc.stdout.splitlines()
    assert len(commands) == 3
    assert "SELECT count() FROM spans LIMIT 0" in commands[0]
    assert "observed_attribute_keys" in commands[1] and "observed_attribute_values" in commands[1]
    assert commands[2].endswith("exec -T -w /app/backend -e FUTURE_AGI_E2E_FIXTURE=sql-workbench app python -")
