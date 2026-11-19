"""Artifact checks require management and the model-call data plane, each in its own place."""
import json
import runpy
from pathlib import Path

import pytest

GATE = runpy.run_path(str(Path(__file__).resolve().parents[3] / "scripts/packaging/check_gateway_boundaries.py"))
CHECK = GATE["check_gateway_boundaries"]
SUBPATH_ENTRIES = ("index", "testing", "express", "nextjs", "react/index")
PYTHON_DATA_PLANE = {
    "fi/gateway/__init__.py": b"from fi.gateway._exceptions import AgentCCError as AgentCCError\n",
    "fi/gateway/_client.py": b"class AgentCC:\n    pass\n",
    "fi/gateway/_async_client.py": b"class AsyncAgentCC:\n    pass\n",
    "fi/gateway/py.typed": b"",
    "fi/gateway/testing/mock.py": b"def create_mock_client(): pass\n",
}


def artifacts():
    whl = {"fi/generated/platform/fa_management/gateway.py": b"class Gateway(\nclass AsyncGateway(", "fi/_core/fa_management.py": b""}
    whl.update(PYTHON_DATA_PLANE)
    source = {"futureagi/" + name: text for name, text in whl.items()}
    npm = {}
    for fmt in ("esm", "esnext", "src"):
        npm[f"package/dist/{fmt}/generated/fa-management/gateway.d.ts"] = b"export class Gateway {}"
        npm[f"package/dist/{fmt}/_core/fa-management.d.ts"] = b""
        npm[f"package/dist/{fmt}/futureagi-client.d.ts"] = b"get gateway(): Gateway;"
    for fmt, kind in (("esm", "module"), ("cjs", "commonjs")):
        npm[f"package/dist/gateway/{fmt}/package.json"] = json.dumps({"type": kind}).encode()
        for entry in SUBPATH_ENTRIES:
            for extension in (".js", ".d.ts"):
                npm[f"package/dist/gateway/{fmt}/{entry}{extension}"] = b""
        npm[f"package/dist/gateway/{fmt}/index.js"] = b'export { AgentCC } from "./client.js";'
        npm[f"package/dist/gateway/{fmt}/index.d.ts"] = b'export { AgentCC } from "./client.js";'
        npm[f"package/dist/gateway/{fmt}/client.d.ts"] = b"export declare class AgentCC {}"
        npm[f"package/dist/gateway/{fmt}/gateway-config.js"] = b""
    return whl, source, npm


def test_management_and_data_plane_are_both_required():
    CHECK(*artifacts())


def test_every_registered_entry_is_a_data_plane_member():
    assert len(GATE["DATA_PLANE_ENTRIES"]) == 20
    assert all(path.startswith("package/dist/gateway/") for path in GATE["DATA_PLANE_ENTRIES"])


@pytest.mark.parametrize("fmt", ["esm", "esnext", "src"])
@pytest.mark.parametrize("mutation", ["root_data_module", "root_data_symbol", "management_module", "management_symbol", "management_accessor"])
def test_each_npm_boundary_is_fallible(fmt, mutation):
    whl, source, npm = artifacts()
    path = f"package/dist/{fmt}/generated/fa-management/gateway.d.ts"
    if mutation == "root_data_module":
        npm[f"package/dist/{fmt}/gateway/index.d.ts"] = b""
    elif mutation == "root_data_symbol":
        npm[f"package/dist/{fmt}/index.d.ts"] = b"export class AgentCC {}"
    elif mutation == "management_module":
        del npm[path]
    elif mutation == "management_symbol":
        npm[path] = b"export class Absent {}"
    else:
        npm[f"package/dist/{fmt}/futureagi-client.d.ts"] = b""
    with pytest.raises(AssertionError):
        CHECK(whl, source, npm)


@pytest.mark.parametrize("fmt", ["esm", "cjs"])
@pytest.mark.parametrize("entry", SUBPATH_ENTRIES)
@pytest.mark.parametrize("extension", [".js", ".d.ts"])
def test_registered_data_plane_layout_is_required(fmt, entry, extension):
    whl, source, npm = artifacts()
    del npm[f"package/dist/gateway/{fmt}/{entry}{extension}"]
    with pytest.raises(AssertionError, match="Missing gateway data plane"):
        CHECK(whl, source, npm)


@pytest.mark.parametrize("fmt", ["esm", "cjs"])
@pytest.mark.parametrize("mutation", ["missing", "wrong"])
def test_each_data_plane_module_type_marker_is_required(fmt, mutation):
    whl, source, npm = artifacts()
    marker = f"package/dist/gateway/{fmt}/package.json"
    if mutation == "missing":
        del npm[marker]
    else:
        npm[marker] = json.dumps({"type": "commonjs" if fmt == "esm" else "module"}).encode()
    with pytest.raises(AssertionError, match="Missing gateway module type"):
        CHECK(whl, source, npm)


