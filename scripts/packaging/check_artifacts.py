#!/usr/bin/env python3
"""Check exact runtime file sets, the shipped gateway client and disabled namespaces in candidate archives.

Usage: python check_artifacts.py REPO WHEEL SDIST NPM_TARBALL OUTPUT_JSON
Archives are inspected in memory, never extracted or imported.
"""
import email
import hashlib
import importlib.util
import json
from pathlib import Path, PurePosixPath
import sys
import subprocess
import tarfile
import zipfile

_sandbox_spec = importlib.util.spec_from_file_location(
    "check_sandbox_absence", Path(__file__).with_name("check_sandbox_absence.py")
)
_sandbox_gate = importlib.util.module_from_spec(_sandbox_spec)
_sandbox_spec.loader.exec_module(_sandbox_gate)
check_sandbox_absence = _sandbox_gate.check_sandbox_absence

# The gateway data-plane client ships in both SDKs:
# five subpaths resolved with the default import/require conditions only.
GATEWAY_SUBPATHS = ("./gateway", "./gateway/testing", "./gateway/express", "./gateway/nextjs", "./gateway/react")
GATEWAY_TYPES = {
    "gateway": ["./dist/gateway/cjs/index.d.ts"],
    "gateway/testing": ["./dist/gateway/cjs/testing.d.ts"],
    "gateway/express": ["./dist/gateway/cjs/express.d.ts"],
    "gateway/nextjs": ["./dist/gateway/cjs/nextjs.d.ts"],
    "gateway/react": ["./dist/gateway/cjs/react/index.d.ts"],
}


def digest(path):
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def safe_names(names):
    assert len(names) == len(set(names)), "Duplicate archive members"
    for name in names:
        path = PurePosixPath(name)
        assert not path.is_absolute() and ".." not in path.parts, name


def read_tar(path):
    with tarfile.open(path) as archive:
        safe_names([m.name for m in archive.getmembers()])
        assert not any(m.issym() or m.islnk() for m in archive.getmembers())
        return {m.name: archive.extractfile(m).read() for m in archive.getmembers() if m.isfile()}


def same_files(label, actual, expected):
    missing, extra = sorted(expected - actual), sorted(actual - expected)
    assert not missing and not extra, f"{label}: missing={missing}, extra={extra}"


