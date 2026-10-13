#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SPEC="$ROOT_DIR/openapi/sdk/generated/futureagi-sdk.openapi.json"
SOURCE_SWAGGER="${1:-"${SOURCE_SWAGGER:-"$ROOT_DIR/../future-agi/api_contracts/openapi/swagger.json"}"}"

OPENAPI_TS_PACKAGE="${OPENAPI_TS_PACKAGE:-@hey-api/openapi-ts@0.97.3}"
OPERATION_SCOPE="${SDK_OPERATION_SCOPE:-}"
"$ROOT_DIR/scripts/build-sdk-openapi.sh" "$SOURCE_SWAGGER" "$ROOT_DIR/openapi/sdk/generated" "$OPERATION_SCOPE"

rm -rf "$ROOT_DIR/typescript/futureagi/src/generated/openapi"
npx --yes --package typescript@5.8.3 --package "$OPENAPI_TS_PACKAGE" openapi-ts \
  -i "$SPEC" \
  -o "$ROOT_DIR/typescript/futureagi/src/generated/openapi" \
  -c @hey-api/client-fetch \
  -p @hey-api/typescript @hey-api/sdk \
  --silent

rm -rf "$ROOT_DIR/python/fi/generated/openapi_client"
mkdir -p "$ROOT_DIR/python/fi/generated"
uvx --from openapi-python-client==0.28.4 openapi-python-client generate \
  --path "$SPEC" \
  --meta none \
  --config "$ROOT_DIR/scripts/openapi-python-client.yaml" \
  --overwrite \
  --output-path "$ROOT_DIR/python/fi/generated/openapi_client"

python3 "$ROOT_DIR/scripts/validate-generated-release-gate.py" "$SPEC" \
  "$ROOT_DIR/python/fi/generated/openapi_client/models"
uvx --from ruff==0.15.2 ruff format --isolated --target-version py310 \
  "$ROOT_DIR/python/fi/generated/openapi_client/models/_release_gate_validation.py"

echo "Generated TypeScript and Python low-level SDK clients."
