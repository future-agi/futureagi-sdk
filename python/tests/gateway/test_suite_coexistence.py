"""Regression coverage for directory-local test setup (no SDK calls)."""

from __future__ import annotations

import importlib
import os
import socket
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from tests.gateway import conftest as released
from tests.gateway.unit import conftest as unit
from tests.platform import conftest as platform


def _marks(fn):
    return {mark.name for mark in getattr(fn, "pytestmark", ())}


def test_release_coroutines_get_asyncio_without_marking_unit_coroutines():
    async def release_test():
        pass

    async def unit_test():
        pass

    release_collector = SimpleNamespace(fspath=released.HERE / "test_probe.py")
    unit_collector = SimpleNamespace(fspath=unit.HERE / "test_probe.py")
    list(released.pytest_pycollect_makeitem(release_collector, "test_probe", release_test))
    list(released.pytest_pycollect_makeitem(unit_collector, "test_probe", unit_test))
    assert _marks(release_test) == {"asyncio"}
    assert _marks(unit_test) == set()
    list(unit.pytest_pycollect_makeitem(unit_collector, "test_probe", unit_test))
    assert _marks(unit_test) == {"anyio"}


def test_unit_hook_does_not_mark_a_release_coroutine():
    async def release_test():
        pass

    collector = SimpleNamespace(fspath=released.HERE / "test_probe.py")
    list(unit.pytest_pycollect_makeitem(collector, "test_probe", release_test))
    assert _marks(release_test) == set()


def test_respx_selection_restores_the_release_module_graph_and_import_path():
    import sys

    installed = importlib.import_module("respx")
    before_modules = unit._respx_modules()
    before_path = sys.path[:]
    with unit._unit_respx():
        selected = importlib.import_module("respx")
        from_vendor = Path(selected.__file__).resolve().parent == unit.VENDOR / "respx"
        assert from_vendor == unit._USE_VENDOR
        with unit._unit_respx():
            assert importlib.import_module("respx") is selected
    assert importlib.import_module("respx") is installed
    assert unit._respx_modules() == before_modules
    assert sys.path == before_path

    # The unit tests' imported decorators and runtime imports share one graph.
    with unit._unit_respx():
        assert importlib.import_module("respx") is selected
    assert importlib.import_module("respx") is installed


def test_platform_live_exemption_is_limited_to_the_released_modules():
    for name in ("test_all_operations_live.py", "test_datasets_live.py"):
        assert platform._is_live(SimpleNamespace(fspath=platform.HERE / name))
    assert not platform._is_live(SimpleNamespace(fspath=platform.HERE / "test_transport.py"))
    assert not platform._is_live(SimpleNamespace(fspath=platform.HERE / "unit" / "test_datasets_live.py"))
    assert not platform._is_live(SimpleNamespace(fspath=released.HERE / "test_datasets_live.py"))


def test_platform_env_file_values_are_restored_after_a_live_fixture(monkeypatch, tmp_path):
    import os

    env_file = tmp_path / "live-test.env"
    env_file.write_text("TEST_PLATFORM_ENV_NEW=loaded\nTEST_PLATFORM_ENV_EXISTING=file\n")
    monkeypatch.setattr(platform, "ENV_FILE", env_file)
    monkeypatch.delenv("TEST_PLATFORM_ENV_NEW", raising=False)
    monkeypatch.setenv("TEST_PLATFORM_ENV_EXISTING", "caller")
    with monkeypatch.context() as live_patch:
        platform._load_env_file(live_patch)
        assert os.environ["TEST_PLATFORM_ENV_NEW"] == "loaded"
        assert os.environ["TEST_PLATFORM_ENV_EXISTING"] == "caller"
    assert "TEST_PLATFORM_ENV_NEW" not in os.environ
    assert os.environ["TEST_PLATFORM_ENV_EXISTING"] == "caller"


def _platform_request(name="test_datasets_live.py"):
    # The dataset module includes a test that never requests the client fixture.
    return SimpleNamespace(node=SimpleNamespace(fspath=platform.HERE / name))


