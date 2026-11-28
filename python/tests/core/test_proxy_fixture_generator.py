"""The shared proxy rows (tests/fixtures/loopback/proxy_env.json) are regenerated from CPython and the routers of
httpx and requests by scripts/gen_proxy_env_fixture.py, not from the SDK's own rule; the committed file and its
digest equal that output."""

from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "scripts" / "gen_proxy_env_fixture.py"
FIXTURE = ROOT / "tests" / "fixtures" / "loopback" / "proxy_env.json"


def _generator():
    spec = importlib.util.spec_from_file_location("gen_proxy_env_fixture", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_the_committed_rows_equal_the_regenerated_rows():
    assert _generator().render(_generator().build()) == FIXTURE.read_text(encoding="utf-8")


def test_the_digest_file_matches_the_regenerated_rows():
    text = _generator().render(_generator().build())
    recorded = FIXTURE.with_name(FIXTURE.name + ".sha256").read_text().split()
    assert recorded == [hashlib.sha256(text.encode("utf-8")).hexdigest(), FIXTURE.name]


def test_the_generator_does_not_import_the_code_under_test():
    source = SCRIPT.read_text(encoding="utf-8")
    assert "fi._core" not in source and "from fi" not in source and "import fi" not in source


def test_the_header_does_not_claim_a_row_count():
    assert "16,518" not in json.loads(FIXTURE.read_text(encoding="utf-8"))["description"]
