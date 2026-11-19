"""Shared pytest setup for python/tests.

The namespace-ownership suites import helpers from sibling test modules by their
bare names (``from test_namespace_ownership_repair import SUPPORTED``). CI runs
``PYTHONPATH=python pytest -q python/tests`` from the repository root, where
pytest imports this package as ``tests.*`` and the bare names do not resolve.
Putting this directory on ``sys.path`` makes both invocations work without
changing how the test modules import their helpers.
"""

from __future__ import annotations

import sys
from pathlib import Path

_TESTS_DIR = str(Path(__file__).resolve().parent)
if _TESTS_DIR not in sys.path:
    sys.path.append(_TESTS_DIR)
