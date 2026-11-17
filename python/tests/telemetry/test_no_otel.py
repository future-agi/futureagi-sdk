import os
from pathlib import Path
import subprocess
import sys


def test_resolve_read_all_without_otel_or_threads():
    # Run this suite in a clean SDK+pytest environment as well. A finder makes
    # accidental OTel imports fail even when the main suite has OTel installed.
    script = r'''
import importlib.abc
import sys
import threading
class NoOTel(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname.startswith("opentelemetry"):
            raise AssertionError("OpenTelemetry imported by SDK")
sys.meta_path.insert(0, NoOTel())
from conftest import Source
from fi.context.client import SnapshotClient
before = set(threading.enumerate())
source = Source()
snapshot = SnapshotClient(source, kind="skill").resolve("refund")
assert snapshot.read_all().files["SKILL.md"] == "Refund instructions"
assert not any(key.startswith("opentelemetry") for key in sys.modules)
assert not any(key == "fi.telemetry._registry" for key in sys.modules)
assert set(threading.enumerate()) == before
'''
    env = dict(os.environ)
    env["PYTHONPATH"] = os.pathsep.join([str(Path(__file__).parent), str(Path(__file__).parents[2])])
    subprocess.run([sys.executable, "-c", script], env=env, check=True, capture_output=True, text=True)
