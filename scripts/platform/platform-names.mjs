import { readFileSync } from "node:fs";
import { escapePointer, METHODS } from "./openapi-walk.mjs";

// The public spelling is the key; the authenticated input uses the source spelling.
export function sourceExtension(key) {
  if (key === "x-sdk-operation") return "x-omega-sdk";
  return key.replace(/^x-sdk-/u, "x-omega-");
}

const operationNames = new Map(Object.entries(JSON.parse(
  readFileSync(new URL("./operation-names.json", import.meta.url), "utf8"),
)));

const componentNames = new Map([
  ["OmegaError", "PlatformError"],
  ["OmegaNestedError", "NestedError"],
  ["OmegaGatewayError", "GatewayError"],
  ["OmegaEeError", "ServiceError"],
  ["OmegaHubError", "HubError"],
  ["OmegaBearer", "PlatformBearer"],
  ["OmegaRunControlStatus", "GetWorkspaceConversationControlStatusResponse"],
  ["OmegaRunCancelResult", "CancelWorkspaceConversationResponse"],
  ["OmegaWorkforceRetirement", "RetireWorkforceAgentResponse"],
  ["OmegaPostWorkspaceConversationsByIdMessagesResponse2", "SendWorkspaceConversationMessageAcceptedResponse"],
  ["CreateWorkspaceScheduleResponse2", "CreateWorkspaceScheduleCreatedResponse"],
  ["RunWorkspaceScheduleResponse2", "RunWorkspaceScheduleAcceptedResponse"],
]);

export const publicOperationId = (name) => operationNames.get(name) ?? name;

export function publicComponentName(name) {
  if (componentNames.has(name)) return componentNames.get(name);
  // Some source schema names derive from an operation ID and a request/response suffix.
  const match = /^(Omega.+)(Request|Response)$/u.exec(name);
  if (match) {
    const op = match[1][0].toLowerCase() + match[1].slice(1);
    if (operationNames.has(op)) {
      const renamed = operationNames.get(op);
      return renamed[0].toUpperCase() + renamed.slice(1) + match[2];
    }
  }
  return name.replace(/^Omega(?=RunEvent|Exec|DeploymentLog)/u, "")
    .replace(/^WorkspaceConversationsIdEvidence/u, "ConversationEvidence");
}

/** Rename metadata on a scoped document in place. Protocol names and values are not metadata. */
export function projectNames(spec, rules) {
  const refs = new Map();
  const schemas = new Map();
  const security = new Map();
  for (const [kind, entries] of Object.entries(spec.components)) {
    const renamed = Object.entries(entries).map(([name, node]) => {
      const next = publicComponentName(name);
      if (kind === "schemas") {
        schemas.set(name, next);
        if (typeof node.title === "string") node.title = publicComponentName(node.title);
      }
      if (kind === "securitySchemes") security.set(name, next);
      refs.set(`#/components/${kind}/${escapePointer(name)}`, `#/components/${kind}/${escapePointer(next)}`);
      return [next, node];
    });
    if (new Set(renamed.map(([name]) => name)).size !== renamed.length) throw new Error(`component name collision in ${kind}`);
    spec.components[kind] = Object.fromEntries(renamed);
  }

  const renameSecurity = (requirements) => requirements?.map((requirement) =>
    Object.fromEntries(Object.entries(requirement).map(([name, scopes]) => [security.get(name) ?? name, scopes])));
  if (spec.security) spec.security = renameSecurity(spec.security);
  const ids = new Set();
  for (const item of Object.values(spec.paths)) {
    for (const method of METHODS) {
      const op = item[method];
      if (!op) continue;
      if (op.operationId !== undefined) {
        op.operationId = publicOperationId(op.operationId);
        if (ids.has(op.operationId)) throw new Error(`operation ID collision: ${op.operationId}`);
        ids.add(op.operationId);
      }
      if (op.security) op.security = renameSecurity(op.security);
      const stream = op["x-sdk-stream"];
      if (stream?.events) stream.events = refs.get(stream.events) ?? stream.events;
    }
  }

  // Reference targets change; discriminator keys, HTTP names, and schema fields do not.
  function visit(node, isNameMap = false) {
    if (Array.isArray(node)) {
      node.forEach((entry) => visit(entry));
      return;
    }
    if (!node || typeof node !== "object") return;
    if (!isNameMap && node.discriminator?.propertyName) {
      const mapping = node.discriminator.mapping;
      const targets = new Set(Object.values(mapping ?? {}));
      for (const key of ["allOf", "anyOf", "oneOf"]) {
        for (const { $ref } of node[key] ?? []) {
          if (refs.has($ref) && refs.get($ref) !== $ref && !targets.has($ref) &&
              !targets.has($ref.split("/").at(-1))) {
            throw new Error("renaming an implicitly tagged schema requires an explicit discriminator mapping");
          }
        }
      }
      for (const [tag, target] of Object.entries(mapping ?? {})) mapping[tag] = refs.get(target) ?? schemas.get(target) ?? target;
    }
    for (const [key, value] of Object.entries(node)) {
      if (!isNameMap && key === "$ref") node[key] = refs.get(value) ?? value;
      else if (!isNameMap && key === "description" && typeof value === "string") {
        node[key] = value.replace(/\bOmega(?:RunEvent|Exec|DeploymentLog)Frame\b/gu, publicComponentName)
          .replace(" (see x-omega-idempotency on the operation for where it is kept and for how long)", "");
      } else if (isNameMap || !["const", "default", "enum", "example", "examples"].includes(key)) {
        visit(value, !isNameMap && rules.nameMaps.includes(key));
      }
    }
  }
  visit(spec);
}
