"""Public source identities and CLI for the annotation contract snapshot."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def source_identity(files: list[dict]) -> str:
    return hashlib.sha256(json.dumps(files, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def derive(serializer: dict, model_fields: dict) -> dict:
    """Apply DRF's ModelSerializer rules to the parsed facts."""
    declared = serializer["declared_fields"]
    read_only_meta = set(serializer["read_only_fields"])
    writable, required, read_only, write_only = [], [], [], []
    for name in serializer["meta_fields"]:
        if name in declared:
            info = declared[name]
            ro = bool(info.get("read_only")) or info["field"] in {
                "SerializerMethodField", "ReadOnlyField", "HiddenField"}
            req = info.get("required", not (ro or info.get("has_default")))
            wo = bool(info.get("write_only"))
        elif name in read_only_meta:
            ro, req, wo = True, False, False
        elif name in model_fields:
            info = model_fields[name]
            ro = (info.get("editable") is False or bool(info.get("auto_now"))
                  or bool(info.get("auto_now_add")))
            req = not (ro or info.get("has_default") or info.get("null") or info.get("blank"))
            wo = False
        else:
            raise SystemExit(f"field {name!r} is neither declared nor a model field")
        (read_only if ro else writable).append(name)
        if req and not ro:
            required.append(name)
        if wo:
            write_only.append(name)
    return {"writable": writable, "required": required, "read_only": read_only, "write_only": write_only}


def main(api: dict, argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Write or check the annotation queue contract.")
    parser.add_argument("--backend", required=True, help="a backend git checkout")
    parser.add_argument("--ref", default="origin/dev")
    parser.add_argument("--out", default=str(api["SNAPSHOT"]))
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args(argv)
    fresh = api["build"](args.backend, args.ref)
    out = Path(args.out)
    if args.check:
        old = json.loads(out.read_text())
        before, after = old["source"]["sha256"], fresh["source"]["sha256"]
        changed = api["changed_facts"](old, fresh)
        if changed:
            print(f"DRIFT in {', '.join(changed)}: snapshot {before[:12]}, backend {after[:12]}")
            for key in changed:
                print(f"- {key} (snapshot): {json.dumps(old.get(key), sort_keys=True)}")
                print(f"+ {key} (backend): {json.dumps(fresh[key], sort_keys=True)}")
            return 1
        blobs = api["changed_blobs"](old, fresh)
        for path, old_blob, new_blob in blobs:
            print(f"WARNING: {path} changed (sha256 {(old_blob or 'none')[:12]} -> "
                  f"{(new_blob or 'none')[:12]}) but the parsed facts did not. "
                  "Read the retained source diff for scope-id behavior not modeled by this parser.")
        print(f"fields unchanged: snapshot {before[:12]}, backend {after[:12]}"
              + (f"; {len(blobs)} pinned file(s) changed, see WARNING above" if blobs else ""))
        return 2 if blobs and args.strict else 0
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(fresh, indent=2) + "\n")
    print(f"wrote {out} from content sha256:{fresh['source']['sha256']}")
    return 0
