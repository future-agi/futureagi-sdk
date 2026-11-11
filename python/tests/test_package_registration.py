"""Source-level packaging guards; archive and consumer checks run after builds."""
import ast
import json
from pathlib import Path
import re
import sys

from packaging.specifiers import SpecifierSet
import pytest


ROOT = Path(__file__).resolve().parents[2]
PACKAGE = ROOT / "typescript" / "futureagi"
SUBPATHS = {"./gateway", "./gateway/testing", "./gateway/express", "./gateway/nextjs", "./gateway/react"}
# Namespaces that stay out of both Python archives; fi/gateway ships.
PYTHON_OFF_EXCLUDES = ("fi/integrations/otel", "fi/deployments", "fi/deployments.py")


def test_gateway_registration_ships_and_resolves_by_default():
    package = json.loads((PACKAGE / "package.json").read_text())
    fragment = json.loads((PACKAGE / "gateway-client" / "registration-fragment.json").read_text())["package"]
    assert {key for key in package["exports"] if key.startswith("./gateway")} == SUBPATHS
    for key in SUBPATHS:
        entry = package["exports"][key]
        # Ordinary consumers resolve every subpath with the default import/require conditions.
        assert entry == fragment["exports"][key]
        assert set(entry) == {"import", "require"}
        for condition, build in (("import", "esm"), ("require", "cjs")):
            assert set(entry[condition]) == {"types", "default"}
            assert all(target.startswith(f"./dist/gateway/{build}/") for target in entry[condition].values())
        assert package["typesVersions"]["*"][key[2:]] == fragment["typesVersions"]["*"][key[2:]]
    assert "futureagi-gateway-preview" not in json.dumps(package)
    assert "dist" not in package["files"]
    assert "dist/gateway" in package["files"]
    assert {"LICENSE", "NOTICE", "CHANGELOG.md"} <= set(package["files"])
    assert package["scripts"]["build"].endswith("&& pnpm run build:gateway")
    assert package["scripts"]["build:gateway"] == "node gateway-client/scripts/build.cjs"
    assert package["peerDependencies"] == {"react": ">=17.0.0 <20"}
    assert package["peerDependenciesMeta"] == {"react": {"optional": True}}


def test_both_webhook_formats_have_declarations():
    package = json.loads((PACKAGE / "package.json").read_text())
    assert package["name"] == "@future-agi/sdk"
    assert package["version"] == "0.2.0"
    for key in (".", "./webhooks"):
        for condition in ("import", "require"):
            assert set(package["exports"][key][condition]) == {"types", "default"}
    assert package["typesVersions"]["*"]["webhooks"] == ["./dist/src/webhooks/index.d.ts"]


def _anyio_requirement(project):
    dependencies = project.split("[tool.poetry.dependencies]\n", 1)[1].split("\n[", 1)[0]
    matches = re.findall(r'^anyio\s*=\s*("[^"]*")\s*$', dependencies, re.MULTILINE)
    assert len(matches) == 1, "anyio must remain an unconditional base dependency"
    return SpecifierSet(ast.literal_eval(matches[0]))


@pytest.mark.parametrize("requirement, equivalent", [
    (">=4.0,<5.0", True), (">=4.0,<5", True), ("<5.0,>=4", True),
    (">=4.1,<5", False), (">=4.0,<6", False), (">=4.0", False),
    (">=3.0,<5.0", False),
])
def test_anyio_requirement_normalization_preserves_both_bounds(requirement, equivalent):
    project = f'[tool.poetry.dependencies]\nanyio = "{requirement}"\n'
    assert (_anyio_requirement(project) == SpecifierSet(">=4.0,<5")) is equivalent


