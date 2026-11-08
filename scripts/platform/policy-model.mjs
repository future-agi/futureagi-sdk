/**
 * The policy table, read from the scoped platform contract: one entry per operation with everything a
 * client needs to call it without a hand-written URL (method, path template, parameters, body class)
 * and to call it safely (retry class, idempotency, stream and pagination shapes, secret fields).
 * Pure: the same document gives the same table. Keys are snake_case; the TypeScript renderer converts.
 */

import { METHODS } from "./openapi-walk.mjs";

/** Verbs that stop work; a client never retries them after a cancel of its own. */
const STOP_VERBS = new Set(["cancel", "interrupt", "kill"]);
const HTTP_IDEMPOTENT = new Set(["GET", "PUT", "DELETE", "HEAD", "OPTIONS"]);

export function resolver(doc) {
  return (node) => {
    let seen = 0;
    while (node && typeof node === "object" && typeof node.$ref === "string") {
      const ref = node.$ref;
      if (!ref.startsWith("#/")) throw new Error(`non-local $ref ${ref}`);
      node = ref
        .slice(2)
        .split("/")
        .reduce((at, part) => at?.[part.replaceAll("~1", "/").replaceAll("~0", "~")], doc);
      if (node === undefined) throw new Error(`dangling $ref ${ref}`);
      seen += 1;
      if (seen > 32) throw new Error(`$ref loop at ${ref}`);
    }
    return node;
  };
}

/** Dotted paths of the fields a schema marks `x-omega-secret` (`*` for map values and array items). */
export function secretPaths(get, schema, prefix, depth = 0, stack = []) {
  const out = new Set();
  if (depth > 12 || schema === undefined || schema === null) return out;
  const ref = typeof schema === "object" ? schema.$ref : undefined;
  if (ref !== undefined) {
    if (stack.includes(ref)) return out;
    stack = [...stack, ref];
  }
  const node = get(schema);
  if (node === null || typeof node !== "object") return out;
  if (node["x-omega-secret"] === true) {
    out.add(prefix);
    return out;
  }
  const add = (set) => set.forEach((p) => out.add(p));
  for (const key of ["oneOf", "anyOf", "allOf"]) for (const branch of node[key] ?? []) add(secretPaths(get, branch, prefix, depth + 1, stack));
  for (const [name, prop] of Object.entries(node.properties ?? {})) add(secretPaths(get, prop, `${prefix}.${name}`, depth + 1, stack));
  if (node.additionalProperties && typeof node.additionalProperties === "object") add(secretPaths(get, node.additionalProperties, `${prefix}.*`, depth + 1, stack));
  if (node.items && typeof node.items === "object") add(secretPaths(get, node.items, `${prefix}.*`, depth + 1, stack));
  return out;
}

function successSchema(get, op) {
  for (const [status, response] of Object.entries(op.responses ?? {})) {
    if (!String(status).startsWith("2")) continue;
    const content = get(response)?.content ?? {};
    if (content["application/json"]) return content["application/json"].schema;
  }
  return undefined;
}

/** `keyed`, `keyed-not-durable`, `http-idempotent` or `unsafe` (the names `fi._http` reads). */
export function retryClass(method, idempotent, durable) {
  if (idempotent) return durable === false ? "keyed-not-durable" : "keyed";
  return HTTP_IDEMPOTENT.has(method) ? "http-idempotent" : "unsafe";
}

function knownEvents(get, ref) {
  const union = get({ $ref: ref });
  const mapping = union?.discriminator?.mapping ?? {};
  const events = Object.keys(mapping);
  if (events.length === 0) throw new Error(`stream union ${ref} has no discriminator mapping`);
  return { title: union.title ?? ref.split("/").pop(), events };
}

