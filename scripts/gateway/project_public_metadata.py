#!/usr/bin/env python3
"""Project retained historical fixture metadata into public source records.

Input mappings are retained outside the public tree. They rename provenance,
never test cases, expected values, comparison rules, statuses or recorded wire
payloads. Outputs remain reproducible from the original records and mapping.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

# Only these fields may carry historical prose or source identities. Other
# strings (including regex match rules and actual frames) are copied verbatim.
TEXT_FIELDS = {"about", "description", "summary", "evidence", "by", "verdict",
               "source", "text", "owner", "ids_from", "note", "reason", "why",
               "recorded_at", "gateway_pin", "golden_cases", "commit", "edits", "//"}
KEY_PREFIXES = ("published_vs_", "wheel_vs_")


def project(value: object, replacements: dict[str, str], key: str = "") -> object:
    if key in {"match", "cases", "frames", "test_id", "expected", "result", "response"}:
        return value

    def text(s: str) -> str:
        for old in sorted(replacements, key=len, reverse=True):
            s = re.sub(r"(?<![A-Za-z0-9])" + re.escape(old) + r"(?![A-Za-z0-9])",
                       lambda _: replacements[old], s)
        return s

    if isinstance(value, dict):
        result = {}
        for k, v in value.items():
            name = "record" if k == "commit" else k
            if k.startswith(KEY_PREFIXES) or " (packed from " in k:
                name = text(k)
            if name in result:
                raise ValueError(f"projection merges keys: {name}")
            result[name] = project(v, replacements, k)
        return result
    if isinstance(value, list):
        return [project(v, replacements, key) for v in value]
    if isinstance(value, str) and (key in TEXT_FIELDS or key.endswith(".map") or key.endswith(".ts")):
        return text(value)
    return value


def render(source: str, replacements: dict[str, str]) -> str:
    """Keep fixture formatting, while checking the metadata-only projection."""
    rendered = source
    for old in sorted(replacements, key=len, reverse=True):
        rendered = re.sub(r"(?<![A-Za-z0-9])" + re.escape(old) + r"(?![A-Za-z0-9])",
                          lambda _: replacements[old], rendered)
    rendered = re.sub(r'"commit"(\s*:)', r'"record"\1', rendered)
    actual, expected = json.loads(rendered), project(json.loads(source), replacements)
    if actual != expected:
        def differing(a: object, b: object, path: str = "") -> list[str]:
            if isinstance(a, dict) and isinstance(b, dict):
                return [p for k in a.keys() | b.keys() for p in differing(a.get(k), b.get(k), path + "/" + k)]
            if isinstance(a, list) and isinstance(b, list) and len(a) == len(b):
                return [p for i, (x, y) in enumerate(zip(a, b)) for p in differing(x, y, path + f"/{i}")]
            return [] if a == b else [path]
        raise ValueError("replacement would change non-metadata fixture data at " + ", ".join(differing(actual, expected)))
    return rendered


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("mapping", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    source = args.source.read_text()
    mapping = json.loads(args.mapping.read_text())
    if not isinstance(mapping, dict) or not all(isinstance(k, str) and isinstance(v, str)
                                               and k and v for k, v in mapping.items()):
        raise ValueError("mapping must contain nonempty string identities")
    args.output.write_text(render(source, mapping))


if __name__ == "__main__":
    main()
