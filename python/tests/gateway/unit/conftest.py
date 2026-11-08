"""Test setup for the fi.gateway unit suite (ported from agentcc 1.0 at the recorded source).

The fixed CI line installs only futureagi and pytest (no respx, no pytest-asyncio), so:

- **respx** comes from ``../_vendor/respx`` (0.23.1, unmodified, BSD-3-Clause), selected
  only while collecting/running this directory. The installed copy and import path
  are restored before any release tests run. ``FI_GATEWAY_TEST_RESPX=installed``
  uses a pip-installed respx instead; the two runs must pass the same test ids.
- **async tests** run on anyio's pytest plugin (anyio is an httpx dependency): every
  coroutine test here gets ``pytest.mark.anyio``, on the asyncio backend only.
- **warnings are errors** per test, as agentcc's ``filterwarnings = ["error", ...]`` did,
  without touching the shared pytest configuration.
- **no egress**: a socket may connect only to a loopback address.

Each hook touches only the items under this directory, never the rest of the suite.
"""

from __future__ import annotations

import inspect
import ipaddress
import os
import socket
import sys
from contextlib import contextmanager
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
VENDOR = HERE.parent / "_vendor"

_USE_VENDOR = os.environ.get("FI_GATEWAY_TEST_RESPX", "vendored") != "installed"
_VENDOR_MODULES = {}
_VENDOR_ACTIVE = False


def _respx_modules():
    return {
        name: module for name, module in sys.modules.copy().items()
        if name == "respx" or name.startswith("respx.")
    }


@contextmanager
def _unit_respx():
    # respx has absolute internal imports, including runtime imports in Router.
    # Keep one cached vendor module graph, but expose it under the canonical
    # name only during a unit collector/test. Never evict the installed plugin
    # permanently or leave the vendor path in the rest of the suite's sys.path.
    global _VENDOR_ACTIVE
    if not _USE_VENDOR or _VENDOR_ACTIVE:
        yield
        return
    saved_modules = _respx_modules()
    saved_path = sys.path[:]
    _VENDOR_ACTIVE = True
    try:
        for name in saved_modules:
            del sys.modules[name]
        sys.modules.update(_VENDOR_MODULES)
        sys.path.insert(0, str(VENDOR))
        yield
    finally:
        _VENDOR_MODULES.update(_respx_modules())
        for name in _respx_modules():
            del sys.modules[name]
        sys.modules.update(saved_modules)
        sys.path[:] = saved_path
        _VENDOR_ACTIVE = False


@pytest.hookimpl(hookwrapper=True, tryfirst=True)
def pytest_make_collect_report(collector):
    if _ours(collector):
        with _unit_respx():
            yield
    else:
        yield


@pytest.hookimpl(hookwrapper=True, tryfirst=True)
def pytest_runtest_protocol(item, nextitem):
    # Enclose setup AND teardown, not just the test function: fixture imports
    # and respx's decorator/context-manager cleanup need the same module graph.
    if _ours(item):
        with _unit_respx():
            yield
    else:
        yield

_WARNINGS_AS_ERRORS = (
    "error",
    "ignore::pytest.PytestUnraisableExceptionWarning",
)


def _ours(item: pytest.Item) -> bool:
    return HERE in Path(str(item.fspath)).resolve().parents


@pytest.hookimpl(hookwrapper=True)
def pytest_pycollect_makeitem(collector: pytest.Collector, name: str, obj: object):  # type: ignore[no-untyped-def]
    # Mark coroutine tests before anyio's own (tryfirst) hook looks for the mark, so it
    # attaches the ``anyio_backend`` fixture to them; a mark added any later is too late.
    if (
        HERE in Path(str(collector.fspath)).resolve().parents
        and inspect.iscoroutinefunction(obj)
        and not any(m.name == "anyio" for m in getattr(obj, "pytestmark", ()))
    ):
        pytest.mark.anyio(obj)
    yield


def pytest_collection_modifyitems(
    config: pytest.Config, items: list[pytest.Item]
) -> None:
    for item in items:
        if _ours(item):
            for spec in reversed(_WARNINGS_AS_ERRORS):
                item.add_marker(pytest.mark.filterwarnings(spec), append=False)


@pytest.fixture(params=["asyncio"])
def anyio_backend(request: pytest.FixtureRequest) -> str:
    # Parametrized, as anyio's own fixture is, so async ids keep agentcc 1.0's
    # ``[asyncio]`` suffix and map one to one in the port manifest.
    return request.param


def _loopback(address: object) -> bool:
    host = address[0] if isinstance(address, tuple) and address else address
    if host == "localhost":
        return True
    try:
        return ipaddress.ip_address(str(host)).is_loopback
    except ValueError:
        return False


@pytest.fixture(autouse=True)
def _no_egress(monkeypatch: pytest.MonkeyPatch) -> None:
    real_connect = socket.socket.connect
    real_connect_ex = socket.socket.connect_ex

    def guard(address: object) -> None:
        if not _loopback(address):
            raise RuntimeError(
                f"fi.gateway unit tests may not open a network connection to {address!r}"
            )

    def connect(self: socket.socket, address: object) -> None:
        if self.family in (socket.AF_INET, socket.AF_INET6):
            guard(address)
        return real_connect(self, address)  # type: ignore[arg-type]

    def connect_ex(self: socket.socket, address: object) -> int:
        if self.family in (socket.AF_INET, socket.AF_INET6):
            guard(address)
        return real_connect_ex(self, address)  # type: ignore[arg-type]

    monkeypatch.setattr(socket.socket, "connect", connect)
    monkeypatch.setattr(socket.socket, "connect_ex", connect_ex)
