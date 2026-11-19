"""Turn fetch-artifacts.sh evidence into artifacts.json and registry-npm.json.

Stdlib only; run with ``python3 -I summarize_artifacts.py <out> <work> <src-the recorded source>``.
Every hash is computed here from the bytes on disk and set beside the value the
registry publishes for that exact version (``npm view <name>@<version> dist``,
never ``dist-tags.latest``, which moves when a newer version is published), so
a match is never self-referential. npm pack's own report is a second,
separate cross-check. The exit is 0 only if no ``problems()`` remain: every
PUBLISHED tarball is present and matches, the wheel matches, and the client and
wheel digests start with the published prefixes below (no others are pinned).

The npm registry projection keeps names, versions, times, dist-tags, dist
hashes and deprecation notices. It leaves out maintainer and publisher records
(they carry e-mail addresses), and only the projection is kept: the raw
answers stay on the recording VM, and fetch-artifacts.sh re-fetches them, so a
fresh host derives the projection again (and gives the same bytes while the
registry is unchanged).
"""

from __future__ import annotations

import base64
import difflib
import hashlib
import json
import pathlib
import sys

EXPECTED_WHEEL_SHA256_PREFIX = (
    "2eb341ee"  # the published agentcc 1.0.0 wheel's digest prefix
)
EXPECTED_CLIENT_SHASUM_PREFIX = "81b5315b"
CLIENT = "@agentcc/client@1.0.0"
PUBLISHED = (
    CLIENT,
    "@agentcc/langchain@1.0.0",
    "@agentcc/vercel@1.0.0",
    "@agentcc/react@1.0.0",
    "@agentcc/llamaindex@1.0.0",
)
DIST_KEYS = ("shasum", "integrity", "tarball", "fileCount", "unpackedSize")
# The two files of a package that are not build output; any other file that
# differs from a the recorded source build gets its unified diff recorded.
NOT_BUILT = ("README.md", "package.json")
TEXT_DIFF_LIMIT = 200_000


def _load(path: pathlib.Path):
    try:
        return json.loads(path.read_text())
    except (OSError, ValueError) as exc:
        return {"_unreadable": f"{type(exc).__name__}"}


def _digest(path: pathlib.Path, name: str) -> str:
    return hashlib.new(name, path.read_bytes()).hexdigest()


def _integrity(path: pathlib.Path) -> str:
    return (
        "sha512-"
        + base64.b64encode(hashlib.sha512(path.read_bytes()).digest()).decode()
    )


def _tree(root: pathlib.Path) -> dict[str, str]:
    return {
        str(p.relative_to(root)): _digest(p, "sha256")
        for p in sorted(root.rglob("*"))
        if p.is_file() and "__pycache__" not in p.parts
    }


def _diff_trees(a: dict[str, str], b: dict[str, str]) -> dict:
    return {
        "identical": len([k for k in a.keys() & b.keys() if a[k] == b[k]]),
        "differ": sorted(k for k in a.keys() & b.keys() if a[k] != b[k]),
        "only_left": sorted(a.keys() - b.keys()),
        "only_right": sorted(b.keys() - a.keys()),
    }


def pypi(out: pathlib.Path, work: pathlib.Path, src98: pathlib.Path) -> dict:
    wheels = sorted((work / "pypi").glob("*.whl"))
    wheel = wheels[0]
    meta = _load(out / "raw" / "pypi-agentcc-1.0.0.json")
    reg = [u for u in meta.get("urls", []) if u.get("filename") == wheel.name]
    computed = _digest(wheel, "sha256")
    registry = reg[0]["digests"]["sha256"] if reg else None
    index = _load(out / "raw" / "pypi-agentcc.json")
    releases = {
        v: sorted((f["filename"], f.get("upload_time_iso_8601")) for f in files)
        for v, files in sorted(index.get("releases", {}).items())
    }
    wheel_tree = _tree(work / "wheel-x" / "agentcc")
    src_tree = _tree(src98 / "sdk" / "python" / "src" / "agentcc")
    return {
        "wheel": wheel.name,
        "sha256_computed": computed,
        "sha256_registry": registry,
        "registry_match": computed == registry,
        "expected_prefix": EXPECTED_WHEEL_SHA256_PREFIX,
        "prefix_match": computed.startswith(EXPECTED_WHEEL_SHA256_PREFIX),
        "upload_time": reg[0].get("upload_time_iso_8601") if reg else None,
        "releases": releases,
        "wheel_vs_release_source_src": _diff_trees(wheel_tree, src_tree),
    }


