#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SPEC="$ROOT_DIR/openapi/sdk/generated/futureagi-sdk.openapi.json"
SOURCE_SWAGGER="${1:-"${SOURCE_SWAGGER:-"$ROOT_DIR/../future-agi/api_contracts/openapi/swagger.json"}"}"

"$ROOT_DIR/scripts/build-sdk-openapi.sh" "$SOURCE_SWAGGER"

rm -rf "$ROOT_DIR/typescript/futureagi/src/generated/openapi"
npx --yes @hey-api/openapi-ts \
  -i "$SPEC" \
  -o "$ROOT_DIR/typescript/futureagi/src/generated/openapi" \
  -c @hey-api/client-fetch \
  -p @hey-api/typescript @hey-api/sdk \
  --silent

rm -rf "$ROOT_DIR/python/fi/generated/openapi_client"
mkdir -p "$ROOT_DIR/python/fi/generated"
uvx --from openapi-python-client openapi-python-client generate \
  --path "$SPEC" \
  --meta none \
  --overwrite \
  --output-path "$ROOT_DIR/python/fi/generated/openapi_client"

echo "Generated TypeScript and Python low-level SDK clients."
