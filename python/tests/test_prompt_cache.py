"""Tests for fi.prompt.cache."""

import subprocess
import sys


def test_importing_fi_prompt_spawns_no_threads():
    code = "import threading, fi.prompt; print([t.name for t in threading.enumerate()])"
    result = subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True, text=True, check=True,
    )
    assert "PromptCacheWorker" not in result.stdout
