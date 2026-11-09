"""Provisioning prerequisites for the real all-operations suite."""
from __future__ import annotations

import json
from pathlib import Path

import httpx
import yaml

from sdkgen.local_api_key import signup_keys


def test_signup_issues_a_human_owned_workspace_scoped_key():
    seen = []

    def respond(request):
        seen.append(request)
        path = request.url.path
        if path == "/accounts/signup/":
            return httpx.Response(201, json={})
        if path == "/accounts/token/":
            return httpx.Response(200, json={"access": "synthetic-login-token"})
        if path == "/accounts/user-info/":
            return httpx.Response(200, json={"organization": {"id": "org-fixture"}, "default_workspace_id": "workspace-fixture"})
        assert path == "/accounts/key/generate_secret_key/" and request.method == "POST"
        assert request.headers["authorization"] == "Bearer synthetic-login-token"
        assert request.headers["x-workspace-id"] == "workspace-fixture"
        assert json.loads(request.content)["key_name"].startswith("sdk-live-")
        return httpx.Response(200, json={"result": {"api_key": "synthetic-user-key", "secret_key": "synthetic-user-secret", "masked_api_key": "synthetic"}})

    with httpx.Client(base_url="https://backend.invalid", transport=httpx.MockTransport(respond)) as http:
        result = signup_keys(http, "fixture")
    assert result["api_key"] == "synthetic-user-key"
    assert result["workspace_id"] == "workspace-fixture"
    assert len(seen) == 4


def test_live_workflow_enables_consumption_and_runs_full_platform_suite():
    root = Path(__file__).resolve().parents[3]
    workflow = yaml.safe_load((root / ".github/workflows/e2e.yml").read_text())
    job = workflow["jobs"]["e2e"]
    assert "context-sdk-gcp" in job["runs-on"]
    assert any(step.get("uses") == "./.github/actions/require-sdk-test-vm" for step in job["steps"])
    boot = next(step["run"] for step in job["steps"] if step.get("id") == "boot")
    assert 'SKILLS_CONTEXT_CONSUMPTION_ENABLED: "true"' in boot
    assert '-f "$RUNNER_TEMP/sdk-context.yml"' in boot
    run = next(step["run"] for step in job["steps"] if step.get("name") == "Python live suite (every catalog operation)")
    assert run == "PYTHONPATH=python flock /tmp/ctxhub-pytest.lock python -m pytest -q python/tests/platform"
