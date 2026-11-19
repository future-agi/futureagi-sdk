"""Extract the connector contract slice from local, pinned backend repositories."""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def snapshot(repo: str | None, commit: str | None, source: str, prefixes: tuple[str, ...], name: str, input_file: Path | None = None) -> dict:
    if input_file:
        raw = input_file.read_bytes()
        old = json.loads((ROOT / "openapi/connectors/source.json").read_text())[name]
        expected = old.get("source_digest", "sha256:" + old.get("source_sha256", ""))
        if "sha256:" + hashlib.sha256(raw).hexdigest() != expected:
            raise ValueError("Connector source input content digest mismatch")
    else:
        if not repo or not commit:
            raise ValueError("Supply a local input or an explicit repository and revision")
        full_commit = subprocess.check_output(["git", "-C", repo, "rev-parse", commit], text=True).strip()
        raw = subprocess.check_output(["git", "-C", repo, "show", f"{full_commit}:{source}"])
    doc = json.loads(raw)
    paths = {key: value for key, value in doc["paths"].items() if key.startswith(prefixes)}
    # Retain only the transitive reference closure of the selected operations.
    pending = [paths]
    refs: dict[str, object] = {}
    while pending:
        value = pending.pop()
        if isinstance(value, list):
            pending.extend(value)
        elif isinstance(value, dict):
            pending.extend(value.values())
            ref = value.get("$ref")
            if ref and ref not in refs:
                if not ref.startswith("#/"):
                    raise ValueError("Only local contract references are supported")
                target = doc
                for part in ref[2:].split("/"):
                    target = target[part]
                refs[ref] = target
                pending.append(target)
    sliced = {k: doc[k] for k in ("openapi", "swagger", "basePath") if k in doc}
    # The full input's info contains private repository and build metadata, not
    # connector wire semantics. Public slices carry a neutral title and version.
    sliced["info"] = {"title": "Customer connector API", "version": doc.get("info", {}).get("version", "1.0.0")}
    sliced["paths"] = paths
    for ref, target in sorted(refs.items()):
        dest = sliced
        *parents, key = ref[2:].split("/")
        for part in parents:
            dest = dest.setdefault(part, {})
        dest[key] = target
    if name == "ee":
        for item in sliced["paths"].values():
            for operation in item.values():
                if isinstance(operation, dict) and isinstance(operation.get("x-omega-idempotency"), dict):
                    operation["x-omega-idempotency"].pop("evidence", None)
        error = sliced.get("components", {}).get("schemas", {}).get("OmegaError")
        if error is not None:
            error["description"] = "Customer error body, mapped to a typed SDK error with code, message, requestId and retryAfterSeconds."
    text = json.dumps(sliced, indent=2) + "\n"
    out = ROOT / "openapi/connectors" / f"{name}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text)
    return {"source_label": "enterprise customer contract" if name == "ee" else "customer connector contract",
            "source_digest": "sha256:" + hashlib.sha256(raw).hexdigest(),
            "slice": f"openapi/connectors/{name}.json", "slice_sha256": hashlib.sha256(text.encode()).hexdigest()}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ee-repo")
    parser.add_argument("--fa-repo")
    parser.add_argument("--ee-commit")
    parser.add_argument("--fa-commit")
    parser.add_argument("--ee-input", type=Path)
    parser.add_argument("--fa-input", type=Path)
    args = parser.parse_args()
    sources = {
        "ee": snapshot(args.ee_repo, args.ee_commit, "packages/server/src/contracts/customer-openapi.v1.json",
                       ("/workspace/integrations", "/workspace/credentials"), "ee", args.ee_input),
        "fa": snapshot(args.fa_repo, args.fa_commit, "api_contracts/openapi/swagger.json", ("/integrations/",), "fa", args.fa_input),
    }
    (ROOT / "openapi/connectors/source.json").write_text(json.dumps(sources, indent=2) + "\n")


if __name__ == "__main__":
    main()
