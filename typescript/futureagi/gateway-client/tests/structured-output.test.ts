import { describe, it, expect } from "@jest/globals";
import { zodToJsonSchema, isZodSchema } from "../src/structured-output.js";

// ---------------------------------------------------------------------------
// Minimal Zod-like mocks (duck-typed to match real Zod _def structure)
// We don't import zod as a dependency — these mocks prove the converter works
// ---------------------------------------------------------------------------

function zodString(opts?: { description?: string; checks?: unknown[] }) {
  return {
    _def: { typeName: "ZodString", description: opts?.description, checks: opts?.checks ?? [] },
    parse: (v: unknown) => v,
  };
}

function zodNumber(opts?: { description?: string; checks?: unknown[] }) {
  return {
    _def: { typeName: "ZodNumber", description: opts?.description, checks: opts?.checks ?? [] },
    parse: (v: unknown) => v,
  };
}

function zodBoolean() {
  return { _def: { typeName: "ZodBoolean" }, parse: (v: unknown) => v };
}

function zodNull() {
  return { _def: { typeName: "ZodNull" }, parse: (v: unknown) => v };
}

function zodLiteral(value: unknown) {
  return { _def: { typeName: "ZodLiteral", value }, parse: (v: unknown) => v };
}

function zodEnum(values: string[]) {
  return { _def: { typeName: "ZodEnum", values }, parse: (v: unknown) => v };
}

function zodArray(itemType: unknown) {
  return { _def: { typeName: "ZodArray", type: itemType }, parse: (v: unknown) => v };
}

function zodObject(shape: Record<string, unknown>, description?: string) {
  return {
    _def: {
      typeName: "ZodObject",
      shape: () => shape,
      description,
    },
    parse: (v: unknown) => v,
  };
}

function zodOptional(innerType: unknown) {
  return { _def: { typeName: "ZodOptional", innerType }, parse: (v: unknown) => v };
}

function zodNullable(innerType: unknown) {
  return { _def: { typeName: "ZodNullable", innerType }, parse: (v: unknown) => v };
}

function zodDefault(innerType: unknown, defaultValue: unknown) {
  return {
    _def: { typeName: "ZodDefault", innerType, defaultValue: () => defaultValue },
    parse: (v: unknown) => v,
  };
}

function zodUnion(options: unknown[]) {
  return { _def: { typeName: "ZodUnion", options }, parse: (v: unknown) => v };
}

function zodRecord(valueType: unknown) {
  return { _def: { typeName: "ZodRecord", valueType }, parse: (v: unknown) => v };
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe("isZodSchema", () => {
  it("returns true for Zod-like objects", () => {
    expect(isZodSchema(zodString())).toBe(true);
    expect(isZodSchema(zodObject({}))).toBe(true);
  });

  it("returns false for non-Zod values", () => {
    expect(isZodSchema(null)).toBe(false);
    expect(isZodSchema(42)).toBe(false);
    expect(isZodSchema("string")).toBe(false);
    expect(isZodSchema({ type: "object" })).toBe(false);
    expect(isZodSchema({ _def: {} })).toBe(false); // no parse()
  });
});

describe("zodToJsonSchema", () => {
  it("converts ZodString", () => {
    const result = zodToJsonSchema(zodString());
    expect(result).toEqual({ type: "string" });
  });

  it("converts ZodString with description", () => {
    const result = zodToJsonSchema(zodString({ description: "A name" }));
    expect(result).toEqual({ type: "string", description: "A name" });
  });

  it("converts ZodString with constraints", () => {
    const result = zodToJsonSchema(
      zodString({ checks: [{ kind: "min", value: 1 }, { kind: "max", value: 100 }, { kind: "email" }] }),
    );
    expect(result.minLength).toBe(1);
    expect(result.maxLength).toBe(100);
    expect(result.format).toBe("email");
  });

  it("converts ZodNumber", () => {
    const result = zodToJsonSchema(zodNumber());
    expect(result).toEqual({ type: "number" });
  });

  it("converts ZodNumber with int check", () => {
    const result = zodToJsonSchema(zodNumber({ checks: [{ kind: "int" }] }));
    expect(result.type).toBe("integer");
  });

  it("converts ZodBoolean", () => {
    expect(zodToJsonSchema(zodBoolean())).toEqual({ type: "boolean" });
  });

  it("converts ZodNull", () => {
    expect(zodToJsonSchema(zodNull())).toEqual({ type: "null" });
  });

  it("converts ZodLiteral", () => {
    expect(zodToJsonSchema(zodLiteral("hello"))).toEqual({ const: "hello" });
  });

  it("converts ZodEnum", () => {
    const result = zodToJsonSchema(zodEnum(["a", "b", "c"]));
    expect(result).toEqual({ type: "string", enum: ["a", "b", "c"] });
  });

  it("converts ZodArray", () => {
    const result = zodToJsonSchema(zodArray(zodString()));
    expect(result).toEqual({ type: "array", items: { type: "string" } });
  });

  it("converts ZodObject", () => {
    const result = zodToJsonSchema(
      zodObject({
        name: zodString({ description: "User name" }),
        age: zodNumber(),
      }),
    );
    expect(result.type).toBe("object");
    expect(result.properties).toEqual({
      name: { type: "string", description: "User name" },
      age: { type: "number" },
    });
    expect(result.required).toEqual(["name", "age"]);
    expect(result.additionalProperties).toBe(false);
  });

  it("handles ZodOptional in object — not required", () => {
    const result = zodToJsonSchema(
      zodObject({
        name: zodString(),
        nickname: zodOptional(zodString()),
      }),
    );
    expect(result.required).toEqual(["name"]);
    expect((result.properties as Record<string, unknown>).nickname).toEqual({ type: "string" });
  });

  it("converts ZodNullable", () => {
    const result = zodToJsonSchema(zodNullable(zodString()));
    expect(result.anyOf).toEqual([{ type: "string" }, { type: "null" }]);
  });

  it("converts ZodDefault", () => {
    const result = zodToJsonSchema(zodDefault(zodNumber(), 42));
    expect(result.type).toBe("number");
    expect(result.default).toBe(42);
  });

  it("converts ZodUnion", () => {
    const result = zodToJsonSchema(zodUnion([zodString(), zodNumber()]));
    expect(result.anyOf).toEqual([{ type: "string" }, { type: "number" }]);
  });

  it("converts ZodRecord", () => {
    const result = zodToJsonSchema(zodRecord(zodNumber()));
    expect(result.type).toBe("object");
    expect(result.additionalProperties).toEqual({ type: "number" });
  });

  it("converts nested objects", () => {
    const result = zodToJsonSchema(
      zodObject({
        user: zodObject({
          name: zodString(),
          tags: zodArray(zodString()),
        }),
      }),
    );
    const userProp = (result.properties as Record<string, Record<string, unknown>>).user;
    expect(userProp.type).toBe("object");
    expect(
      (userProp.properties as Record<string, Record<string, unknown>>).tags,
    ).toEqual({ type: "array", items: { type: "string" } });
  });

  it("throws for non-Zod input", () => {
    expect(() => zodToJsonSchema({ type: "string" })).toThrow("Expected a Zod schema");
  });
});
