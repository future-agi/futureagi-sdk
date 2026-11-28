"""Live: ``run_in_sandboxes`` against a real EE stack, uploaded, then checked on the server.

The cloud E2E workflow opts in by setting ``FI_E2E_REQUIRED``. With that variable set, the test runs and
then it fails on missing configuration instead of skipping. It needs the sandbox environment
(``OMEGA_BASE_URL`` with ``FUTUREAGI_OMEGA_API_KEY``, or with ``FI_API_KEY`` + ``FI_SECRET_KEY``) and
the experiments upload environment (``FI_API_KEY``, ``FI_SECRET_KEY``, ``FI_BASE_URL``). The agent
runs here (no network inside the sandbox is needed); the verifier runs inside.
"""

from __future__ import annotations

import os
import uuid

import pytest

pytestmark = pytest.mark.skipif(not os.environ.get("FI_E2E_REQUIRED"),
                                reason="live sandbox experiments require explicit opt-in: set FI_E2E_REQUIRED=1")

CHECK = "python3 -c \"import sys; sys.exit(0 if open('/workspace/answer.txt').read().strip() == '{want}' else 1)\""


def _require(*names: str) -> None:
    missing = [n for n in names if not os.environ.get(n)]
    if missing:
        pytest.fail(f"live sandbox experiments need {', '.join(missing)}")


def _count(payload: object) -> int:
    if isinstance(payload, list):
        return len(payload)
    if isinstance(payload, dict):
        for key in ("items", "results"):
            if isinstance(payload.get(key), list):
                return len(payload[key])
        if isinstance(payload.get("result"), (dict, list)):
            return _count(payload["result"])
    return 0


def test_live_five_rows_two_at_once_uploaded_and_cleaned():
    _require("OMEGA_BASE_URL", "FI_API_KEY", "FI_SECRET_KEY", "FI_BASE_URL")
    from fi import FutureAGIClient, experiments
    from fi.experiments.sandbox import SandboxEval, reward, run_in_sandboxes
    from fi.sandbox import Sandbox

    tag = uuid.uuid4().hex[:8]
    rows = [{"id": f"live-{tag}-{n}", "n": n} for n in range(5)]

    async def agent(row, sbx, ctx):
        await sbx.files.write("/workspace/answer.txt", str(row["n"] * 2))
        return {"answer": row["n"] * 2}

    spec = SandboxEval(agent=agent, verifier=lambda row: CHECK.format(want=row["n"] * 2),
                       verifier_timeout_s=60, agent_timeout_s=120, name_prefix=f"live-{tag}")
    result = run_in_sandboxes(experiments.dataset(rows, name=f"sandbox-live-{tag}"), spec, [reward()],
                              max_active=2, upload=True, trace=False, progress=False, name=f"sandbox-live-{tag}")
    assert [item.status for item in result.items] == ["completed"] * 5
    assert all(item.output["deleted"] for item in result.items)
    assert result.scores("reward") == [1.0] * 5

    with FutureAGIClient() as client:
        assert _count(client.experiment_runs.list_items(result.run_id)) == 5
    left = [s for s in Sandbox.list().sandboxes
            if str(s.info.get("name", "")).startswith(f"live-{tag}-") and s.state != "destroyed"]
    assert left == []
