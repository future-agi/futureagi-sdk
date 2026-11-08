"""Session-end coverage for both halves of the catalog live tests.

For xdist runs started above this directory, load this plugin on the controller:
``pytest -p tests.platform._live_operation_ledger ...``. Workers never assert a
partial ledger; they send their outcomes to the controller after fixture teardown.
An opted-in worker without that controller handshake fails before making calls.
"""

from __future__ import annotations

from os.path import relpath
from pathlib import Path

import pytest

CATALOG = Path(__file__).resolve().parents[3] / "sdkgen" / "catalog" / "operations.yaml"
OPERATION_MODULES = {"test_all_operations_live.py", "test_all_operations_extended_live.py"}
_PLUGIN_NAME = "platform-operation-ledger"
_WORKER_KEY = "platform_operation_ledger"


class CallLedger(dict):
    """Operation outcomes plus an explicit obligation to check even an empty run."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.required = False
        self.expected_ops = None

    def assert_complete(self, ops):
        record_calls = self
        for op_id in ops:
            outcomes = record_calls.get(op_id, [])
            print(f"{op_id:44} {'ok' if 'ok' in outcomes else ','.join(sorted(set(outcomes))) or 'NOT CALLED'}")
        missing = [op for op in ops if op not in record_calls]
        assert not missing, f"operations no test called: {missing}"


def _report_location(session):
    ledger_path = Path(__file__).with_name("test_all_operations_live.py").resolve()
    test_name = "test_every_operation_was_called"
    for item in session.items:
        if (getattr(item, "originalname", None) or item.name) == test_name and Path(str(item.fspath)).resolve() == ledger_path:
            return item.nodeid, item.location
    # The ledger item may be deselected, or collected only on xdist workers.
    relative_path = Path(relpath(ledger_path, session.config.rootpath)).as_posix()
    return f"{relative_path}::{test_name}", (relative_path, 0, test_name)


class _LedgerPlugin:
    def __init__(self):
        self.calls = CallLedger()

    @pytest.hookimpl(optionalhook=True)
    def pytest_configure_node(self, node):
        # The flag proves this controller can receive and check worker ledgers.
        node.workerinput[_WORKER_KEY] = True

    @pytest.hookimpl(optionalhook=True)
    def pytest_testnodedown(self, node, error):
        payload = getattr(node, "workeroutput", {}).get(_WORKER_KEY)
        if payload is None:
            return  # A crashed worker is already a failing xdist run.
        self.calls.required |= payload["required"]
        for op_id, outcomes in payload["calls"].items():
            self.calls.setdefault(op_id, []).extend(outcomes)

    @pytest.hookimpl(tryfirst=True)
    def pytest_sessionfinish(self, session, exitstatus):
        config = session.config
        if hasattr(config, "workerinput"):
            # Session finish is after ALL fixture finalizers, including deletes.
            config.workeroutput[_WORKER_KEY] = {
                "required": self.calls.required,
                "calls": dict(self.calls),
            }
            return
        if not self.calls.required:
            return
        ops = self.calls.expected_ops
        if ops is None:
            # Also enforce coverage when only the sibling module or a subset ran.
            import yaml

            ops = [e["id"] for e in yaml.safe_load(CATALOG.read_text())["operations"] if e["surfaces"].get("sdk") is not False]
        try:
            self.calls.assert_complete(ops)
        except AssertionError as exc:
            # A deferred assertion is reported as teardown, like a yield fixture,
            # rather than raising an INTERNALERROR from a session-finish hook.
            nodeid, location = _report_location(session)
            report = pytest.TestReport(
                nodeid=nodeid, location=location,
                keywords={}, outcome="failed", longrepr=str(exc), when="teardown",
            )
            config.hook.pytest_runtest_logreport(report=report)
            if session.exitstatus in (pytest.ExitCode.OK, pytest.ExitCode.TESTS_FAILED):
                session.exitstatus = pytest.ExitCode.TESTS_FAILED


def install(config):
    """Install once, whether loaded explicitly or by the platform conftest."""
    plugin = config.pluginmanager.get_plugin(_PLUGIN_NAME)
    if plugin is None:
        plugin = _LedgerPlugin()
        config.pluginmanager.register(plugin, _PLUGIN_NAME)
    return plugin


def pytest_configure(config):
    install(config)


def recording_ledger(config, node):
    ledger = install(config).calls
    if Path(str(node.fspath)).name in OPERATION_MODULES:
        if hasattr(config, "workerinput"):
            assert config.workerinput.get(_WORKER_KEY), (
                "live operation coverage needs its xdist controller plugin; "
                "run with -p tests.platform._live_operation_ledger"
            )
        # Arm on either module's setup, not on ledger-test order or dictionary
        # truthiness. Default-skipped tests never reach this function.
        ledger.required = True
    return ledger
