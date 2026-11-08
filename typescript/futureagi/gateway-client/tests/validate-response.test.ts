import { describe, it, expect } from "@jest/globals";
import { validateJsonResponse, toResponseFormat } from "../src/validate-response.js";
import { isZodSchema, zodToJsonSchema } from "../src/structured-output.js";

// ---------------------------------------------------------------------------
// validateJsonResponse
// ---------------------------------------------------------------------------

describe("validateJsonResponse", () => {
  it("valid object with correct types", () => {
    const schema = {
      type: "object",
      properties: {
        name: { type: "string" },
        age: { type: "number" },
      },
      required: ["name", "age"],
    };
    const result = validateJsonResponse('{"name":"Alice","age":30}', schema);
    expect(result.valid).toBe(true);
    expect(result.errors).toHaveLength(0);
  });

  it("rejects invalid JSON", () => {
    const result = validateJsonResponse("not json", { type: "object" });
    expect(result.valid).toBe(false);
    expect(result.errors[0]).toContain("not valid JSON");
  });

  it("detects type mismatch", () => {
    const schema = { type: "object", properties: { age: { type: "number" } } };
    const result = validateJsonResponse('{"age":"thirty"}', schema);
    expect(result.valid).toBe(false);
    expect(result.errors[0]).toContain('expected type "number"');
  });

  it("detects missing required property", () => {
    const schema = {
      type: "object",
      properties: { name: { type: "string" } },
      required: ["name", "email"],
    };
    const result = validateJsonResponse('{"name":"Alice"}', schema);
    expect(result.valid).toBe(false);
    expect(result.errors[0]).toContain('missing required property "email"');
  });

  it("validates string constraints", () => {
    const schema = {
      type: "object",
      properties: { code: { type: "string", minLength: 3, maxLength: 5 } },
    };
    const short = validateJsonResponse('{"code":"AB"}', schema);
    expect(short.valid).toBe(false);
    expect(short.errors[0]).toContain("minLength");

    const long = validateJsonResponse('{"code":"ABCDEF"}', schema);
    expect(long.valid).toBe(false);
    expect(long.errors[0]).toContain("maxLength");

    const ok = validateJsonResponse('{"code":"ABCD"}', schema);
    expect(ok.valid).toBe(true);
  });

  it("validates number constraints", () => {
    const schema = {
      type: "object",
      properties: { score: { type: "number", minimum: 0, maximum: 100 } },
    };
    const low = validateJsonResponse('{"score":-1}', schema);
    expect(low.valid).toBe(false);

    const high = validateJsonResponse('{"score":101}', schema);
    expect(high.valid).toBe(false);

    const ok = validateJsonResponse('{"score":50}', schema);
    expect(ok.valid).toBe(true);
  });

  it("validates integer type", () => {
    const schema = { type: "integer" };
    expect(validateJsonResponse("3", schema).valid).toBe(true);
    expect(validateJsonResponse("3.5", schema).valid).toBe(false);
  });

  it("validates enum", () => {
    const schema = { type: "string", enum: ["red", "green", "blue"] };
    expect(validateJsonResponse('"red"', schema).valid).toBe(true);
    expect(validateJsonResponse('"yellow"', schema).valid).toBe(false);
  });

  it("validates const", () => {
    const schema = { const: "fixed" };
    expect(validateJsonResponse('"fixed"', schema).valid).toBe(true);
    expect(validateJsonResponse('"other"', schema).valid).toBe(false);
  });

  it("validates array items", () => {
    const schema = {
      type: "array",
      items: { type: "number" },
    };
    expect(validateJsonResponse("[1, 2, 3]", schema).valid).toBe(true);
    expect(validateJsonResponse('[1, "two", 3]', schema).valid).toBe(false);
  });

  it("validates array length constraints", () => {
    const schema = { type: "array", items: { type: "number" }, minItems: 2, maxItems: 4 };
    expect(validateJsonResponse("[1]", schema).valid).toBe(false);
    expect(validateJsonResponse("[1,2,3,4,5]", schema).valid).toBe(false);
    expect(validateJsonResponse("[1,2,3]", schema).valid).toBe(true);
  });

  it("validates pattern", () => {
    const schema = { type: "string", pattern: "^\\d{3}-\\d{4}$" };
    expect(validateJsonResponse('"123-4567"', schema).valid).toBe(true);
    expect(validateJsonResponse('"abc-defg"', schema).valid).toBe(false);
  });

  it("validates nested objects", () => {
    const schema = {
      type: "object",
      properties: {
        address: {
          type: "object",
          properties: { city: { type: "string" }, zip: { type: "string" } },
          required: ["city"],
        },
      },
    };
    const result = validateJsonResponse('{"address":{"zip":"12345"}}', schema);
    expect(result.valid).toBe(false);
    expect(result.errors[0]).toContain("city");
  });

  it("validates anyOf", () => {
    const schema = {
      anyOf: [{ type: "string" }, { type: "number" }],
    };
    expect(validateJsonResponse('"hello"', schema).valid).toBe(true);
    expect(validateJsonResponse("42", schema).valid).toBe(true);
    expect(validateJsonResponse("true", schema).valid).toBe(false);
  });

  it("validates null type", () => {
    const schema = { type: "null" };
    expect(validateJsonResponse("null", schema).valid).toBe(true);
    expect(validateJsonResponse('"hello"', schema).valid).toBe(false);
  });

  it("validates boolean type", () => {
    const schema = { type: "boolean" };
    expect(validateJsonResponse("true", schema).valid).toBe(true);
    expect(validateJsonResponse("1", schema).valid).toBe(false);
  });

  it("validates additionalProperties: false", () => {
    const schema = {
      type: "object",
      properties: { name: { type: "string" } },
      additionalProperties: false,
    };
    const result = validateJsonResponse('{"name":"Alice","extra":true}', schema);
    expect(result.valid).toBe(false);
    expect(result.errors[0]).toContain("unexpected property");
  });

  it("validates exclusiveMinimum/exclusiveMaximum", () => {
    const schema = { type: "number", exclusiveMinimum: 0, exclusiveMaximum: 10 };
    expect(validateJsonResponse("0", schema).valid).toBe(false);
    expect(validateJsonResponse("10", schema).valid).toBe(false);
    expect(validateJsonResponse("5", schema).valid).toBe(true);
  });
});

// ---------------------------------------------------------------------------
// toResponseFormat
// ---------------------------------------------------------------------------

describe("toResponseFormat", () => {
  it("wraps a JSON Schema object", () => {
    const schema = { type: "object", properties: { name: { type: "string" } } };
    const rf = toResponseFormat(schema, "user");

    expect(rf).toEqual({
      type: "json_schema",
      json_schema: {
        name: "user",
        strict: true,
        schema,
      },
    });
  });

  it("defaults name to 'response'", () => {
    const schema = { type: "object" };
    const rf = toResponseFormat(schema);

    expect((rf as any).json_schema.name).toBe("response");
  });

  it("throws for invalid input", () => {
    expect(() => toResponseFormat("not a schema")).toThrow("expected a Zod schema or JSON Schema");
    expect(() => toResponseFormat(null)).toThrow();
    expect(() => toResponseFormat(42)).toThrow();
  });
});
