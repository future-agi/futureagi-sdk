/**
 * The runtime shape of a policy entry in each language: the fields of the platform core's
 * `OperationSpec`, `StreamSpec` and `PaginationSpec` (`python/fi/_core/policy.py`,
 * `typescript/futureagi/src/_core/policy.ts`), and the contract facts those specs do not carry, which
 * the emitter writes to a separate extras table so that nothing the contract states is dropped.
 *
 * Python writes every field, in the dataclass's order, so a changed default in the core cannot change
 * the table without a regenerate-and-diff showing it. TypeScript leaves out a field that has no value,
 * because its optional fields take `undefined`, never `null`. `durable` is false only where the contract
 * says `durable: false`; an idempotent operation that does not state it counts as durable (keyed), and its
 * extras say `durable_unstated`, so the table still tells a stated durability from an assumed one.
 */

/** `OperationSpec` fields, in the order `python/fi/_core/policy.py` declares them. */
export const OPERATION_FIELDS = [
  "name",
  "family",
  "method",
  "path",
  "path_params",
  "query",
  "body",
  "timeout",
  "rate",
  "role",
  "headers",
  "content_type",
  "idempotent",
  "durable",
  "idempotency_key_required",
  "not_found_means_applied",
  "human_only",
  "multi_segment",
  "stream",
  "pagination",
  "secret_fields",
  "operation_id"
];

/** `StreamSpec` fields, in declaration order. */
export const STREAM_FIELDS = [
  "kind",
  "resume",
  "events",
  "known_events",
  "keepalive_seconds",
  "cancel_on_disconnect",
  "poll_param",
  "poll_value",
  "poll_wait_param",
  "poll_max_wait_ms"
];

/** `PaginationSpec` fields, in declaration order. */
export const PAGINATION_FIELDS = ["style", "items_field", "cursor_param", "limit_param", "next_cursor_field", "has_more_field", "truncated_field"];

/** Operation fields the TypeScript `OperationSpec` does not declare (they go to its extras table). */
export const TS_ONLY_EXTRAS = ["timeout", "rate", "role"];

function pick(source, fields) {
  return Object.fromEntries(fields.map((f) => [f, source[f] === undefined ? null : source[f]]));
}

/** One model entry (`policy-model.mjs`) as the core's `OperationSpec`, snake_case, every field set. */
export function runtimeEntry(entry) {
  const shaped = {
    ...entry,
    durable: entry.durable !== false,
    idempotency_key_required: entry.key_required === true,
    human_only: entry.human_only === true,
    stream: entry.stream ? pick(entry.stream, STREAM_FIELDS) : null,
    pagination: entry.pagination ? pick(entry.pagination, PAGINATION_FIELDS) : null
  };
  return pick(shaped, OPERATION_FIELDS);
}

/** The contract facts of one entry that the core's specs do not carry; only the ones it has. */
export function extrasEntry(entry) {
  const out = {};
  if (entry.replay_omits.length > 0) out.replay_omits = entry.replay_omits;
  if (entry.stream?.resume_when) out.resume_when = entry.stream.resume_when;
  if (entry.pagination?.opaque_cursor === true) out.opaque_cursor = true;
  if (entry.stop === true) out.stop = true;
  if (entry.idempotent && entry.durable === null) out.durable_unstated = true;
  return out;
}

function camel(key) {
  return key.replace(/_([a-z])/gu, (_, c) => c.toUpperCase());
}

/** A snake_case runtime value as TypeScript data: camelCase keys, `null` fields left out. */
export function tsValue(value) {
  if (Array.isArray(value)) return value.map(tsValue);
  if (value === null || typeof value !== "object") return value;
  return Object.fromEntries(
    Object.entries(value)
      .filter(([, v]) => v !== null && v !== undefined)
      .map(([k, v]) => [camel(k), tsValue(v)])
  );
}

/** The TypeScript `OperationSpec` of one model entry. */
export function tsEntry(entry) {
  const runtime = runtimeEntry(entry);
  for (const field of TS_ONLY_EXTRAS) delete runtime[field];
  return tsValue(runtime);
}

/** The TypeScript extras of one model entry: the shared extras plus the fields its spec lacks. */
export function tsExtrasEntry(entry) {
  const own = Object.fromEntries(TS_ONLY_EXTRAS.map((f) => [f, entry[f] ?? null]));
  return tsValue({ ...own, ...extrasEntry(entry) });
}
