#!/usr/bin/env bash
# Regenerate every platform file from the committed scoped contract. No EE checkout is needed; to move
# the pin, run scripts/platform/check-pin.sh and scripts/platform/build-platform-openapi.sh first.
#
#   scripts/generate-platform-sdk.sh            # write into the tree
#   scripts/generate-platform-sdk.sh --out DIR  # write the same files under DIR (used by check.sh)
#
# Pinned tools (fetched by npx / uvx, nothing is added to package.json or pyproject.toml):
# @hey-api/openapi-ts 0.97.3 with typescript 5.8.3 (TypeScript types and operations) and black 22.10.0
# (formats the generated Python, the repository's pre-commit formatter).
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SPEC="$ROOT_DIR/openapi/platform/generated/futureagi-platform.openapi.json"
OPENAPI_TS_PACKAGE="${OPENAPI_TS_PACKAGE:-@hey-api/openapi-ts@0.97.3}"
BLACK_PACKAGE="${BLACK_PACKAGE:-black==22.10.0}"
BLACK_PYTHON="${BLACK_PYTHON:-3.11}"

OUT=""
if [[ $# -eq 2 && "$1" == "--out" ]]; then
  OUT="$2"
elif [[ $# -ne 0 ]]; then
  echo "usage: $0 [--out DIR]" >&2
  exit 2
fi
if [[ -n "$OUT" ]]; then
  TS_DIR="$OUT/typescript/futureagi/src/generated/platform"
  PY_DIR="$OUT/python/fi/generated/platform"
else
  TS_DIR="$ROOT_DIR/typescript/futureagi/src/generated/platform"
  PY_DIR="$ROOT_DIR/python/fi/generated/platform"
fi

# TypeScript: hey-api owns the directory except policy.gen.ts, which the policy emitter adds after it,
# and __tests__/, the hand-written gate tests that jest runs.
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT
npx --yes --package typescript@5.8.3 --package "$OPENAPI_TS_PACKAGE" openapi-ts \
  -i "$SPEC" \
  -o "$WORK/ts" \
  -c @hey-api/client-fetch \
  -p @hey-api/typescript @hey-api/sdk \
  --silent
mkdir -p "$TS_DIR" "$PY_DIR"
find "$TS_DIR" -mindepth 1 -maxdepth 1 ! -name __tests__ -exec rm -rf {} +
cp -R "$WORK/ts/." "$TS_DIR/"

# The policy table for both languages, then the Python types.
node "$ROOT_DIR/scripts/platform/emit-policy.mjs" --out "$WORK/policy"
mv "$WORK/policy/policy.gen.ts" "$TS_DIR/policy.gen.ts"
mv "$WORK/policy/policy.py" "$PY_DIR/policy.py"
python3 "$ROOT_DIR/scripts/platform/gen-py/types_emit.py" --spec "$SPEC" --out "$PY_DIR"
if [[ -n "$OUT" ]]; then
  cp "$ROOT_DIR/python/fi/generated/platform/__init__.py" "$PY_DIR/__init__.py"
fi
uvx --python "$BLACK_PYTHON" --from "$BLACK_PACKAGE" black --quiet "$PY_DIR/policy.py" "$PY_DIR/types.py"

# Console facades follow the same scoped input. Hidden release trees omit their generator.
if [[ -f "$ROOT_DIR/scripts/platform/generate-console.py" ]]; then
  CONSOLE_OUT="${OUT:-$ROOT_DIR}"
  python3 "$ROOT_DIR/scripts/platform/generate-console.py" --out "$CONSOLE_OUT"
  uvx --python "$BLACK_PYTHON" --from "$BLACK_PACKAGE" black --quiet \
    "$CONSOLE_OUT/python/fi/agents/_async_client.py" \
    "$CONSOLE_OUT/python/fi/agents/schedules/_async_client.py" \
    "$CONSOLE_OUT/python/fi/environments/_async_client.py"
fi

echo "generate-platform-sdk: wrote $TS_DIR and $PY_DIR"
