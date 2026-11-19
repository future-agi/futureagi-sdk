/**
 * The contract a case is validated against: the scoped platform contract this repository publishes
 * (`openapi/platform/generated/futureagi-platform.openapi.json`). Every operation in it is admitted.
 * Paths are matched by template shape (`{id}` and `{sandboxId}` are the same slot).
 */
import { createHash } from "node:crypto";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { checkSchema, resolvePointer } from "./schema-check.mjs";

const METHODS = ["get", "post", "put", "patch", "delete"];

/** The committed scoped contract, the default for validate.mjs and the http runner. */
export const SCOPED_CONTRACT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../../../openapi/platform/generated/futureagi-platform.openapi.json");

export const shapeOf = (template) => template.replace(/\{[^}]+\}/g, "{}");
export const opKey = (method, template) => `${method.toUpperCase()} ${shapeOf(template)}`;

function deref(doc, node) {
  let current = node;
  for (let i = 0; i < 16 && current && typeof current === "object" && current.$ref; i += 1) current = resolvePointer(doc, current.$ref);
  return current;
}

/**
 * Build the contract from an OpenAPI document. Returns { operations: Map<key, op>, openapi, sha256,
 * source, counts }; each operation carries its `x-omega-sdk` family and method.
 */
export function buildContract({ openapi, source = "unknown", text, scope }) {
  const operations = new Map();
  for (const [docPath, item] of Object.entries(openapi.paths ?? {})) {
    for (const method of METHODS) {
      const op = item[method];
      if (!op) continue;
      const key = opKey(method, docPath);
      operations.set(key, { key, method: method.toUpperCase(), path: docPath, docPath, documented: true, operationId: op.operationId ?? null, sdk: op["x-omega-sdk"] ?? null, op });
    }
  }
  if (scope) {
    const declared = [...scope.operations].sort();
    const actual = [...operations.values()].map((o) => `${o.sdk?.family}.${o.sdk?.method}`).sort();
    if (JSON.stringify(declared) !== JSON.stringify(actual)) throw new Error("contract operations do not match the declared scope");
  }
  return {
    operations,
    scope,
    openapi,
    source,
    sha256: text ? createHash("sha256").update(text).digest("hex") : null,
    counts: { operations: operations.size },
  };
}

/** The JSON request-body schema of an operation, or null. */
export function requestSchema(contract, operation) {
  const body = deref(contract.openapi, operation.op?.requestBody);
  const schema = body?.content?.["application/json"]?.schema;
  return schema ? deref(contract.openapi, schema) : null;
}

/** The JSON response schema for one status, or null (also null for streams). */
export function responseSchema(contract, operation, status) {
  const responses = operation.op?.responses ?? {};
  const response = deref(contract.openapi, responses[String(status)]);
  const schema = response?.content?.["application/json"]?.schema;
  return schema ? deref(contract.openapi, schema) : null;
}

/** The SSE frame union an operation declares (`x-omega-stream.events`), resolved, or null. */
export function eventSchema(contract, operation) {
  const ref = operation.op?.["x-omega-stream"]?.events;
  return typeof ref === "string" ? deref(contract.openapi, { $ref: ref }) ?? null : null;
}

export function checkBody(contract, operation, body) {
  const schema = requestSchema(contract, operation);
  if (!schema) return [];
  return checkSchema(schema, body, { root: contract.openapi, at: "body" });
}

export function checkResponse(contract, operation, status, body) {
  const schema = responseSchema(contract, operation, status);
  if (!schema) return { checked: false, errors: [] };
  return { checked: true, errors: checkSchema(schema, body, { root: contract.openapi, at: "response" }) };
}

const FAMILY_PREFIXES = {
  sandboxes: ["/workspace/sandboxes"],
  runs: ["/workspace/conversations"],
  deployments: ["/workspace/deployments"],
  platform: ["/workspace/capabilities", "/workspace/credentials", "/workspace/approvals", "/workspace/workforce", "/workspace/environments", "/workspace/schedules"],
};

export function familyOfPath(path) {
  for (const [family, prefixes] of Object.entries(FAMILY_PREFIXES)) {
    if (prefixes.some((prefix) => path === prefix || path.startsWith(`${prefix}/`))) return family;
  }
  return null;
}

/**
 * Validate one case against the contract. Returns { key, documented, errors[], notes[] }.
 * A body marked `"bodyInvalidOnPurpose": true` must FAIL the request schema (a malformed-body case).
 */
export function validateCase(contract, testCase) {
  const errors = [];
  const notes = [];
  const op = testCase.op;
  const key = opKey(op.method, op.path);
  const operation = contract.operations.get(key);
  if (!operation) {
    if (!testCase.offManifest) errors.push(`${key} is not an operation of the contract`);
    return { key, documented: false, errors, notes };
  }
  if (operation.sdk && testCase.sdk?.family !== "client" && (testCase.sdk?.family !== operation.sdk.family || testCase.sdk?.method !== operation.sdk.method)) {
    errors.push(`sdk ${testCase.sdk?.family}.${testCase.sdk?.method} but the contract names ${operation.sdk.family}.${operation.sdk.method}`);
  }
  const family = familyOfPath(op.path);
  if (testCase.family !== "cross" && family && testCase.family !== family) errors.push(`family ${testCase.family} but the path is ${family}`);
  if (testCase.sdk?.family && testCase.sdk.family !== "client" && family && testCase.sdk.family !== family) errors.push(`sdk.family ${testCase.sdk.family} but the path is ${family}`);
  const body = testCase.call?.body;
  if (body !== undefined && testCase.call?.rawBody === undefined) {
    const bodyErrors = checkBody(contract, operation, stripPlaceholders(body));
    if (testCase.call?.bodyInvalidOnPurpose) {
      if (bodyErrors.length === 0) errors.push("bodyInvalidOnPurpose, but the body passes the request schema");
    } else if (bodyErrors.length) errors.push(...bodyErrors);
  }
  return { key, documented: true, operationId: operation.operationId, errors, notes };
}

/** Placeholders cannot be checked for format, so a whole-string placeholder becomes a typical value. */
function stripPlaceholders(value) {
  if (typeof value === "string") return /^\$\{[^}]+\}$/.test(value) ? "placeholder" : value;
  if (Array.isArray(value)) return value.map(stripPlaceholders);
  if (value && typeof value === "object") return Object.fromEntries(Object.entries(value).map(([k, v]) => [k, stripPlaceholders(v)]));
  return value;
}
