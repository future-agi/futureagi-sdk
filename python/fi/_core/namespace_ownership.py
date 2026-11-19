"""Read-only distribution ownership checks shared by the wheel gate and doctor."""
from __future__ import annotations

import base64
import csv
import hashlib
import io
from importlib import metadata
import json
from pathlib import Path, PurePosixPath
import re
from typing import Any, Iterable

def manifest() -> dict[str, Any]:
    """Read the versioned ownership contract shipped in the wheel."""
    return json.loads(Path(__file__).with_suffix(".json").read_text(encoding="utf-8"))


def canonical_name(name: str) -> str:
    """Normalize a distribution name using Python packaging's separator rules."""
    return re.sub(r"[-_.]+", "-", name).lower()


def matches(path: str, pattern: str) -> bool:
    """Match an exact file, directory prefix, or top-level namespace family."""
    if pattern.endswith("*"):
        return path.split("/", 1)[0].startswith(pattern[:-1]) and "/" in path
    return path.startswith(pattern) if pattern.endswith("/") else path == pattern


def policy(name: str, rules: dict[str, Any]) -> dict[str, Any] | None:
    """Return a distribution's ownership rule, including instrumentation families."""
    name = canonical_name(name)
    if name in rules["distributions"]:
        return rules["distributions"][name]
    return next((rule for prefix, rule in rules["distribution_families"].items()
                 if name.startswith(prefix)), None)


def supported_version(version: str, rule: dict[str, Any]) -> bool:
    """Require a stable minimum version without adding a packaging dependency."""
    minimum = rule.get("minimum_version")
    if minimum is None:
        return True
    parsed = re.fullmatch(r"(\d+)\.(\d+)\.(\d+)(?:\.post\d+)?(?:\+[a-zA-Z0-9.-]+)?", version)
    return bool(parsed and tuple(map(int, parsed.groups())) >= tuple(minimum))


def owns(name: str, path: str, rules: dict[str, Any]) -> bool:
    """Whether a supported distribution may ship this installed runtime path."""
    rule = policy(name, rules)
    if rule is None or any(matches(path, p) for p in rules["forbidden_paths"]):
        return False
    return (any(matches(path, p) for p in rule["paths"])
            and not any(matches(path, p) for p in rule.get("excludes", [])))


def file_digest(path: Path, algorithm: str) -> str:
    """Compute the URL-safe, unpadded digest used by wheel RECORD."""
    if algorithm not in {"sha256", "sha384", "sha512"}:
        raise ValueError("unsupported RECORD hash algorithm")
    digest = hashlib.new(algorithm)
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return base64.urlsafe_b64encode(digest.digest()).rstrip(b"=").decode("ascii")


def _usable_uninstall_record(dist: Any, rows: list[list[str]]) -> bool:
    """Require RECORD to cover this installation's identifying metadata."""
    info = getattr(dist, "_path", None)
    if not rows or not isinstance(info, Path) or not info.name.endswith(".dist-info"):
        return False
    required = {f"{info.name}/METADATA", f"{info.name}/RECORD"}
    if dist.read_text("entry_points.txt") is not None:
        required.add(f"{info.name}/entry_points.txt")
    return required <= {str(PurePosixPath(row[0])) for row in rows if row}


def _record_paths(owner: dict[str, Any]) -> dict[str, Path]:
    """Keep lexical claims; the SIMPLE audit fails closed on unknown locations."""
    from .namespace_footprint import lexical_records
    try:
        return lexical_records(owner)
    except (OSError, RuntimeError, ValueError):
        return {}


def _may_delete(target: Path, protected: Path) -> bool:
    """Include directory claims, path aliases and pip's implicit bytecode removal."""
    left, right = str(target).casefold(), str(protected).casefold()
    if left == right or left.startswith(right + "/") or right.startswith(left + "/"):
        return True
    if str(target).endswith(".py") and str(protected).endswith((".pyc", ".pyo")):
        return (str(protected)[:-1].casefold() == left
                or (str(protected.parent).casefold() == str(target.parent / "__pycache__").casefold()
                    and protected.name.casefold().startswith(target.name[:-3].casefold() + ".")))
    return False


