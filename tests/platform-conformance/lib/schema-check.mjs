/**
 * A small, zero-dependency structural JSON Schema checker.
 *
 * It checks what the conformance suite relies on: `$ref` (a JSON pointer into the root
 * document), `type` (including "integer" and "null" and type lists), `required`, `properties`,
 * `additionalProperties` (false or a schema), `enum`, `const`, `pattern`, `minLength`,
 * `maxLength`, `minimum`, `maximum`, `items`, `minItems`, `maxItems`, `allOf`, `anyOf` and
 * `oneOf` (exactly one branch). `format`, `description` and vendor keys are ignored. It is a
 * structural check, not a full JSON Schema implementation, and every receipt says so.
 */

const MAX_DEPTH = 64;

/** Resolve a local JSON pointer (`#/components/schemas/X`) against the root document. */
export function resolvePointer(root, ref) {
  if (typeof ref !== "string" || !ref.startsWith("#")) throw new Error(`only local $ref is supported: ${ref}`);
  let node = root;
  for (const raw of ref.slice(1).split("/").filter((part) => part !== "")) {
    const part = raw.replace(/~1/g, "/").replace(/~0/g, "~");
    if (node === null || typeof node !== "object" || !(part in node)) throw new Error(`unresolvable $ref ${ref}`);
    node = node[part];
  }
  return node;
}

export function jsonType(value) {
  if (value === null) return "null";
  if (Array.isArray(value)) return "array";
  if (typeof value === "number") return Number.isInteger(value) ? "integer" : "number";
  return typeof value;
}

function typeMatches(expected, value) {
  const actual = jsonType(value);
  if (expected === actual) return true;
  return expected === "number" && actual === "integer";
}

function check(schema, value, at, ctx, depth) {
  if (depth > MAX_DEPTH) return [`${at}: schema nesting deeper than ${MAX_DEPTH}`];
  if (schema === true || schema === undefined || schema === null) return [];
  if (schema === false) return [`${at}: no value is allowed here`];
  if (schema.$ref) return check(resolvePointer(ctx.root, schema.$ref), value, at, ctx, depth + 1);
  const errors = [];
  if (schema.type !== undefined) {
    const types = Array.isArray(schema.type) ? schema.type : [schema.type];
    if (!types.some((type) => typeMatches(type, value))) {
      return [`${at}: expected ${types.join("|")}, got ${jsonType(value)}`];
    }
  }
  if (schema.const !== undefined && JSON.stringify(schema.const) !== JSON.stringify(value)) {
    errors.push(`${at}: expected the constant ${JSON.stringify(schema.const)}`);
  }
  if (Array.isArray(schema.enum) && !schema.enum.some((item) => JSON.stringify(item) === JSON.stringify(value))) {
    errors.push(`${at}: ${JSON.stringify(value)} is not one of ${JSON.stringify(schema.enum)}`);
  }
  if (typeof value === "string") {
    if (schema.minLength !== undefined && [...value].length < schema.minLength) errors.push(`${at}: shorter than ${schema.minLength}`);
    if (schema.maxLength !== undefined && [...value].length > schema.maxLength) errors.push(`${at}: longer than ${schema.maxLength}`);
    if (schema.pattern !== undefined && !new RegExp(schema.pattern, "u").test(value)) errors.push(`${at}: does not match ${schema.pattern}`);
  }
  if (typeof value === "number") {
    if (schema.minimum !== undefined && value < schema.minimum) errors.push(`${at}: below ${schema.minimum}`);
    if (schema.maximum !== undefined && value > schema.maximum) errors.push(`${at}: above ${schema.maximum}`);
  }
  if (Array.isArray(value)) {
    if (schema.minItems !== undefined && value.length < schema.minItems) errors.push(`${at}: fewer than ${schema.minItems} items`);
    if (schema.maxItems !== undefined && value.length > schema.maxItems) errors.push(`${at}: more than ${schema.maxItems} items`);
    if (schema.items && typeof schema.items === "object") {
      value.forEach((item, index) => errors.push(...check(schema.items, item, `${at}[${index}]`, ctx, depth + 1)));
    }
  }
  if (value !== null && typeof value === "object" && !Array.isArray(value)) {
    for (const name of schema.required ?? []) {
      if (!(name in value)) errors.push(`${at}: missing required ${name}`);
    }
    const props = schema.properties ?? {};
    for (const [name, child] of Object.entries(value)) {
      if (name in props) errors.push(...check(props[name], child, `${at}.${name}`, ctx, depth + 1));
      else if (schema.additionalProperties === false) errors.push(`${at}: unknown property ${name}`);
      else if (schema.additionalProperties && typeof schema.additionalProperties === "object") {
        errors.push(...check(schema.additionalProperties, child, `${at}.${name}`, ctx, depth + 1));
      }
    }
  }
  for (const part of schema.allOf ?? []) errors.push(...check(part, value, at, ctx, depth + 1));
  if (Array.isArray(schema.anyOf) && !schema.anyOf.some((part) => check(part, value, at, ctx, depth + 1).length === 0)) {
    errors.push(`${at}: matches none of anyOf`);
  }
  if (Array.isArray(schema.oneOf)) {
    const matched = schema.oneOf.filter((part) => check(part, value, at, ctx, depth + 1).length === 0).length;
    if (matched !== 1) errors.push(`${at}: matches ${matched} branches of oneOf, not exactly one`);
  }
  return errors;
}

/** Check `value` against `schema`; `root` is the document `$ref`s resolve in. Returns error strings. */
export function checkSchema(schema, value, { root = schema, at = "$" } = {}) {
  return check(schema, value, at, { root }, 0);
}
