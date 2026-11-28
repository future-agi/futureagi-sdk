"""Remove disabled credential reads using the canonical public scope projection."""
import json
from pathlib import Path
import subprocess

READS = {"platform.credentials.bindings", "platform.credentials.get", "platform.credentials.list"}


def hide_platform_credentials(root: Path) -> None:
    scope_path = root / "openapi/platform/scope.json"
    scope = json.loads(scope_path.read_text())
    present = READS & set(scope["operations"])
    if not present:
        return
    if present != READS:
        raise ValueError("Credential read scope is incomplete")
    scope["operations"] = [name for name in scope["operations"] if name not in READS]
    subprocess.run([
        "node", str(Path(__file__).with_name("project_platform_scope.mjs")), str(root),
    ], input=json.dumps(scope), text=True, check=True)
