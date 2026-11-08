"""Offline regression pins for the live ledger; no SDK clients or live opt-in."""

from __future__ import annotations

import importlib
import importlib.util
from pathlib import Path
from types import SimpleNamespace

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
LIVE_MODULES = ["test_all_operations_live.py", "test_all_operations_extended_live.py"]
LEDGER_NAME = "test_every_operation_was_called"


def _ledger_module():
    name = f"{__package__}._live_operation_ledger"
    # Guard inside each test call: missing base code fails, not a setup/import error.
    assert importlib.util.find_spec(name) is not None, "deferred ledger module is required"
    module = importlib.import_module(name)
    for symbol in ("CallLedger", "_LedgerPlugin", "recording_ledger", "install"):
        assert callable(getattr(module, symbol, None)), f"deferred ledger needs {symbol}"
    return module


class _PluginManager:
    def __init__(self):
        self.plugins = {}

    def get_plugin(self, name):
        return self.plugins.get(name)

    def register(self, plugin, name):
        assert name not in self.plugins
        self.plugins[name] = plugin


def _session(root=REPO_ROOT, items=()):
    reports = []
    config = SimpleNamespace(
        rootpath=root,
        pluginmanager=_PluginManager(),
        hook=SimpleNamespace(pytest_runtest_logreport=lambda report: reports.append(report)),
    )
    return SimpleNamespace(config=config, items=list(items), exitstatus=pytest.ExitCode.OK), reports


def _must_not_check(*args, **kwargs):
    pytest.fail("an unarmed or worker ledger must not check coverage or read a catalog")


@pytest.mark.parametrize("partial", [{}, {"called": ["ok"]}], ids=["empty", "partial"])
def test_assert_complete_rejects_missing_operations(partial):
    ledger_module = _ledger_module()
    calls = ledger_module.CallLedger(partial)
    with pytest.raises(AssertionError, match="operations no test called:.*never_called"):
        calls.assert_complete(["called", "never_called"])


def test_assert_complete_accepts_error_outcomes():
    ledger_module = _ledger_module()
    calls = ledger_module.CallLedger({"called": ["ok"], "never_called": ["404"]})
    calls.assert_complete(["called", "never_called"])


def test_sessionfinish_reports_missing_operation():
    ledger_module = _ledger_module()
    plugin = ledger_module._LedgerPlugin()
    plugin.calls.required = True
    plugin.calls.expected_ops = ["called", "never_called"]
    plugin.calls["called"] = ["ok"]
    session, reports = _session()

    plugin.pytest_sessionfinish(session, session.exitstatus)

    assert session.exitstatus == pytest.ExitCode.TESTS_FAILED
    assert len(reports) == 1
    assert reports[0].failed and reports[0].when == "teardown"
    assert "operations no test called: ['never_called']" in str(reports[0].longrepr)


def test_sessionfinish_does_not_check_unarmed_ledger(monkeypatch):
    ledger_module = _ledger_module()
    plugin = ledger_module._LedgerPlugin()
    monkeypatch.setattr(plugin.calls, "assert_complete", _must_not_check)
    monkeypatch.setattr(ledger_module, "CATALOG", SimpleNamespace(read_text=_must_not_check))
    session, reports = _session()

    plugin.pytest_sessionfinish(session, session.exitstatus)

    assert not plugin.calls.required
    assert reports == []
    assert session.exitstatus == pytest.ExitCode.OK


def test_sessionfinish_falls_back_to_catalog(monkeypatch, tmp_path):
    ledger_module = _ledger_module()
    catalog = tmp_path / "operations.yaml"
    catalog.write_text(
        "operations:\n"
        "  - id: called\n    surfaces: {sdk: true}\n"
        "  - id: never_called\n    surfaces: {}\n"
        "  - id: not_sdk\n    surfaces: {sdk: false}\n"
    )
    monkeypatch.setattr(ledger_module, "CATALOG", catalog)
    plugin = ledger_module._LedgerPlugin()
    plugin.calls.required = True
    plugin.calls["called"] = ["ok"]
    assert plugin.calls.expected_ops is None
    session, reports = _session()

    plugin.pytest_sessionfinish(session, session.exitstatus)

    assert session.exitstatus == pytest.ExitCode.TESTS_FAILED
    assert len(reports) == 1 and reports[0].when == "teardown" and reports[0].failed
    assert "operations no test called: ['never_called']" in str(reports[0].longrepr)
    assert "not_sdk" not in str(reports[0].longrepr)

    plugin.calls["never_called"] = ["403"]
    complete_session, complete_reports = _session()
    plugin.pytest_sessionfinish(complete_session, complete_session.exitstatus)
    assert complete_reports == []
    assert complete_session.exitstatus == pytest.ExitCode.OK


def test_worker_payloads_merge_to_complete_coverage():
    ledger_module = _ledger_module()
    plugin = ledger_module._LedgerPlugin()
    ops = ["first", "second"]
    payloads = [
        {"required": True, "calls": {"first": ["ok"]}},
        {"required": False, "calls": {"second": ["404"]}},
    ]
    for payload in payloads:
        with pytest.raises(AssertionError, match="operations no test called"):
            ledger_module.CallLedger(payload["calls"]).assert_complete(ops)
        node = SimpleNamespace(workeroutput={ledger_module._WORKER_KEY: payload})
        plugin.pytest_testnodedown(node, error=None)

    assert plugin.calls.required
    assert dict(plugin.calls) == {"first": ["ok"], "second": ["404"]}
    plugin.calls.assert_complete(ops)
    plugin.calls.expected_ops = ops
    session, reports = _session()
    plugin.pytest_sessionfinish(session, session.exitstatus)
    assert reports == []
    assert session.exitstatus == pytest.ExitCode.OK