def _set_opt_in(monkeypatch, value):
    monkeypatch.delenv("FI_E2E_REQUIRED", raising=False)
    if value is not None:
        monkeypatch.setenv("FI_E2E_REQUIRED", value)


@pytest.mark.parametrize("name", sorted(platform._LIVE_MODULES))
@pytest.mark.parametrize("opt_in", [None, ""])
@pytest.mark.parametrize("has_keys", [False, True])
def test_platform_without_opt_in_skips_before_reading_credentials(monkeypatch, name, opt_in, has_keys):
    _set_opt_in(monkeypatch, opt_in)
    monkeypatch.setenv("FI_BASE_URL", "http://localhost:8100")
    for key in ("FI_API_KEY", "FI_SECRET_KEY"):
        monkeypatch.delenv(key, raising=False)
        if has_keys:
            monkeypatch.setenv(key, "test-placeholder")
    reader = Mock(side_effect=AssertionError("credential file must not be read"))
    exists = Mock(return_value=True)
    monkeypatch.setattr(platform, "ENV_FILE", SimpleNamespace(exists=exists, read_text=reader))

    with pytest.raises(pytest.skip.Exception, match="explicit opt-in.*FI_E2E_REQUIRED=1"):
        platform._live_environment.__wrapped__(_platform_request(name), monkeypatch, None)
    exists.assert_not_called()
    reader.assert_not_called()


@pytest.mark.parametrize("opt_in", [None, "", "1", "0"])
def test_platform_collection_skips_live_items_only_without_release_opt_in(monkeypatch, opt_in):
    _set_opt_in(monkeypatch, opt_in)
    items, marks = [], {}
    for name in (*sorted(platform._LIVE_MODULES), "test_transport.py"):
        marks[name] = []
        items.append(SimpleNamespace(fspath=platform.HERE / name, add_marker=marks[name].append))
    platform.pytest_collection_modifyitems(None, items)
    for name in platform._LIVE_MODULES:
        assert "platform_live" in {mark.name for mark in marks[name]}
        skipped = [mark for mark in marks[name] if mark.name == "skip"]
        assert bool(skipped) == (not bool(opt_in))
        if skipped:
            assert skipped[0].kwargs["reason"] == platform._LIVE_SKIP_REASON
    assert [mark.name for mark in marks["test_transport.py"]] == ["platform_offline"]


@pytest.mark.parametrize("name,opt_in", [
    ("test_all_operations_live.py", None),
    ("test_datasets_live.py", None),
    ("test_datasets_live.py", ""),
    ("test_transport.py", None),
    ("test_transport.py", "1"),
])
def test_platform_default_denied_and_offline_tests_keep_the_real_guard(monkeypatch, tmp_path, name, opt_in):
    _set_opt_in(monkeypatch, opt_in)
    monkeypatch.setenv("FI_API_KEY", "test-placeholder")
    monkeypatch.setenv("FI_SECRET_KEY", "test-placeholder")
    install = Mock(wraps=platform._egress.install)
    finish = Mock(wraps=platform._egress.assert_no_attempts)
    monkeypatch.setattr(platform._egress, "install", install)
    monkeypatch.setattr(platform._egress, "assert_no_attempts", finish)
    connect, resolve = socket.socket.connect, socket.getaddrinfo
    guard = platform._no_egress.__wrapped__(_platform_request(name), monkeypatch, tmp_path)
    next(guard)
    try:
        install.assert_called_once_with(monkeypatch, tmp_path)
        assert socket.socket.connect is not connect
        assert socket.getaddrinfo is not resolve
        assert "FI_API_KEY" not in os.environ and "FI_SECRET_KEY" not in os.environ
        assert os.environ["FI_BASE_URL"] == "http://127.0.0.1:9"
    finally:
        with pytest.raises(StopIteration):
            next(guard)
    finish.assert_called_once_with()


