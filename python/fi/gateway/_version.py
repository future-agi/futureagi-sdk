"""The gateway client's version: the installed futureagi distribution's version.

Read from the distribution metadata, not from ``fi/__init__``: another distribution
(agent-learning-kit) installs its own ``fi/__init__.py`` over ours. A source
tree without installed metadata reads the version from ``python/pyproject.toml``.
"""

from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version
from pathlib import Path


def futureagi_version() -> str:
    try:
        return version("futureagi")
    except PackageNotFoundError:
        pass
    pyproject = Path(__file__).resolve().parents[2] / "pyproject.toml"
    try:
        lines = pyproject.read_text(encoding="utf-8").splitlines()
    except OSError:
        return "unknown"
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("version = "):
            return stripped.split("=", 1)[1].strip().strip('"').strip("'")
    return "unknown"
