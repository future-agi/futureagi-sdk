#!/usr/bin/env bash
# Rebuild from an exact local input, authenticated by its content digest.
# Usage: scripts/platform/build-platform-openapi.sh --input <customer-openapi.json>
# Private repository revisions belong in the caller's non-exported evidence, not this tree.
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
SOURCE_JSON="$ROOT_DIR/openapi/platform/source.json"
OUT_DIR="$ROOT_DIR/openapi/platform/generated"
[[ $# -eq 2 && "$1" == "--input" ]] || { printf 'usage: %s --input <customer-openapi.json>\n' "$0" >&2; exit 2; }
INPUT="$2"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
node "$ROOT_DIR/scripts/platform/scope-filter.mjs" "$INPUT" "$TMP/scoped.json" "$TMP/operations.txt"
# pin projects legacy metadata as well, but only after exact input digest verification.
node "$ROOT_DIR/scripts/platform/source-pin.mjs" pin "$SOURCE_JSON" "$INPUT" "$TMP/scoped.json"
mkdir -p "$OUT_DIR"
mv "$TMP/scoped.json" "$OUT_DIR/futureagi-platform.openapi.json"
mv "$TMP/operations.txt" "$OUT_DIR/futureagi-platform.operations.txt"
node "$ROOT_DIR/scripts/platform/hygiene-scan.mjs" openapi/platform
printf 'build-platform-openapi: content-addressed contract written\n'