def test_python_candidate_floor_typing_and_gateway_inclusion():
    project = (ROOT / "python" / "pyproject.toml").read_text()
    assert 'version = "0.7.0"' in project
    assert 'python = ">=3.10"' in project
    assert _anyio_requirement(project) == SpecifierSet(">=4.14.2,<5")
    excluded = project.split("exclude = [", 1)[1].split("]", 1)[0]
    assert '"fi/gateway' not in excluded
    for namespace in PYTHON_OFF_EXCLUDES:
        assert f'"{namespace}"' in excluded
    assert '"fi/**/__pycache__"' in excluded and '"fi/**/*.pyc"' in excluded
    assert (ROOT / "python" / "fi" / "gateway" / "py.typed").is_file()
    assert (ROOT / "python" / "fi" / "py.typed").is_file()
    assert "ai-evaluation" not in project
    assert "Python :: 3.14" not in project
    assert "Python :: 3.9" not in project


def _import_time_modules(body):
    """Top-level names imported when a module loads: not in functions, TYPE_CHECKING or ImportError guards."""
    for node in body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        if isinstance(node, ast.If) and "TYPE_CHECKING" in ast.unparse(node.test):
            yield from _import_time_modules(node.orelse)
            continue
        if isinstance(node, ast.Try):
            handled = any(h.type is not None and re.search(r"\b(ImportError|ModuleNotFoundError)\b", ast.unparse(h.type)) for h in node.handlers)
            if not handled:
                yield from _import_time_modules(node.body)
            for block in [h.body for h in node.handlers] + [node.orelse, node.finalbody]:
                yield from _import_time_modules(block)
            continue
        if isinstance(node, ast.Import):
            yield from (alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            yield node.module.split(".")[0]
        for field in ("body", "orelse"):
            if isinstance(node, (ast.ClassDef, ast.If, ast.With, ast.For, ast.While)):
                yield from _import_time_modules(getattr(node, field, []))


def _required_dependencies():
    project = (ROOT / "python" / "pyproject.toml").read_text()
    section = project.split("[tool.poetry.dependencies]\n", 1)[1].split("\n[", 1)[0]
    required = set()
    for line in section.splitlines():
        match = re.match(r"^([A-Za-z0-9_.-]+)\s*=\s*(.+)$", line.strip())
        if match and match.group(1) != "python" and "optional = true" not in match.group(2):
            required.add(re.sub(r"[-_.]+", "-", match.group(1)).lower())
    return required


def test_gateway_import_time_dependencies_are_declared():
    # A wheel-only install must import fi.gateway: every third-party module it loads
    # at import time is a required (non-extra) dependency of futureagi.
    gateway = ROOT / "python" / "fi" / "gateway"
    modules = set()
    for path in gateway.rglob("*.py"):
        modules.update(_import_time_modules(ast.parse(path.read_text(encoding="utf-8")).body))
    third_party = {m for m in modules if m not in sys.stdlib_module_names and m not in {"fi", "__future__"}}
    assert {"httpx", "pydantic"} <= third_party
    undeclared = {m for m in third_party if re.sub(r"[-_.]+", "-", m).lower() not in _required_dependencies()}
    assert not undeclared, f"fi.gateway imports undeclared dependencies: {sorted(undeclared)}"


def test_webhooks_are_not_a_standalone_distribution():
    project = (ROOT / "python" / "futureagi-webhooks" / "pyproject.toml").read_text()
    assert "package-mode = false" in project
    assert "publish" not in project
    assert "repositories" not in project


def test_gateway_ci_copy_is_audited_and_identical():
    workflow = ROOT / ".github" / "workflows" / "gateway-client.yml"
    template = PACKAGE / "gateway-client" / "ci" / "gateway-client.yml"
    assert workflow.read_bytes() == template.read_bytes()
    audit = json.loads((ROOT / ".github" / "ci" / "workflow-policy.json").read_text())
    assert workflow.name in audit["audit"]


def test_readmes_use_the_supported_package_scope():
    for file in (ROOT / "README.md", ROOT / "python" / "README.md", PACKAGE / "README.md"):
        assert "@futureagi/sdk" not in file.read_text()
