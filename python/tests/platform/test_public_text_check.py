"""The public-text check that runs in the proof: it flags the words the public text must not carry and reads only added lines."""
import subprocess
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[3] / "scripts" / "check_sdk_public_text.py"


def test_the_checker_flags_what_it_should_and_passes_plain_text():
    done = subprocess.run([sys.executable, str(SCRIPT), "--self-test"], capture_output=True, text=True)
    assert done.returncode == 0, done.stdout + done.stderr
    assert "self-test ok" in done.stdout
