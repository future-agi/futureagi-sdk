"""The futureagi extras that install tracing add-ons (pyproject [tool.poetry.extras]) and the install lines the SDK
prints (``instrument.EXTRAS`` / ``install_line``) agree, and poetry.lock was regenerated with them: an install line
never names an extra that does not exist or that installs another package (the [openai] re-lock, owed since wave 1)."""

import re
import sys
from pathlib import Path

import pytest

from fi.experiments._tracing.instrument import EXTRAS, INSTRUMENTORS, install_line

if sys.version_info >= (3, 11):
    import tomllib
else:  # pragma: no cover - 3.10
    tomllib = pytest.importorskip("tomli")

ROOT = Path(__file__).resolve().parents[3]  # python/
PYPROJECT = tomllib.loads((ROOT / "pyproject.toml").read_text())
EXTRA_DEFS = PYPROJECT["tool"]["poetry"]["extras"]
LOCK = (ROOT / "poetry.lock").read_text()


def _norm(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name).lower()


@pytest.mark.parametrize("name", sorted(EXTRAS))
def test_each_extra_the_sdk_names_exists_and_installs_its_instrumentor(name):
    extra = EXTRAS[name]
    pkg = INSTRUMENTORS[name][2]
    assert extra in EXTRA_DEFS, f"[{extra}] is not a futureagi extra"
    assert _norm(pkg) in {_norm(p) for p in EXTRA_DEFS[extra]}
    assert "fi-instrumentation-otel" in EXTRA_DEFS[extra] and "python-dotenv" in EXTRA_DEFS[extra]
    assert install_line(name) == f'pip install "futureagi[{extra}]"'


@pytest.mark.parametrize("name", sorted(EXTRAS))
def test_the_lock_holds_each_extra_and_its_package(name):
    extra, pkg = EXTRAS[name], INSTRUMENTORS[name][2]
    locked = re.search(r"^\[extras\]\n(.*?)(?:\n\n|\Z)", LOCK, re.S | re.M)
    assert locked and re.search(rf"^{re.escape(extra)} = \[", locked.group(1), re.M), f"poetry.lock has no [{extra}]"
    assert f'name = "{_norm(pkg)}"' in LOCK


def test_the_openai_extra_is_traceai_openai_and_anthropic_has_none():
    assert EXTRAS["openai"] == "openai" and "traceAI-openai" in EXTRA_DEFS["openai"]
    # traceAI-anthropic 0.1.10 cannot import with anthropic>=1.0 (F3): an [anthropic] extra would install it broken
    assert "anthropic" not in EXTRAS and "anthropic" not in EXTRA_DEFS
    assert install_line("anthropic") == "pip install traceAI-anthropic"
