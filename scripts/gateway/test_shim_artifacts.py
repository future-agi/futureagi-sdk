"""Archive admission, including negative controls for OFF and preview gateways."""
import base64
import csv
import hashlib
import importlib.util
import sys
import subprocess
import io
import json
from pathlib import Path
import tarfile
import tempfile
import unittest
import zipfile

SCRIPT = Path(__file__).with_name("check_shim_artifacts.py")
spec = importlib.util.spec_from_file_location("shim_artifacts", SCRIPT)
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)
LICENSE = (SCRIPT.parents[2] / "LICENSE").read_text()


def seal(path):
    """Rewrite a wheel's RECORD so it lists exactly its members with their hashes."""
    with zipfile.ZipFile(path) as archive:
        files = {info.filename: archive.read(info) for info in archive.infolist()
                 if not info.is_dir() and not info.filename.endswith(".dist-info/RECORD")}
    info = next((name.split("/")[0] for name in files if name.split("/")[0].endswith(".dist-info")), None)
    if info is not None:
        write_wheel(path, files, info)


def write_wheel(path, files, info, extra_rows=()):
    """A wheel holding *files*, its RECORD rows, and any *extra_rows* claimed without a member."""
    record = io.StringIO()
    writer = csv.writer(record, lineterminator="\n")
    for name, content in files.items():
        digest = base64.urlsafe_b64encode(hashlib.sha256(content).digest()).rstrip(b"=").decode()
        writer.writerow([name, "sha256=" + digest, str(len(content))])
    for row in extra_rows:
        writer.writerow(row)
    writer.writerow([f"{info}/RECORD", "", ""])
    with zipfile.ZipFile(path, "w") as archive:
        for name, content in files.items():
            archive.writestr(name, content)
        archive.writestr(f"{info}/RECORD", record.getvalue())


def tarball(path, manifest, extra=None):
    rows = {"package/package.json": json.dumps(manifest), "package/LICENSE": LICENSE, **(extra or {})}
    with tarfile.open(path, "w:gz") as archive:
        for name, data in rows.items():
            content = data.encode()
            info = tarfile.TarInfo(name)
            info.size = len(content)
            archive.addfile(info, io.BytesIO(content))


