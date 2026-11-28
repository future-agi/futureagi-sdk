"""Published base requirements must exclude versions below the patched floors."""
from pathlib import Path

from packaging.specifiers import SpecifierSet
from packaging.version import Version
import pytest

try:
    import tomllib
except ModuleNotFoundError:  # Python 3.10: tomli is provided by the test toolchain.
    import tomli as tomllib


MINIMUM_VERSIONS = {
    "anyio": "4.14.2",
    "certifi": "2026.10.18",
    "idna": "3.15",
    "requests": "2.33.0",
    "urllib3": "2.8.0",
}


@pytest.mark.parametrize("package, minimum", MINIMUM_VERSIONS.items())
def test_published_base_dependency_floor(package, minimum):
    project = Path(__file__).resolve().parents[1] / "pyproject.toml"
    with project.open("rb") as stream:
        dependencies = tomllib.load(stream)["tool"]["poetry"]["dependencies"]
    requirement = dependencies[package]
    assert isinstance(requirement, str), f"{package} must remain unconditional"
    specifiers = SpecifierSet(requirement)
    assert any(
        specifier.operator == ">=" and Version(specifier.version) >= Version(minimum)
        for specifier in specifiers
    ), f"{package}: declared {requirement}, requires a floor of at least {minimum}"
    if package == "anyio":
        assert any(
            specifier.operator == "<" and Version(specifier.version) == Version("5")
            for specifier in specifiers
        ), "anyio must retain its <5 upper bound"
