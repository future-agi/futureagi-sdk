"""Hash-bound archive inspection without extracting or executing archive members."""
import hashlib
import json
from pathlib import Path, PurePosixPath
import tarfile
import zipfile


def digest(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return "sha256:" + h.hexdigest()


def names_safe(names):
    if len(names) != len(set(names)):
        raise ValueError("Duplicate archive member")
    for name in names:
        if PurePosixPath(name).is_absolute() or ".." in PurePosixPath(name).parts or "\\" in name:
            raise ValueError("Unsafe archive member")


def inspect(wheel, tarball, manifest):
    records = {a["kind"]: a for a in manifest["artifacts"]}
    for kind, path in (("wheel", wheel), ("npm", tarball)):
        row = records[kind]
        if Path(path).name != row["file"] or digest(path) != row["first"]:
            raise ValueError("Candidate artifact identity mismatch")
        if row.get("second", row["first"]) != row["first"]:
            raise ValueError("Candidate builds were not identical")
    with zipfile.ZipFile(wheel) as archive:
        py = archive.namelist()
        names_safe(py)
        if any((i.external_attr >> 16) & 0o170000 == 0o120000 for i in archive.infolist()):
            raise ValueError("Wheel symlink refused")
    with tarfile.open(tarball) as archive:
        members = archive.getmembers()
        ts = [m.name for m in members]
        names_safe(ts)
        if any(m.issym() or m.islnk() or m.isdev() or m.isfifo() for m in members):
            raise ValueError("Non-regular npm archive member")
        pkg = json.load(archive.extractfile("package/package.json"))
        if pkg["name"] != "@future-agi/sdk":
            raise ValueError("Wrong npm package")
        docs = "\n".join(archive.extractfile(m).read().decode("utf8", "replace") for m in members
                         if m.isfile() and m.name.lower().endswith(("readme.md", ".mdx")))
        declarations = {m.name: archive.extractfile(m).read().decode('utf8') for m in members
                        if m.isfile() and m.name.endswith(('.d.ts', '.d.mts', '.d.cts'))}
    return {"py": py, "ts": ts, "package": pkg, "docs": docs, "ts_declarations": declarations}


def absence_checks(inventory, policy, language, expected=None):
    from ts_inventory import compare, derive
    declarations = inventory.get('ts_declarations', {})
    physical = {row['namespace']: row['files'] for row in derive(inventory['ts'], declarations, expected)}
    drift = compare(inventory['ts'], policy, expected, declarations) if language == 'ts' and expected is not None else None
    rows = [drift] if drift else []
    for name, spec in policy["surfaces"].items():
        if policy["states"][name][language] != "OFF":
            continue
        leaks = physical[name] if language == 'ts' else sorted({file for file in inventory['py']
                 for module in spec['py_modules'] for path in [module.replace('.', '/')]
                 if file.startswith('fi/' + path + '/') or file == 'fi/' + path + '.py'})
        rows.append({"name": "absence." + name + ".archive", "state": "FAIL" if leaks else "PASS", "leaks": leaks})
        if drift:
            rows.append({**drift, 'name': 'absence.' + name + '.inventory'})
        if language == "ts":
            exports = inventory["package"].get("exports", {})
            leaked = [x for x in exports if any(x == "./" + p or x.startswith("./" + p + "/") for p in spec["ts_subpaths"])]
            rows.append({"name": "absence." + name + ".export-map", "state": "FAIL" if leaked else "PASS", "leaks": leaked})
        if policy.get("docs_complete"):
            text = inventory["docs"] + policy.get("docs_text", "")
            leaked = [token for token in spec["docs_tokens"] if token in text]
            rows.append({"name": "absence." + name + ".docs", "state": "FAIL" if leaked else "PASS", "leaks": leaked})
        else:
            rows.append({"name": "absence." + name + ".docs", "state": "NOT-EVALUATED", "reason": "Complete candidate documentation not supplied"})
    return rows