class ArtifactAdmission(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.wheel = self.root / "futureagi.whl"
        self.shim = self.root / "agentcc.whl"
        self.npm = self.root / "sdk.tgz"
        with zipfile.ZipFile(self.wheel, "w") as archive:
            archive.writestr("fi/gateway/__init__.py", "")
            archive.writestr("futureagi-0.7.0.dist-info/METADATA", "Name: futureagi\nVersion: 0.7.0\n")
        with zipfile.ZipFile(self.shim, "w") as archive:
            archive.writestr("agentcc/__init__.py", "")
            archive.writestr("agentcc-2.0.0.dist-info/METADATA", "Name: agentcc\nVersion: 2.0.0\nRequires-Python: >=3.10\nRequires-Dist: futureagi<1,>=0.7.0\n")
            archive.writestr("agentcc-2.0.0.dist-info/licenses/LICENSE", LICENSE)
        export = {"import": {"types": "./index.d.ts", "default": "./index.js"}, "require": {"types": "./index.d.ts", "default": "./index.js"}}
        self.pkg = {"name": "@future-agi/sdk", "version": "0.2.0", "exports": {"./gateway" + suffix: export for suffix in ("", "/testing", "/express", "/nextjs", "/react")}}
        self.files = {"package/index.d.ts": "", "package/index.js": ""}
        self.packages = []
        for name in sorted(gate.NAMES):
            path = self.root / (name.split("/")[1] + ".tgz")
            keys = (".", "./testing", "./express", "./nextjs") if name == "@agentcc/client" else (".",)
            manifest = {"name": name, "version": "2.0.0", "dependencies": {"@future-agi/sdk": ">=0.2.0 <1.0.0"},
                        "exports": {key: export for key in keys}}
            tarball(path, manifest, self.files)
            self.packages.append(path)

    def inspect(self, sealed=True, **kwargs):
        tarball(self.npm, self.pkg, self.files)
        if sealed:
            seal(self.wheel)
            seal(self.shim)
        return gate.inspect(self.wheel, self.npm, self.shim, self.packages, **kwargs)

    def test_complete_candidate_does_not_self_accept(self):
        self.assertFalse(self.inspect()["release_accepted"])

    def test_off_wheel_is_refused(self):
        with zipfile.ZipFile(self.wheel, "w") as archive:
            archive.writestr("fi/__init__.py", "")
        with self.assertRaisesRegex(ValueError, "OFF"):
            self.inspect()

    def test_preview_cannot_qualify_release(self):
        self.pkg["exports"] = {k: {"futureagi-gateway-preview": v, "default": None} for k, v in self.pkg["exports"].items()}
        with self.assertRaisesRegex(ValueError, "private-preview"):
            self.inspect()
        self.assertEqual(self.inspect(private_preview=True)["mode"], "private-preview")

    def test_removed_export_target_is_refused(self):
        del self.files["package/index.js"]
        with self.assertRaisesRegex(ValueError, "target absent"):
            self.inspect()

    def test_overlapping_namespace_is_refused(self):
        with zipfile.ZipFile(self.shim, "a") as archive:
            archive.writestr("fi/extra.py", "")
        with self.assertRaisesRegex(ValueError, "overlaps"):
            self.inspect()

    def test_data_installation_paths_cannot_claim_fi(self):
        for scheme in ("purelib", "platlib"):
            with self.subTest(scheme=scheme):
                with zipfile.ZipFile(self.shim, "a") as archive:
                    archive.writestr(f"agentcc-2.0.0.data/{scheme}/fi/gateway/_verification_marker.py", "")
                with self.assertRaisesRegex(ValueError, "overlaps"):
                    self.inspect()
                self.setUp()

    def test_data_installation_paths_cannot_overlap_other_sdk_files(self):
        with zipfile.ZipFile(self.wheel, "a") as archive:
            archive.writestr("futureagi-0.7.0.data/platlib/shared_helper.py", "")
        with zipfile.ZipFile(self.shim, "a") as archive:
            archive.writestr("agentcc-2.0.0.data/purelib/shared_helper.py", "")
        with self.assertRaisesRegex(ValueError, "overlaps"):
            self.inspect()

    def test_data_scheme_cannot_overwrite_site_packages(self):
        # Derive the physical alias from a real disposable installation scheme.
        venv = self.root / "consumer"
        subprocess.run(["uv", "venv", str(venv)], check=True, capture_output=True)
        py = venv / "bin/python"
        paths = json.loads(subprocess.check_output([str(py), "-I", "-c",
            'import json,sysconfig; print(json.dumps({k:sysconfig.get_path(k) for k in ("data","purelib")}))'], text=True))
        relative = Path(paths["purelib"]).relative_to(paths["data"]) / "fi/gateway/__init__.py"
        target = Path(paths["data"]) / relative
        target.parent.mkdir(parents=True)
        target.write_text("SDK_SENTINEL = True\n")
        with zipfile.ZipFile(self.shim) as archive:
            files = {name: archive.read(name) for name in archive.namelist()}
        files["agentcc-2.0.0.data/data/" + relative.as_posix()] = b"SHIM_OVERWROTE_SDK = True\n"
        files["agentcc-2.0.0.dist-info/WHEEL"] = b"Wheel-Version: 1.0\nRoot-Is-Purelib: true\nTag: py3-none-any\n"
        record = io.StringIO()
        writer = csv.writer(record)
        for name, content in files.items():
            writer.writerow([name, "", str(len(content))])
        writer.writerow(["agentcc-2.0.0.dist-info/RECORD", "", ""])
        files["agentcc-2.0.0.dist-info/RECORD"] = record.getvalue().encode()
        self.shim = self.root / "agentcc-2.0.0-py3-none-any.whl"
        with zipfile.ZipFile(self.shim, "w") as archive:
            for name, content in files.items():
                archive.writestr(name, content)
        # Negative control: the installer really aliases the SDK path. This is
        # an isolated venv with only a sentinel, never the test environment.
        subprocess.run(["uv", "pip", "install", "--python", str(py), "--no-index", "--no-deps", str(self.shim)],
                       check=True, capture_output=True)
        self.assertEqual(target.read_text(), "SHIM_OVERWROTE_SDK = True\n")
        with self.assertRaisesRegex(ValueError, "Unsupported shim installation scheme"):
            self.inspect()

    def test_other_nonlibrary_shim_schemes_are_refused(self):
        for scheme in ("scripts", "headers", "data"):
            with self.subTest(scheme=scheme):
                with zipfile.ZipFile(self.shim, "a") as archive:
                    archive.writestr(f"agentcc-2.0.0.data/{scheme}/extra", "")
                with self.assertRaisesRegex(ValueError, "Unsupported shim installation scheme"):
                    self.inspect()
                self.setUp()

    def test_manifest_only_shims_are_refused(self):
        for path in self.packages:
            with self.subTest(package=path.name):
                manifest = gate.npm_manifest(path)
                tarball(path, manifest)
                with self.assertRaisesRegex(ValueError, "target absent"):
                    self.inspect()
                tarball(path, manifest, self.files)

    def test_missing_shim_export_and_conditions_are_refused(self):
        for path in self.packages:
            manifest = gate.npm_manifest(path)
            for key in manifest["exports"]:
                broken = json.loads(json.dumps(manifest))
                del broken["exports"][key]
                tarball(path, broken, self.files)
                with self.subTest(package=path.name, key=key):
                    with self.assertRaisesRegex(ValueError, "export missing"):
                        self.inspect()
            for mode in ("import", "require"):
                for field in ("types", "default"):
                    broken = json.loads(json.dumps(manifest))
                    del broken["exports"]["."][mode][field]
                    tarball(path, broken, self.files)
                    with self.subTest(package=path.name, mode=mode, field=field):
                        with self.assertRaisesRegex(ValueError, "target absent"):
                            self.inspect()
            tarball(path, manifest, self.files)

    def test_shim_target_extensions_and_nonfiles_are_refused(self):
        path = self.packages[0]
        manifest = gate.npm_manifest(path)
        for target in ("./README.md", "./../index.js", "index.js"):
            broken = json.loads(json.dumps(manifest))
            broken["exports"]["."]["import"]["default"] = target
            tarball(path, broken, {**self.files, "package/" + target.removeprefix("./"): ""})
            with self.subTest(target=target):
                with self.assertRaisesRegex(ValueError, "target"):
                    self.inspect()
        tarball(path, manifest, self.files)
        with tarfile.open(path) as archive:
            rows = {member.name: archive.extractfile(member).read() for member in archive.getmembers()}
        with tarfile.open(path, "w:gz") as archive:
            for name, content in rows.items():
                info = tarfile.TarInfo(name)
                if name == "package/index.js":
                    info.type = tarfile.SYMTYPE
                    info.linkname = "missing.js"
                    archive.addfile(info)
                else:
                    info.size = len(content)
                    archive.addfile(info, io.BytesIO(content))
        with self.assertRaisesRegex(ValueError, "target absent"):
            self.inspect()

    def test_missing_integration_is_refused(self):
        self.packages.pop()
        with self.assertRaisesRegex(ValueError, "five distinct"):
            self.inspect()


    def test_record_only_ownership_claim_is_refused(self):
        # The archive has no fi/ member; only its RECORD claims the SDK's package file.
        seal(self.wheel)
        with zipfile.ZipFile(self.shim) as archive:
            files = {i.filename: archive.read(i) for i in archive.infolist() if not i.filename.endswith("/RECORD")}
        write_wheel(self.shim, files, "agentcc-2.0.0.dist-info",
                    extra_rows=[["fi/gateway/__init__.py", "sha256=" + "A" * 43, "0"]])
        with self.assertRaisesRegex(ValueError, "RECORD claims files the archive does not contain"):
            self.inspect(sealed=False)

    def test_record_must_list_every_member_with_its_hash_and_size(self):
        seal(self.wheel)
        with zipfile.ZipFile(self.shim) as archive:
            files = {i.filename: archive.read(i) for i in archive.infolist() if not i.filename.endswith("/RECORD")}
        write_wheel(self.shim, {k: v for k, v in files.items() if k != "agentcc/__init__.py"}, "agentcc-2.0.0.dist-info")
        with zipfile.ZipFile(self.shim, "a") as archive:
            archive.writestr("agentcc/__init__.py", files["agentcc/__init__.py"])
        with self.assertRaisesRegex(ValueError, "RECORD omits archive members"):
            self.inspect(sealed=False)
        write_wheel(self.shim, {**files, "agentcc/__init__.py": b"changed = True\n"}, "agentcc-2.0.0.dist-info")
        with zipfile.ZipFile(self.shim) as archive:
            record = archive.read("agentcc-2.0.0.dist-info/RECORD")
            rows = {n: archive.read(n) for n in archive.namelist() if not n.endswith("/RECORD")}
        rows["agentcc/__init__.py"] = files["agentcc/__init__.py"]
        with zipfile.ZipFile(self.shim, "w") as archive:
            for name, content in rows.items():
                archive.writestr(name, content)
            archive.writestr("agentcc-2.0.0.dist-info/RECORD", record)
        with self.assertRaisesRegex(ValueError, "hash or size"):
            self.inspect(sealed=False)

    def test_destinations_are_normalised_before_overlap_checks(self):
        # Case-folding and Unicode-composing filesystems write these onto SDK paths.
        for name in ("FI/gateway/_marker.py", "Fi/Gateway/__init__.py", "agentcc-2.0.0.data/purelib/FI/x.py"):
            with self.subTest(name=name):
                with zipfile.ZipFile(self.shim, "a") as archive:
                    archive.writestr(name, "")
                with self.assertRaisesRegex(ValueError, "overlaps"):
                    self.inspect()
                self.setUp()
        decomposed, composed = "cafe\u0301.py", "caf\u00e9.py"
        with zipfile.ZipFile(self.wheel, "a") as archive:
            archive.writestr("futureagi-0.7.0.data/purelib/" + composed, "")
        with zipfile.ZipFile(self.shim, "a") as archive:
            archive.writestr("agentcc-2.0.0.data/purelib/" + decomposed, "")
        with self.assertRaisesRegex(ValueError, "overlaps"):
            self.inspect()
        self.setUp()
        for unsafe in ("agentcc/../fi/x.py", "C:/fi/x.py"):
            with self.subTest(unsafe=unsafe):
                with zipfile.ZipFile(self.shim, "a") as archive:
                    archive.writestr(unsafe, "")
                with self.assertRaisesRegex(ValueError, "Unsafe"):
                    self.inspect()
                self.setUp()

    def test_pip_25_record_only_claim_deletes_sdk_files_so_the_gate_refuses_it(self):
        """The installed-environment regression: a RECORD-only claim on fi/gateway/__init__.py.

        Negative control, in a disposable environment with pip 25.x: the claim survives
        installation and uninstalling the shim then deletes the SDK's file. The gate
        refuses that wheel, and the sealed wheel it admits leaves the file in place.
        """
        pip_version = subprocess.check_output([sys.executable, "-I", "-m", "pip", "--version"], text=True).split()[1]
        self.assertTrue(pip_version.startswith("25."), pip_version)
        meta = "Metadata-Version: 2.1\nName: {0}\nVersion: {1}\n"
        wheel_meta = b"Wheel-Version: 1.0\nGenerator: test\nRoot-Is-Purelib: true\nTag: py3-none-any\n"
        sdk_files = {"fi/__init__.py": b"", "fi/gateway/__init__.py": b"SDK_SENTINEL = True\n",
                     "futureagi-0.7.0.dist-info/METADATA": meta.format("futureagi", "0.7.0").encode(),
                     "futureagi-0.7.0.dist-info/WHEEL": wheel_meta}
        shim_files = {"agentcc/__init__.py": b"",
                      "agentcc-2.0.0.dist-info/METADATA": (meta.format("agentcc", "2.0.0") + "Requires-Python: >=3.10\nRequires-Dist: futureagi<1,>=0.7.0\n").encode(),
                      "agentcc-2.0.0.dist-info/WHEEL": wheel_meta,
                      "agentcc-2.0.0.dist-info/licenses/LICENSE": LICENSE.encode()}
        self.wheel = self.root / "futureagi-0.7.0-py3-none-any.whl"
        write_wheel(self.wheel, sdk_files, "futureagi-0.7.0.dist-info")
        probe = self.root / "probe" / "agentcc-2.0.0-py3-none-any.whl"
        sealed = self.root / "sealed" / "agentcc-2.0.0-py3-none-any.whl"
        probe.parent.mkdir()
        sealed.parent.mkdir()
        write_wheel(probe, shim_files, "agentcc-2.0.0.dist-info", extra_rows=[["fi/gateway/__init__.py", "", ""]])
        write_wheel(sealed, shim_files, "agentcc-2.0.0.dist-info")

        def install_then_uninstall(shim):
            venv = self.root / ("venv-" + shim.parent.name)
            subprocess.run(["uv", "venv", "--python", sys.executable, str(venv)], check=True, capture_output=True)
            pip = [sys.executable, "-I", "-m", "pip", "--python", str(venv / "bin/python")]
            subprocess.run([*pip, "install", "--no-index", "--no-deps", str(self.wheel), str(shim)], check=True, capture_output=True)
            sentinel = next(venv.glob("lib/python*/site-packages/fi/gateway/__init__.py"))
            self.assertEqual(sentinel.read_bytes(), b"SDK_SENTINEL = True\n")
            subprocess.run([*pip, "uninstall", "-y", "agentcc"], check=True, capture_output=True)
            return sentinel.exists()

        self.assertFalse(install_then_uninstall(probe), "negative control: pip kept the RECORD-only claim")
        self.shim = probe
        with self.assertRaisesRegex(ValueError, "RECORD claims files the archive does not contain"):
            self.inspect(sealed=False)
        self.assertTrue(install_then_uninstall(sealed))
        self.shim = sealed
        self.assertFalse(self.inspect(sealed=False)["release_accepted"])

if __name__ == "__main__":
    unittest.main(verbosity=2)
