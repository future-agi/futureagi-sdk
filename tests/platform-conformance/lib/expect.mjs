/**
 * Check one observed outcome against a case's expectation. Pure; every runner uses it.
 *
 * outcome: { status, code, errorClass, body, events: [{type,...}], headers: {name: value} }
 * expect:  { status, code, codePresent, errorClass, fields, events, retryAfter, noLeak }
 *   fields: { "<dotted.path>": "string"|"integer"|"number"|"boolean"|"array"|"object"|"null"
 *             | { equals: v } | { present: false } | { oneOf: [..] } | { minItems: n } }
 *   events: { include: [types], exclude: [types], last: type, minCount: n, exitCode: n, afterSeq: n }
 *   noLeak: strings that must not appear anywhere in the body or headers (planted secrets).
 */
import { jsonType } from "./schema-check.mjs";

const asList = (value) => (Array.isArray(value) ? value : [value]);

export function get(obj, dotted) {
  let node = obj;
  for (const part of dotted.split(".")) {
    if (node === null || typeof node !== "object") return { found: false };
    if (Array.isArray(node) && /^\d+$/.test(part)) {
      if (Number(part) >= node.length) return { found: false };
      node = node[Number(part)];
      continue;
    }
    if (!(part in node)) return { found: false };
    node = node[part];
  }
  return { found: true, value: node };
}

function checkField(body, dotted, rule) {
  const { found, value } = get(body, dotted);
  if (typeof rule === "string") {
    if (!found) return `${dotted}: missing (expected ${rule})`;
    const type = jsonType(value);
    return type === rule || (rule === "number" && type === "integer") ? null : `${dotted}: ${type}, expected ${rule}`;
  }
  if (rule && typeof rule === "object") {
    if ("present" in rule) return found === rule.present ? null : `${dotted}: present=${found}, expected ${rule.present}`;
    if (!found) return `${dotted}: missing`;
    if ("equals" in rule && JSON.stringify(value) !== JSON.stringify(rule.equals)) return `${dotted}: ${JSON.stringify(value)} != ${JSON.stringify(rule.equals)}`;
    if ("oneOf" in rule && !rule.oneOf.some((v) => JSON.stringify(v) === JSON.stringify(value))) return `${dotted}: ${JSON.stringify(value)} not in ${JSON.stringify(rule.oneOf)}`;
    if ("minItems" in rule && !(Array.isArray(value) && value.length >= rule.minItems)) return `${dotted}: fewer than ${rule.minItems} items`;
    return null;
  }
  return `${dotted}: unknown rule`;
}

function checkEvents(events = [], rule) {
  const failures = [];
  const types = events.map((e) => e.type);
  for (const type of rule.include ?? []) if (!types.includes(type)) failures.push(`events: no ${type} (saw ${[...new Set(types)].join(",") || "none"})`);
  for (const type of rule.exclude ?? []) if (types.includes(type)) failures.push(`events: unexpected ${type}`);
  if (rule.last && types.at(-1) !== rule.last) failures.push(`events: last is ${types.at(-1) ?? "none"}, expected ${rule.last}`);
  if (rule.minCount && events.length < rule.minCount) failures.push(`events: ${events.length} < ${rule.minCount}`);
  if (rule.exitCode !== undefined) {
    const exit = [...events].reverse().find((e) => e.type === "exit");
    if (!exit) failures.push("events: no exit event");
    else if (exit.data?.exitCode !== rule.exitCode) failures.push(`events: exitCode ${exit.data?.exitCode}, expected ${rule.exitCode}`);
  }
  if (rule.afterSeq !== undefined) {
    const early = events.filter((e) => typeof e.data?.seq === "number" && e.data.seq <= rule.afterSeq);
    if (early.length) failures.push(`events: ${early.length} event(s) at or before seq ${rule.afterSeq} after a resume`);
  }
  return failures;
}

/** Returns { pass, failures[] }. */
export function checkOutcome(expect, outcome) {
  const failures = [];
  if (expect.status !== undefined && !asList(expect.status).includes(outcome.status)) {
    failures.push(`status ${outcome.status}, expected ${asList(expect.status).join("|")}${outcome.code ? ` (code ${outcome.code})` : ""}`);
  }
  if (expect.code !== undefined && !asList(expect.code).includes(outcome.code)) failures.push(`code ${outcome.code}, expected ${asList(expect.code).join("|")}`);
  if (expect.codePresent && (!outcome.code || /^http_\d+$/.test(outcome.code))) failures.push(`no typed error code (got ${outcome.code ?? "none"})`);
  if (expect.errorClass !== undefined && !asList(expect.errorClass).includes(outcome.errorClass)) failures.push(`errorClass ${outcome.errorClass}, expected ${asList(expect.errorClass).join("|")}`);
  if (expect.retryAfter && !(outcome.retryAfterSeconds > 0)) failures.push("no Retry-After");
  for (const [dotted, rule] of Object.entries(expect.fields ?? {})) {
    const failure = checkField(outcome.body, dotted, rule);
    if (failure) failures.push(failure);
  }
  if (expect.events) failures.push(...checkEvents(outcome.events, expect.events));
  for (const secret of expect.noLeak ?? []) {
    const haystack = `${JSON.stringify(outcome.body ?? null)}\n${JSON.stringify(outcome.headers ?? {})}\n${JSON.stringify(outcome.events ?? [])}`;
    if (secret && haystack.includes(secret)) failures.push("a planted secret appears in the response");
  }
  return { pass: failures.length === 0, failures };
}
