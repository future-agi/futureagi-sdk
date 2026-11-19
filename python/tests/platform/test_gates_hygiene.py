"""The hygiene scan and the lints over the public platform files."""

from __future__ import annotations

import copy
import os
import re
import subprocess
import typing
from pathlib import Path

import pytest

from ._gates_support import REPO, SCOPED, guard_sockets, load, read_json


@pytest.fixture(autouse=True)
def no_egress(monkeypatch: pytest.MonkeyPatch) -> None:
    guard_sockets(monkeypatch)


@pytest.fixture(scope="module")
def spec() -> dict[str, typing.Any]:
    return read_json(SCOPED)


CASES = REPO / "scripts" / "platform" / "test" / "hygiene-cases.json"
# Each leak is assembled, so this file itself passes the scan it tests.
LEAK = "see /Vol" + "umes/x and zz-example-internal"


def _scanner() -> typing.Any:
    return load("platform_hygiene", "scripts/platform/hygiene_scan.py")


def _with_case_names(scan: typing.Any) -> dict[str, typing.Any]:
    """The real rules plus the made-up names of the shared cases (no real internal name is spelled here)."""
    rules = scan.load_rules()
    extra = {scan.sha256(name): rule for rule, name in read_json(CASES)["names"]}
    rules["names"] = {
        **rules["names"],
        "sha256": {**rules["names"]["sha256"], **extra},
    }
    return rules


def _tree(root: Path, files: dict[str, str]) -> None:
    for rel, text in files.items():
        (root / rel).parent.mkdir(parents=True, exist_ok=True)
        (root / rel).write_text(text, encoding="utf-8")


def test_hygiene_scan_is_clean() -> None:
    scan = _scanner()
    count, hits = scan.scan_paths(list(scan.DEFAULT_PATHS), scan.load_rules())
    assert count > 0
    assert hits == []
    files = scan.list_files(list(scan.DEFAULT_PATHS))
    assert scan.RULES_PATH in files, "the rule file is scanned and passes its own scan"
    assert scan.load_rules()["names"]["sha256"]
    for core in (
        "python/fi/_core/policy.py",
        "typescript/futureagi/src/_core/policy.ts",
        "typescript/futureagi/src/_core/__tests__/gates.test.ts",
    ):
        assert core in files, f"the default scan covers the platform cores: {core}"


def test_the_shared_cases_agree_with_the_node_scanner() -> None:
    scan = _scanner()
    rules = _with_case_names(scan)
    cases = read_json(CASES)
    for case in cases["text"]:
        got = sorted(
            h["rule"] for h in scan.scan_text(case["text"], case["ext"], rules)
        )
        assert got == sorted(case["rules"]), case["text"]
    for case in cases["candidates"]:
        assert scan.name_candidates(case["line"], case["maxWords"]) == case["expect"]


def test_outside_git_no_file_is_skipped_for_its_name_or_extension(
    tmp_path: Path,
) -> None:
    scan = _scanner()
    _tree(
        tmp_path,
        {
            "kit/cases/x/hygiene-rules.json": '{"note": "' + LEAK + '"}',
            "kit/notes.csv": LEAK,
            "kit/dist/out.txt": LEAK,
            "kit/__pycache__/x.txt": LEAK,
        },
    )
    (tmp_path / "kit" / "blob.bin").write_bytes(b"abc\0def")
    _, hits = scan.scan_paths(["kit"], _with_case_names(scan), root=tmp_path)
    assert sorted(f"{h['file']} {h['rule']}" for h in hits) == [
        "kit/blob.bin not-text",
        "kit/cases/x/hygiene-rules.json gcp-project",
        "kit/cases/x/hygiene-rules.json volumes-path",
        "kit/dist/out.txt gcp-project",
        "kit/dist/out.txt volumes-path",
        "kit/notes.csv gcp-project",
        "kit/notes.csv volumes-path",
    ]


