"""Generate the Python SDK, the TypeScript SDK and the MCP tool list from one contract + one catalog.

Inputs
    sdkgen/contracts/swagger.json    API contract (sliced from the monorepo by sync_contract.py)
    sdkgen/catalog/operations.yaml   shared names + which surface ships what

Outputs (never edited by hand)
    python/fi/platform/_generated/{models,resources}.py           pydantic models, resource classes
    python/fi/platform/resources/__init__.py                      what fi.Client exposes
    typescript/futureagi/src/platform/_generated/{models,resources}.ts
    typescript/futureagi/src/platform/resources/index.ts
    sdkgen/mcp/tools.generated.json                               MCP tool manifest

Scaffolds (written once when a resource first appears, then owned by hand)
    python/fi/platform/resources/<resource>.py
    typescript/futureagi/src/platform/resources/<resource>.ts
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import yaml

from . import mcp, python, typescript
from .catalog import CatalogError, Op, Param, load

ROOT = Path(__file__).resolve().parents[2]
SDKGEN = ROOT / "sdkgen"
CONTRACT = SDKGEN / "contracts" / "swagger.json"
CATALOG = SDKGEN / "catalog" / "operations.yaml"
PY_PLATFORM = ROOT / "python" / "fi" / "platform"
TS_PLATFORM = ROOT / "typescript" / "futureagi" / "src" / "platform"
OUT_MCP = SDKGEN / "mcp" / "tools.generated.json"

TARGETS = ("python", "typescript", "mcp")

__all__ = ["CatalogError", "Op", "Param", "TARGETS", "build", "load", "load_ops", "scaffolds"]


def load_ops() -> tuple[dict, list[Op], str]:
    """(contract, validated operations, sha256 of the contract file)."""
    raw = CONTRACT.read_bytes()
    spec = json.loads(raw)
    ops = load(spec, yaml.safe_load(CATALOG.read_text()))
    return spec, ops, hashlib.sha256(raw).hexdigest()


def build(targets: tuple[str, ...] = TARGETS) -> dict[Path, str]:
    """Generated files: {path: text}. Each one is overwritten on every run."""
    spec, ops, contract_sha = load_ops()
    out: dict[Path, str] = {}
    if "python" in targets:
        out[PY_PLATFORM / "_generated" / "models.py"] = python.emit_models(spec, ops)
        out[PY_PLATFORM / "_generated" / "resources.py"] = python.emit_resources(ops)
        out[PY_PLATFORM / "resources" / "__init__.py"] = python.emit_resource_index(ops)
    if "typescript" in targets:
        out[TS_PLATFORM / "_generated" / "models.ts"] = typescript.emit_models(spec, ops)
        out[TS_PLATFORM / "_generated" / "resources.ts"] = typescript.emit_resources(ops)
        out[TS_PLATFORM / "resources" / "index.ts"] = typescript.emit_resource_index(ops)
    if "mcp" in targets:
        out[OUT_MCP] = mcp.emit_mcp(spec, ops, contract_sha)
    return out


def scaffolds(targets: tuple[str, ...] = TARGETS) -> dict[Path, str]:
    """Hand-owned files the generator creates only when missing: one per top-level resource."""
    _, ops, _ = load_ops()
    out: dict[Path, str] = {}
    if "python" in targets:
        for ns in python.top_level(ops):
            out[PY_PLATFORM / "resources" / f"{ns[0]}.py"] = python.scaffold_resource(ns)
    if "typescript" in targets:
        for ns in typescript.top_level(ops):
            out[TS_PLATFORM / "resources" / f"{ns[0]}.ts"] = typescript.scaffold_resource(ns)
    return out