def _safe_repairs(manual: list[str], commands: list[tuple[str, str]],
                  inventory: dict[str, list[dict[str, Any]]], rules: dict[str, Any],
                  affected: set[str]) -> list[str]:
    """Gate EVERY destructive step on SIMPLE footprints and supported ownership."""
    from .namespace_footprint import SimpleState, physical_namespace_paths, script_names

    blocked: list[str] = []
    supported = [(name, owner, _record_paths(owner))
                 for name, installs in inventory.items() for owner in installs if owner["supported"]]
    audit = SimpleState()
    namespace_errors = audit.namespace_errors(
        [(name, owner, policy(name, rules)["paths"]) for name, owner, _ in supported])
    uncertain = {
        n: "malformed RECORD leaves an incomplete inventory" if any(o["malformed_record"] for o in group)
        else "editable source ownership cannot be bounded by RECORD"
        for n, group in inventory.items() if any(
            o["malformed_record"] or (o["editable"] and (o["supported"] or n in affected)) for o in group)
    }
    for name in sorted({name for name, _ in commands}):
        installs = inventory.get(name, [])
        reasons = [f"{n}'s {reason}" for n, reason in sorted(uncertain.items())]
        protected_names = set(uncertain)
        shared: set[str] = set()
        unverified: set[str] = set()
        if len(installs) != 1:
            reasons.append("the uninstall target is absent or ambiguous")
        for owner in installs:
            if not owner["record"] or not owner["valid_record"]:
                reasons.append("no complete, valid uninstall RECORD is available")
            if not owner["valid_scripts"]:
                reasons.append("entry-point or distutils script paths cannot be established; "
                               "wrapper removal cannot be bounded")
            paths, simple_errors = audit.removal_paths(owner)
            reasons.extend(simple_errors)
            for protected_name, error in namespace_errors:
                protected_names.add(protected_name)
                reasons.append(f"{protected_name}'s {error}")
            if simple_errors or namespace_errors or uncertain:
                unverified.update(path for path, _ in paths)
            scripts = script_names(owner)
            for other_name, other, protected in supported:
                if other is owner:
                    continue  # Replacing this owner's own exclusive files is safe.
                other_scripts = script_names(other)
                if not other["valid_scripts"]:
                    protected_names.add(other_name)
                    shared.update(script for _, script in other["scripts"])
                    reasons.append(f"{other_name}'s entry-point or distutils script paths cannot be established")
                script_overlap = scripts & other_scripts
                script_overlap.update(path for path, p in protected.items()
                                      if p.name.casefold() in scripts
                                      or PurePosixPath(path).name.casefold() in scripts)
                script_overlap.update(path for path, target in paths
                                      if target.name.casefold() in other_scripts
                                      or PurePosixPath(path).name.casefold() in other_scripts
                                      or (other_scripts and target.is_dir()))
                if script_overlap:
                    protected_names.add(other_name)
                    shared.update(script_overlap)
                    reasons.append("entry-point wrappers may be removed independently of RECORD")
                if other["metadata_path"] is None:
                    protected_names.add(other_name)
                    reasons.append(f"{other_name}'s metadata location is unknown")
                for path, target in paths:
                    claimed = (any(_may_delete(target, p) for p in protected.values())
                               or (other["metadata_path"] is not None
                                   and _may_delete(target, other["metadata_path"])))
                    physical = physical_namespace_paths(other, target, policy(other_name, rules)["paths"])
                    if physical is None:
                        reasons.append(f"{other_name}'s namespace mapping cannot be established")
                    possible = physical is None or any(owns(other_name, p, rules) for p in physical)
                    if simple_errors or namespace_errors:
                        aliases = physical_namespace_paths(other, target, policy(other_name, rules)["paths"],
                                                           diagnostic_aliases=True)
                        possible |= aliases is not None and any(owns(other_name, p, rules) for p in aliases)
                    if claimed or possible:
                        protected_names.add(other_name)
                        shared.add(path)
                        if not other["record"] or not other["valid_record"] or path not in protected:
                            reasons.append(f"{other_name}'s RECORD cannot establish complete shared-file ownership")
                        elif claimed:
                            reasons.append(f"{other_name}'s RECORD claims a file in {name}'s removal footprint")
        if shared:
            reasons.append("the removal footprint includes files a supported distribution owns or needs")
        if reasons:
            names = ", ".join(sorted({name, *protected_names}))
            details = ", ".join(repr(path) for path in sorted(shared | unverified)) or "the target's RECORD paths"
            blocked.append(f"Manual repair required for {names}: {'; '.join(sorted(set(reasons)))} "
                           f"({details}). First back up or restore the supported owner's files, "
                           "then repair the diagnosed installation and its ownership metadata with "
                           "the original installer, then re-run futureagi-py doctor --offline. "
                           "Do not remove or replace supported companions.")
            for target, command in commands:
                if target == name:
                    blocked.append(f"Manual guidance for {name}: command text for reference only "
                                   f"(not a repair step): {command!r}. Do not run this command "
                                   "unless the ownership problem is resolved and a fresh "
                                   "futureagi-py doctor --offline check emits it for a SIMPLE state.")
    if blocked:
        return [*manual, *blocked, rules["repair_commands"][-1]]
    return [*manual, *(command for _, command in commands), rules["repair_commands"][-1]]