def test_in_a_git_checkout_the_scan_reads_what_git_would_commit(
    tmp_path: Path,
) -> None:
    scan = _scanner()
    _tree(
        tmp_path,
        {
            ".gitignore": "kit/ignored/\n",
            "kit/tracked.md": LEAK,
            "kit/ignored/a.txt": LEAK,
            "kit/ignored/forced.txt": LEAK,
            "kit/new.txt": LEAK,
        },
    )
    env = {**os.environ, "GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_NOSYSTEM": "1"}

    def git(*args: str) -> None:
        base = ["git", "-c", "user.name=t", "-c", "user.email=t@example.com"]
        subprocess.run(
            [*base, "-c", "commit.gpgsign=false", *args],
            cwd=tmp_path,
            env=env,
            check=True,
            capture_output=True,
            timeout=60,
        )

    git("init", "-q")
    git("add", ".gitignore", "kit/tracked.md")
    git("add", "-f", "kit/ignored/forced.txt")
    git("commit", "-q", "-m", "base")
    expected = ["kit/ignored/forced.txt", "kit/new.txt", "kit/tracked.md"]
    assert scan.list_files(["kit"], tmp_path) == expected
    _, hits = scan.scan_paths(["kit"], _with_case_names(scan), root=tmp_path)
    assert sorted({h["file"] for h in hits}) == expected


def test_a_malformed_names_block_is_a_hit(tmp_path: Path) -> None:
    scan = _scanner()
    rules = scan.load_rules()
    rules["names"] = {"maxWords": 0, "sha256": {"ABC": "rig", scan.sha256("x"): ""}}
    _, hits = scan.scan_paths(["none"], rules, root=tmp_path)
    assert [h["rule"] for h in hits] == ["invalid-names"] * 3


def test_hygiene_scan_catches_what_the_scoped_spec_must_not_carry(
    spec: dict[str, typing.Any]
) -> None:
    scan = load("platform_hygiene", "scripts/platform/hygiene_scan.py")
    rules = scan.load_rules()
    dirty = copy.deepcopy(spec)
    op = dirty["paths"]["/workspace/deployments"]["post"]
    op["x-omega-auth-authority"] = "workspace"
    op["x-omega-idempotency"] = {"durable": True, "evidence": "kept somewhere"}
    dirty["components"]["schemas"]["Probe"] = {
        "type": "object",
        "properties": {"x-omega-shaped-property": {"type": "string"}},
    }
    rules_hit = sorted(f["rule"] for f in scan.structural_findings(dirty, rules))
    assert rules_hit == [
        "extension-not-allowed",
        "extension-subkey-not-allowed",
        "forbidden-key",
    ]
    leak = "see " + "/Vol" + "umes/x and " + "workspace/service" + ".ts"
    assert {h["rule"] for h in scan.scan_text(leak, ".json", rules)} == {
        "volumes-path",
        "ee-source-path",
        "source-ts-path",
    }


def _platform_sources() -> list[Path]:
    roots = [
        REPO / "scripts" / "platform",
        REPO / "python" / "tests" / "platform",
        REPO / "tests" / "platform-conformance",
    ]
    roots += [
        REPO / "python" / "fi" / n
        for n in (
            "_core",
            "deployments",
            "sandboxes",
            "agents",
            "environments",
            "workspace",
        )
    ]
    roots += [
        REPO / "typescript" / "futureagi" / "src" / n
        for n in (
            "_core",
            "deployments",
            "sandboxes",
            "agents",
            "environments",
            "workspace",
        )
    ]
    files = []
    for root in roots:
        for path in sorted(root.rglob("*")) if root.is_dir() else []:
            skip = {"node_modules", "__pycache__", "generated", "_gen"} & set(
                path.parts
            )
            if (
                path.is_file()
                and not skip
                and path.suffix in {".py", ".ts", ".mjs", ".js", ".cjs", ".sh"}
            ):
                files.append(path)
    return files


@pytest.mark.parametrize("tree", ["python", "typescript", "scripts", "tests"])
def test_platform_modules_stay_under_400_lines(tree: str) -> None:
    # Report SDK failures independently without exempting any existing source root.
    over = []
    for path in _platform_sources():
        if path.relative_to(REPO).parts[0] != tree:
            continue
        lines = len(path.read_text(encoding="utf-8").splitlines())
        if lines > 400:
            over.append(f"{path.relative_to(REPO)}: {lines}")
    assert over == []