def _npm_view_projection(view) -> dict:
    if not isinstance(view, dict) or "error" in view or "_unreadable" in view:
        err = view.get("error", {}) if isinstance(view, dict) else {}
        return {
            "published": False,
            "error_code": err.get("code"),
            "error_summary": err.get("summary"),
        }
    versions = view.get("versions") or []
    return {
        "published": True,
        "name": view.get("name"),
        "dist_tags": view.get("dist-tags"),
        "versions": versions if isinstance(versions, list) else [versions],
        "time": {k: v for k, v in sorted((view.get("time") or {}).items())},
        "latest_dist": {k: (view.get("dist") or {}).get(k) for k in DIST_KEYS},
        "deprecated": view.get("deprecated"),
        "license": view.get("license"),
        "repository": view.get("repository"),
        "homepage": view.get("homepage"),
        "peerDependencies": view.get("peerDependencies"),
    }


def npm_registry(out: pathlib.Path) -> dict:
    exits = _exit_lines(out / "npm-view-exit.txt")
    listed = {}
    for query in ("scope-agentcc", "text-agentcc"):
        found = _load(out / "raw" / f"npm-search-{query}.json")
        listed[query] = (
            sorted(p["name"] for p in found) if isinstance(found, list) else found
        )
    views = {}
    for name in sorted(exits):
        raw = _load(out / "raw" / f"npm-view-{name.replace('/', '__')}.json")
        views[name] = {"npm_view_exit": exits[name], **_npm_view_projection(raw)}
    for spec, code in sorted(_exit_lines(out / "npm-view-dist-exit.txt").items()):
        name, version = spec.rsplit("@", 1)
        raw = _load(out / "raw" / f"npm-view-dist-{spec.replace('/', '__')}.json")
        answered = isinstance(raw, dict) and not {"error", "_unreadable"} & raw.keys()
        dist = {k: raw.get(k) for k in DIST_KEYS} if code == 0 and answered else {}
        views.setdefault(name, {}).setdefault("version_dist", {})[version] = {
            "npm_view_exit": code,
            **dist,
        }
    return {"search": listed, "packages": views}


def _exit_lines(path: pathlib.Path) -> dict[str, int]:
    try:
        lines = path.read_text().splitlines()
    except OSError:
        return {}
    return {name: int(code) for name, code in (line.rsplit(" ", 1) for line in lines)}


def _pack_entries(path: pathlib.Path) -> list:
    data = _load(path)
    return data if isinstance(data, list) else []


def npm_artifacts(out: pathlib.Path, work: pathlib.Path, registry: dict) -> dict:
    result = {}
    for entry in _pack_entries(out / "raw" / "npm-pack-published.json"):
        tgz = work / "npm-published" / entry["filename"]
        name, version = entry["name"], entry["version"]
        dist = (
            registry["packages"].get(name, {}).get("version_dist", {}).get(version, {})
        )
        sha1, integrity = _digest(tgz, "sha1"), _integrity(tgz)
        result[entry["id"]] = {
            "source": "registry.npmjs.org",
            "filename": entry["filename"],
            "sha1_computed": sha1,
            "integrity_computed": integrity,
            "registry_shasum": dist.get("shasum"),
            "registry_integrity": dist.get("integrity"),
            "registry_match": bool(dist.get("shasum") and dist.get("integrity"))
            and (sha1, integrity) == (dist.get("shasum"), dist.get("integrity")),
            "npm_pack_shasum": entry.get("shasum"),
            "npm_pack_integrity": entry.get("integrity"),
            "npm_pack_match": (sha1, integrity)
            == (entry.get("shasum"), entry.get("integrity")),
            "file_count": len(entry.get("files", [])),
        }
    if CLIENT in result:
        result[CLIENT]["expected_prefix"] = EXPECTED_CLIENT_SHASUM_PREFIX
        result[CLIENT]["prefix_match"] = result[CLIENT]["sha1_computed"].startswith(
            EXPECTED_CLIENT_SHASUM_PREFIX
        )
    for raw in sorted((out / "raw").glob("npm-pack-*-release-source.json")) + sorted(
        (out / "raw").glob("npm-pack-client-*.json")
    ):
        tag = "release-source" if "release-source" in raw.name else raw.stem.removeprefix("npm-pack-client-")
        for entry in _pack_entries(raw):
            tgz = work / "tarballs" / f"local-{tag}" / entry["filename"]
            result[f"{entry['id']} (packed from {tag})"] = {
                "source": f"git {tag}, built on this VM",
                "filename": entry["filename"],
                "sha1_computed": _digest(tgz, "sha1") if tgz.exists() else None,
                "npm_pack_shasum": entry.get("shasum"),
                "integrity_computed": _integrity(tgz) if tgz.exists() else None,
                "file_count": len(entry.get("files", [])),
            }
    return result


