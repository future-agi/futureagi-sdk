"""Structural lockfile content projection; comments and non-metadata fields stay visible.

JSON uses exact token spans, YAML uses its composed node spans, and TOML uses a
round-tripping syntax tree. Parser errors are findings, never file exemptions.
Parser dependencies for YAML/TOML are pinned in requirements-hygiene.txt.
"""
from __future__ import annotations

import json
from pathlib import Path
import re
import sys

LOCKFILES = {"package-lock.json", "pnpm-lock.yaml", "pnpm-lock.yml", "pnpm-lock", "poetry.lock", "uv.lock"}
DEPENDENCIES = {"dependencies", "devDependencies", "optionalDependencies", "peerDependencies", "requires"}
VERSION = re.compile(r"(?:[<>=!~^ ]*v?[0-9xX*]+(?:[.][0-9xX*]+)*(?:[-+._]?[a-zA-Z0-9][a-zA-Z0-9.+_-]*)?)(?:[ ,|]+[<>=!~^ ]*v?[0-9xX*]+(?:[.][0-9xX*]+)*(?:[-+._]?[a-zA-Z0-9][a-zA-Z0-9.+_-]*)?)*")
DIGEST = re.compile(r"(?:(?:sha(?:1|256|384|512)|md5):[a-fA-F0-9]{32,128}|(?:sha(?:1|256|384|512))-[A-Za-z0-9+/]{16,}={0,2}(?:\s+sha(?:1|256|384|512)-[A-Za-z0-9+/]{16,}={0,2})*|[a-fA-F0-9]{32}|[a-fA-F0-9]{40}|[a-fA-F0-9]{64}|[a-fA-F0-9]{96}|[a-fA-F0-9]{128})")


def _skip(name, keys, value):
    if not isinstance(value, str) or not keys:
        return False
    key = keys[-1]
    if name == "package-lock.json":
        package = len(keys) >= 3 and keys[0] == "packages" and "node_modules/" in str(keys[1])
        legacy = len(keys) >= 3 and keys[0] == "dependencies" and all(keys[i] == "dependencies" for i in range(0, len(keys) - 2, 2))
        direct = package and len(keys) == 3 or legacy and len(keys) % 2 == 1
        root_ranges = len(keys) == 2 and keys[0] in DEPENDENCIES
        package_ranges = len(keys) == 4 and keys[-2] in DEPENDENCIES and (package or keys[:2] == ["packages", ""])
        legacy_ranges = len(keys) >= 4 and keys[-2] in DEPENDENCIES and all(keys[i] == "dependencies" for i in range(0, len(keys) - 2, 2))
        if direct and key in {"integrity", "shasum"}:
            return bool(DIGEST.fullmatch(value))
        return bool(VERSION.fullmatch(value)) and (direct and key == "version" or root_ranges or package_ranges or legacy_ranges)
    if name.startswith("pnpm-lock"):
        package = len(keys) >= 3 and keys[0] in {"packages", "snapshots"}
        importer = len(keys) >= 4 and keys[0] == "importers" and keys[2] in DEPENDENCIES
        if package and len(keys) == 4 and keys[-2:] == ["resolution", "integrity"]:
            return bool(DIGEST.fullmatch(value))
        return bool(VERSION.fullmatch(value)) and (package and len(keys) == 4 and keys[-2] in DEPENDENCIES or importer and len(keys) == 5 and key in {"version", "specifier"})
    package = len(keys) >= 3 and keys[0] == "package" and isinstance(keys[1], int)
    if key in {"hash", "sha256", "checksum", "content-hash"}:
        artifact = package and keys[2] in {"files", "wheels", "sdist"}
        metadata = keys == ["metadata", "content-hash"] or keys[:2] == ["metadata", "files"]
        return bool(DIGEST.fullmatch(value)) and (artifact or metadata)
    return bool(VERSION.fullmatch(value)) and package and (len(keys) == 3 and key == "version" or len(keys) == 4 and keys[2] == "dependencies" or len(keys) == 5 and keys[2] == "dependencies" and key == "version")


def _blank(value):
    return "".join("\n" if c == "\n" else " " for c in value)


