"""Inspect and test installed compatibility artifacts against one SDK artifact pair.

All execution belongs on a disposable build host. By default a source-only or
private-preview gateway is refused. --private-preview is development evidence,
never release qualification. No package is published or fetched by name in place
of one of the supplied local artifacts.
"""
from __future__ import annotations

import argparse
import base64
import csv
import hashlib
import io
import json
from pathlib import Path
import tarfile
import unicodedata
import zipfile

NAMES = {"@agentcc/client", "@agentcc/langchain", "@agentcc/llamaindex", "@agentcc/react", "@agentcc/vercel"}
# Signature files sit beside RECORD and are the only members RECORD may omit.
RECORD_SIGNATURES = ("RECORD.jws", "RECORD.p7s")


def digest(path: Path) -> str:
    """Hash an artifact without executing or extracting its contents."""
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def npm_manifest(path: Path) -> dict:
    """Read the manifest and license without extracting the supplied archive."""
    with tarfile.open(path) as archive:
        names = set(archive.getnames())
        if "package/LICENSE" not in names:
            raise ValueError(f"Missing LICENSE in {path.name}")
        license_text = archive.extractfile("package/LICENSE").read().decode()
        if "Apache License" not in license_text or "Version 2.0" not in license_text:
            raise ValueError(f"Not an Apache-2.0 license: {path.name}")
        return json.load(archive.extractfile("package/package.json"))


def destination_key(path: str) -> str:
    """The comparison form of an installed path.

    Installers write RECORD paths onto filesystems that may fold case or compose
    Unicode, so two spellings that land on one file are one destination.
    """
    return unicodedata.normalize("NFC", path).casefold()


def wheel_record(archive: zipfile.ZipFile) -> list[str]:
    """The installation claims of a wheel: its RECORD rows, proven equal to its members.

    Installers keep every RECORD row as an ownership claim, and uninstalling deletes
    each claimed path, archive member or not. A row with no member, a member with no
    row, a duplicate, or a hash or size that does not match the member is refused.
    """
    records = [n for n in archive.namelist() if n.count("/") == 1 and n.endswith(".dist-info/RECORD")]
    if len(records) != 1:
        raise ValueError("Expected exactly one wheel RECORD")
    record = records[0]
    signatures = {record.rsplit("/", 1)[0] + "/" + name for name in RECORD_SIGNATURES}
    rows: dict[str, tuple[str, str]] = {}
    for row in csv.reader(io.StringIO(archive.read(record).decode("utf-8"))):
        if not row:
            continue
        if len(row) != 3:
            raise ValueError("Malformed wheel RECORD row")
        if row[0] in rows:
            raise ValueError("Wheel RECORD lists one path twice")
        rows[row[0]] = (row[1], row[2])
    members = {info.filename for info in archive.infolist() if not info.is_dir()}
    if set(rows) - members:
        raise ValueError("Wheel RECORD claims files the archive does not contain")
    if members - set(rows) - signatures:
        raise ValueError("Wheel RECORD omits archive members")
    for path, (digest, size) in rows.items():
        if path == record or path in signatures:
            if digest or size:
                raise ValueError("Wheel RECORD must not hash itself or its signatures")
            continue
        algorithm, _, value = digest.partition("=")
        data = archive.read(path)
        expected = base64.urlsafe_b64encode(hashlib.new(algorithm, data).digest()).rstrip(b"=").decode() \
            if algorithm in {"sha256", "sha384", "sha512"} else None
        if expected is None or value != expected or size != str(len(data)):
            raise ValueError("Wheel RECORD hash or size does not match the archive member")
    return sorted(rows)


def wheel_destinations(archive: zipfile.ZipFile, *, shim: bool = False) -> set[tuple[str, str]]:
    """Compare library destinations; refuse nonlibrary schemes in shims.

    The destinations are read from RECORD, which must equal the archive members
    (wheel_record), and compared in their normalised form (destination_key).
    A data-scheme entry can alias site-packages under the installation prefix.
    Compatibility wheels need only library files, so reject other schemes rather
    than assuming physically distinct roots for every consumer environment.
    """
    destinations = set()
    for filename in wheel_record(archive):
        parts = filename.split("/")
        if any(part in {"", ".", ".."} or ":" in part for part in parts) or "\\" in filename:
            raise ValueError("Unsafe wheel installation path")
        scheme = "site-packages"
        if parts[0].endswith(".data"):
            if len(parts) < 3 or parts[1] not in {"purelib", "platlib", "scripts", "headers", "data"}:
                raise ValueError("Unknown wheel installation scheme")
            if shim and parts[1] not in {"purelib", "platlib"}:
                raise ValueError("Unsupported shim installation scheme: " + parts[1])
            scheme = "site-packages" if parts[1] in {"purelib", "platlib"} else parts[1]
            parts = parts[2:]
        destination = (scheme, destination_key("/".join(parts)))
        if destination in destinations:
            raise ValueError("Wheel overlaps its own installation destinations")
        destinations.add(destination)
    return destinations


