#!/usr/bin/env node
/** Reproject an already-public, pinned contract through the canonical scope filter. */
import { createHash } from "node:crypto";
import { existsSync, readFileSync, writeFileSync } from "node:fs";
import path from "node:path";
import { publicComponentName, publicOperationId } from "../platform/platform-names.mjs";
import { scopeContract, loadRules } from "../platform/scope-filter.mjs";

const [root, mode, ...rest] = process.argv.slice(2);
if (!root || (mode !== undefined && mode !== "--legacy-names") || rest.length) {
  throw new Error("usage: project_platform_scope.mjs <repository> [--legacy-names]");
}
const platform = path.join(root, "openapi/platform");
const specPath = path.join(platform, "generated/futureagi-platform.openapi.json");
const sourcePath = path.join(platform, "source.json");
const source = JSON.parse(readFileSync(sourcePath, "utf8"));
const input = readFileSync(specPath);
const digest = (bytes) => createHash("sha256").update(bytes).digest("hex");
if (digest(input) !== source.scoped.sha256) throw new Error("Scoped input does not match its pin");
const scope = JSON.parse(readFileSync(0, "utf8"));
if (mode === "--legacy-names") {
  const prior = JSON.parse(readFileSync(path.join(platform, "scope.json"), "utf8"));
  if (JSON.stringify([...prior.operations].sort()) !== JSON.stringify([...scope.operations].sort())) {
    throw new Error("Migrate names without changing the operation scope");
  }
}
// Wording patches were applied when the public input was pinned. Reachability, tags,
// extension stripping and all hygiene checks still use the canonical implementation.
const { spec, operations } = scopeContract(JSON.parse(input), scope, { ...loadRules(), wording: [] }, { publicInput: mode !== "--legacy-names" });
const text = JSON.stringify(spec, null, 2) + "\n";
const mapPath = path.join(platform, "wrapper-map.json");
if (mode === "--legacy-names" && existsSync(mapPath)) {
  const mapping = JSON.parse(readFileSync(mapPath, "utf8"));
  for (const name of scope.operations) {
    const wrapper = mapping.operations[name];
    if (!wrapper) continue;
    if (wrapper.operation_id) wrapper.operation_id = publicOperationId(wrapper.operation_id);
    if (wrapper.body?.schema) wrapper.body.schema = publicComponentName(wrapper.body.schema);
    if (typeof wrapper.response === "string") wrapper.response = publicComponentName(wrapper.response);
  }
  writeFileSync(mapPath, JSON.stringify(mapping, null, 2) + "\n");
}
source.scoped.sha256 = digest(text);
writeFileSync(path.join(platform, "scope.json"), JSON.stringify(scope, null, 2) + "\n");
writeFileSync(specPath, text);
writeFileSync(path.join(platform, "generated/futureagi-platform.operations.txt"), operations.join("\n") + "\n");
writeFileSync(sourcePath, JSON.stringify(source, null, 2) + "\n");