def _json_projection(text, name):
    # Parse first: syntax errors and duplicate object members fail closed.
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError("duplicate lockfile key")
            result[key] = value
        return result
    json.loads(text, object_pairs_hook=pairs)
    decoder = json.JSONDecoder()
    spans = []

    def whitespace(i):
        while i < len(text) and text[i].isspace():
            i += 1
        return i

    def walk(i, keys):
        i = whitespace(i)
        if text[i] == "{":
            i = whitespace(i + 1)
            while text[i] != "}":
                key, end = decoder.raw_decode(text, i)
                i = walk(whitespace(end) + 1, [*keys, key])
                i = whitespace(i)
                if text[i] == ",":
                    i = whitespace(i + 1)
            return i + 1
        if text[i] == "[":
            i, index = whitespace(i + 1), 0
            while text[i] != "]":
                i = whitespace(walk(i, [*keys, index]))
                index += 1
                if text[i] == ",":
                    i = whitespace(i + 1)
            return i + 1
        value, end = decoder.raw_decode(text, i)
        if _skip(name, keys, value):
            spans.append((i, end))
        return end
    walk(0, [])
    return _mask(text, spans)


def _mask(text, spans):
    for start, end in sorted(spans, reverse=True):
        text = text[:start] + _blank(text[start:end]) + text[end:]
    return text


def _package_key(value):
    # Keep the package name visible; only a valid package version suffix is metadata.
    match = re.fullmatch(r"(/?(?:@[a-zA-Z0-9_.-]+/)?[a-zA-Z0-9_.-]+)[@/]([^()]+)", value)
    if match and VERSION.fullmatch(match[2]):
        return match[1] + value[len(match[1])] + _blank(match[2])
    return value


def _yaml_projection(text, name):
    import yaml
    spans = []
    replacements = []
    root = yaml.compose(text, Loader=yaml.SafeLoader)

    def walk(node, keys, active):
        if id(node) in active:
            raise ValueError("recursive lockfile alias")
        active = {*active, id(node)}
        if isinstance(node, yaml.MappingNode):
            seen = set()
            for key, value in node.value:
                if not isinstance(key, yaml.ScalarNode) or key.value in seen:
                    raise ValueError("invalid or duplicate lockfile key")
                seen.add(key.value)
                if len(keys) == 1 and keys[0] in {"packages", "snapshots"}:
                    projected = _package_key(key.value)
                    if projected != key.value:
                        raw = text[key.start_mark.index:key.end_mark.index]
                        # No decoded/escaped key can gain a wider exemption.
                        if raw.strip("'\"") == key.value:
                            replacements.append((key.start_mark.index, key.end_mark.index, raw.replace(key.value, projected)))
                walk(value, [*keys, key.value], active)
        elif isinstance(node, yaml.SequenceNode):
            for index, item in enumerate(node.value):
                walk(item, [*keys, index], active)
        elif _skip(name, keys, node.value):
            spans.append((node.start_mark.index, node.end_mark.index))
    if root is None:
        raise ValueError("empty lockfile")
    walk(root, [], set())
    for start, end, value in replacements:
        text = text[:start] + value + text[end:]
    return _mask(text, spans)


def _toml_projection(text, name):
    import tomlkit
    from tomlkit.items import String
    doc = tomlkit.parse(text)

    def walk(node, keys):
        entries = list(node.items()) if hasattr(node, "items") else list(enumerate(node)) if isinstance(node, list) else []
        for key, value in entries:
            here = [*keys, key]
            if isinstance(value, String) and _skip(name, here, str(value)):
                # Valid metadata is single-line and needs no escaping. Assigning a
                # scalar preserves TOML comments, whitespace and inline-table structure.
                node[key] = _blank(str(value))
            else:
                walk(value, here)
    walk(doc, [])
    result = doc.as_string()
    if result.count("\n") != text.count("\n"):
        raise ValueError("lockfile projection changed line positions")
    return result


def project(text, file):
    name = Path(file).name
    if name not in LOCKFILES:
        return text
    if name == "package-lock.json":
        return _json_projection(text, name)
    if name.startswith("pnpm-lock"):
        return _yaml_projection(text, name)
    return _toml_projection(text, name)


if __name__ == "__main__":
    try:
        print(json.dumps({"text": project(sys.stdin.read(), sys.argv[1])}))
    except Exception as exc:
        print(json.dumps({"error": type(exc).__name__ + ": lockfile could not be parsed structurally"}))
        sys.exit(1)
