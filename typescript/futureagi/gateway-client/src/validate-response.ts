// ---------------------------------------------------------------------------
// Structured Output Validation — validateJsonResponse + toResponseFormat
// ---------------------------------------------------------------------------

import { AgentCCError } from "./errors.js";
import { isZodSchema, zodToJsonSchema } from "./structured-output.js";
import type { ResponseFormat } from "./types/chat/completion-create-params.js";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface ValidationResult {
  valid: boolean;
  errors: string[];
}

// ---------------------------------------------------------------------------
// validateJsonResponse
// ---------------------------------------------------------------------------

/**
 * Validate a completion's text output against a JSON Schema.
 * Lightweight validator covering type, required, enum, const,
 * min/max, pattern, minLength/maxLength, items, properties.
 */
export function validateJsonResponse(
  text: string,
  schema: Record<string, unknown>,
): ValidationResult {
  const errors: string[] = [];

  let parsed: unknown;
  try {
    parsed = JSON.parse(text);
  } catch {
    return { valid: false, errors: ["Response is not valid JSON"] };
  }

  validateNode(parsed, schema, "", errors);
  return { valid: errors.length === 0, errors };
}

function validateNode(
  value: unknown,
  schema: Record<string, unknown>,
  path: string,
  errors: string[],
): void {
  // const
  if ("const" in schema) {
    if (value !== schema.const) {
      errors.push(`${path || "/"}: expected const ${JSON.stringify(schema.const)}, got ${JSON.stringify(value)}`);
    }
    return;
  }

  // enum
  if ("enum" in schema && Array.isArray(schema.enum)) {
    if (!schema.enum.includes(value)) {
      errors.push(`${path || "/"}: value ${JSON.stringify(value)} not in enum [${schema.enum.join(", ")}]`);
    }
    return;
  }

  // anyOf / oneOf — check if at least one sub-schema passes
  if ("anyOf" in schema && Array.isArray(schema.anyOf)) {
    const subErrors: string[][] = [];
    for (const sub of schema.anyOf as Record<string, unknown>[]) {
      const subErr: string[] = [];
      validateNode(value, sub, path, subErr);
      if (subErr.length === 0) return; // passes at least one
      subErrors.push(subErr);
    }
    errors.push(`${path || "/"}: does not match any of the anyOf schemas`);
    return;
  }

  if ("oneOf" in schema && Array.isArray(schema.oneOf)) {
    let matches = 0;
    for (const sub of schema.oneOf as Record<string, unknown>[]) {
      const subErr: string[] = [];
      validateNode(value, sub, path, subErr);
      if (subErr.length === 0) matches++;
    }
    if (matches !== 1) {
      errors.push(`${path || "/"}: expected exactly one oneOf match, got ${matches}`);
    }
    return;
  }

  // type check
  const schemaType = schema.type as string | undefined;
  if (schemaType) {
    if (!checkType(value, schemaType)) {
      errors.push(`${path || "/"}: expected type "${schemaType}", got ${typeof value}${value === null ? " (null)" : ""}`);
      return;
    }
  }

  // object properties
  if (schemaType === "object" || (!schemaType && schema.properties)) {
    if (typeof value !== "object" || value === null || Array.isArray(value)) {
      if (!schemaType) return; // no type constraint, skip
      return;
    }
    const obj = value as Record<string, unknown>;

    // required
    if (Array.isArray(schema.required)) {
      for (const req of schema.required as string[]) {
        if (!(req in obj)) {
          errors.push(`${path || "/"}:  missing required property "${req}"`);
        }
      }
    }

    // properties
    if (schema.properties && typeof schema.properties === "object") {
      const props = schema.properties as Record<string, Record<string, unknown>>;
      for (const [key, propSchema] of Object.entries(props)) {
        if (key in obj) {
          validateNode(obj[key], propSchema, `${path}/${key}`, errors);
        }
      }
    }

    // additionalProperties
    if (schema.additionalProperties === false) {
      const allowed = new Set(
        schema.properties ? Object.keys(schema.properties as object) : [],
      );
      for (const key of Object.keys(obj)) {
        if (!allowed.has(key)) {
          errors.push(`${path || "/"}:  unexpected property "${key}"`);
        }
      }
    }
  }

  // array items
  if (schemaType === "array" && Array.isArray(value)) {
    if (schema.items && typeof schema.items === "object") {
      const itemSchema = schema.items as Record<string, unknown>;
      for (let i = 0; i < value.length; i++) {
        validateNode(value[i], itemSchema, `${path}/${i}`, errors);
      }
    }
    if (typeof schema.minItems === "number" && value.length < schema.minItems) {
      errors.push(`${path || "/"}: array length ${value.length} < minItems ${schema.minItems}`);
    }
    if (typeof schema.maxItems === "number" && value.length > schema.maxItems) {
      errors.push(`${path || "/"}: array length ${value.length} > maxItems ${schema.maxItems}`);
    }
  }

  // string constraints
  if (schemaType === "string" && typeof value === "string") {
    if (typeof schema.minLength === "number" && value.length < schema.minLength) {
      errors.push(`${path || "/"}: string length ${value.length} < minLength ${schema.minLength}`);
    }
    if (typeof schema.maxLength === "number" && value.length > schema.maxLength) {
      errors.push(`${path || "/"}: string length ${value.length} > maxLength ${schema.maxLength}`);
    }
    if (typeof schema.pattern === "string") {
      const re = new RegExp(schema.pattern);
      if (!re.test(value)) {
        errors.push(`${path || "/"}: string does not match pattern "${schema.pattern}"`);
      }
    }
  }

  // number constraints
  if ((schemaType === "number" || schemaType === "integer") && typeof value === "number") {
    if (typeof schema.minimum === "number" && value < schema.minimum) {
      errors.push(`${path || "/"}: ${value} < minimum ${schema.minimum}`);
    }
    if (typeof schema.maximum === "number" && value > schema.maximum) {
      errors.push(`${path || "/"}: ${value} > maximum ${schema.maximum}`);
    }
    if (typeof schema.exclusiveMinimum === "number" && value <= schema.exclusiveMinimum) {
      errors.push(`${path || "/"}: ${value} <= exclusiveMinimum ${schema.exclusiveMinimum}`);
    }
    if (typeof schema.exclusiveMaximum === "number" && value >= schema.exclusiveMaximum) {
      errors.push(`${path || "/"}: ${value} >= exclusiveMaximum ${schema.exclusiveMaximum}`);
    }
  }
}