def main(repo, wheel, sdist, tarball, output):
    repo, wheel, sdist, tarball, output = map(Path, (repo, wheel, sdist, tarball, output))
    with zipfile.ZipFile(wheel) as archive:
        safe_names(archive.namelist())
        whl = {name: archive.read(name) for name in archive.namelist() if not name.endswith("/")}
    source = read_tar(sdist)
    npm = read_tar(tarball)
    spec = importlib.util.spec_from_file_location("check_ownership", Path(__file__).with_name("check_ownership.py"))
    ownership_gate = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(ownership_gate)
    ownership_gate.check_combination([wheel])
    fi = repo / "python" / "fi"
    expected = {
        "fi/" + p.relative_to(fi).as_posix() for p in fi.rglob("*")
        if p.is_file() and "__pycache__" not in p.parts and p.suffix != ".pyc"
        and not p.relative_to(fi).as_posix().startswith("integrations/otel/")
    }
    same_files("wheel fi", {p for p in whl if p.startswith("fi/")}, expected)
    source_runtime = {p.split("/", 1)[1] for p in source if "/fi/" in p}
    same_files("sdist fi", source_runtime, expected)
    # agent-learning-kit alone owns fi.alk; the SDK must not even ship an error stub.
    assert not (fi / "alk").exists(), "SDK source tree must not contain fi/alk"
    assert not any(p.startswith("fi/alk/") for p in whl), "SDK wheel must not contain fi/alk"
    assert not any(p.startswith("fi/alk/") for p in source_runtime), "SDK sdist must not contain fi/alk"
    assert "fi/py.typed" in whl
    metadata_path, = [p for p in whl if p.endswith(".dist-info/METADATA")]
    metadata = email.message_from_bytes(whl[metadata_path])
    assert metadata["Name"] == "futureagi" and metadata["Version"] == "0.7.0"
    assert metadata["Requires-Python"] == ">=3.10"
    assert any(d.startswith("anyio ") or d.startswith("anyio(") or d.startswith("anyio (") for d in metadata.get_all("Requires-Dist", []))
    assert not any("ai-evaluation" in d for d in metadata.get_all("Requires-Dist", []))
    assert not any("3.14" in c for c in metadata.get_all("Classifier", []))
    assert "fi/gateway/__init__.py" in whl, "Missing gateway client in the wheel"
    assert any(p.endswith("/fi/gateway/__init__.py") for p in source), "Missing gateway client in the sdist"
    assert not any("/fi/integrations/otel/" in "/" + p for p in whl)
    assert not any("/fi/integrations/otel/" in p for p in source)
    for path in whl:
        assert path.startswith(("fi/", "futureagi-0.7.0.dist-info/")), path
    for path in source:
        relative = path.split("/", 1)[1]
        # Runtime modules only: no test suites or vendored test fixtures (python/tests/gateway/_vendor).
        assert relative.startswith("fi/") or relative in {
            "pyproject.toml", "README.md", "CHANGELOG.md", "LICENSE", "NOTICE", "PKG-INFO"
        }, path

    pkg = json.loads(npm["package/package.json"])
    assert pkg["name"] == "@future-agi/sdk" and pkg["version"] == "0.2.0"
    features = json.loads((repo / "openapi/connectors/features.json").read_text())
    connector_namespaces = {"mcp_core": "connectors", "data_integrations": "integrations", "credential_reads": "credentials"}
    assert all(type(features[feature]) is bool for feature in connector_namespaces)
    assert "typesVersions" in pkg and isinstance(pkg["typesVersions"], dict) and pkg["typesVersions"], "typesVersions must be present and nonempty"
    assert all(isinstance(mapping, dict) and mapping for mapping in pkg["typesVersions"].values()), "typesVersions mappings must be nonempty"
    expected_exports = {".", "./webhooks", *GATEWAY_SUBPATHS}
    expected_exports.update("./" + namespace for feature, namespace in connector_namespaces.items() if features[feature])
    for feature, namespace in connector_namespaces.items():
        if not features[feature]:
            assert not any(path.startswith(f"fi/{namespace}/") for path in whl)
            assert not any(f"/fi/{namespace}/" in path for path in source)
            assert not any(path.startswith(f"package/dist/{fmt}/{namespace}/") for path in npm for fmt in ("esm", "src", "esnext")), f"Hidden npm namespace: {namespace}"
        for mapping in pkg["typesVersions"].values():
            assert (namespace in mapping) is features[feature], f"typesVersions availability: {namespace}"
    if not features["credential_reads"]:
        hidden_types = ("ListWorkspaceCredentialsResponse", "GetWorkspaceCredentialResponse", "ListWorkspaceCredentialBindingsResponse", "Workspace Credentials")
        for fmt in ("esm", "esnext", "src"):
            declarations = [content for name, content in npm.items() if name.startswith(f"package/dist/{fmt}/") and name.endswith(".d.ts")]
            assert declarations, f"Missing {fmt} declarations"
            for content in declarations:
                assert not any(name.encode() in content for name in hidden_types), f"Hidden credential declaration in {fmt}"
    if (repo / "typescript/futureagi/src/agents/runs/index.ts").is_file():
        expected_exports.add("./agents/runs")
    assert set(pkg["exports"]) == expected_exports, "Exact feature-derived exports"
    boundary_spec = importlib.util.spec_from_file_location(
        "check_gateway_boundaries", Path(__file__).with_name("check_gateway_boundaries.py")
    )
    boundary = importlib.util.module_from_spec(boundary_spec)
    boundary_spec.loader.exec_module(boundary)
    boundary.check_gateway_boundaries(whl, source, npm)
    assert not any(
        part == "evals" or part.startswith("evals.")
        for path in npm if path.startswith("package/dist/") for part in PurePosixPath(path).parts
    ), "Disabled evaluation runner is present in the npm artifact"
    assert not any("evals" in key for mapping in pkg.get("typesVersions", {}).values() for key in mapping)
    for mapping in pkg["typesVersions"].values():
        assert {key: mapping.get(key) for key in GATEWAY_TYPES} == GATEWAY_TYPES, "Gateway typesVersions mappings"
    for key in GATEWAY_SUBPATHS:
        assert set(pkg["exports"][key]) == {"import", "require"}, "Gateway subpaths resolve with default conditions: " + key
    assert pkg.get("peerDependencies") == {"react": ">=17.0.0 <20"}, "React is the only peer"
    assert pkg.get("peerDependenciesMeta") == {"react": {"optional": True}}, "The React peer stays optional"
    assert not pkg.get("scripts")
    dist = repo / "typescript" / "futureagi" / "dist"
    expected_dist = set()
    for dirname in ("esm", "src", "esnext", "gateway"):
        for path in (dist / dirname).rglob("*"):
            if not path.is_file():
                continue
            relative = path.relative_to(dist).as_posix()
            if "__tests__" in path.parts or ".test." in path.name or ".spec." in path.name or path.suffix == ".tsbuildinfo":
                continue
            if any(part == "evals" or part.startswith("evals.") for part in PurePosixPath(relative).parts):
                continue
            expected_dist.add("package/dist/" + relative)
    same_files("npm dist", {p for p in npm if p.startswith("package/dist/")}, expected_dist)
    same_files("npm root", {p for p in npm if not p.startswith("package/dist/")}, {
        "package/package.json", "package/README.md", "package/CHANGELOG.md", "package/LICENSE", "package/NOTICE"
    })
    for entry in pkg["exports"].values():
        for condition in ("import", "require"):
            for target in entry[condition].values():
                assert "package/" + target.removeprefix("./") in npm, target
    check_sandbox_absence(whl, source, npm)
    subprocess.run([
        sys.executable, "-I", str(repo / "scripts/packaging/check_deployments_absent.py"),
        str(wheel), str(sdist), str(tarball),
    ], check=True)
    result = {"gateway": "on", "sandboxes": "off", "deployments": "off", "artifacts": [
        {"name": str(path.name), "digest": digest(path), "files": sorted(files)}
        for path, files in ((wheel, whl), (sdist, source), (tarball, npm))
    ]}
    output.write_text(json.dumps(result, indent=2) + "\n")
    print("Exact runtime inventories, metadata, gateway presence and disabled-namespace absence: PASS")


if __name__ == "__main__":
    main(*sys.argv[1:])
