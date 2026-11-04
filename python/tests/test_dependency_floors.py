"""Manifest-only dependency regressions; no SDK imports or installed packages."""

import json
import re
import unittest
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:  # Python 3.9 and 3.10
    tomllib = None


ROOT = Path(__file__).resolve().parents[2]
DEPENDENCY_KEYS = {
    "python", "certifi", "idna", "requests", "urllib3", "anyio",
    "opentelemetry-api", "opentelemetry-sdk",
}
EXTRAS = {
    "gateway-tokens": ["tiktoken"],
    "gateway-otel": ["opentelemetry-api", "opentelemetry-sdk"],
}
BRANCHES = {
    "requests": (">=2.32.4", ">=2.33.0"),
    "urllib3": (">=2.6.3", ">=2.8.0"),
    "anyio": (">=4.0,<5.0", ">=4.14.2,<5.0"),
    "opentelemetry-api": (">=1.0", ">=1.45.1"),
    "opentelemetry-sdk": (">=1.0", ">=1.45.1"),
}
BASE_FLOORS = {
    "certifi": ">=2024.6",
    "idna": ">=3.7",
    "requests": ">=2.32",
    "urllib3": ">=2.2",
    "anyio": ">=4.0,<5.0",
    "opentelemetry-api": ">=1.0",
    "opentelemetry-sdk": ">=1.0",
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


def _lower_bound(constraint):
    assert isinstance(constraint, str), "Missing version constraint"
    match = re.match(r">=(\d+(?:\.\d+)*)(?:,|$)", constraint)
    assert match is not None, "Expected an inclusive minimum: " + constraint
    parts = tuple(int(part) for part in match.group(1).split("."))
    return parts + (0,) * max(0, 3 - len(parts))


class DependencyFloorsTest(unittest.TestCase):
    def test_python_support_allows_the_one_line_310_switch(self):
        # Dropping 3.9 only changes this declaration; lower branches become dead.
        self.assertIn(_dependencies().get("python"), {">3.9", ">=3.10"})

    def test_unconditional_python_floors(self):
        dependencies = _dependencies()
        for package, expected in {"certifi": ">=2026.10.18", "idna": ">=3.15"}.items():
            with self.subTest(package=package):
                self.assertEqual(dependencies.get(package), expected)

    def test_python_marker_branches_exactly(self):
        dependencies = _dependencies()
        for package, (older, current) in BRANCHES.items():
            with self.subTest(package=package):
                actual = dependencies.get(package)
                self.assertIsInstance(actual, list, package)
                expected = [
                    {"version": older, "python": "<3.10"},
                    {"version": current, "python": ">=3.10"},
                ]
                if package in {"opentelemetry-api", "opentelemetry-sdk"}:
                    for branch in expected:
                        branch["optional"] = True
                self.assertEqual(actual, expected)

    def test_python39_floors_never_decrease(self):
        dependencies = _dependencies()
        for package, baseline in BASE_FLOORS.items():
            with self.subTest(package=package):
                actual = dependencies.get(package)
                if package in BRANCHES:
                    self.assertIsInstance(actual, list, package)
                    self.assertTrue(all(isinstance(row, dict) for row in actual))
                    older = [row for row in actual if row.get("python") == "<3.10"]
                    self.assertEqual(len(older), 1, package)
                    actual = older[0].get("version")
                self.assertGreaterEqual(_lower_bound(actual), _lower_bound(baseline))

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

    def test_fallback_matches_manifest_parser(self):
        fallback = _parse_manifest_subset(_read("python/pyproject.toml"))
        dependencies = _dependencies()
        self.assertEqual(fallback.get("dependencies"), {
            key: dependencies.get(key) for key in DEPENDENCY_KEYS
        })
        self.assertEqual(fallback.get("extras"), _poetry().get("extras"))


if __name__ == "__main__":
    unittest.main()
