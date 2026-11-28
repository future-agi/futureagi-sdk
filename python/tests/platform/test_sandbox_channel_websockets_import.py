"""The websockets check of the sync channel module runs at that module's import and nowhere an async-only user
imports. Each case is an import in a fresh interpreter.

A websockets that has the redirecting sync connect class but not its ``process_redirect`` hook is built in the
subprocess (no released version is like that), and the released versions are used when a Python that has them is
named in ``FI_TEST_WEBSOCKETS_16`` (websockets 16.1.1) and ``FI_TEST_WEBSOCKETS_17`` (websockets 17.4)."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

PYTHON_DIR = str(Path(__file__).resolve().parents[2])

HOOKLESS = """
import sys, types
import websockets.sync.client as client
class reconnect:
    pass
client.reconnect = reconnect
"""

ASYNC_ONLY = "import fi.sandbox, fi.sandbox._channel._async.stream\nassert 'fi.sandbox._channel._sync.stream' not in sys.modules\n"
SYNC = "import fi.sandbox._channel._sync.stream\n"


def run(python: str, code: str):
    env = {**os.environ, "PYTHONPATH": PYTHON_DIR}
    return subprocess.run([python, "-c", "import sys\n" + code], capture_output=True, text=True, env=env, cwd=PYTHON_DIR)


def test_a_websockets_without_the_redirect_hook_is_refused_from_the_sync_module_only():
    asynchronous = run(sys.executable, HOOKLESS + ASYNC_ONLY)
    assert asynchronous.returncode == 0, asynchronous.stderr
    synchronous = run(sys.executable, HOOKLESS + SYNC)
    assert synchronous.returncode != 0
    assert "ImportError" in synchronous.stderr and "process_redirect" in synchronous.stderr


def test_the_sync_stream_is_reachable_from_the_package_when_the_hook_is_missing():
    code = HOOKLESS + "import fi.sandbox\ntry:\n    fi.sandbox.ExecStream\nexcept ImportError as e:\n    print('ImportError', e)\n"
    result = run(sys.executable, code)
    assert result.returncode == 0, result.stderr
    assert "process_redirect" in result.stdout


@pytest.mark.parametrize("variable", ["FI_TEST_WEBSOCKETS_16", "FI_TEST_WEBSOCKETS_17"])
def test_the_released_websockets_versions_import_in_both_flavours(variable):
    python = os.environ.get(variable)
    if not python:
        pytest.skip(f"{variable} names no Python with that websockets")
    assert run(python, ASYNC_ONLY).returncode == 0
    assert run(python, SYNC).returncode == 0


def test_the_released_versions_and_the_hook():
    python16, python17 = os.environ.get("FI_TEST_WEBSOCKETS_16"), os.environ.get("FI_TEST_WEBSOCKETS_17")
    if not (python16 and python17):
        pytest.skip("FI_TEST_WEBSOCKETS_16 and FI_TEST_WEBSOCKETS_17 are not both set")
    probe = "import websockets.sync.client as c; r = getattr(c, 'reconnect', None); print(hasattr(r, 'process_redirect'))"
    assert run(python16, probe).stdout.strip() == "False"
    assert run(python17, probe).stdout.strip() == "True"
