#!/usr/bin/env bash
# Compare the authenticated current input with a candidate local contract.
# Private revision resolution is caller-owned and never persisted here.
# Usage: scripts/platform/check-pin.sh --current <input.json> --candidate <candidate.json>
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
[[ $# -eq 4 && "$1" == "--current" && "$3" == "--candidate" ]] || { printf 'usage: %s --current <input.json> --candidate <candidate.json>\n' "$0" >&2; exit 2; }
node "$ROOT_DIR/scripts/platform/source-pin.mjs" verify "$ROOT_DIR/openapi/platform/source.json" "$2"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
node "$ROOT_DIR/scripts/platform/pin-diff.mjs" "$2" "$4" --scope "$ROOT_DIR/openapi/platform/scope.json" | tee "$TMP/report.txt"
node "$ROOT_DIR/scripts/platform/pin-diff.mjs" --counts "$ROOT_DIR/openapi/platform/generated/futureagi-platform.openapi.json"
BREAKING="$(sed -n 's/^BREAKING: //p' "$TMP/report.txt")"
[[ "$BREAKING" == "0" ]]
