#!/usr/bin/env node
/**
 * Make the public, scoped copy of the platform customer contract.
 *
 *   node scripts/platform/scope-filter.mjs <pinned-contract.json> <out.openapi.json> <out.operations.txt>
 *
 * The scope is an allowlist:
 * - only the operations `openapi/platform/scope.json` names are kept, each with only the keys in
 *   OPERATION_KEYS plus the operation-level extensions in `hygiene-rules.json`;
 * - only the components those operations reach (refs, discriminator mappings, stream frame unions);
 * - every other extension is removed (evidence, auth-authority, control-scope, workforce-action,
 *   hub-auth, provenance, error codes, frames, service, deferred, the contract's own info block);
 * - `info` and `servers` are written here, so nothing from the source's prose about its own build
 *   reaches the public copy; the "wording" patches in `hygiene-rules.json` remove internal references from kept
 *   descriptions: the rules identify references by patterns that must each match exactly
 *   once; a re-pin with zero or multiple matches fails.
 * The result must pass the hygiene scan, or this exits non-zero and writes nothing.
 */

import { readFileSync, writeFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { METHODS, collectRefs, extensionAllowed, pointerParent, structuralFindings } from "./openapi-walk.mjs";
import { loadRules, scanText } from "./hygiene-scan.mjs";
import { projectNames, publicOperationId, sourceExtension } from "./platform-names.mjs";

export { loadRules };

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../..");
const OPERATION_KEYS = ["operationId", "summary", "description", "tags", "parameters", "requestBody", "responses", "security", "deprecated"];
const PATH_ITEM_KEYS = ["summary", "description", "parameters"];
const COMPONENT_KINDS = ["schemas", "responses", "parameters", "requestBodies", "headers"];

const INFO = {
  title: "Future AGI platform API",
  description:
    "The Future AGI platform operations admitted to this SDK release. " +
    "This is a scoped public copy of the platform's customer contract; openapi/platform/source.json names the source and its sha256. " +
    "The SDK retries GET operations and follows each mutation's retry policy. The x-sdk-idempotent extension identifies operations that accept an idempotency key. " +
    "Responses are forward compatible: the SDK accepts unknown fields and enum values from a newer server."
};
const SERVERS = [
  {
    url: "/omega/api",
    description:
      "Relative to your Future AGI API origin (FI_BASE_URL), with a Future AGI API key pair. The SDK derives the platform origin from FI_BASE_URL, or takes FI_PLATFORM_BASE_URL."
  },
  {
    url: "{origin}",
    description: "Your platform service origin, with an account key as a Bearer token.",
    variables: { origin: { default: "http://127.0.0.1", description: "Your service origin: scheme, host and port." } }
  }
];

function pick(object, keys) {
  return Object.fromEntries(keys.filter((k) => object[k] !== undefined).map((k) => [k, object[k]]));
}

/** Copy the allowed fields and translate the source's schema metadata. */
function stripExtensions(node, rules, metadataKey, isNameMap = false) {
  if (Array.isArray(node)) return node.map((item) => stripExtensions(item, rules, metadataKey));
  if (node === null || typeof node !== "object") return node;
  return Object.fromEntries(Object.entries(node).flatMap(([key, value]) => {
    const publicKey = !isNameMap && key === metadataKey("x-sdk-secret") ? "x-sdk-secret" : key;
    if (!isNameMap && key !== metadataKey(publicKey)) return [];
    if (!extensionAllowed(publicKey, value, { where: "other", isName: isNameMap }, rules)) return [];
    return [[publicKey, stripExtensions(value, rules, metadataKey, !isNameMap && rules.nameMaps.includes(key))]];
  }));
}

function sdkName(op, metadataKey) {
  const sdk = op[metadataKey("x-sdk-operation")];
  if (!sdk || !sdk.family || !sdk.method) throw new Error(`operation ${op.operationId} has no SDK metadata`);
  return `${sdk.family}.${sdk.method}`;
}

function scopedOperation(op, rules, metadataKey) {
  const extensions = rules.extensions.operation.filter((key) => op[metadataKey(key)] !== undefined);
  const kept = {
    ...Object.fromEntries(Object.entries(pick(op, OPERATION_KEYS)).map(([key, value]) =>
      [key, stripExtensions(value, rules, metadataKey, rules.nameMaps.includes(key))])),
    ...Object.fromEntries(extensions.map((key) => [key, structuredClone(op[metadataKey(key)])])),
  };
  for (const [key, allowed] of Object.entries(rules.extensions.subkeys)) {
    if (kept[key] && typeof kept[key] === "object") kept[key] = pick(kept[key], allowed);
  }
  return kept;
}

function resolveComponent(doc, ref) {
  const match = /^#\/components\/([^/]+)\/([^/]+)$/u.exec(ref);
  if (!match) throw new Error(`unsupported $ref ${ref}`);
  const [, kind, name] = match;
  const found = doc.components?.[kind]?.[name];
  if (found === undefined) throw new Error(`dangling $ref ${ref}`);
  return { kind, name, node: found };
}

/** Components reachable from the kept paths, by kind, in the source's order. */
function reachable(doc, keptPaths) {
  const seen = new Set();
  const queue = [...collectRefs(keptPaths)];
  while (queue.length > 0) {
    const ref = queue.shift();
    if (seen.has(ref)) continue;
    seen.add(ref);
    for (const next of collectRefs(resolveComponent(doc, ref).node)) if (!seen.has(next)) queue.push(next);
  }
  const out = {};
  for (const kind of COMPONENT_KINDS) {
    const names = Object.keys(doc.components?.[kind] ?? {}).filter((n) => seen.has(`#/components/${kind}/${n}`));
    if (names.length > 0) out[kind] = Object.fromEntries(names.map((n) => [n, doc.components[kind][n]]));
  }
  return out;
}

function securityNames(requirements) {
  return (requirements ?? []).flatMap((r) => Object.keys(r));
}

function applyWording(spec, wording) {
  for (const patch of wording ?? []) {
    const { parent, key } = pointerParent(spec, patch.pointer);
    const text = parent[key];
    if (typeof text !== "string") throw new Error(`wording ${patch.pointer}: not a string`);
    const count = [...text.matchAll(new RegExp(patch.pattern, "gu"))].length;
    if (count !== 1) throw new Error(`wording ${patch.pointer}: /${patch.pattern}/ found ${count} times (remove the patch if the source changed)`);
    parent[key] = text.replace(new RegExp(patch.pattern, "u"), () => patch.replace);
  }
}

/** Build the scoped document. Throws on any scope, contract or hygiene problem. */
export function scopeContract(doc, scope, rules, { publicInput = false } = {}) {
  const metadataKey = publicInput ? (key) => key : sourceExtension;
  const wanted = new Set(scope.operations);
  if (wanted.size !== scope.operations.length) throw new Error("scope.json lists an operation twice");
  const found = new Map();
  const paths = {};
  for (const [route, item] of Object.entries(doc.paths ?? {})) {
    const keptItem = {};
    for (const method of METHODS) {
      const op = item[method];
      if (op === undefined) continue;
      const name = sdkName(op, metadataKey);
      if (!wanted.has(name)) continue;
      if (found.has(name)) throw new Error(`${name} appears twice in the contract`);
      if (op[metadataKey("x-sdk-human-only")] === true) throw new Error(`${name} is human-only and cannot be in scope`);
      found.set(name, { method: method.toUpperCase(), route, operationId: publicOperationId(op.operationId) });
      keptItem[method] = scopedOperation(op, rules, metadataKey);
    }
    if (Object.keys(keptItem).length > 0) {
      const head = stripExtensions(pick(item, PATH_ITEM_KEYS), rules, metadataKey);
      paths[route] = { ...head, ...keptItem };
    }
  }
  const missing = [...wanted].filter((n) => !found.has(n));
  if (missing.length > 0) throw new Error(`scope.json names operations the contract does not have: ${missing.join(", ")}`);

  const components = reachable(doc, paths);
  for (const [kind, entries] of Object.entries(components)) components[kind] = stripExtensions(entries, rules, metadataKey, true);
  const opSecurity = Object.values(paths).flatMap((item) => METHODS.flatMap((m) => securityNames(item[m]?.security)));
  const schemeNames = new Set([...securityNames(doc.security), ...opSecurity]);
  const schemes = doc.components?.securitySchemes ?? {};
  const securitySchemes = stripExtensions(
    Object.fromEntries(Object.entries(schemes).filter(([name]) => schemeNames.has(name))), rules, metadataKey, true);

  const usedTags = new Set(Object.values(paths).flatMap((item) => METHODS.flatMap((m) => item[m]?.tags ?? [])));

  const spec = {
    openapi: doc.openapi,
    info: { ...INFO, version: doc.info.version },
    servers: SERVERS,
    security: structuredClone(doc.security ?? []),
    tags: (doc.tags ?? []).filter((t) => usedTags.has(t.name)).map((t) => stripExtensions(t, rules, metadataKey)),
    paths,
    components: { ...components, securitySchemes }
  };
  applyWording(spec, rules.wording);
  projectNames(spec, rules);
  const problems = [...structuralFindings(spec, rules), ...scanText(JSON.stringify(spec, null, 2), ".json", rules)];
  if (problems.length > 0) throw new Error(`hygiene: ${problems.map((p) => `${p.rule} ${p.at ?? ""} ${p.text}`).join("; ")}`);
  const operations = [...found.entries()]
    .sort(([a], [b]) => (a < b ? -1 : a > b ? 1 : 0))
    .map(([name, f]) => `${name} ${f.method} ${f.route} ${f.operationId}`);
  return { spec, operations };
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const [input, outSpec, outOps] = process.argv.slice(2);
  if (!input || !outSpec || !outOps) {
    process.stderr.write("usage: scope-filter.mjs <pinned-contract.json> <out.openapi.json> <out.operations.txt>\n");
    process.exit(2);
  }
  try {
    const doc = JSON.parse(readFileSync(input, "utf8"));
    const scope = JSON.parse(readFileSync(path.join(ROOT, "openapi/platform/scope.json"), "utf8"));
    const { spec, operations } = scopeContract(doc, scope, loadRules());
    writeFileSync(outSpec, `${JSON.stringify(spec, null, 2)}\n`);
    writeFileSync(outOps, `${operations.join("\n")}\n`);
    process.stdout.write(`scope-filter: ${operations.length} operations, ${Object.keys(spec.components.schemas ?? {}).length} schemas\n`);
  } catch (error) {
    process.stderr.write(`scope-filter: ${error.message}\n`);
    process.exit(1);
  }
}
