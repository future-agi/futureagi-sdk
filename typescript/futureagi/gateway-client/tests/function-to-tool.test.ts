import { describe, it, expect } from "@jest/globals";
import { functionToTool } from "../src/function-to-tool.js";

// Minimal Zod mock
function zodObject(shape: Record<string, unknown>, desc?: string) {
  return {
    _def: { typeName: "ZodObject", shape: () => shape, description: desc },
    parse: (v: unknown) => v,
  };
}
function zodString(desc?: string) {
  return { _def: { typeName: "ZodString", description: desc, checks: [] }, parse: (v: unknown) => v };
}
function zodNumber() {
  return { _def: { typeName: "ZodNumber", checks: [] }, parse: (v: unknown) => v };
}
function zodEnum(values: string[]) {
  return { _def: { typeName: "ZodEnum", values }, parse: (v: unknown) => v };
}
function zodOptional(inner: unknown) {
  return { _def: { typeName: "ZodOptional", innerType: inner }, parse: (v: unknown) => v };
}

describe("functionToTool", () => {
  it("converts Zod schema to tool definition", () => {
    const schema = zodObject({
      city: zodString("City name"),
      unit: zodOptional(zodEnum(["celsius", "fahrenheit"])),
    });

    const tool = functionToTool(schema, {
      name: "get_weather",
      description: "Get current weather",
    });

    expect(tool.type).toBe("function");
    expect(tool.function.name).toBe("get_weather");
    expect(tool.function.description).toBe("Get current weather");
    expect(tool.function.parameters).toBeDefined();
    const params = tool.function.parameters as Record<string, unknown>;
    expect(params.type).toBe("object");
    expect((params.properties as Record<string, Record<string, unknown>>).city.type).toBe("string");
    expect(params.required).toEqual(["city"]);
  });

  it("accepts plain JSON Schema", () => {
    const schema = {
      type: "object",
      properties: { query: { type: "string" } },
      required: ["query"],
    };

    const tool = functionToTool(schema, { name: "search" });

    expect(tool.function.name).toBe("search");
    expect(tool.function.parameters).toEqual(schema);
  });

  it("adds strict flag when requested", () => {
    const tool = functionToTool(
      { type: "object", properties: {} },
      { name: "test", strict: true },
    );

    expect((tool.function as Record<string, unknown>).strict).toBe(true);
  });

  it("omits description when not provided", () => {
    const tool = functionToTool(
      { type: "object", properties: {} },
      { name: "test" },
    );

    expect(tool.function.description).toBeUndefined();
  });

  it("throws for invalid schema", () => {
    expect(() =>
      functionToTool("not a schema" as unknown, { name: "test" }),
    ).toThrow("functionToTool");
  });

  it("throws for null schema", () => {
    expect(() =>
      functionToTool(null, { name: "test" }),
    ).toThrow("functionToTool");
  });
});
