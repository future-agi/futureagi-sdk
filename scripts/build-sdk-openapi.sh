#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SOURCE_SWAGGER="${1:-"$ROOT_DIR/../future-agi/api_contracts/openapi/swagger.json"}"
OUT_DIR="${2:-"$ROOT_DIR/openapi/sdk/generated"}"
ALIASES_FILE="$ROOT_DIR/openapi/sdk/operation-aliases.json"
WRAPPER_MAP_FILE="$ROOT_DIR/openapi/sdk/wrapper-map.json"

mkdir -p "$OUT_DIR"

OPS_FILE="$OUT_DIR/futureagi-sdk.operations.txt"
CONVERTED="$OUT_DIR/futureagi-management.openapi.json"
FILTERED="$OUT_DIR/futureagi-sdk.filtered.openapi.json"
PRUNED="$OUT_DIR/futureagi-sdk.pruned.openapi.json"
PUBLIC_SPEC="$OUT_DIR/futureagi-sdk.openapi.json"

SDK_PATH_PATTERN='^/(model-hub/(annotation-queues|annotations-labels|scores|develops|dataset/|datasets|experiments/v2|api-keys|default-provider|knowledge-base|prompt-templates|prompt-labels|prompt-history-executions|api/models_list|model-providers/get-model-details|eval-templates|delete-eval-template)|sdk/api/v1|simulate/(agent-definitions|run-tests|test-executions|call-executions|api/(call-executions|run-tests|test-executions|personas)|scenarios|simulator-agents|prompt-templates/.*/simulations|prompt-simulations/scenarios|export)|tracer/(bulk-annotation|get-annotation-labels|project/list_projects|trace/|trace-session|trace-annotation|users|user-alerts|user-alert-logs|feed/issues)|accounts/(user-info|organization/members|workspace/list|workspace/switch|workspace/.*/members))'

jq -r --arg pattern "$SDK_PATH_PATTERN" '
  .paths
  | to_entries[]
  | select(.key | test($pattern))
  | .value
  | to_entries[]
  | select(.key | IN("get", "post", "put", "patch", "delete"))
  | .value.operationId
' "$SOURCE_SWAGGER" | sort -u > "$OPS_FILE"

OPERATIONS="$(paste -sd, "$OPS_FILE")"

npx --yes swagger2openapi \
  --patch \
  --targetVersion 3.0.3 \
  --outfile "$CONVERTED" \
  "$SOURCE_SWAGGER" >/dev/null

npx --yes @hey-api/openapi-ts \
  --input "$CONVERTED" \
  --output "$OUT_DIR/.tmp-filter-check" \
  --dry-run \
  --silent >/dev/null

jq --arg pattern "$SDK_PATH_PATTERN" '
  .paths |= with_entries(
    select(.key | test($pattern))
    | .value |= with_entries(select(.key | IN("get", "post", "put", "patch", "delete", "parameters")))
  )
  | .components.schemas |= with_entries(.)
' "$CONVERTED" > "$FILTERED"

node "$ROOT_DIR/scripts/prune-openapi-components.mjs" "$FILTERED" "$PRUNED"

TMP_FILE="$(mktemp)"
jq --slurpfile aliases "$ALIASES_FILE" '
  def fix_schema:
    if type == "object" then
      (if .type? == "file" then .type = "string" | .format = "binary" else . end)
      | (if .type? == "object" and .nullable? == true then
          del(.nullable)
        else
          .
        end)
      | (if .type? == "object" and (has("properties") | not) and (has("additionalProperties") | not) then
          .additionalProperties = true
        else
          .
        end)
      | (if has("default") and (
            (has("$ref"))
            or ((.type? == "object") and ((.default | type) == "object"))
            or (.type? == "array")
            or ((has("enum")) and (.default as $default | (.enum | index($default)) == null))
          ) then
          del(.default)
        else
          .
        end)
      | (if has("default") and has("type") and (
            ((.type == "string") and ((.default | type) != "string"))
            or ((.type == "integer" or .type == "number") and ((.default | type) != "number"))
            or ((.type == "boolean") and ((.default | type) != "boolean"))
            or ((.type == "array") and ((.default | type) != "array"))
            or ((.type == "object") and ((.default | type) != "object"))
          ) then
          del(.default)
        else
          .
        end)
      | (if .type? == "object" and .nullable? == true and (has("properties") | not) then
          del(.nullable)
        else
          .
        end)
      | (if has("responses") then
          .responses |= with_entries(
            if (.value | type) == "object" then
              .value.description = (
                if ((.value.description // "") == "") then "Response" else .value.description end
              )
            else
              .
            end
          )
        else
          .
        end)
      | with_entries(.value |= fix_schema)
    elif type == "array" then
      map(fix_schema)
    else
      .
    end;

  def patch_operation($path; $method):
    ($aliases[0][(($method | ascii_upcase) + " " + $path)] // null) as $alias
    | if $alias == null then
        .
      else
        .operationId = $alias.operationId
        | .tags = [$alias.tag]
      end;

  fix_schema
  | (if .components.schemas.TestExecutionStatus? then
      .components.schemas.TestExecutionStatusSummary = .components.schemas.TestExecutionStatus
      | del(.components.schemas.TestExecutionStatus)
      | walk(
          if type == "object" and .["$ref"]? == "#/components/schemas/TestExecutionStatus" then
            .["$ref"] = "#/components/schemas/TestExecutionStatusSummary"
          else
            .
          end
        )
    else
      .
    end)
  | .info.title = "Future AGI Public SDK API"
  | .info.version = "0.1.0"
  | .servers = [{"url": "https://api.futureagi.com"}]
  | .paths |= with_entries(
      .key as $path
      | .value |= with_entries(
          if .key | IN("get", "post", "put", "patch", "delete") then
            .key as $method
            | .value |= patch_operation($path; $method)
          else
            .
          end
        )
    )
  | .tags = (
      [
        .paths[]
        | to_entries[]
        | select(.key | IN("get", "post", "put", "patch", "delete"))
        | .value.tags[]?
      ]
      | unique
      | map({name: .})
    )
' "$PRUNED" > "$TMP_FILE"
mv "$TMP_FILE" "$PUBLIC_SPEC"
chmod 0644 "$PUBLIC_SPEC"

rm -rf "$OUT_DIR/.tmp-filter-check"
rm -f "$CONVERTED" "$FILTERED" "$PRUNED"

node - "$PUBLIC_SPEC" "$WRAPPER_MAP_FILE" <<'NODE'
const fs = require("fs");

const spec = JSON.parse(fs.readFileSync(process.argv[2], "utf8"));
const wrapperMap = JSON.parse(fs.readFileSync(process.argv[3], "utf8"));

const operationIds = new Set();
for (const pathItem of Object.values(spec.paths ?? {})) {
  for (const [method, operation] of Object.entries(pathItem ?? {})) {
    if (!["get", "post", "put", "patch", "delete"].includes(method)) {
      continue;
    }
    if (operation?.operationId) {
      operationIds.add(operation.operationId);
    }
  }
}

const missing = [];
for (const [namespace, methods] of Object.entries(wrapperMap)) {
  for (const [method, operationId] of Object.entries(methods ?? {})) {
    if (!operationIds.has(operationId)) {
      missing.push(`${namespace}.${method} -> ${operationId}`);
    }
  }
}

if (missing.length > 0) {
  console.error(`Wrapper map references missing operationIds:\n${missing.join("\n")}`);
  process.exit(1);
}
NODE

echo "Built $PUBLIC_SPEC with $(wc -l < "$OPS_FILE" | tr -d " ") operations."
