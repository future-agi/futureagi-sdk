"""Keep management and model-call artifact boundaries independent.

Both surfaces ship. The management API (``client.gateway``) lives in the core SDK
tree; the gateway data-plane client lives only in its own namespace: ``fi/gateway``
in the wheel and sdist, ``dist/gateway/{esm,cjs}`` in the npm tarball. Each must
be present, and neither may leak into the other's location.
"""
import json
from pathlib import PurePosixPath
import re


# Only these twelve generated management members may carry "gateway" in their
# name outside the data-plane tree. In particular, dist/{esm,esnext,src}/gateway
# is not where the data plane lives.
MANAGEMENT_MEMBERS = frozenset(
    f"package/dist/{fmt}/generated/fa-management/gateway{extension}"
    for fmt in ("esm", "esnext", "src")
    for extension in (".js", ".js.map", ".d.ts", ".d.ts.map")
)
DATA_PLANE_PREFIX = "package/dist/gateway/"
# The five registered subpaths (./gateway, ./gateway/testing, ./gateway/express,
# ./gateway/nextjs, ./gateway/react), each in both module systems.
DATA_PLANE_ENTRIES = tuple(
    f"{DATA_PLANE_PREFIX}{fmt}/{entry}{extension}"
    for fmt in ("esm", "cjs")
    for entry in ("index", "testing", "express", "nextjs", "react/index")
    for extension in (".js", ".d.ts")
)
# dist/gateway/cjs must be marked CommonJS inside the "type": "module" package.
DATA_PLANE_MODULE_TYPES = {"esm": "module", "cjs": "commonjs"}
PYTHON_DATA_PLANE = ("fi/gateway/__init__.py", "fi/gateway/_client.py", "fi/gateway/_async_client.py", "fi/gateway/py.typed")
DATA_SYMBOL = re.compile(rb"\b(?:AsyncAgentCC|AgentCC)\b")


def _check_python_data_plane(archive, prefix, label):
    for module in PYTHON_DATA_PLANE:
        assert prefix + module in archive, f"Missing gateway data plane ({label}): {module}"
    assert re.search(rb"^class AgentCC\b", archive[prefix + "fi/gateway/_client.py"], re.M), f"Missing gateway client ({label})"
    assert re.search(rb"^class AsyncAgentCC\b", archive[prefix + "fi/gateway/_async_client.py"], re.M), f"Missing async gateway client ({label})"
    for name in archive:
        relative = name[len(prefix):] if name.startswith(prefix) else name
        if not relative.startswith("fi/gateway/"):
            continue
        parts = PurePosixPath(relative).parts
        assert "__pycache__" not in parts and not relative.endswith((".pyc", ".pyo")), f"Gateway bytecode ({label}): {name}"
        assert not any(
            part in {"tests", "_vendor", "conftest.py"} or part.startswith("test_") for part in parts
        ), f"Gateway test file ({label}): {name}"


def check_gateway_boundaries(whl, source, npm):
    source_prefix = next(iter(source)).split("/", 1)[0] + "/"
    for archive, prefix, label in ((whl, "", "wheel"), (source, source_prefix, "sdist")):
        _check_python_data_plane(archive, prefix, label)
    for path in DATA_PLANE_ENTRIES:
        assert path in npm, "Missing gateway data plane: " + path
    for fmt, kind in DATA_PLANE_MODULE_TYPES.items():
        marker = f"{DATA_PLANE_PREFIX}{fmt}/package.json"
        assert marker in npm and json.loads(npm[marker]) == {"type": kind}, "Missing gateway module type: " + marker
        for extension in (".js", ".d.ts"):
            entry = f"{DATA_PLANE_PREFIX}{fmt}/index{extension}"
            assert re.search(rb"\bAgentCC\b", npm[entry]), "Missing gateway data-plane symbol: " + entry
    for name, content in npm.items():
        if name.startswith(DATA_PLANE_PREFIX):
            continue
        assert "gateway" not in name.lower() or name in MANAGEMENT_MEMBERS, "Gateway module outside the data plane: " + name
        if name.endswith((".d.ts", ".js", ".mjs", ".cjs")):
            assert not DATA_SYMBOL.search(content), "Gateway symbol outside the data plane: " + name
    for archive, prefix in ((whl, ""), (source, source_prefix)):
        assert prefix + "fi/generated/platform/fa_management/gateway.py" in archive, "Missing management Python namespace"
        assert prefix + "fi/_core/fa_management.py" in archive, "Missing management Python core"
        assert b"class Gateway(" in archive[prefix + "fi/generated/platform/fa_management/gateway.py"]
        assert b"class AsyncGateway(" in archive[prefix + "fi/generated/platform/fa_management/gateway.py"]
        assert not DATA_SYMBOL.search(archive[prefix + "fi/generated/platform/fa_management/gateway.py"]), "Gateway symbol in management"
    for fmt in ("esm", "esnext", "src"):
        path = f"package/dist/{fmt}/generated/fa-management/gateway.d.ts"
        assert path in npm, "Missing management declaration: " + fmt
        assert re.search(rb"\bclass Gateway\b", npm[path]), "Missing management Gateway symbol: " + fmt
        assert f"package/dist/{fmt}/_core/fa-management.d.ts" in npm, "Missing management core: " + fmt
        root = npm[f"package/dist/{fmt}/futureagi-client.d.ts"]
        assert re.search(rb"\bgateway\s*[:(]", root), "Missing management accessor: " + fmt