function checkType(value: unknown, type: string): boolean {
  switch (type) {
    case "string":
      return typeof value === "string";
    case "number":
      return typeof value === "number";
    case "integer":
      return typeof value === "number" && Number.isInteger(value);
    case "boolean":
      return typeof value === "boolean";
    case "null":
      return value === null;
    case "array":
      return Array.isArray(value);
    case "object":
      return typeof value === "object" && value !== null && !Array.isArray(value);
    default:
      return true;
  }
}

// ---------------------------------------------------------------------------
// toResponseFormat
// ---------------------------------------------------------------------------

/**
 * Convert a Zod schema or JSON Schema into an OpenAI `response_format`
 * parameter suitable for structured output.
 *
 * @example
 * ```typescript
 * import { z } from "zod";
 * const schema = z.object({ temp: z.number(), city: z.string() });
 * const rf = toResponseFormat(schema, "weather");
 * // { type: "json_schema", json_schema: { name: "weather", strict: true, schema: {...} } }
 * ```
 */
export function toResponseFormat(
  schema: unknown,
  name?: string,
): ResponseFormat {
  let jsonSchema: Record<string, unknown>;

  if (isZodSchema(schema)) {
    jsonSchema = zodToJsonSchema(schema);
  } else if (schema && typeof schema === "object" && !Array.isArray(schema)) {
    jsonSchema = schema as Record<string, unknown>;
  } else {
    throw new AgentCCError(
      "toResponseFormat: expected a Zod schema or JSON Schema object",
    );
  }

  return {
    type: "json_schema",
    json_schema: {
      name: name ?? "response",
      strict: true,
      schema: jsonSchema,
    },
  } as ResponseFormat;
}