def _text_diff(a: pathlib.Path, b: pathlib.Path, name: str) -> list[str] | None:
    try:
        old, new = a.read_text("utf-8"), b.read_text("utf-8")
    except (OSError, UnicodeDecodeError):
        return None
    if len(old) + len(new) > TEXT_DIFF_LIMIT:
        return None
    return list(
        difflib.unified_diff(
            old.splitlines(),
            new.splitlines(),
            f"published/{name}",
            f"release-source-build/{name}",
            n=1,
            lineterm="",
        )
    )


def published_vs_release_source(work: pathlib.Path) -> dict:
    """Each published tarball's files against a build of the recorded source; for a differing
    file other than README.md and package.json, the unified diff (published first)."""
    root = work / "unpacked"
    out = {}
    for n in ("client", "langchain", "vercel", "react", "llamaindex"):
        pub = root / f"agentcc-{n}-1.0.0" / "package"
        loc = root / f"local-release-source/agentcc-{n}-1.0.0" / "package"
        if not (pub.exists() and loc.exists()):
            continue
        result = _diff_trees(_tree(pub), _tree(loc))
        result["text_diffs"] = {
            f: _text_diff(pub / f, loc / f, f)
            for f in result["differ"]
            if f not in NOT_BUILT
        }
        out[f"@agentcc/{n}@1.0.0"] = result
    return out


def problems(artifacts: dict, registry: dict) -> list[str]:
    """Every reason the artifacts are not the published ones (empty when they are)."""
    out = []
    wheel = artifacts.get("pypi_agentcc_1_0_0", {})
    if not wheel.get("registry_match"):
        out.append("the PyPI wheel's sha256 is not the registry's")
    if not wheel.get("prefix_match"):
        out.append(
            f"the PyPI wheel's sha256 does not start with {EXPECTED_WHEEL_SHA256_PREFIX}"
        )
    npm = artifacts.get("npm", {})
    for spec in PUBLISHED:
        entry = npm.get(spec)
        if entry is None:
            out.append(f"{spec}: no tarball was packed")
            continue
        if not entry.get("registry_match"):
            out.append(f"{spec}: the tarball is not the registry's dist for {spec}")
        if not entry.get("npm_pack_match"):
            out.append(f"{spec}: npm pack reported other hashes than the tarball's")
        name = spec.rsplit("@", 1)[0]
        if not registry.get("packages", {}).get(name, {}).get("published"):
            out.append(f"{name}: npm view does not list it as published")
    if not npm.get(CLIENT, {}).get("prefix_match"):
        out.append(
            f"{CLIENT}: the shasum does not start with {EXPECTED_CLIENT_SHASUM_PREFIX}"
        )
    return out


def main(argv: list[str]) -> int:
    out, work, src98 = (pathlib.Path(a) for a in argv[1:4])
    registry = npm_registry(out)
    artifacts = {
        "tools": (out / "tools.txt").read_text().splitlines(),
        "pypi_agentcc_1_0_0": pypi(out, work, src98),
        "npm": npm_artifacts(out, work, registry),
        "published_vs_release_source_build": published_vs_release_source(work),
    }
    found = problems(artifacts, registry)
    artifacts["hash_check"] = {"ok": not found, "problems": found}
    for name, data in (("artifacts.json", artifacts), ("registry-npm.json", registry)):
        (out / name).write_text(
            json.dumps(data, indent=1, sort_keys=True, ensure_ascii=True) + "\n"
        )
    print(f"summarize_artifacts: hashes {'MISMATCH' if found else 'MATCH'}")
    for problem in found:
        print("  -", problem)
    return 1 if found else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
