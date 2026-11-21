"""Emit the one missing read-only fixture mount for the v1.59.0 E2E stack.

future-agi#4200 (fb10aa6d2649da92c267c4275198ce91860dd381) added just this
mount. Use the file already in the release checkout, never a later stack or
fixture. Remove this exception when testing a release that contains the fix.
"""
import hashlib
import os
import subprocess
import sys
from pathlib import Path

TAG = "v1.59.0"
COMMIT = "08de8321155538f1a9295982dfd55dd93a1cfc98"
IMAGE = "futureagi/standalone:" + TAG
INDEX = "955911af13d752b0cc8de794e492e24f1c4a67ed04ab80e34392438aa60b58e1"
FIXTURE = "e2e/stack/backend/e2e_legacy_eval.py"
TARGET = "/app/backend/sdk/views/e2e_legacy_eval.py"
FILES = {
    "docker-compose.yml": "9015e1607a43bd71344f1b1f8371f046bbee6a744e271b33f5034a618442a1c7",
    "e2e/stack/docker-compose.standalone-e2e.yml": "77a2cf621851694ff975aa218813ab4b388bdf0fe5d7c062a7fbac317f54b363",
    "e2e/stack/backend/bootstrap_sql.py": "a06b2450979431bd6042fa46b17be9a255caa9a7cd2b287e934e5315cd8a8f6c",
    FIXTURE: "00b4bc3afa3b1252155dffde2373e23e6ef84cd96b14dfb16f259bb6a494899f",
}


def overlay(stack: Path, version: str, ref: str) -> str:
    if version != TAG or ref not in {TAG, "refs/tags/" + TAG, COMMIT}:
        raise ValueError("unsupported release stack pair for the v1.59.0 fixture")
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=stack, text=True).strip()
    if head != COMMIT:
        raise ValueError("release checkout does not resolve to " + COMMIT)
    # Checking both compose files BEFORE merging matters: Compose's keyed merge
    # would silently replace a pre-existing mount at this target.
    for name, expected in FILES.items():
        path = stack / name
        if path.is_symlink() or not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            raise ValueError("release stack input missing or changed: " + name)
    raw = subprocess.check_output(["docker", "buildx", "imagetools", "inspect", "--raw", IMAGE])
    if hashlib.sha256(raw).hexdigest() != INDEX:
        raise ValueError("release image index does not match sha256:" + INDEX)
    # Use the *verified index* for the pull too; a tag can move after inspection.
    # This only binds Compose's image selector, not the app's version variable.
    return f"services:\n  app:\n    image: {IMAGE}@sha256:{INDEX}\n    volumes:\n      - ./{FIXTURE}:{TARGET}:ro\n"


if __name__ == "__main__":
    try:
        sys.stdout.write(overlay(Path.cwd(), os.environ["FUTURE_AGI_VERSION"], os.environ["BACKEND_REF"]))
    except (ValueError, OSError, subprocess.CalledProcessError) as exc:
        sys.exit(str(exc))