def test_worker_sessionfinish_exports_without_checking(monkeypatch):
    ledger_module = _ledger_module()
    plugin = ledger_module._LedgerPlugin()
    plugin.calls.required = True
    plugin.calls["called"] = ["ok", "404"]
    monkeypatch.setattr(plugin.calls, "assert_complete", _must_not_check)
    monkeypatch.setattr(ledger_module, "CATALOG", SimpleNamespace(read_text=_must_not_check))
    session, reports = _session()
    session.config.workerinput = {ledger_module._WORKER_KEY: True}
    session.config.workeroutput = {}

    plugin.pytest_sessionfinish(session, session.exitstatus)

    assert session.config.workeroutput.get(ledger_module._WORKER_KEY) == {
        "required": True, "calls": {"called": ["ok", "404"]},
    }
    assert reports == []
    assert session.exitstatus == pytest.ExitCode.OK


@pytest.mark.parametrize("module_name", LIVE_MODULES, ids=["primary", "extended"])
def test_recording_ledger_arms_either_live_module(module_name):
    ledger_module = _ledger_module()
    session, _ = _session()
    node = SimpleNamespace(fspath=Path(__file__).with_name(module_name))

    calls = ledger_module.recording_ledger(session.config, node)

    assert calls.required
    assert calls is ledger_module.install(session.config).calls
    assert ledger_module.recording_ledger(session.config, node) is calls


@pytest.mark.parametrize("module_name", LIVE_MODULES, ids=["primary", "extended"])
def test_recording_ledger_rejects_worker_without_handshake(module_name):
    ledger_module = _ledger_module()
    session, _ = _session()
    session.config.workerinput = {}
    node = SimpleNamespace(fspath=Path(__file__).with_name(module_name))

    with pytest.raises(AssertionError, match="needs its xdist controller plugin"):
        ledger_module.recording_ledger(session.config, node)

    assert not ledger_module.install(session.config).calls.required


@pytest.mark.parametrize("module_name", LIVE_MODULES, ids=["primary", "extended"])
def test_recording_ledger_accepts_controller_handshake(module_name):
    ledger_module = _ledger_module()
    session, _ = _session()
    worker = SimpleNamespace(workerinput={})
    ledger_module.install(session.config).pytest_configure_node(worker)
    session.config.workerinput = worker.workerinput
    node = SimpleNamespace(fspath=Path(__file__).with_name(module_name))

    assert session.config.workerinput.get(ledger_module._WORKER_KEY) is True
    assert ledger_module.recording_ledger(session.config, node).required


def test_recording_ledger_does_not_arm_offline_module():
    ledger_module = _ledger_module()
    session, _ = _session()
    session.config.workerinput = {}
    calls = ledger_module.recording_ledger(session.config, SimpleNamespace(fspath=Path(__file__)))
    assert not calls.required


@pytest.mark.parametrize("root_subdir", ["", "python"], ids=["repo-root", "python-root"])
def test_failure_report_uses_collected_ledger_item(root_subdir):
    ledger_module = _ledger_module()
    root = REPO_ROOT / root_subdir
    ledger_path = Path(__file__).with_name("test_all_operations_live.py")
    relative_path = ledger_path.relative_to(root).as_posix()
    item = SimpleNamespace(
        fspath=ledger_path, name=LEDGER_NAME,
        nodeid=f"{relative_path}::{LEDGER_NAME}[collected]",
        location=(relative_path, 354, LEDGER_NAME),
    )
    # A same-name item from another module must not supply this ledger's identity.
    decoy = SimpleNamespace(fspath=Path(__file__), name=LEDGER_NAME)
    session, reports = _session(root, items=[decoy, item])
    plugin = ledger_module._LedgerPlugin()
    plugin.calls.required = True
    plugin.calls.expected_ops = ["never_called"]

    plugin.pytest_sessionfinish(session, session.exitstatus)

    assert len(reports) == 1
    assert reports[0].nodeid == item.nodeid
    assert reports[0].location == item.location
    assert reports[0].failed and reports[0].when == "teardown"
    assert session.exitstatus == pytest.ExitCode.TESTS_FAILED


@pytest.mark.parametrize("root_subdir", ["", "python"], ids=["repo-root", "python-root"])
def test_failure_report_falls_back_to_session_root(root_subdir):
    ledger_module = _ledger_module()
    root = REPO_ROOT / root_subdir
    ledger_path = Path(__file__).with_name("test_all_operations_live.py")
    relative_path = ledger_path.relative_to(root).as_posix()
    session, reports = _session(root)
    plugin = ledger_module._LedgerPlugin()
    plugin.calls.required = True
    plugin.calls.expected_ops = ["never_called"]

    plugin.pytest_sessionfinish(session, session.exitstatus)

    assert len(reports) == 1
    assert reports[0].nodeid == f"{relative_path}::{LEDGER_NAME}"
    assert reports[0].location == (relative_path, 0, LEDGER_NAME)
    assert reports[0].failed and reports[0].when == "teardown"
    assert session.exitstatus == pytest.ExitCode.TESTS_FAILED