URL_RULE = REPO / "scripts" / "platform" / "lint" / "url-path-rule.json"


def _url_path_hits(files: list[Path], root: Path) -> list[str]:
    """The no-url-paths lint in Python, from the same rule file as the Node lint."""
    rule = read_json(URL_RULE)
    literal = re.compile(rule["pattern"])
    skip_file = re.compile(rule["skipFiles"])
    comments = tuple(rule["commentPrefixes"])
    hits = []
    for path in files:
        rel = path.relative_to(root)
        if (
            set(rel.parts[:-1]) & set(rule["skipDirs"])
            or skip_file.search(path.name)
            or path.suffix not in rule["extensions"]
        ):
            continue
        lines = path.read_text(encoding="utf-8").splitlines()
        for number, line in enumerate(lines, start=1):
            if not line.strip().startswith(comments) and literal.search(line):
                hits.append(f"{rel.as_posix()}:{number}")
    return hits


@pytest.mark.parametrize("prefix", ["python/fi/", "typescript/futureagi/src/"], ids=["python", "typescript"])
def test_no_hand_written_url_paths_in_platform_modules(prefix: str) -> None:
    sources = [
        path
        for path in _platform_sources()
        if path.relative_to(REPO).as_posix().startswith(prefix)
    ]
    assert sources
    assert _url_path_hits(sources, REPO) == []


def test_the_url_path_rule_allows_the_mount_and_skips_test_fixtures(
    tmp_path: Path,
) -> None:
    files = {
        "src/_core/origins.ts": 'export const PLATFORM_PATH = "/omega/api";\n',
        "src/_core/client.ts": (
            'const p = "/omega/api/workspace/x";\n'
            "const q = `/workspace/sandboxes`;\n"
            '// "/workspace/in-a-comment"\n'
        ),
        "src/_core/__fixtures__/platform.ts": 'path: "/workspace/sandboxes",\n',
        "src/_core/__tests__/a.test.ts": 'path: "/workspace/sandboxes",\n',
        "fi/_core/test_x.py": 'PATH = "/agentcc/api-keys"\n',
        "fi/_core/_client.py": 'PATH = "/agentcc/api-keys"\n',
    }
    for rel, text in files.items():
        (tmp_path / rel).parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / rel).write_text(text, encoding="utf-8")
    found = _url_path_hits(
        sorted(p for p in tmp_path.rglob("*") if p.is_file()), tmp_path
    )
    assert found == [
        "fi/_core/_client.py:1",
        "src/_core/client.ts:1",
        "src/_core/client.ts:2",
    ]


def test_a_hygiene_exemption_covers_one_line_by_its_hash_and_rule(
    tmp_path: Path,
) -> None:
    scan = _scanner()
    marker = "/Vol" + "umes/"  # assembled, so this file passes the scan it tests
    exempt = f'(re.compile(r"{marker}x"), "a local path"),'
    entry = {
        "path": "gates.py",
        "lineSha256": scan.sha256(exempt),
        "rules": ["volumes-path"],
        "why": "its pattern list",
    }
    rules = {**scan.load_rules(), "exemptions": [entry]}
    gates = tmp_path / "gates.py"

    def found() -> list[tuple[int, str]]:
        _, hits = scan.scan_paths(["gates.py"], rules, root=tmp_path)
        return sorted((h["line"], h["rule"]) for h in hits)

    gates.write_text(f"    {exempt}\nsee {marker}x\n", encoding="utf-8")
    assert found() == [(2, "volumes-path")]
    gates.write_text(f"    {exempt}  # edited\n", encoding="utf-8")
    assert found() == [(0, "stale-exemption"), (1, "volumes-path")]
    gates.write_text(f"    {exempt}\n", encoding="utf-8")
    assert found() == []
    entry["rules"] = ["home-path"]
    assert found() == [(0, "stale-exemption"), (1, "volumes-path")]
    entry["rules"] = ["volumes-path"]
    entry["lineSha256"] = exempt
    assert (0, "invalid-exemption") in found(), "a plain-text line is not accepted"
