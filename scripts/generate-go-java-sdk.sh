#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SPEC="$ROOT_DIR/openapi/sdk/generated/futureagi-sdk.openapi.json"
SOURCE_SWAGGER="${1:-"${SOURCE_SWAGGER:-"$ROOT_DIR/../future-agi/api_contracts/openapi/swagger.json"}"}"
GENERATOR_IMAGE="${OPENAPI_GENERATOR_IMAGE:-openapitools/openapi-generator-cli:v7.12.0}"

"$ROOT_DIR/scripts/build-sdk-openapi.sh" "$SOURCE_SWAGGER"

docker run --rm "$GENERATOR_IMAGE" version >/dev/null

rm -rf "$ROOT_DIR/go/futureagi"
docker run --rm \
  -u "$(id -u):$(id -g)" \
  -v "$ROOT_DIR:/local" \
  "$GENERATOR_IMAGE" generate \
  -i "/local/openapi/sdk/generated/futureagi-sdk.openapi.json" \
  -g go \
  -o "/local/go/futureagi" \
  --git-host github.com \
  --git-user-id future-agi \
  --git-repo-id futureagi-sdk/go \
  --global-property=apiTests=false,modelTests=false,modelDocs=false \
  --additional-properties=packageName=futureagi,packageVersion=0.1.0,enumClassPrefix=true,isGoSubmodule=true,hideGenerationTimestamp=true
rm -rf \
  "$ROOT_DIR/go/futureagi/.github" \
  "$ROOT_DIR/go/futureagi/.openapi-generator" \
  "$ROOT_DIR/go/futureagi/.openapi-generator-ignore" \
  "$ROOT_DIR/go/futureagi/.travis.yml" \
  "$ROOT_DIR/go/futureagi/git_push.sh"

rm -rf "$ROOT_DIR/java/futureagi"
docker run --rm \
  -u "$(id -u):$(id -g)" \
  -v "$ROOT_DIR:/local" \
  "$GENERATOR_IMAGE" generate \
  -i "/local/openapi/sdk/generated/futureagi-sdk.openapi.json" \
  -g java \
  -o "/local/java/futureagi" \
  --git-host github.com \
  --git-user-id future-agi \
  --git-repo-id futureagi-sdk \
  --global-property=apiTests=false,modelTests=false,modelDocs=false \
  --additional-properties=artifactId=futureagi-sdk,artifactVersion=0.1.0,groupId=com.futureagi,invokerPackage=com.futureagi.sdk,apiPackage=com.futureagi.sdk.api,modelPackage=com.futureagi.sdk.model,library=native,serializationLibrary=jackson,dateLibrary=java8,enumClassPrefix=true,hideGenerationTimestamp=true,useRuntimeException=true
rm -rf \
  "$ROOT_DIR/java/futureagi/.github" \
  "$ROOT_DIR/java/futureagi/.openapi-generator" \
  "$ROOT_DIR/java/futureagi/.openapi-generator-ignore" \
  "$ROOT_DIR/java/futureagi/.travis.yml" \
  "$ROOT_DIR/java/futureagi/git_push.sh"

echo "Generated Go and Java low-level SDK clients."
