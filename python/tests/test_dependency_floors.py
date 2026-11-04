"""Manifest-only dependency regressions; no SDK imports or installed packages."""

import json
import re
import unittest
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:  # Python 3.10
    tomllib = None


ROOT = Path(__file__).resolve().parents[2]
SINGLE_FLOORS = {
    "certifi": ">=2026.10.18",
    "idna": ">=3.15",
    "requests": ">=2.33.0",
    "urllib3": ">=2.8.0",
    "anyio": ">=4.14.2,<5.0",
    "scipy": ">=1.15.0",
    "opentelemetry-api": {"version": ">=1.45.1", "optional": True},
    "opentelemetry-sdk": {"version": ">=1.45.1", "optional": True},
}
DEPENDENCY_KEYS = {"python", "eval-type-backport"} | set(SINGLE_FLOORS)
EXTRAS = {
    "gateway-tokens": ["tiktoken"],
    "gateway-otel": ["opentelemetry-api", "opentelemetry-sdk"],
}


def _read(relative):
    path = ROOT / relative
    assert path.is_file(), "Missing manifest: " + relative
    return path.read_text(encoding="utf-8")


def _inline_table(text):
    """Parse only the string/bool fields used by these Poetry constraints."""
    assert text.startswith("{") and text.endswith("}"), text
    body = text[1:-1].strip()
    result = {}
    field = re.compile(
        r'\s*([a-z-]+)\s*=\s*("[^"\n]*"|true|false)\s*(,|$)'
    )
    while body:
        match = field.match(body)
        assert match is not None, "Unsupported constraint field: " + body
        key, value, separator = match.groups()
        assert key in {"version", "python", "optional"}, key
        assert key not in result, "Duplicate constraint field: " + key
        result[key] = json.loads(value)
        body = body[match.end():]
        assert not body or separator == ",", text
    return result


def _parse_manifest_subset(text):
    """Exact-key fallback, not a general TOML parser or a resolver."""
    dependencies = {}
    extras = {}
    sections = {
        "[tool.poetry.dependencies]": dependencies,
        "[tool.poetry.extras]": extras,
    }
    section = ""
    pending_key = None
    pending_rows = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if pending_key is not None:
            if line == "]":
                dependencies[pending_key] = pending_rows
                pending_key = None
                pending_rows = []
            else:
                pending_rows.append(_inline_table(line.rstrip(",").strip()))
            continue
        if line.startswith("["):
            section = line
            continue
        target = sections.get(section)
        if target is None:
            continue
        key, separator, value = line.partition("=")
        key, value = key.strip(), value.strip()
        if target is dependencies and key not in DEPENDENCY_KEYS:
            continue
        assert separator == "=", "Missing assignment: " + line
        assert key not in target, "Duplicate manifest key: " + key
        if target is extras:
            # All current extras are simple lists of quoted package names.
            assert key in EXTRAS, "Unexpected extra: " + key
            try:
                target[key] = json.loads(value)
            except ValueError as error:
                raise AssertionError("Invalid extra: " + key) from error
        elif value == "[":
            pending_key = key
        elif value.startswith("{"):
            target[key] = _inline_table(value)
        else:
            assert re.fullmatch(r'"[^"\n]*"', value), value
            target[key] = json.loads(value)
    assert pending_key is None, "Unclosed constraint array"
    return {"dependencies": dependencies, "extras": extras}


def _poetry():
    text = _read("python/pyproject.toml")
    if tomllib is None:
        return _parse_manifest_subset(text)
    try:
        data = tomllib.loads(text)
    except ValueError as error:
        raise AssertionError("Invalid pyproject.toml") from error
    tool = data.get("tool")
    assert isinstance(tool, dict), "Missing [tool] table"
    poetry = tool.get("poetry")
    assert isinstance(poetry, dict), "Missing [tool.poetry] table"
    return poetry


def _dependencies():
    dependencies = _poetry().get("dependencies")
    assert isinstance(dependencies, dict), "Missing dependency table"
    return dependencies


def _yaml_block(lines, key, indent):
    """Read one exact mapping block from the workflows, not general YAML."""
    header = " " * indent + key + ":"
    matches = [index for index, line in enumerate(lines) if line == header]
    assert len(matches) == 1, "Expected one mapping: " + key
    start = matches[0] + 1
    end = len(lines)
    for index in range(start, len(lines)):
        line = lines[index]
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if len(line) - len(line.lstrip(" ")) <= indent:
            end = index
            break
    return lines[start:end]


def _python_matrix(relative, job):
    lines = _read(relative).splitlines()
    for indent, key in enumerate(("jobs", job, "strategy", "matrix")):
        lines = _yaml_block(lines, key, indent * 2)
    rows = [line.strip() for line in lines if line.strip()
            and not line.lstrip().startswith("#")]
    assert rows, "Missing Python matrix: " + relative
    try:
        if rows[0].startswith("python:"):
            assert len(rows) == 1, "Unexpected matrix keys: " + relative
            versions = json.loads(rows[0].partition(":")[2])
        else:
            assert rows[0] == "include:", "Expected an include matrix: " + relative
            values = []
            for row in rows[1:]:
                key, separator, value = row.removeprefix("- ").partition(":")
                assert separator == ":" and key in {"python", "typescript"}, row
                if key == "python":
                    values.append(value)
            assert values, "Missing Python include rows: " + relative
            versions = [json.loads(value) for value in values]
    except ValueError as error:
        raise AssertionError("Invalid Python matrix: " + relative) from error
    assert isinstance(versions, list), "Expected a version list: " + relative
    assert versions and all(isinstance(version, str) for version in versions)
    return versions


