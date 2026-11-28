"""Synthetic candidate archives exercise the checker without builds or installs.

The real ownership checker verifies RECORD and all ordinary namespace paths. A
fixture-only wrapper admits the two exact guard paths pending their separate
ownership-manifest change; it does not admit other root modules or .pth files.
Only the gateway-content checker and the deployment subprocess are replaced by
call-recording stubs: these fixtures are not executable gateway distributions.
Actual built-archive proof must run those boundaries without these test doubles.
"""

import base64
import copy
import csv
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import tarfile
from types import SimpleNamespace
import zipfile

import pytest


REPO = Path(__file__).resolve().parents[3]
GUARDS = {"_futureagi_namespace_guard.py", "futureagi_namespace_guard.pth"}
CONNECTORS = {
    "mcp_core": "connectors",
    "data_integrations": "integrations",
    "credential_reads": "credentials",
}
GATEWAYS = {
    "gateway": "index",
    "gateway/testing": "testing",
    "gateway/express": "express",
    "gateway/nextjs": "nextjs",
    "gateway/react": "react/index",
}


def _write(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)


def _metadata(version):
    return (
        "Metadata-Version: 2.1\nName: futureagi\n"
        f"Version: {version}\nRequires-Python: >=3.10\n"
        "Requires-Dist: anyio (>=4.14.2,<5.0)\n\n"
    ).encode()


def _tar(path, files):
    with tarfile.open(path, "w:gz") as archive:
        for name, content in sorted(files.items()):
            info = tarfile.TarInfo(name)
            info.size = len(content)
            archive.addfile(info, io.BytesIO(content))


def _package(version, features):
    entries = {
        ".": "index",
        "./platform": "platform/index",
        "./platform/models": "platform/models",
        "./webhooks": "webhooks/index",
        "./agents/runs": "agents/runs/index",
        "./sandbox": "sandbox/index",
        "./sandbox/ai-sdk": "sandbox-integrations/ai-sdk/index",
    }
    entries.update(
        ("./" + namespace, namespace + "/index")
        for feature, namespace in CONNECTORS.items() if features[feature]
    )
    exports, types = {}, {}
    for key, target in entries.items():
        exports[key] = {
            condition: {"types": f"./dist/{fmt}/{target}.d.ts", "default": f"./dist/{fmt}/{target}.js"}
            for condition, fmt in (("import", "esm"), ("require", "src"))
        }
        if key != ".":
            types[key.removeprefix("./")] = [f"./dist/src/{target}.d.ts"]
    for key, target in GATEWAYS.items():
        exports["./" + key] = {
            condition: {"types": f"./dist/gateway/{fmt}/{target}.d.ts", "default": f"./dist/gateway/{fmt}/{target}.js"}
            for condition, fmt in (("import", "esm"), ("require", "cjs"))
        }
        types[key] = [f"./dist/gateway/cjs/{target}.d.ts"]
    return {
        "name": "@future-agi/sdk", "version": version, "exports": exports,
        "typesVersions": {"*": types},
        "peerDependencies": {"react": ">=17.0.0 <20", "ai": ">=7.0.156 <7.1.0"},
        "peerDependenciesMeta": {"react": {"optional": True}, "ai": {"optional": True}},
    }


