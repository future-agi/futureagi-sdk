"""Copy a pulled E-OLD recording into the repository and write golden/MANIFEST.json.

    python3 -I tests/fixtures/gateway/e-old/install_goldens.py <pulled out-dir> <repo root>

<pulled out-dir> is record-e-old.sh's output, copied back from the VM: run1/ and
run2/ (the two recordings), byte-identity.txt, fetch/ (registry evidence) and
npm-locks/. Only run 1 is copied (run 2 is byte-identical by then; it was
recorded from another checkout path with relocated installs); the manifest
records every golden file's sha256 and the identity check's counts. Raw
registry answers (they carry maintainer e-mail addresses) are not copied.
"""

from __future__ import annotations

import hashlib
import json
import shutil
import sys
from pathlib import Path


def main(argv: list[str]) -> int:
    pulled, repo = Path(argv[1]), Path(argv[2])
    fixtures = repo / "tests" / "fixtures" / "gateway"
    golden = fixtures / "golden"
    lines = (pulled / "byte-identity.txt").read_text().splitlines()
    # DIFFERENT (one file), FILE SETS DIFFER, VENVS DIFFER (run 2's venv)
    different = sum(1 for line in lines if "DIFFER" in line)
    if different:
        print(
            f"refusing: {different} files differ between run 1 and run 2",
            file=sys.stderr,
        )
        return 1
    for target in sorted(p.name for p in (pulled / "run1").iterdir()):
        dest = golden / target
        if dest.exists():
            shutil.rmtree(dest)
        shutil.copytree(pulled / "run1" / target, dest)
    for name in ("artifacts.json", "registry-npm.json"):
        shutil.copy2(pulled / "fetch" / name, fixtures / "e-old" / name)
    for lock in sorted((pulled / "npm-locks").glob("*/package-lock.json")):
        shutil.copy2(
            lock, fixtures / "e-old" / "npm" / lock.parent.name / "package-lock.json"
        )
    files = {
        str(p.relative_to(golden)): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in sorted(golden.rglob("*.json"))
        if p.name != "MANIFEST.json"
    }
    environments = {}
    for target in sorted(p.name for p in golden.iterdir() if p.is_dir()):
        environments[target] = json.loads((golden / target / "index.json").read_text())[
            "environment"
        ]
    manifest = {
        "about": "sha256 of every golden file; the goldens are run 1 of two recordings in fresh processes that cmp found byte-identical (tests/fixtures/gateway/e-old/record-e-old.sh).",
        "files": files,
        "goldens": environments,
        "byte_identity": {
            "runs": 2,
            "files": len(lines),
            "different": different,
            "run2": "recorded from a copy of the recorders at another checkout path, with the npm installs copied and the venv built again at another path",
        },
    }
    (golden / "MANIFEST.json").write_text(
        json.dumps(manifest, indent=1, sort_keys=True) + "\n"
    )
    print(f"installed {len(environments)} goldens, {len(files)} files")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