@pytest.mark.parametrize("opt_in", ["1", "0", "false"])
def test_platform_opt_in_loads_defaults_restores_them_and_exempts_live_only(monkeypatch, tmp_path, opt_in):
    _set_opt_in(monkeypatch, opt_in)
    monkeypatch.delenv("FI_API_KEY", raising=False)
    monkeypatch.delenv("FI_SECRET_KEY", raising=False)
    monkeypatch.setenv("FI_BASE_URL", "http://localhost:8100")
    reader = Mock(return_value=(
        "FI_API_KEY=test-api-placeholder\nFI_SECRET_KEY=test-secret-placeholder\n"
        "FI_BASE_URL=http://127.0.0.1:8100\n"
    ))
    monkeypatch.setattr(platform, "ENV_FILE", SimpleNamespace(exists=lambda: True, read_text=reader))
    install = Mock(side_effect=AssertionError("opted-in live tests must retain release environment"))
    monkeypatch.setattr(platform._egress, "install", install)
    request = _platform_request()
    assert platform._live_enabled(request.node)
    assert not platform._live_enabled(_platform_request("test_transport.py").node)
    with monkeypatch.context() as live_patch:
        guard = platform._no_egress.__wrapped__(request, live_patch, tmp_path)
        next(guard)
        try:
            platform._live_environment.__wrapped__(request, live_patch, None)
            reader.assert_called_once_with()
            install.assert_not_called()
            assert os.environ["FI_API_KEY"] == "test-api-placeholder"
            assert os.environ["FI_SECRET_KEY"] == "test-secret-placeholder"
            assert os.environ["FI_BASE_URL"] == "http://localhost:8100"
        finally:
            with pytest.raises(StopIteration):
                next(guard)
    assert "FI_API_KEY" not in os.environ and "FI_SECRET_KEY" not in os.environ
    assert os.environ["FI_BASE_URL"] == "http://localhost:8100"
    assert os.environ["FI_E2E_REQUIRED"] == opt_in


@pytest.mark.parametrize("name", sorted(platform._LIVE_MODULES))
@pytest.mark.parametrize("missing", ["FI_API_KEY", "FI_SECRET_KEY", "FI_BASE_URL"])
@pytest.mark.parametrize("opt_in", ["1", "0"])
def test_platform_required_live_setup_fails_without_any_required_value(monkeypatch, name, missing, opt_in):
    _set_opt_in(monkeypatch, opt_in)
    for key, value in {
        "FI_API_KEY": "test-api-placeholder",
        "FI_SECRET_KEY": "test-secret-placeholder",
        "FI_BASE_URL": "http://localhost:8100",
    }.items():
        monkeypatch.setenv(key, value)
    monkeypatch.delenv(missing)
    reader = Mock(return_value="")
    monkeypatch.setattr(platform, "ENV_FILE", SimpleNamespace(exists=lambda: True, read_text=reader))
    with pytest.raises(pytest.fail.Exception, match="no backend configured"):
        platform._live_environment.__wrapped__(_platform_request(name), monkeypatch, None)
    reader.assert_called_once_with()


@pytest.mark.parametrize("opt_in", [None, "", "1", "0"])
def test_platform_backend_requirement_retains_release_fail_or_skip_semantics(monkeypatch, opt_in):
    _set_opt_in(monkeypatch, opt_in)
    for key in ("FI_API_KEY", "FI_SECRET_KEY", "FI_BASE_URL"):
        monkeypatch.delenv(key, raising=False)
    outcome = pytest.fail.Exception if opt_in else pytest.skip.Exception
    with pytest.raises(outcome, match="no backend configured"):
        platform._require_backend()


@pytest.mark.parametrize("name,opt_in", [
    ("test_datasets_live.py", None),
    ("test_transport.py", "1"),
])
def test_platform_non_live_setup_never_loads_credentials_or_instruments(monkeypatch, name, opt_in):
    _set_opt_in(monkeypatch, opt_in)
    reader = Mock(side_effect=AssertionError("credential file must not be read"))
    monkeypatch.setattr(platform, "ENV_FILE", SimpleNamespace(exists=lambda: True, read_text=reader))
    request = _platform_request(name)
    if name == "test_transport.py":
        platform._live_environment.__wrapped__(request, monkeypatch, None)
    recorder = platform.record_calls.__wrapped__(request, monkeypatch, None)
    assert next(recorder) is None
    with pytest.raises(StopIteration):
        next(recorder)
    reader.assert_not_called()