class Candidate:
    def __init__(self, root, checker, calls, python_version="0.8.0", npm_version="0.3.0", features=None):
        self.root, self.checker, self.calls = root, checker, calls
        self.repo = root / "repo"
        self.wheel = root / "candidate.whl"
        self.sdist = root / "candidate.tar.gz"
        self.tarball = root / "candidate.tgz"
        self.output = root / "result.json"
        self.manifest = {"python": python_version, "typescript/futureagi": npm_version}
        self.pyproject = f'[tool.poetry]\nname = "futureagi"\nversion = "{python_version}"\n'
        self.features = {feature: True for feature in CONNECTORS} if features is None else features
        self.pkg = _package(npm_version, self.features)
        self.source_pkg = copy.deepcopy(self.pkg)
        # Source lifecycle scripts are not shipped in the candidate package.
        self.source_pkg["scripts"] = {"prepare": "build"}
        runtime = {"fi/py.typed": b"", "fi/gateway/__init__.py": b""}
        guards = {name: b"# synthetic namespace guard\n" for name in GUARDS}
        self.whl = {**runtime, **guards}
        self.set_wheel_version(python_version)
        self.sdist_prefix = f"futureagi-{python_version}/"
        self.source = {
            self.sdist_prefix + name: content
            for name, content in {**runtime, **guards, "PKG-INFO": _metadata(python_version),
                                  "pyproject.toml": self.pyproject.encode()}.items()
        }
        for name, content in {**runtime, **guards}.items():
            _write(self.repo / "python" / name, content)
        for entry in ("agents/runs", "sandbox", "sandbox-integrations/ai-sdk"):
            _write(self.repo / "typescript/futureagi/src" / entry / "index.ts", b"export {};\n")
        self.npm = {"package/" + name: b"synthetic\n" for name in ("README.md", "CHANGELOG.md", "LICENSE", "NOTICE")}
        for entry in self.pkg["exports"].values():
            for condition in entry.values():
                for target in condition.values():
                    self.npm["package/" + target.removeprefix("./")] = b"export {};\n"
        self.npm["package/dist/esnext/index.d.ts"] = b"export {};\n"
        for name, content in self.npm.items():
            if name.startswith("package/dist/"):
                _write(self.repo / "typescript/futureagi" / name.removeprefix("package/"), content)

    def set_wheel_version(self, version):
        self.whl = {name: content for name, content in self.whl.items() if ".dist-info/" not in name}
        info = f"futureagi-{version}.dist-info/"
        self.whl[info + "METADATA"] = _metadata(version)
        self.whl[info + "WHEEL"] = b"Wheel-Version: 1.0\nRoot-Is-Purelib: true\nTag: py3-none-any\n"

    def check(self, tamper=None):
        _write(self.repo / ".release-please-manifest.json", json.dumps(self.manifest).encode())
        _write(self.repo / "python/pyproject.toml", self.pyproject.encode())
        _write(self.repo / "typescript/futureagi/package.json", json.dumps(self.source_pkg).encode())
        _write(self.repo / "openapi/connectors/features.json", json.dumps(self.features).encode())
        metadata_path, = [name for name in self.whl if name.endswith(".dist-info/METADATA")]
        record = metadata_path.removesuffix("METADATA") + "RECORD"
        rows = io.StringIO()
        writer = csv.writer(rows)
        for name, content in sorted(self.whl.items()):
            digest = base64.urlsafe_b64encode(hashlib.sha256(content).digest()).rstrip(b"=").decode()
            writer.writerow((name, "sha256=" + digest, len(content)))
        writer.writerow((record, "", ""))
        wheel_files = {**self.whl, record: rows.getvalue().encode()}
        if tamper is not None:
            wheel_files[tamper] += b"tampered"
        with zipfile.ZipFile(self.wheel, "w") as archive:
            for name, content in wheel_files.items():
                archive.writestr(name, content)
        _tar(self.sdist, self.source)
        _tar(self.tarball, {**self.npm, "package/package.json": json.dumps(self.pkg).encode()})
        self.checker.main(self.repo, self.wheel, self.sdist, self.tarball, self.output)
        return json.loads(self.output.read_text())


@pytest.fixture
def candidate_factory(tmp_path, monkeypatch):
    spec = importlib.util.spec_from_file_location("candidate_artifacts", REPO / "scripts/packaging/check_artifacts.py")
    checker = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(checker)
    calls = []

    def make_module(spec):
        if spec.name == "check_gateway_boundaries":
            spec.loader = SimpleNamespace(exec_module=lambda module: None)
            return SimpleNamespace(check_gateway_boundaries=lambda *archives: calls.append("gateway"))
        assert spec.name == "check_ownership"
        module = importlib.util.module_from_spec(spec)
        loader = spec.loader

        def load_ownership(module):
            loader.exec_module(module)
            real_owns = module.ownership.owns
            real_check = module.check_combination

            def owns(name, path, rules):
                return (name == "futureagi" and path in GUARDS) or real_owns(name, path, rules)

            def check_combination(paths):
                result = real_check(paths)
                calls.append("ownership")
                return result

            monkeypatch.setattr(module.ownership, "owns", owns)
            monkeypatch.setattr(module, "check_combination", check_combination)

        spec.loader = SimpleNamespace(exec_module=load_ownership)
        return module

    # Replace only this checker's import interface, not process-wide importlib.
    monkeypatch.setattr(checker, "importlib", SimpleNamespace(util=SimpleNamespace(
        spec_from_file_location=importlib.util.spec_from_file_location,
        module_from_spec=make_module,
    )))

    def deployments(command, *, check):
        assert check is True and command[1] == "-I"
        assert Path(command[2]).name == "check_deployments_absent.py"
        assert command[3:] == [str(tmp_path / name) for name in ("candidate.whl", "candidate.tar.gz", "candidate.tgz")]
        calls.append("deployments")

    monkeypatch.setattr(checker, "subprocess", SimpleNamespace(run=deployments))
    return lambda **kwargs: Candidate(tmp_path, checker, calls, **kwargs)


