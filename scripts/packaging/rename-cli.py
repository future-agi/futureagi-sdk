#!/usr/bin/env python3
"""Rename the SDK executable, not its distribution or plugin group (Python 3.10+).

Run from any directory: python scripts/packaging/rename-cli.py NEW_NAME [--dry-run].
The current name comes from python/pyproject.toml, so a second choice replaces the
first and repeating the same choice is a no-op. Command/flag names are reserved,
including nested subcommands and aliases, so later swaps cannot rewrite them.
Only tracked SDK sources, tests, installed-wheel journeys, examples and
documentation are considered; bytes/newlines outside matches stay unchanged.
No imports of the SDK, installed metadata, installer or network calls.

The top-level commands were checked against _cli/main.py, _cli/registry.py and
all five modules in [tool.poetry.plugins."futureagi.cli"]. agent_runs contributes
agents runs, not a top-level agent-runs command. Legacy/documented spellings are
also covered. Bare "the futureagi version" is a distribution noun, not a command.
"""
from __future__ import annotations

import argparse
import os
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[2]
SCOPE = (
    "python/pyproject.toml", "python/fi", "python/tests", "python/README.md",
    "python/CHANGELOG.md", "CHANGELOG.md", "examples",
    "python/futureagi-webhooks/README.md", "typescript/futureagi/README.md",
    "scripts/journeys/installed_cli.py", "scripts/journeys/test_cli_entrypoint.py",
)
COMMANDS = (
    "doctor", "login", "logout", "webhooks", "agents", "evals", "run", "upload",
    "agent-runs", "experiments", "auth", "--help", "-h", "--version",
)
# Keep nested commands/aliases reserved too: `tool webhooks list --help` must
# never become `tool webhooks NEXT --help` on a subsequent swap from `list`.
# These are not executable heads, so they must not be added to COMMANDS above.
RESERVED_NAMES = frozenset((*COMMANDS, "version",
    "list", "ls", "get", "show", "create", "update", "enable", "disable", "test",
    "deliveries", "delivery", "redeliver", "rotate-secret", "revoke-previous-secret",
    "delete", "rm", "events", "verify",
    "validate", "plan", "apply", "export", "import", "runs", "send", "cancel",
    "interrupt", "resume", "retry", "fork", "tree", "observations", "evidence",
    "proof-pack", "control-status", "approvals", "list-approvals", "rating-get",
    "rating-set", "ratings-summary", "ratings-trajectory", "wait", "wait-for-approval",
))
NAME = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]*\Z")


def current_name(text: str) -> str:
    table = re.search(r"(?ms)^\[tool\.poetry\.scripts\][ \t]*\r?\n(.*?)(?=^\[|\Z)", text)
    if table is None:
        raise ValueError("missing [tool.poetry.scripts]")
    entries = list(re.finditer(
        r'''(?m)^[ \t]*(?P<quote>["']?)(?P<name>[A-Za-z0-9][A-Za-z0-9._-]*)(?P=quote)[ \t]*=[ \t]*["']fi\._cli\.main:main["']''',
        table[1],
    ))
    if len(entries) != 1:
        raise ValueError("expected exactly one fi._cli.main:main console script")
    return entries[0]["name"]


def tracked_paths(root: Path) -> list[Path]:
    result = subprocess.run(
        ["git", "-C", str(root), "ls-files", "-z", "--", *SCOPE],
        check=True, capture_output=True, env={**os.environ, "GIT_NO_LAZY_FETCH": "1"},
    )
    paths = [root / os.fsdecode(p) for p in result.stdout.split(b"\0") if p]
    # Do not follow a tracked symlink out of the checkout (including its parents).
    return sorted(p for p in paths if p.is_file() and not p.is_symlink()
                  and not any(parent.is_symlink() for parent in p.parents if parent != root))