@pytest.mark.parametrize("fmt", ["esm", "cjs"])
@pytest.mark.parametrize("extension", [".js", ".d.ts"])
def test_data_plane_entry_must_export_the_client(fmt, extension):
    whl, source, npm = artifacts()
    npm[f"package/dist/gateway/{fmt}/index{extension}"] = b"export {};"
    with pytest.raises(AssertionError, match="Missing gateway data-plane symbol"):
        CHECK(whl, source, npm)


@pytest.mark.parametrize("path", [
    "package/dist/esm/nested/gateway-client/index.js",
    "package/dist/esnext/nested/gateway.js",
    "package/gateway-client/index.cjs",
    "package/dist/src/generated/other/gateway.js",
    "package/dist/esm/generated/fa-management/gateway-extra.js",
    "package/dist/esm/gateway/index.js",
])
def test_gateway_modules_outside_management_and_data_plane_are_absent(path):
    whl, source, npm = artifacts()
    npm[path] = b""
    with pytest.raises(AssertionError, match="Gateway module outside the data plane"):
        CHECK(whl, source, npm)


@pytest.mark.parametrize("fmt", ["esm", "esnext", "src"])
@pytest.mark.parametrize("extension", [".js", ".mjs", ".cjs", ".d.ts"])
@pytest.mark.parametrize("symbol", ["AgentCC", "AsyncAgentCC"])
def test_data_plane_symbols_stay_out_of_the_core_tree(fmt, extension, symbol):
    whl, source, npm = artifacts()
    npm[f"package/dist/{fmt}/boundary-control{extension}"] = f"export class {symbol} {{}}".encode()
    with pytest.raises(AssertionError, match="Gateway symbol outside the data plane"):
        CHECK(whl, source, npm)


def test_all_twelve_management_members_remain_allowed():
    whl, source, npm = artifacts()
    for fmt in ("esm", "esnext", "src"):
        for extension in (".js", ".js.map", ".d.ts.map"):
            npm[f"package/dist/{fmt}/generated/fa-management/gateway{extension}"] = b""
    CHECK(whl, source, npm)


@pytest.mark.parametrize("archive", [0, 1])
@pytest.mark.parametrize("module", ["fi/generated/platform/fa_management/gateway.py", "fi/_core/fa_management.py"])
def test_each_python_management_module_is_required(archive, module):
    values = artifacts()
    del values[archive][("futureagi/" if archive else "") + module]
    with pytest.raises(AssertionError):
        CHECK(*values)


@pytest.mark.parametrize("archive", [0, 1])
@pytest.mark.parametrize("module", ["fi/gateway/__init__.py", "fi/gateway/_client.py", "fi/gateway/_async_client.py", "fi/gateway/py.typed"])
def test_each_python_data_plane_module_is_required(archive, module):
    values = artifacts()
    del values[archive][("futureagi/" if archive else "") + module]
    with pytest.raises(AssertionError, match="Missing gateway data plane"):
        CHECK(*values)


@pytest.mark.parametrize("archive", [0, 1])
@pytest.mark.parametrize("module,symbol", [("fi/gateway/_client.py", "AgentCC"), ("fi/gateway/_async_client.py", "AsyncAgentCC")])
def test_each_python_client_class_is_required(archive, module, symbol):
    values = artifacts()
    values[archive][("futureagi/" if archive else "") + module] = f"{symbol} = None\n".encode()
    with pytest.raises(AssertionError, match="Missing (async )?gateway client"):
        CHECK(*values)


@pytest.mark.parametrize("archive", [0, 1])
@pytest.mark.parametrize("member", [
    "fi/gateway/__pycache__/_client.cpython-310.pyc",
    "fi/gateway/_client.pyc",
    "fi/gateway/tests/test_client.py",
    "fi/gateway/test_client.py",
    "fi/gateway/_vendor/respx/__init__.py",
    "fi/gateway/conftest.py",
])
def test_python_data_plane_ships_no_tests_or_bytecode(archive, member):
    values = artifacts()
    values[archive][("futureagi/" if archive else "") + member] = b""
    with pytest.raises(AssertionError, match="Gateway (bytecode|test file)"):
        CHECK(*values)


def test_python_management_must_not_carry_the_data_plane():
    whl, source, npm = artifacts()
    whl["fi/generated/platform/fa_management/gateway.py"] += b"\nclass AgentCC: pass\n"
    with pytest.raises(AssertionError, match="Gateway symbol in management"):
        CHECK(whl, source, npm)
