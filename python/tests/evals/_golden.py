"""The recording of ai-evaluation 1.1.0 (``record_upstream.py`` writes it; it is never edited by hand)."""

from __future__ import annotations

import functools
import json
from pathlib import Path
from typing import Any, Dict

FIXTURES = Path(__file__).resolve().parent / "fixtures"
GOLDEN = FIXTURES / "golden-ai-evaluation-1.1.0.json"


@functools.lru_cache(maxsize=1)
def golden() -> Dict[str, Any]:
    if not GOLDEN.exists():
        raise AssertionError(f"{GOLDEN.name} is missing: record it with record_upstream.py on ai-evaluation 1.1.0")
    data = json.loads(GOLDEN.read_text())
    installed = data["installed"]
    assert installed["version"] == "1.1.0" and installed["mismatched"] == [], (
        "the golden file was not recorded on the exact published 1.1.0 files"
    )
    return data


@functools.lru_cache(maxsize=1)
def census() -> Dict[str, Any]:
    return json.loads((FIXTURES / "census-fi-evals.json").read_text())