def check_exports(path: Path, exports: dict, required: tuple[str, ...], *,
                  private_preview: bool = False) -> None:
    """Require regular JavaScript and declaration files for both module systems."""
    if not isinstance(exports, dict) or any(key not in exports for key in required):
        raise ValueError("Package export missing")
    with tarfile.open(path) as archive:
        files = {member.name: member for member in archive.getmembers()}
        for key in required:
            export = exports[key]
            if isinstance(export, dict) and "futureagi-gateway-preview" in export:
                if not private_preview:
                    raise ValueError("A private-preview export cannot qualify release shims")
                export = export["futureagi-gateway-preview"]
            if not isinstance(export, dict) or not all(mode in export for mode in ("import", "require")):
                raise ValueError("Both ESM and CJS exports are required")
            for mode in ("import", "require"):
                condition = export[mode]
                for field in ("types", "default"):
                    target = condition.get(field) if isinstance(condition, dict) else None
                    extensions = (".d.ts", ".d.mts", ".d.cts") if field == "types" else (".js", ".mjs", ".cjs")
                    if (not isinstance(target, str) or not target.startswith("./")
                            or any(part in {"", ".", ".."} for part in target[2:].split("/"))
                            or "\\" in target or not target.endswith(extensions)):
                        raise ValueError("Package export target absent or invalid")
                    member = files.get("package/" + target[2:])
                    if member is None or not member.isfile():
                        raise ValueError("Package export target absent from tarball")


def inspect(wheel: Path, tarball: Path, shim_wheel: Path, npm: list[Path], *, private_preview: bool = False) -> dict:
    """Fail closed on absent gateway files, wrong coordinates or shared Python paths."""
    with zipfile.ZipFile(wheel) as sdk, zipfile.ZipFile(shim_wheel) as shim:
        sdk_names, shim_names = set(sdk.namelist()), set(shim.namelist())
        if "fi/gateway/__init__.py" not in sdk_names:
            raise ValueError("SDK gateway is OFF: fi.gateway is absent from the wheel")
        sdk_metadata = [p for p in sdk_names if p.endswith(".dist-info/METADATA")]
        if len(sdk_metadata) != 1:
            raise ValueError("Expected one SDK wheel metadata record")
        sdk_text = sdk.read(sdk_metadata[0]).decode()
        if "Name: futureagi\n" not in sdk_text or "Version: 0.7.0\n" not in sdk_text:
            raise ValueError("Expected the exact futureagi 0.7.0 wheel")
        if "agentcc/__init__.py" not in shim_names:
            raise ValueError("Not an agentcc compatibility wheel")
        sdk_destinations = wheel_destinations(sdk)
        shim_destinations = wheel_destinations(shim, shim=True)
        if sdk_destinations & shim_destinations or any(
            scheme == "site-packages" and (name == "fi" or name.startswith("fi/"))
            for scheme, name in shim_destinations
        ):
            raise ValueError("Compatibility wheel overlaps the SDK namespace")
        if not any(p.endswith("/LICENSE") and b"Apache License" in shim.read(p) for p in shim_names):
            raise ValueError("Compatibility wheel has no Apache-2.0 LICENSE")
        metadata = [p for p in shim_names if p.endswith(".dist-info/METADATA")]
        if len(metadata) != 1:
            raise ValueError("Ambiguous compatibility wheel metadata")
        text = shim.read(metadata[0]).decode()
        for field in ("Name: agentcc\n", "Version: 2.0.0\n", "Requires-Python: >=3.10\n", "Requires-Dist: futureagi<1,>=0.7.0\n"):
            if field not in text:
                raise ValueError(f"Missing metadata field {field.strip()}")
    pkg = npm_manifest(tarball)
    if pkg.get("name") != "@future-agi/sdk" or pkg.get("version") != "0.2.0":
        raise ValueError("Expected the exact SDK 0.2.0 tarball")
    gateway_keys = tuple("./gateway" + suffix for suffix in ("", "/testing", "/express", "/nextjs", "/react"))
    check_exports(tarball, pkg.get("exports", {}), gateway_keys, private_preview=private_preview)
    packages = [npm_manifest(p) for p in npm]
    if len(packages) != 5 or {p.get("name") for p in packages} != NAMES:
        raise ValueError("Exactly the five distinct compatibility tarballs are required")
    for path, package in zip(npm, packages):
        required = (".", "./testing", "./express", "./nextjs") if package["name"] == "@agentcc/client" else (".",)
        exports = package.get("exports", {})
        check_exports(path, exports, required)
        # Extra advertised subpaths must work as well; names cannot mask dead code.
        check_exports(path, exports, tuple(exports))
        if package.get("version") != "2.0.0" or package.get("dependencies", {}).get("@future-agi/sdk") != ">=0.2.0 <1.0.0":
            raise ValueError("Invalid compatibility version or SDK dependency")
        if any(k in package.get("scripts", {}) for k in ("install", "postinstall", "prepare")):
            raise ValueError("Installed shims must not run lifecycle scripts")
    return {"mode": "private-preview" if private_preview else "candidate",
            "release_accepted": False,
            "artifacts": {p.name: digest(p) for p in [wheel, tarball, shim_wheel, *npm]}}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--wheel", type=Path, required=True)
    parser.add_argument("--tarball", type=Path, required=True)
    parser.add_argument("--shim-wheel", type=Path, required=True)
    parser.add_argument("--npm", type=Path, nargs=5, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--private-preview", action="store_true")
    args = parser.parse_args()
    result = inspect(args.wheel, args.tarball, args.shim_wheel, args.npm, private_preview=args.private_preview)
    # This is the archive preflight; installed behavior and golden parity must also pass.
    result["installed_and_golden_verification_owed"] = True
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2) + "\n")
    print("Archive preflight passed; installed behavior and golden comparison are separate gates")


if __name__ == "__main__":
    main()
