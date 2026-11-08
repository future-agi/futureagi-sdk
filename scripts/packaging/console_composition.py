"""Account for every Console test module in enabled and withdrawn compositions."""
import ast
import hashlib
import re
from pathlib import Path

# Counts distinguish test declarations (the historical fifty Python tests) from
# collected parametrizations. Both are pinned; neither is credited as a pass
# when its module is withdrawn.
CONSOLE_TESTS = (
    ("python/tests/core/test_agent_runs.py", 16, 89),
    ("python/tests/core/test_agent_code.py", 18, 36),
    ("python/tests/core/test_composed_agent_registration.py", 3, 6),
    ("python/tests/platform/test_console_facades.py", 11, 489),
    ("python/tests/platform/test_agent_code_async.py", 2, 7),
    ("typescript/futureagi/src/agents/console.test.ts", 7, 216),
    ("typescript/futureagi/src/agents/runs/__tests__/runs.test.ts", 13, 38),
)
DELETE_ROOTS = (
    "python/fi/agents", "python/fi/environments",
    "typescript/futureagi/src/agents", "typescript/futureagi/src/environments",
    "scripts/platform/generate-console.py",
    *(name for name, _, _ in CONSOLE_TESTS if name.endswith(".py")),
)


def files(root):
    return {p.relative_to(root).as_posix() for p in root.rglob("*")
            if p.is_file() and not set(p.relative_to(root).parts) & {".git", "node_modules", "__pycache__", ".pytest_cache"}}


def is_test(name):
    p = Path(name)
    return (p.name.startswith("test_") and p.suffix == ".py") or p.name.endswith((".test.ts", ".test.js", ".spec.ts"))


def declarations(path):
    text = path.read_text()
    if path.suffix == ".py":
        return sum(isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name.startswith("test_")
                   for n in ast.walk(ast.parse(text)))
    return len(re.findall(r"^\s*(?:test|it)(?:\(|\.each\()", text, flags=re.M))


def begin(root, composition):
    root = Path(root)
    assert composition in ("WITHDRAWN", "D-2"), composition
    before = files(root)
    identities = []
    for name, count, collected in CONSOLE_TESTS:
        assert name in before, "Missing Console module before composition: " + name
        assert declarations(root / name) == count, "Console test declaration count changed: " + name
        identities.append({"id": "console-module:" + name, "module": name,
                           "test_count": count, "collected_test_count": collected,
                           "sha256": hashlib.sha256((root / name).read_bytes()).hexdigest(),
                           "status": "ABSENT" if composition == "WITHDRAWN" else "PRESENT"})
    for name in DELETE_ROOTS:
        assert (root / name).exists(), "Missing deletion root: " + name
    planned = {name for name in before if any(name == p or name.startswith(p + "/") for p in DELETE_ROOTS)}
    assert {name for name in planned if is_test(name)} == {name for name, _, _ in CONSOLE_TESTS}, "Unregistered Console test deletion"
    return {"composition": composition, "identities": identities, "before": before,
            "planned": planned if composition == "WITHDRAWN" else set(),
            "test_hashes": {name: hashlib.sha256((root / name).read_bytes()).hexdigest()
                            for name in before if is_test(name)}}


def finish(root, snapshot):
    root = Path(root)
    after = files(root)
    removed = snapshot["before"] - after
    expected = snapshot["planned"]
    assert removed == expected, {"missing_deletions": sorted(expected - removed), "extra_deletions": sorted(removed - expected)}
    for name, digest in snapshot["test_hashes"].items():
        if name not in expected:
            assert hashlib.sha256((root / name).read_bytes()).hexdigest() == digest, "Retained test changed: " + name
    for row in snapshot["identities"]:
        assert (row["module"] in after) == (snapshot["composition"] == "D-2"), row["module"]
    return {"composition": snapshot["composition"], "identities": snapshot["identities"],
            "deleted_files": sorted(removed), "python_test_declarations": 50,
            "python_collected_tests": 627, "typescript_test_declarations": 20,
            "typescript_collected_tests": 254}