def rewrite(text: str, relative: str, old: str, new: str) -> tuple[str, int]:
    """Match executable contexts, never perform a global package-name replacement."""
    name = rf"(?P<name>{re.escape(old)})"
    boundary = r"(?:(?<![\w./@-])|(?<=\\n))"
    end = r"(?=$|[\s`\"'\\,.;:|)/\]])"
    commands = "|".join(re.escape(c) for c in COMMANDS)
    patterns = [
        boundary + name + rf"(?=[ \t]+(?:{commands}){end})",
        boundary + name + r"(?=[ \t]+(?:COMMAND\b|\[-h\]))",
        # version without -- is only a command with an explicit shell/code cue.
        r"(?:^[ \t]*(?:\$[ \t]+)?|[`\"']|Run: |usage: )" + name + r"(?=[ \t]+version\b)",
        boundary + name + r"(?=`{0,2} (?:CLI\b|binary\b|entry point\b|command(?: line| group)?\b))",
        r'''\bprog\s*=\s*["']''' + name + r'''(?=["'])''',
        # Command builders and argv assertions, not lists of distribution owners.
        r'''shlex\.join\(\[["']''' + name + r'''(?=["'],)''',
        r'''["']argv["'], \[["']''' + name + r'''(?=["'],)''',
        r'''\[["']''' + name + rf'''(?=["'], ["'](?:{commands})["'])''',
    ]
    scoped = {
        "python/fi/_cli/main.py": [r'version=f"' + name + r'(?= \{installed_version\})'],
        "python/fi/_cli/registry.py": [r'f"' + name + r'(?=: )'],
        "scripts/journeys/installed_cli.py": [
            r'''Path\(sysconfig\.get_path\(["']scripts["']\)\)[ \t]*/[ \t]*["']''' + name + r'''(?=["'])''',
        ],
        "scripts/journeys/test_cli_entrypoint.py": [
            r'''cfg\.(?:has_option|set|remove_option)\(["']console_scripts["'],[ \t]*["']''' + name + r'''(?=["'])''',
            r'''shutil\.which\(["']''' + name + r'''(?=["'])''',
        ],
        "python/tests/test_cli_core.py": [
            r"Resume with: " + name + r"(?= (?:\{|thing\b))",
        ],
        "python/tests/experiments/unit/test_upload_review.py": [
            r'resume\[0\] == "' + name + r'(?=")',
        ],
        "python/tests/evals/test_provenance.py": [
            r'assert names == \["' + name + r'(?="\])',
        ],
        "python/tests/test_namespace_ownership_footprint.py": [
            r'"console_scripts": \["' + name + r'(?="\])',
            r'"bin/' + name + r'(?=")',
            r'"C:' + name + r'(?=")',
        ],
    }
    if relative in {
        "python/tests/test_namespace_ownership_footprint.py",
        "python/tests/test_namespace_ownership_aliases.py",
    }:
        # Only launcher names, not assert_manual_only's distribution-owner names.
        patterns += [
            r'(?<=")' + name + r'(?=\.exe"|-script\.py")',
            r'@pytest\.mark\.parametrize\("script", \["' + name + r'(?=")',
        ]
    patterns += scoped.get(relative, [])
    spans = set()
    for pattern in patterns:
        spans.update(match.span("name") for match in re.finditer(pattern, text, flags=re.MULTILINE))
    # A package after pip is still a package even when the following token happens
    # to be a CLI command/flag (e.g. pip install futureagi --version).
    installs = [match.span() for match in re.finditer(
        r"\bpip(?:3)?[ \t]+(?:install|uninstall|show|download|wheel)\b[^`\n;&|]*", text,
    )]
    spans = {span for span in spans if not any(start <= span[0] < stop for start, stop in installs)}
    # This test scans arbitrary commands with a regex: escape punctuation in the
    # chosen executable, rather than making '.' a wildcard on subsequent swaps.
    regex_context = 'return set(re.findall(r"`?' + re.escape(old) + ' ([a-z][a-z-]*)", text))'
    regex_replacement = 'return set(re.findall(r"`?' + re.escape(new) + ' ([a-z][a-z-]*)", text))'
    edits = {span: new for span in spans}
    # Quote dotted executable names so TOML does not interpret them as dotted keys.
    # Also covers embedded pyproject snippets in tests; \n may be escaped.
    binding = (boundary + r'''(?P<key>(?P<quote>["']?)''' + re.escape(old)
               + r'''(?P=quote))(?=[ \t]*=[ \t]*["']fi\._cli\.main:main["'])''')
    for match in re.finditer(binding, text):
        edits[match.span("key")] = f'"{new}"' if "." in new else new
    for (start, stop), replacement in sorted(edits.items(), reverse=True):
        text = text[:start] + replacement + text[stop:]
    count = len(edits)
    if relative == "python/tests/experiments/unit/test_review_fixes.py" and regex_context in text:
        text = text.replace(regex_context, regex_replacement)
        count += 1
    return text, count


def rename(root: Path, new: str, *, dry_run: bool = False) -> tuple[int, int]:
    if not NAME.fullmatch(new):
        raise ValueError("NEW_NAME must start with an ASCII letter/digit and contain only letters, digits, '.', '_' or '-'")
    if new in RESERVED_NAMES:
        raise ValueError("NEW_NAME must not equal a subcommand or flag; choose a distinct executable name")
    project = root / "python/pyproject.toml"
    old = current_name(project.read_bytes().decode("utf-8"))
    main = (root / "python/fi/_cli/main.py").read_bytes().decode("utf-8")
    if not re.search(r'''\bprog\s*=\s*["']''' + re.escape(old) + r'''["']''', main):
        raise ValueError("main.py prog and the console script disagree; refusing a partial rename")
    changes = []
    if old != new:
        for path in tracked_paths(root):
            raw = path.read_bytes()
            if b"\0" in raw:
                continue
            try:
                before = raw.decode("utf-8")
            except UnicodeDecodeError:
                continue
            after, count = rewrite(before, path.relative_to(root).as_posix(), old, new)
            if after != before:
                changes.append((path, after.encode("utf-8"), count))
        if not any(path == project for path, _, _ in changes):
            raise ValueError("python/pyproject.toml is not tracked; nothing was written")
    for path, data, count in changes:
        if not dry_run:
            path.write_bytes(data)
        print(f"{path.relative_to(root)}: {count}")
    occurrences = sum(count for _, _, count in changes)
    verb = "Would rename" if dry_run else "Renamed"
    print(f"{verb} {old} -> {new}: {len(changes)} files, {occurrences} occurrences")
    return len(changes), occurrences


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("new_name", metavar="NEW_NAME")
    parser.add_argument("--dry-run", action="store_true", help="show counts without changing files")
    args = parser.parse_args()
    try:
        rename(ROOT, args.new_name, dry_run=args.dry_run)
    except (ValueError, OSError, subprocess.CalledProcessError) as exc:
        parser.error(str(exc))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
