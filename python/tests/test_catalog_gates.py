"""Static gates on the catalog slice: one public name per server operation.

The catalog adds FA operations that the generated core's wrapper map does not cover.
An operation the wrapper map already names (same method and path, path parameter
names aside) must not get a second public name here, and a catalog method must not
reuse a public method path that either wrapper map already offers.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ROWS = json.loads((ROOT / "openapi/catalog/operations.json").read_text())["operations"]
CORE_SPEC = ROOT / "openapi/sdk/generated/futureagi-sdk.openapi.json"
CORE_WRAPPERS = ROOT / "openapi/sdk/wrapper-map.json"
PLATFORM_WRAPPERS = ROOT / "openapi/platform/wrapper-map.json"


def _endpoint(method: str, path: str) -> tuple[str, str]:
    return method.upper(), re.sub(r"\{[^}]+\}", "{}", path)


def _snake(name: str) -> str:
    return re.sub(r"(?<!^)(?=[A-Z])", "_", name).lower()


def core_wrapped() -> dict[tuple[str, str], str]:
    """Each endpoint the generated core's wrapper map names, with its public method."""
    by_id: dict[str, tuple[str, str]] = {}
    for path, item in json.loads(CORE_SPEC.read_text())["paths"].items():
        for method, operation in item.items():
            if isinstance(operation, dict) and "operationId" in operation:
                by_id[operation["operationId"]] = _endpoint(method, path)
    wrapped: dict[tuple[str, str], str] = {}
    for group, methods in json.loads(CORE_WRAPPERS.read_text()).items():
        for public, operation_id in methods.items():
            assert operation_id in by_id, f"{group}.{public}: {operation_id} is not in the spec"
            wrapped[by_id[operation_id]] = ".".join(_snake(p) for p in f"{group}.{public}".split("."))
    return wrapped


def clashes(rows: list[dict], wrapped: dict[tuple[str, str], str]) -> list[str]:
    found = []
    for row in rows:
        key = _endpoint(row["method"], row["path"])
        if key in wrapped:
            found.append(f"{row['public']}: {key[0]} {key[1]} is already client.{wrapped[key]}")
    return found


def test_no_catalog_operation_is_a_second_name_for_a_wrapped_one() -> None:
    assert clashes(ROWS, core_wrapped()) == []


def test_no_two_catalog_operations_share_an_endpoint() -> None:
    keys = [_endpoint(row["method"], row["path"]) for row in ROWS]
    assert len(keys) == len(set(keys))


def test_no_catalog_method_reuses_a_wrapped_public_method_path() -> None:
    public = {f"client.{name}" for name in core_wrapped().values()}
    for entry in json.loads(PLATFORM_WRAPPERS.read_text())["operations"].values():
        public |= {method["py"] for method in entry.get("methods", [])}
    reused = [row["public"] for row in ROWS if f"client.{row['public']}" in public]
    assert reused == []


def test_the_clash_check_bites() -> None:
    wrapped = core_wrapped()
    (method, path), name = next(iter(wrapped.items()))
    row = {"public": "sample.read", "method": method, "path": path.replace("{}", "{other}")}
    assert clashes([row], wrapped) == [f"sample.read: {method} {path} is already client.{name}"]


def test_generated_files_end_with_one_newline() -> None:
    folders = [ROOT / "python/fi/generated/platform/catalog", ROOT / "typescript/futureagi/src/generated/catalog"]
    files = [p for folder in folders for p in sorted(folder.iterdir()) if p.suffix in {".py", ".ts"}]
    assert len(files) >= 8
    bad = [str(p.relative_to(ROOT)) for p in files if not p.read_text().endswith("\n") or p.read_text().endswith("\n\n")]
    assert bad == []