class DependencyFloorsTest(unittest.TestCase):
    def test_python_support_requires_310(self):
        self.assertEqual(_dependencies().get("python"), ">=3.10")

    def test_single_python_floors_exactly(self):
        dependencies = _dependencies()
        for package, expected in SINGLE_FLOORS.items():
            with self.subTest(package=package):
                # Equality rejects arrays, Python markers and lost optional flags.
                self.assertEqual(dependencies.get(package), expected)

    def test_python39_only_constraints_removed(self):
        self.assertNotIn("eval-type-backport", _dependencies())
        self.assertNotRegex(
            _read("python/pyproject.toml"),
            r'''\bpython\s*=\s*["']<\s*3\.10["']''',
        )

    def test_workflow_python_matrices(self):
        for relative, job, expected in (
            (".github/workflows/ci.yml", "python", ["3.10", "3.11", "3.13"]),
            (".github/workflows/e2e.yml", "e2e", ["3.10", "3.12"]),
        ):
            with self.subTest(workflow=relative):
                versions = _python_matrix(relative, job)
                self.assertNotIn("3.9", versions)
                self.assertIn("3.10", versions)
                self.assertEqual(versions, expected)

    def test_extras_membership_unchanged(self):
        self.assertEqual(_poetry().get("extras"), EXTRAS)

    def test_typescript_dependency_floors(self):
        try:
            package = json.loads(_read("typescript/futureagi/package.json"))
        except ValueError as error:
            raise AssertionError("Invalid package.json") from error
        self.assertIsInstance(package, dict)
        dependencies = package.get("dependencies")
        self.assertIsInstance(dependencies, dict)
        for name, expected in {
            "axios": "^1.20.0", "uuid": "^11.1.1", "form-data": "^4.0.6",
        }.items():
            with self.subTest(package=name):
                self.assertEqual(dependencies.get(name), expected)

    def test_workspace_has_only_existing_package_directories(self):
        lines = [
            line.strip() for line in _read("typescript/pnpm-workspace.yaml").splitlines()
            if line.strip() and not line.lstrip().startswith("#")
        ]
        self.assertTrue(lines, "Missing workspace packages")
        self.assertEqual(lines[0], "packages:")
        packages = []
        for line in lines[1:]:
            match = re.fullmatch(r"-\s+(['\"])([^'\"]+)\1", line)
            self.assertIsNotNone(match, "Expected a literal package directory")
            packages.append(match.group(2))
        self.assertEqual(packages, ["futureagi"])
        for package in packages:
            with self.subTest(package=package):
                directory = ROOT / "typescript" / package
                self.assertTrue(directory.is_dir(), package)
                self.assertTrue((directory / "package.json").is_file(), package)

    def test_workspace_root_depends_only_on_workspace_packages(self):
        root = json.loads(_read("typescript/package.json"))
        dependencies = root.get("dependencies", {})
        workspace = {name for name, spec in dependencies.items() if str(spec).startswith("workspace:")}
        self.assertNotIn("@future-agi/ai-evaluation", dependencies,
                         "The retired ai-evaluation package is not a workspace member")
        self.assertEqual(workspace, {"@future-agi/sdk"})

    def test_workspace_root_is_private(self):
        root = json.loads(_read("typescript/package.json"))
        self.assertIs(root.get("private"), True,
                      "The TypeScript workspace root must never be published")

    def test_fallback_reads_legacy_scalar_and_optional_constraints(self):
        result = _parse_manifest_subset(
            '[tool.poetry.dependencies]\n'
            'requests = ">=2.32"\n'
            'anyio = ">=4.0,<5.0"\n'
            'opentelemetry-api = { version = ">=1.0", optional = true }\n'
        )
        self.assertEqual(result.get("dependencies"), {
            "requests": ">=2.32",
            "anyio": ">=4.0,<5.0",
            "opentelemetry-api": {"version": ">=1.0", "optional": True},
        })

    def test_fallback_reads_base_marker_constraints(self):
        result = _parse_manifest_subset(
            '[tool.poetry.dependencies]\n'
            'requests = [\n'
            '    { version = ">=2.32.4", python = "<3.10" },\n'
            '    { version = ">=2.33.0", python = ">=3.10" }\n'
            ']\n'
            'eval-type-backport = { version = ">=0.2", python = "<3.10" }\n'
        )
        self.assertEqual(result.get("dependencies"), {
            "requests": [
                {"version": ">=2.32.4", "python": "<3.10"},
                {"version": ">=2.33.0", "python": ">=3.10"},
            ],
            "eval-type-backport": {"version": ">=0.2", "python": "<3.10"},
        })

    def test_fallback_matches_manifest_parser(self):
        fallback = _parse_manifest_subset(_read("python/pyproject.toml"))
        dependencies = _dependencies()
        self.assertEqual(fallback.get("dependencies"), {
            key: dependencies.get(key) for key in DEPENDENCY_KEYS
            if key in dependencies
        })
        self.assertEqual(fallback.get("extras"), _poetry().get("extras"))


if __name__ == "__main__":
    unittest.main()
