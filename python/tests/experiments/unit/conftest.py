"""Unit tests for fi.experiments: no network, no model, no server.

Every test gets a private run directory, no FI keys, an FI_BASE_URL that points at a closed local
port, and a fresh OpenTelemetry global provider.
"""

import pytest


@pytest.fixture(autouse=True)
def _isolated(monkeypatch, tmp_path):
    for name in ("FI_API_KEY", "FI_SECRET_KEY", "FI_JUDGE_MODEL", "CI"):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("FI_BASE_URL", "http://127.0.0.1:9")
    monkeypatch.setenv("FI_RUN_DIR", str(tmp_path / "runs"))
    monkeypatch.setenv("FI_LOGIN_FILE", str(tmp_path / "login.json"))
    monkeypatch.chdir(tmp_path)
    _no_judge_retry_wait(monkeypatch)
    from tests.experiments.unit.otel_isolation import isolated_otel

    with isolated_otel():
        yield


def _no_judge_retry_wait(monkeypatch):
    """judge() retries a 429 or 5xx after a wait; unit tests never wait for real."""
    from fi.experiments.evaluators import _judge_http

    async def instant(seconds):
        return None

    monkeypatch.setattr(_judge_http, "_sleep", instant)