def _repair_commands(issues: list[dict[str, Any]], inventory: dict[str, list[dict[str, Any]]],
                     rules: dict[str, Any]) -> list[str]:
    """Address diagnosed owners only; unusable or ambiguous installs need manual repair."""
    if not issues:
        return []
    affected: dict[str, list[dict[str, Any]]] = {}
    invalid_records = {i["distribution"] for i in issues if i["kind"] == "invalid-record-path"}
    unrestorable = {name for name, installations in inventory.items()
                    if len(installations) > 1 or any(
                        owner["supported"] and (not owner["record"] or name in invalid_records)
                        for owner in installations)}
    manual_only: set[str] = set()
    for issue in issues:
        if "distribution" in issue:
            affected.setdefault(issue["distribution"], []).append(issue)
        elif issue["kind"] == "overlap" and unrestorable.intersection(issue["distributions"]):
            for name in set(issue["distributions"]):
                affected.setdefault(name, []).append(issue)
                manual_only.add(name)
    manual: list[str] = []
    steps: list[tuple[str, str]] = []
    for name, problems in sorted(affected.items()):
        details = ", ".join(sorted({repr(i["path"]) for i in problems if "path" in i})) or "metadata"
        installations = inventory[name]
        if len(installations) > 1:
            locations = "; ".join(sorted(
                f"version {i['version']!r} at {i['location']!r} "
                f"({'supported' if i['supported'] else 'unsupported'})" for i in installations))
            manual.append(f"Manual repair required for {name}: multiple installations share this "
                         f"name ({locations}). Use the original installer to target the diagnosed "
                         f"installation by metadata location ({details}); remove only a diagnosed "
                         "unsupported installation and its metadata, or correct a supported "
                         "installation without uninstalling it. Before continuing, preserve supported "
                         "companions and restore their shared files. Do not use name-only uninstall "
                         "or reinstall commands to resolve this ambiguity.")
            continue
        owner = installations[0]
        if not re.fullmatch(r"[a-z0-9](?:[a-z0-9-]*[a-z0-9])?", name):
            manual.append(f"Manual repair required for {name!r}: invalid distribution name; "
                         f"use the original installer to resolve {details} before continuing.")
        elif not owner["record"] or name in manual_only or name in invalid_records:
            action = ("repair this supported distribution's metadata and diagnosed entries"
                      if owner["supported"] else
                      "remove this distribution, including its metadata and diagnosed entries")
            reason = ("its RECORD contains invalid paths and cannot be trusted for uninstall"
                      if name in invalid_records else
                      "its diagnosed paths overlap an owner that cannot be safely restored automatically"
                      if name in manual_only else "no usable RECORD is available")
            manual.append(f"Manual repair required for {name}: {reason}. "
                         f"Use the original installer to {action} ({details}) before continuing; "
                         "preserve supported companions and restore any of their shared files.")
        elif not owner["supported"] and name != "futureagi":
            steps.append((name, f"pip uninstall {name}"))
        elif any(i["kind"] in {"legacy-console-script", "unowned-path", "invalid-record-path"}
                 for i in problems):
            manual.append(f"Manual repair required for {name}: obtain a corrected installation "
                         f"that no longer claims the diagnosed forbidden paths or console scripts "
                         f"({details}) before continuing; do not uninstall supported companions.")
    for issue in issues:
        if issue["kind"] != "overlap":
            continue
        names = set(issue["distributions"])
        if not names & affected.keys():
            manual.append(f"Manual repair required for {', '.join(sorted(names))}: resolve "
                         f"duplicate ownership metadata for {issue['path']!r} with the original "
                         "installer before continuing; preserve supported companions.")
    steps.extend(("futureagi", command) for command in rules["repair_commands"][:-1])
    return _safe_repairs(manual, steps, inventory, rules, set(affected) | {n for n, _ in steps})


