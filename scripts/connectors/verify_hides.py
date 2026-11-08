"""Build each independently hidden feature and verify the wheel/tarball absence."""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tarfile
import tempfile
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "out/hides"
FEATURES = {"oauth_connect": (None, "connect_app", "connectApp"),
            "slack_channels": (None, "slack_channels", "slackChannels"),
            "mcp_core": ("connectors", None, None),
            "data_integrations": ("integrations", None, None),
            "credential_reads": ("credentials", None, None)}


def run(args, cwd, **kw):
    subprocess.run([str(a) for a in args], cwd=cwd, check=True, **kw)


def checkpoint(repo, target):
    """Retained methods keep their wire tests; hidden methods get absence assertions."""
    results = {}
    for version, interpreter in (("312", ROOT / ".venv-conn/bin/python"), ("310", ROOT / ".venv-conn310/bin/python")):
        report = target / f"python{version}.xml"
        with (target / f"python{version}.log").open("w") as log:
            run([interpreter, "-m", "pytest", "tests/connectors", "-q", "-ra", f"--junitxml={report}"], repo / "python",
                env=dict(os.environ, PYTHONPATH=str(repo / "python")), stdout=log, stderr=subprocess.STDOUT)
        suites = ET.parse(report).getroot().findall("testsuite")
        assert all(int(s.get(k, "0")) == 0 for s in suites for k in ("failures", "errors", "skipped"))
        results[f"python{version}"] = sum(int(s.get("tests", "0")) for s in suites)
    report = target / "typescript.json"
    with (target / "typescript.log").open("w") as log:
        run(["pnpm", "exec", "jest", "src/connectors-tests", "--runInBand", "--json", f"--outputFile={report}"],
            repo / "typescript/futureagi", stdout=log, stderr=subprocess.STDOUT)
    result = json.loads(report.read_text())
    assert result["numPendingTests"] == result["numTodoTests"] == result["numFailedTests"] == 0
    results["typescript"] = result["numPassedTests"]
    with (target / "typecheck.log").open("w") as log:
        run(["pnpm", "exec", "tsc", "--noEmit"], repo / "typescript/futureagi", stdout=log, stderr=subprocess.STDOUT)
    return results


def verify(feature, scratch):
    repo = scratch / feature
    # Start from the exact committed tree, not test/build residue in the source copy.
    run(["git", "clone", "--quiet", "--shared", "--no-hardlinks", ROOT, repo], scratch)
    source_head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    assert subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo, text=True).strip() == source_head
    for rel in ("typescript/node_modules", "typescript/futureagi/node_modules"):
        (repo / rel).symlink_to(ROOT / rel, target_is_directory=True)
    hidden = ("mcp_core", "data_integrations", "credential_reads") if feature == "all_off" else (feature,)
    for item in hidden:
        run([sys.executable, "-I", repo / "scripts/connectors/hide.py", item], repo)
    run(["node", repo / "scripts/connectors/generate.mjs", "--check"], repo)
    target = OUT / feature
    target.mkdir(parents=True, exist_ok=True)
    patch = subprocess.check_output(["git", "diff", "--binary"], cwd=repo)
    (target / "hide.patch").write_bytes(patch)
    run(["git", "add", "-u"], repo)
    tree = subprocess.check_output(["git", "write-tree"], cwd=repo, text=True).strip()
    counts = checkpoint(repo, target)
    run([sys.executable, "-m", "build", "--wheel", "--no-isolation", "--outdir", target], repo / "python")
    run(["pnpm", "run", "build"], repo / "typescript/futureagi")
    run(["node", repo / "typescript/futureagi/gateway-client/scripts/stage-package.cjs", target / "candidate"],
        repo, stdout=subprocess.DEVNULL)
    wheel = next(target.glob("*.whl"))
    tarball = next((target / "candidate").glob("*.tgz"))
    removals = [FEATURES[item] for item in hidden]
    absent_features = [name for name, on in json.loads((repo / "openapi/connectors/features.json").read_text()).items() if not on]
    py_tree = scratch / f"{feature}-wheel"
    ts_tree = scratch / f"{feature}-tarball"
    with zipfile.ZipFile(wheel) as archive:
        names = archive.namelist()
        for namespace, _, _ in removals:
            if namespace:
                assert not any(n.startswith(f"fi/{namespace}/") for n in names)
        assert not any(n.endswith(f"connectors/{item}.py") for n in names for item in absent_features)
        archive.extractall(py_tree)
    with tarfile.open(tarball) as archive:
        names = archive.getnames()
        for namespace, _, _ in removals:
            if namespace:
                assert not any(n.startswith(f"package/dist/{fmt}/{namespace}/") for n in names for fmt in ("src", "esm", "esnext"))
        assert not any(f"/generated/connectors/{item}." in n for n in names for item in absent_features)
        archive.extractall(ts_tree, filter="data")
    # Both runtime clients must lack the namespace/method in the installed artifact.
    py_smoke = '''import importlib, sys
sys.path.insert(0, sys.argv[1])
from fi import FutureAGIClient, AsyncFutureAGIClient
namespace, method, group = sys.argv[2:]
for cls in (FutureAGIClient, AsyncFutureAGIClient):
    client = cls(base_url="http://127.0.0.1:9")
    if namespace:
        assert not hasattr(client, namespace)
    else:
        assert not hasattr(getattr(client, group), method)
if namespace:
    try:
        importlib.import_module("fi." + namespace)
    except ModuleNotFoundError:
        pass
    else:
        raise AssertionError("hidden namespace imported")
'''
    group = "connectors" if feature == "oauth_connect" else "integrations"
    for namespace, py_method, _ in removals:
        run([sys.executable, "-I", "-c", py_smoke, py_tree, namespace or "", py_method or "", group], scratch)
    package = ts_tree / "package"
    # Hiding a namespace must remove both modern and legacy declaration routes.
    # Retained parents (including OAuth-only hides) still resolve in every mode.
    absent = [arg for namespace, _, _ in removals if namespace for arg in ("--absent", namespace)]
    with (target / "consumer-resolution.json").open("w") as log:
        run(["node", repo / "scripts/packaging/check-consumer-resolution.cjs", package, *absent],
            scratch, stdout=log)
    (package / "node_modules").symlink_to(ROOT / "typescript/futureagi/node_modules", target_is_directory=True)
    ts_smoke = '''const {createRequire} = require("node:module");
const r = createRequire(process.argv[1] + "/package.json");
const {FutureAGIClient} = r("@future-agi/sdk");
const c = new FutureAGIClient({baseUrl: "http://127.0.0.1:9"});
const [namespace, method, group] = process.argv.slice(2);
if (namespace) {
  if (namespace in c) throw Error("hidden accessor exposed");
  try { r("@future-agi/sdk/" + namespace); throw Error("hidden subpath imported"); }
  catch (e) { if (e.code !== "ERR_PACKAGE_PATH_NOT_EXPORTED") throw e; }
} else if (method in c[group]) throw Error("hidden method exposed");
'''
    for namespace, _, ts_method in removals:
        run(["node", "-e", ts_smoke, package, namespace or "", ts_method or "", group], scratch)
    return {"feature": feature, "tree": tree, "wheel": wheel.name, "tarball": tarball.name, "absence": "PASS", "checkpoint": counts}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    results = []
    with tempfile.TemporaryDirectory(prefix="connector-hide-") as tmp:
        for feature in (*FEATURES, "all_off"):
            results.append(verify(feature, Path(tmp)))
            (OUT / "results.json").write_text(json.dumps(results, indent=2) + "\n")


if __name__ == "__main__":
    main()
