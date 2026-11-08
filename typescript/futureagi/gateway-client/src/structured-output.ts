// ---------------------------------------------------------------------------
// Structured Output — Zod → JSON Schema conversion + createParsed support
// ---------------------------------------------------------------------------

import { AgentCCError } from "./errors.js";

// ---------------------------------------------------------------------------
// Zod detection (duck-typing — no import of zod)
// ---------------------------------------------------------------------------

export function isZodSchema(value: unknown): boolean {
  return (
    value !== null &&
    typeof value === "object" &&
    "_def" in (value as Record<string, unknown>) &&
    typeof (value as Record<string, unknown>).parse === "function"
  );
}

// ---------------------------------------------------------------------------
// zodToJsonSchema — converts Zod schema → JSON Schema
// ---------------------------------------------------------------------------

export function zodToJsonSchema(
  schema: unknown,
): Record<string, unknown> {
  if (!isZodSchema(schema)) {
    throw new AgentCCError("Expected a Zod schema");
  }
  return convertZodNode(schema as ZodLike);
}

// Internal Zod-like shape (duck-typed)
interface ZodLike {
  _def: {
    typeName?: string;
    description?: string;
    innerType?: ZodLike;
    type?: ZodLike;
    shape?: () => Record<string, ZodLike>;
    values?: string[];
    value?: unknown;
    options?: ZodLike[];
    items?: ZodLike[];
    valueType?: ZodLike;
    defaultValue?: () => unknown;
    checks?: Array<{ kind: string; value?: unknown; message?: string }>;
    enum?: Record<string, string | number>;
    [key: string]: unknown;
  };
}

function convertZodNode(node: ZodLike): Record<string, unknown> {
  const def = node._def;
  const typeName = def.typeName as string | undefined;
  const result: Record<string, unknown> = {};

  if (def.description) {
    result.description = def.description;
  }

  switch (typeName) {
    case "ZodString": {
      result.type = "string";
      addStringConstraints(result, def.checks);
      break;
    }
    case "ZodNumber": {
      result.type = "number";
      addNumberConstraints(result, def.checks);
      break;
    }
    case "ZodBoolean":
      result.type = "boolean";
      break;
    case "ZodNull":
      result.type = "null";
      break;
    case "ZodLiteral":
      result.const = def.value;
      break;
    case "ZodEnum":
      result.type = "string";
      result.enum = def.values;
      break;
    case "ZodNativeEnum":
      result.type = "string";
      result.enum = Object.values(def.enum ?? {});
      break;
    case "ZodArray":
      result.type = "array";
      if (def.type) {
        result.items = convertZodNode(def.type);
      }
      break;
    case "ZodObject": {
      result.type = "object";
      const shape = def.shape?.() ?? {};
      const properties: Record<string, unknown> = {};
      const required: string[] = [];
      for (const [key, value] of Object.entries(shape)) {
        properties[key] = convertZodNode(value);
        // Check if field is optional
        const innerTypeName = (value as ZodLike)._def?.typeName;
        if (innerTypeName !== "ZodOptional" && innerTypeName !== "ZodDefault") {
          required.push(key);
        }
      }
      result.properties = properties;
      if (required.length > 0) {
        result.required = required;
      }
      result.additionalProperties = false;
      break;
    }
    case "ZodOptional":
      if (def.innerType) {
        return convertZodNode(def.innerType);
      }
      break;
    case "ZodNullable": {
      if (def.innerType) {
        const inner = convertZodNode(def.innerType);
        result.anyOf = [inner, { type: "null" }];
      }
      break;
    }
    case "ZodDefault": {
      if (def.innerType) {
        const inner = convertZodNode(def.innerType);
        Object.assign(result, inner);
        try {
          result.default = def.defaultValue?.();
        } catch {
          // ignore if defaultValue() fails
        }
      }
      break;
    }
    case "ZodUnion":
    case "ZodDiscriminatedUnion": {
      const options = def.options as ZodLike[] | undefined;
      if (options) {
        result.anyOf = options.map((o) => convertZodNode(o));
      }
      break;
    }
    case "ZodRecord": {
      result.type = "object";
      if (def.valueType) {
        result.additionalProperties = convertZodNode(def.valueType);
      }
      break;
    }
    case "ZodTuple": {
      result.type = "array";
      if (def.items) {
        result.prefixItems = (def.items as ZodLike[]).map((i) =>
          convertZodNode(i),
        );
        result.items = false;
      }
      break;
    }
    case "ZodAny":
    case "ZodUnknown":
      // No constraints
      break;
    default:
      // Fallback: try to recurse into innerType
      if (def.innerType) {
        return convertZodNode(def.innerType);
      }
      break;
  }

  return result;
}

// ---------------------------------------------------------------------------
// Constraint helpers
// ---------------------------------------------------------------------------

function addStringConstraints(
  result: Record<string, unknown>,
  checks?: Array<{ kind: string; value?: unknown }>,
): void {
  if (!checks) return;
  for (const check of checks) {
    if (check.kind === "min" && typeof check.value === "number") {
      result.minLength = check.value;
    }
    if (check.kind === "max" && typeof check.value === "number") {
      result.maxLength = check.value;
    }
    if (check.kind === "regex" && check.value instanceof RegExp) {
      result.pattern = (check.value as RegExp).source;
    }
    if (check.kind === "email") {
      result.format = "email";
    }
    if (check.kind === "url") {
      result.format = "uri";
    }
    if (check.kind === "uuid") {
      result.format = "uuid";
    }
  }
}

function addNumberConstraints(
  result: Record<string, unknown>,
  checks?: Array<{ kind: string; value?: unknown; inclusive?: boolean }>,
): void {
  if (!checks) return;
  for (const check of checks) {
    if (check.kind === "min" && typeof check.value === "number") {
      if (check.inclusive === false) result.exclusiveMinimum = check.value;
      else result.minimum = check.value;
    }
    if (check.kind === "max" && typeof check.value === "number") {
      if (check.inclusive === false) result.exclusiveMaximum = check.value;
      else result.maximum = check.value;
    }
    if (check.kind === "int") {
      result.type = "integer";
    }
    if (check.kind === "multipleOf" && typeof check.value === "number") {
      result.multipleOf = check.value;
    }
  }
}