@pytest.mark.parametrize("python_version,npm_version", [("0.8.0", "0.3.0"), ("0.7.0", "0.2.0"), ("1.2.3", "2.3.4")])
def test_accepts_exact_archives_for_pinned_versions(candidate_factory, python_version, npm_version):
    candidate = candidate_factory(python_version=python_version, npm_version=npm_version)
    result = candidate.check()
    assert candidate.calls == ["ownership", "gateway", "deployments"]
    assert len(result["artifacts"]) == 3
    assert GUARDS <= set(result["artifacts"][0]["files"])
    assert {candidate.sdist_prefix + name for name in GUARDS} <= set(result["artifacts"][1]["files"])
    assert all(artifact["digest"].startswith("sha256:") for artifact in result["artifacts"])


@pytest.mark.parametrize("archive", ["wheel", "sdist", "npm"])
def test_rejects_wrong_archive_version(candidate_factory, archive):
    candidate = candidate_factory()
    if archive == "wheel":
        candidate.set_wheel_version("0.7.0")
    elif archive == "sdist":
        candidate.source[candidate.sdist_prefix + "PKG-INFO"] = _metadata("0.7.0")
    else:
        candidate.pkg["version"] = "0.2.0"
    with pytest.raises(AssertionError, match=archive + " metadata"):
        candidate.check()


@pytest.mark.parametrize("component", ["python", "typescript/futureagi"])
@pytest.mark.parametrize("changed", ["manifest", "source"])
def test_rejects_manifest_source_disagreement(candidate_factory, component, changed):
    candidate = candidate_factory()
    if changed == "manifest":
        candidate.manifest[component] = "9.9.9"
    elif component == "python":
        candidate.pyproject = candidate.pyproject.replace('version = "0.8.0"', 'version = "9.9.9"')
    else:
        candidate.source_pkg["version"] = "9.9.9"
    with pytest.raises(AssertionError, match="source version disagrees with release manifest"):
        candidate.check()


def test_python_version_comes_from_poetry_table(candidate_factory):
    candidate = candidate_factory()
    candidate.pyproject = (
        '[tool.other]\nversion = "9.9.9"\n\n'
        "[tool.poetry]\nname = 'futureagi'\nversion = '0.8.0' # release\n\n"
        '[tool.other.nested]\nversion = "8.8.8"\n'
    )
    candidate.check()


def test_rejects_wrong_dist_info_directory(candidate_factory):
    candidate = candidate_factory()
    candidate.whl = {name.replace("futureagi-0.8.0.dist-info/", "futureagi-9.9.9.dist-info/"): content
                     for name, content in candidate.whl.items()}
    with pytest.raises(ValueError, match="dist-info directory disagrees with METADATA"):
        candidate.check()


def test_rejects_wrong_sdist_root(candidate_factory):
    candidate = candidate_factory()
    candidate.source = {name.replace(candidate.sdist_prefix, "futureagi-9.9.9/"): content
                        for name, content in candidate.source.items()}
    with pytest.raises(AssertionError, match="sdist root"):
        candidate.check()


@pytest.mark.parametrize("archive", ["wheel", "sdist"])
@pytest.mark.parametrize("guard", sorted(GUARDS))
def test_requires_each_named_guard(candidate_factory, archive, guard):
    candidate = candidate_factory()
    if archive == "wheel":
        del candidate.whl[guard]
    else:
        del candidate.source[candidate.sdist_prefix + guard]
    with pytest.raises(AssertionError, match="namespace guard"):
        candidate.check()


@pytest.mark.parametrize("name", ["other.py", "other.pth", "_futureagi_namespace_guard.py/extra.py"])
@pytest.mark.parametrize("archive", ["wheel", "sdist"])
def test_rejects_unowned_root_entries(candidate_factory, archive, name):
    candidate = candidate_factory()
    if archive == "wheel":
        candidate.whl[name] = b"# not owned\n"
        error, message = ValueError, "unowned runtime path"
    else:
        candidate.source[candidate.sdist_prefix + name] = b"# not owned\n"
        error, message = AssertionError, "futureagi-0.8.0/"
    with pytest.raises(error, match=message):
        candidate.check()


