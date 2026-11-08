"""Run the full connector checkpoint on each independent source hide (cloud only)."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "out/hidden-contracts"
FEATURES = ("oauth_connect", "slack_channels", "mcp_core", "data_integrations", "credential_reads")


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    results = []
    with tempfile.TemporaryDirectory(prefix="hidden-contracts-") as scratch:
        for feature in FEATURES:
            repo = Path(scratch) / feature
            shutil.copytree(ROOT, repo, ignore=shutil.ignore_patterns(".git", "node_modules", ".venv*", "dist", "out", "__pycache__", "*.pyc"))
            subprocess.run([sys.executable, "-I", str(repo / "scripts/connectors/hide.py"), feature], check=True)
            env = dict(os.environ, PYTHONPATH=str(repo / "python"))
            row = {"feature": feature}
            # Keep the cross-map check independent of collection errors in the old suite.
            for label, tests in (("maps", ["tests/connectors/test_wrapper_maps.py"]), ("checkpoint", ["tests/connectors"])):
                with (OUT / f"{feature}-{label}.log").open("w") as log:
                    outcome = subprocess.run([sys.executable, "-m", "pytest", *tests, "-q", "-ra"], cwd=repo / "python", env=env, stdout=log, stderr=subprocess.STDOUT)
                row[label] = outcome.returncode
            results.append(row)
            (OUT / "results.json").write_text(json.dumps(results, indent=2) + "\n")
    return int(any(r["maps"] or r["checkpoint"] for r in results))


if __name__ == "__main__":
    sys.exit(main())