def inspect_installed(distributions: Iterable[Any] | None = None) -> dict[str, Any]:
    """Inspect RECORD ownership and integrity; uninstalled source is not certified."""
    # Keep policy-only loading by the standalone wheel gate dependency-free.
    from .namespace_footprint import distutils_scripts

    rules = manifest()
    issues: list[dict[str, Any]] = []
    owners: dict[str, list[str]] = {}
    logical: dict[str, str] = {}
    installed = []
    editable_installs = []
    inventory: dict[str, list[dict[str, Any]]] = {}
    checked = 0
    source = metadata.distributions() if distributions is None else distributions
    for dist in source:
        name = canonical_name(dist.metadata.get("Name", ""))
        version = dist.version
        rule = policy(name, rules)
        if rule is not None or name in rules["unsupported_distributions"]:
            installed.append({"name": name, "version": version})
        if name in rules["unsupported_distributions"] or (rule and not supported_version(version, rule)):
            issues.append({"kind": "unsupported-distribution", "distribution": name, "version": version})
        entries = list(dist.entry_points)
        scripts = [(entry.group, entry.name) for entry in entries
                   if entry.group in {"console_scripts", "gui_scripts"}]
        info = getattr(dist, "_path", None)
        implicit_scripts, complete_scripts = distutils_scripts(info)
        scripts.extend(implicit_scripts)
        for entry in entries:
            if entry.group == "console_scripts" and entry.name in rules["forbidden_console_scripts"]:
                issues.append({"kind": "legacy-console-script", "distribution": name, "path": entry.name})
        # Read RECORD directly: Distribution.files may hide absent files.
        record = dist.read_text("RECORD")
        rows, malformed = [], False
        reader = csv.reader(io.StringIO(record or ""), strict=True)
        try:
            for row in reader:
                if not any(field.strip() for field in row):
                    continue
                if len(row) != 3:
                    malformed = True
                    issues.append({"kind": "invalid-record", "distribution": name,
                                   "path": row[0] or "RECORD", "row": reader.line_num})
                else:
                    rows.append(row)
        except csv.Error:
            malformed = True
            issues.append({"kind": "invalid-record", "distribution": name,
                           "path": f"RECORD row {reader.line_num}", "row": reader.line_num})
        try:
            direct = json.loads(dist.read_text("direct_url.json") or "{}")
            editable = isinstance(direct, dict) and isinstance(direct.get("dir_info"), dict) \
                and direct["dir_info"].get("editable") is True
        except (OSError, ValueError, TypeError):
            editable = True  # Unknown source metadata cannot authorize a repair.
        inventory.setdefault(name, []).append({
            "editable": editable, "malformed_record": malformed,
            "record": _usable_uninstall_record(dist, rows),
            "rows": rows, "locate": getattr(dist, "locate_file", None),
            "metadata_path": info.absolute() if isinstance(info, Path) else None,
            "scripts": scripts,
            "valid_scripts": complete_scripts and all(
                script and script not in {".", ".."}
                and not any(c in script for c in ":/\\\x00") for _, script in scripts),
            "valid_record": not malformed and all(row[0] and "\x00" not in row[0]
                                and not any(c in row[0] for c in ":\\")
                                and not PurePosixPath(row[0]).is_absolute()
                                and ".." not in PurePosixPath(row[0]).parts for row in rows),
            "supported": bool(rule and supported_version(version, rule)
                              and name not in rules["unsupported_distributions"]),
            "version": version,
            "location": str(getattr(dist, "_path", "unknown metadata location")),
        })
        if record is None:
            if rule is not None or name in rules["unsupported_distributions"]:
                issues.append({"kind": "missing-record", "distribution": name})
            continue
        editable_install = False
        checked_before = checked
        if name == "futureagi" and not malformed:
            from fi._core.editable_ownership import inspect_editable

            try:
                editable_install = inspect_editable(dist, rows)
                if editable_install:
                    editable_installs.append(name)
            except (OSError, ValueError, TypeError, SyntaxError):
                issues.append({"kind": "invalid-editable-mapping", "distribution": name})
        for path, digest, size in rows:
            if not path.startswith("fi/"):
                continue
            parts = PurePosixPath(path).parts
            if ".." in parts or "\\" in path:
                issues.append({"kind": "invalid-record-path", "distribution": name, "path": path})
                continue
            # Generated bytecode is not wheel-owned; pip records it without hashes.
            if "__pycache__" in parts or path.endswith(".pyc"):
                continue
            target = Path(dist.locate_file(path))
            identity = str(target.absolute())
            owners.setdefault(identity, []).append(name)
            logical[identity] = path
            if not owns(name, path, rules):
                issues.append({"kind": "unowned-path", "distribution": name, "path": path})
            if name != "futureagi":
                continue
            checked += 1
            try:
                if not target.is_file():
                    issues.append({"kind": "missing-file", "distribution": name, "path": path})
                elif not digest or "=" not in digest:
                    issues.append({"kind": "missing-hash", "distribution": name, "path": path})
                elif (file_digest(target, digest.split("=", 1)[0]) != digest.split("=", 1)[1]
                      or (size and target.stat().st_size != int(size))):
                    issues.append({"kind": "hash-mismatch", "distribution": name, "path": path})
            except (OSError, ValueError):
                issues.append({"kind": "unreadable-file", "distribution": name, "path": path})
        if name == "futureagi" and checked == checked_before and not editable_install:
            issues.append({"kind": "empty-runtime-record", "distribution": name})
    for identity, names in owners.items():
        if len(names) > 1:
            issues.append({"kind": "overlap", "path": logical[identity], "distributions": sorted(names)})
    present = any(d["name"] == "futureagi" for d in installed)
    repair = _repair_commands(issues, inventory, rules)
    return {"status": "FAIL" if issues else ("PASS" if present else "NOT-INSTALLED"),
            "checked_files": checked, "distributions": installed, "issues": issues,
            "editable_installs": editable_installs, "repair_commands": repair}