def test_record_integrity_is_not_mocked(candidate_factory):
    candidate = candidate_factory()
    with pytest.raises(ValueError, match="RECORD content mismatch"):
        candidate.check(tamper="fi/py.typed")


@pytest.mark.parametrize("key", ["./platform", "./platform/models"])
def test_rejects_missing_platform_export(candidate_factory, key):
    candidate = candidate_factory()
    del candidate.pkg["exports"][key]
    with pytest.raises(AssertionError, match="Exact feature-derived exports"):
        candidate.check()


def test_rejects_extra_export_even_if_registered_in_source(candidate_factory):
    candidate = candidate_factory()
    candidate.pkg["exports"]["./extra"] = candidate.pkg["exports"]["."]
    candidate.source_pkg["exports"]["./extra"] = candidate.source_pkg["exports"]["."]
    with pytest.raises(AssertionError, match="Exact feature-derived exports"):
        candidate.check()


def test_rejects_scripts_in_npm_tarball(candidate_factory):
    candidate = candidate_factory()
    candidate.pkg["scripts"] = {"postinstall": "build"}
    with pytest.raises(AssertionError, match="npm scripts"):
        candidate.check()


@pytest.mark.parametrize("feature", CONNECTORS)
def test_feature_disabled_export_is_not_required(candidate_factory, feature):
    candidate = candidate_factory(features={name: name != feature for name in CONNECTORS})
    candidate.check()


@pytest.mark.parametrize("feature", CONNECTORS)
def test_disabled_export_is_not_admitted(candidate_factory, feature):
    candidate = candidate_factory(features={name: name != feature for name in CONNECTORS})
    candidate.pkg["exports"]["./" + CONNECTORS[feature]] = candidate.pkg["exports"]["."]
    with pytest.raises(AssertionError, match="Exact feature-derived exports"):
        candidate.check()


@pytest.mark.parametrize("archive", ["wheel", "sdist", "npm"])
@pytest.mark.parametrize("change", ["missing", "extra"])
def test_runtime_inventory_stays_exact(candidate_factory, archive, change):
    candidate = candidate_factory()
    files, prefix, existing, label = {
        "wheel": (candidate.whl, "fi/", "py.typed", "wheel fi"),
        "sdist": (candidate.source, candidate.sdist_prefix + "fi/", "py.typed", "sdist fi"),
        "npm": (candidate.npm, "package/dist/esm/", "index.js", "npm dist"),
    }[archive]
    if change == "missing":
        del files[prefix + existing]
    else:
        files[prefix + "extra.py"] = b"# extra\n"
    with pytest.raises(AssertionError, match=label):
        candidate.check()


def test_npm_root_inventory_stays_exact(candidate_factory):
    candidate = candidate_factory()
    candidate.npm["package/extra.txt"] = b"extra\n"
    with pytest.raises(AssertionError, match="npm root"):
        candidate.check()


def test_gateway_conditions_stay_exact(candidate_factory):
    candidate = candidate_factory()
    candidate.pkg["exports"]["./gateway"]["development"] = candidate.pkg["exports"]["./gateway"]["import"]
    with pytest.raises(AssertionError, match="Gateway subpaths resolve with default conditions"):
        candidate.check()


def test_gateway_type_mappings_stay_exact(candidate_factory):
    candidate = candidate_factory()
    candidate.pkg["typesVersions"]["*"]["gateway"] = ["./dist/esm/index.d.ts"]
    with pytest.raises(AssertionError, match="Gateway typesVersions mappings"):
        candidate.check()


def test_sandbox_integration_export_remains_required(candidate_factory):
    candidate = candidate_factory()
    del candidate.pkg["exports"]["./sandbox/ai-sdk"]
    with pytest.raises(AssertionError, match="Exact feature-derived exports"):
        candidate.check()


def test_deferred_evals_remain_excluded(candidate_factory):
    candidate = candidate_factory()
    candidate.npm["package/dist/esm/evals/index.js"] = b"export {};\n"
    with pytest.raises(AssertionError, match="Disabled evaluation runner"):
        candidate.check()
