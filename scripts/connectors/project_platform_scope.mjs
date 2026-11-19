#!/usr/bin/env node
/** Reproject an already-public, pinned contract through the canonical scope filter. */
import { createHash } from "node:crypto";
import { readFileSync, writeFileSync } from "node:fs";
import path from "node:path";
import { scopeContract, loadRules } from "../platform/scope-filter.mjs";

const root = process.argv[2];
if (!root) throw new Error("usage: project_platform_scope.mjs <repository>");
const platform = path.join(root, "openapi/platform");
const specPath = path.join(platform, "generated/futureagi-platform.openapi.json");
const sourcePath = path.join(platform, "source.json");
const source = JSON.parse(readFileSync(sourcePath, "utf8"));
const input = readFileSync(specPath);
const digest = (bytes) => createHash("sha256").update(bytes).digest("hex");
if (digest(input) !== source.scoped.sha256) throw new Error("Scoped input does not match its pin");
const scope = JSON.parse(readFileSync(0, "utf8"));
// Wording patches were applied when the public input was pinned. Reachability, tags,
// extension stripping and all hygiene checks still use the canonical implementation.
const { spec, operations } = scopeContract(JSON.parse(input), scope, { ...loadRules(), wording: [] });
const text = JSON.stringify(spec, null, 2) + "\n";
source.scoped.sha256 = digest(text);
writeFileSync(path.join(platform, "scope.json"), JSON.stringify(scope, null, 2) + "\n");
writeFileSync(specPath, text);
writeFileSync(path.join(platform, "generated/futureagi-platform.operations.txt"), operations.join("\n") + "\n");
writeFileSync(sourcePath, JSON.stringify(source, null, 2) + "\n");
