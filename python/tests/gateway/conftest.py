"""Asyncio ownership for the released, top-level gateway tests.

The shared pytest configuration must use asyncio_mode = "strict": the unit
unit/ suite uses anyio, not pytest-asyncio. Give only the released coroutine
tests the explicit asyncio mark that replaces their former global auto mode.
Existing anyio marks/parametrization are retained, as in the release auto mode.
There are no inherited autouse fixtures or process-wide plugin changes here.
"""

from __future__ import annotations

import inspect
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent


@pytest.fixture
def wire_snapshot():
    """Opt-in send-time capture, shared with the published-contract helpers.

    Call this from a mock transport handler, before returning its response.
    The independent request preserves wire assertions without interfering with
    the SDK's scrubbing of the original request after dispatch.
    """
    from ._wire_capture import wire_snapshot as snapshot

    return snapshot


@pytest.hookimpl(hookwrapper=True)
def pytest_pycollect_makeitem(collector: pytest.Collector, name: str, obj: object):
    # Before pytest-asyncio converts marked coroutines into runnable items. A
    # collection_modifyitems mark would be too late for strict-mode conversion.
    if (
        Path(str(collector.fspath)).resolve().parent == HERE
        and inspect.iscoroutinefunction(obj)
        and not any(m.name == "asyncio" for m in getattr(obj, "pytestmark", ()))
    ):
        pytest.mark.asyncio(obj)
    yield
