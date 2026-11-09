"""An unused, sdist-only dependency runs third-party build code on every base install.

Keep rouge-score out of installed base requirements and guard against shipped
source depending on it. Reinstall futureagi after changing its dependencies.
"""

import ast
import os
import re
import tokenize
from importlib import metadata
from pathlib import Path


def test_installed_base_requirements_exclude_rouge_score():
    try:
        requirements = metadata.requires("futureagi")
    except metadata.PackageNotFoundError as exc:
        raise AssertionError(
            "futureagi must be installed to check its base dependencies; "
            "run python -m pip install -e ./python before running this test."
        ) from exc
    # Missing or empty Requires-Dist would make the check below vacuous.
    assert requirements, "Installed futureagi metadata lists no requirements"

    rouge_requirements = []
    base_checked = 0
    for requirement in requirements:
        name_and_specifier, _, marker = requirement.partition(";")
        # Inspect all non-extra markers, not just the current interpreter's ones.
        if re.search(r"\bextra\b", marker, flags=re.IGNORECASE):
            continue
        base_checked += 1
        # Valid Requires-Dist entries start with the distribution name. No
        # version, URL or marker evaluation is needed for this name-only guard.
        match = re.match(r"\s*([A-Za-z0-9][A-Za-z0-9._-]*)", name_and_specifier)
        assert match is not None, "Cannot read requirement name: {!r}".format(requirement)
        normalized_name = re.sub(r"[-_.]+", "-", match.group(1)).lower()
        if normalized_name == "rouge-score":
            rouge_requirements.append(requirement)

    assert base_checked, "Installed futureagi metadata lists no base requirements"
    assert not rouge_requirements, (
        "rouge-score must not be a base dependency of futureagi: {}. "
        "Reinstall futureagi if the installed metadata is stale."
    ).format(rouge_requirements)


def _is_rouge_module(name):
    return name == "rouge_score" or name.startswith("rouge_score.")


def _rouge_import_lines(tree):
    # Recognize importlib aliases as well as the usual qualified call.
    importlib_names = {"importlib"}
    import_module_names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == "importlib":
                    importlib_names.add(alias.asname or alias.name)
        elif isinstance(node, ast.ImportFrom) and node.level == 0:
            if node.module == "importlib":
                for alias in node.names:
                    if alias.name == "import_module":
                        import_module_names.add(alias.asname or alias.name)

    lines = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            if any(_is_rouge_module(alias.name) for alias in node.names):
                lines.add(node.lineno)
        elif isinstance(node, ast.ImportFrom):
            if node.level == 0 and _is_rouge_module(node.module or ""):
                lines.add(node.lineno)
        elif isinstance(node, ast.Call):
            function = node.func
            qualified = (
                isinstance(function, ast.Attribute)
                and function.attr == "import_module"
                and isinstance(function.value, ast.Name)
                and function.value.id in importlib_names
            )
            unqualified = (
                isinstance(function, ast.Name)
                and function.id in import_module_names
            )
            if not (qualified or unqualified):
                continue
            module_name = node.args[0] if node.args else next(
                (keyword.value for keyword in node.keywords if keyword.arg == "name"),
                None,
            )
            if (
                isinstance(module_name, ast.Constant)
                and isinstance(module_name.value, str)
                and _is_rouge_module(module_name.value)
            ):
                lines.add(node.lineno)
    return sorted(lines)


def _raise_walk_error(error):
    raise error


def test_shipped_source_does_not_import_rouge_score():
    package_root = Path(__file__).resolve().parents[1] / "fi"
    assert package_root.is_dir(), "Expected the repository's python/fi source directory"
    # Mirror [tool.poetry].exclude in pyproject.toml; these are not shipped.
    excluded = {("evals",), ("integrations", "otel")}
    violations = []
    scanned = 0
    for directory, subdirectories, filenames in os.walk(
        package_root, onerror=_raise_walk_error
    ):
        directory = Path(directory)
        subdirectories[:] = sorted(
            name for name in subdirectories
            if (directory / name).relative_to(package_root).parts not in excluded
        )
        for filename in sorted(filenames):
            if not filename.endswith(".py"):
                continue
            source_path = directory / filename
            relative_path = source_path.relative_to(package_root)
            with tokenize.open(source_path) as source:
                tree = ast.parse(source.read(), filename=str(relative_path))
            scanned += 1
            violations.extend(
                "fi/{}:{}".format(relative_path.as_posix(), line)
                for line in _rouge_import_lines(tree)
            )

    assert scanned, "No shipped Python source files were checked"
    assert not violations, "Shipped source imports rouge_score:\n{}".format(
        "\n".join(violations)
    )