function entry(get, route, method, item, op) {
  const sdk = op["x-omega-sdk"];
  const name = `${sdk.family}.${sdk.method}`;
  const params = [...(item.parameters ?? []), ...(op.parameters ?? [])].map(get);
  const pathParams = [...route.matchAll(/\{([^}]+)\}/gu)].map((m) => m[1]);
  const query = [...new Set(params.filter((p) => p.in === "query").map((p) => p.name))].sort();
  const headers = [...new Set(params.filter((p) => p.in === "header").map((p) => p.name.toLowerCase()))]
    .filter((h) => h !== "idempotency-key")
    .sort();
  const bodyNode = op.requestBody ? get(op.requestBody) : undefined;
  const contentType = Object.keys(bodyNode?.content ?? {})[0] ?? null;
  const requestSchema = contentType ? bodyNode.content[contentType].schema : undefined;
  const body = op["x-omega-body-class"] ?? (contentType === null ? "none" : contentType === "application/json" ? "json" : "bundle");
  const idempotent = op["x-omega-idempotent"] === true;
  const idem = op["x-omega-idempotency"] ?? {};
  const durable = idempotent ? (idem.durable === undefined ? null : idem.durable) : null;
  const upper = method.toUpperCase();
  const secrets = new Set([...secretPaths(get, requestSchema, "request"), ...secretPaths(get, successSchema(get, op), "response")]);
  const spec = {
    name,
    operation_id: op.operationId ?? null,
    family: sdk.family,
    method: upper,
    path: route,
    path_params: pathParams,
    multi_segment: pathParams.filter((p) => p === "path" && route.endsWith("{path}")),
    query,
    headers,
    body,
    content_type: contentType,
    timeout: op["x-omega-timeout-class"] ?? (method === "get" ? "read" : "write"),
    rate: op["x-omega-rate-class"] ?? null,
    role: op["x-omega-min-role"] ?? null,
    retry: retryClass(upper, idempotent, durable),
    idempotent,
    durable,
    key_required: idempotent && idem.keyRequired === true,
    replay_omits: idempotent ? [...(idem.replayOmits ?? [])] : [],
    not_found_means_applied: op["x-omega-not-found-on-retry-means-applied"] === true,
    human_only: op["x-omega-human-only"] === true,
    stop: STOP_VERBS.has(sdk.method.split(".").pop()),
    secret_fields: [...secrets].sort(),
    stream: null,
    pagination: null
  };
  const stream = op["x-omega-stream"];
  if (stream) {
    const { title, events } = knownEvents(get, stream.events);
    const poll = stream.pollFallback ?? {};
    spec.stream = {
      kind: stream.kind,
      resume: stream.resume,
      resume_when: stream.resumeWhen ?? null,
      events: title,
      known_events: events,
      keepalive_seconds: stream.keepaliveSeconds ?? null,
      cancel_on_disconnect: stream.cancelOnDisconnect === true,
      poll_param: poll.param ?? null,
      poll_value: poll.value ?? null,
      poll_wait_param: poll.waitParam ?? null,
      poll_max_wait_ms: poll.maxWaitMs ?? null
    };
  }
  const paging = op["x-omega-pagination"];
  if (paging) {
    spec.pagination = {
      style: paging.style,
      items_field: paging.itemsField,
      cursor_param: paging.cursorParam ?? null,
      limit_param: paging.limitParam ?? null,
      next_cursor_field: paging.nextCursorField ?? null,
      has_more_field: paging.hasMoreField ?? null,
      truncated_field: paging.truncatedField ?? null,
      opaque_cursor: paging.opaqueCursor === true
    };
  }
  return spec;
}

/** `{ operations: [entry...] sorted by name, events: {union title: [event...]} }`. */
export function buildPolicy(doc) {
  const get = resolver(doc);
  const operations = [];
  for (const [route, item] of Object.entries(doc.paths ?? {})) {
    for (const method of METHODS) {
      const op = item[method];
      if (op === undefined) continue;
      if (!op["x-omega-sdk"]?.family || !op["x-omega-sdk"]?.method) throw new Error(`${method.toUpperCase()} ${route} has no x-omega-sdk`);
      operations.push(entry(get, route, method, item, op));
    }
  }
  const names = operations.map((o) => o.name);
  const twice = [...new Set(names.filter((n, i) => names.indexOf(n) !== i))];
  if (twice.length > 0) throw new Error(`duplicate SDK names: ${twice.join(", ")}`);
  operations.sort((a, b) => (a.name < b.name ? -1 : a.name > b.name ? 1 : 0));
  const events = {};
  for (const op of operations) if (op.stream) events[op.stream.events] = op.stream.known_events;
  return { operations, events: Object.fromEntries(Object.entries(events).sort(([a], [b]) => (a < b ? -1 : 1))) };
}

/** Counts by retry class, plus the shapes the acceptance names (used by check-pin and the gates). */
export function policyCounts(operations) {
  const counts = { operations: operations.length, keyed: 0, "keyed-not-durable": 0, "http-idempotent": 0, unsafe: 0 };
  for (const op of operations) counts[op.retry] += 1;
  return {
    ...counts,
    idempotent: operations.filter((o) => o.idempotent).length,
    durable_unstated: operations.filter((o) => o.idempotent && o.durable === null).length,
    streams: operations.filter((o) => o.stream).length,
    paginated: operations.filter((o) => o.pagination).length,
    not_found_means_applied: operations.filter((o) => o.not_found_means_applied).length
  };
}
