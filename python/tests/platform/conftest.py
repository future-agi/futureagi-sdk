"""Keep offline lane tests and released credentialed-live tests separate.

Live tests require FI_E2E_REQUIRED=1, as in the released E2E workflow. Match
release truthiness: any nonempty value opts in; unset/empty means skip, even
with credentials or -m platform_live. Check before reading .env.local or
exempting a test from no-egress. Opted-in tests fail on missing configuration.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from tests.core import _egress
from . import _live_operation_ledger

HERE = Path(__file__).resolve().parent
ENV_FILE = HERE.parents[2] / ".env.local"
_LIVE_MODULES = {"test_all_operations_live.py", "test_all_operations_extended_live.py", "test_datasets_live.py"}
_LIVE_SKIP_REASON = "platform live tests require explicit opt-in: set FI_E2E_REQUIRED=1"


def _is_live(node) -> bool:
    path = Path(str(node.fspath)).resolve()
    # An unrelated mark must not opt a lane test out of the no-egress guard.
    return path.parent == HERE and path.name in _LIVE_MODULES


def _live_opted_in() -> bool:
    # Release _require_backend uses nonempty env truthiness, not a parsed bool.
    # Never discover consent by loading the credential file itself.
    return bool(os.environ.get("FI_E2E_REQUIRED"))


def _live_enabled(node) -> bool:
    return _is_live(node) and _live_opted_in()


def pytest_configure(config):
    _live_operation_ledger.install(config)
    config.addinivalue_line("markers", "platform_live: released credentialed backend tests")
    config.addinivalue_line("markers", "platform_offline: platform tests with no-egress enforcement")


def pytest_collection_modifyitems(config, items):
    for item in items:
        if HERE in Path(str(item.fspath)).resolve().parents:
            item.add_marker(pytest.mark.platform_live if _is_live(item) else pytest.mark.platform_offline)
            if _is_live(item) and not _live_opted_in():
                item.add_marker(pytest.mark.skip(reason=_LIVE_SKIP_REASON))


def _load_env_file(monkeypatch) -> None:
    if not ENV_FILE.exists():
        return
    for line in ENV_FILE.read_text().splitlines():
        key, _, value = line.partition("=")
        if key and value and key.strip() not in os.environ:
            monkeypatch.setenv(key.strip(), value.strip())


@pytest.fixture(autouse=True)
def _live_environment(request, monkeypatch, _no_egress):
    # Recheck at setup even if another hook removed the collection skip. The
    # guard dependency keeps default-denied tests guarded before this skip.
    if _is_live(request.node):
        if not _live_opted_in():
            pytest.skip(_LIVE_SKIP_REASON)
        _load_env_file(monkeypatch)
        # Also cover live tests that construct their own client (bad credentials)
        # instead of requesting the client fixture. CI must fail, never skip.
        _require_backend()


@pytest.fixture(autouse=True)
def _no_egress(request, monkeypatch, tmp_path):
    if _live_enabled(request.node):
        yield
        return
    _egress.install(monkeypatch, tmp_path)
    yield
    _egress.assert_no_attempts()


@pytest.fixture
def anyio_backend():
    return "asyncio"


def _require_backend() -> None:
    if not (os.environ.get("FI_API_KEY") and os.environ.get("FI_SECRET_KEY") and os.environ.get("FI_BASE_URL")):
        message = "no backend configured: run sdkgen/local_api_key.py (writes .env.local)"
        if os.environ.get("FI_E2E_REQUIRED"):  # CI: missing configuration fails, not skips
            pytest.fail(message)
        pytest.skip(message)


@pytest.fixture
def client(_live_environment, record_calls):
    _require_backend()
    from fi.platform import Client

    # Strict: a response that does not match the contract fails instead of warning.
    with Client(strict_responses=True) as client:
        yield client


@pytest.fixture(autouse=True)
def record_calls(request, monkeypatch, _live_environment):
    # Depend on the opt-in/configuration gate before importing or patching SDK
    # transports. Keep the shared ledger for the final coverage assertion, but
    # never count offline mocks or alter lane transport behaviour.
    if not _live_enabled(request.node):
        yield
        return

    called = _live_operation_ledger.recording_ledger(request.config, request.node)
    from fi.platform import APIError
    from fi.platform._transport import AsyncTransport, SyncTransport

    sync_request, async_request = SyncTransport.request, AsyncTransport.request

    def record(op, outcome):
        if not op.id.startswith("raw:"):
            called.setdefault(op.id, []).append(outcome)

    def request(self, op, **kwargs):
        try:
            result = sync_request(self, op, **kwargs)
        except APIError as exc:
            record(op, str(exc.status_code))
            raise
        record(op, "ok")
        return result

    async def arequest(self, op, **kwargs):
        try:
            result = await async_request(self, op, **kwargs)
        except APIError as exc:
            record(op, str(exc.status_code))
            raise
        record(op, "ok")
        return result

    monkeypatch.setattr(SyncTransport, "request", request)
    monkeypatch.setattr(AsyncTransport, "request", arequest)
    yield called
