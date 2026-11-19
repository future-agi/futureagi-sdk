/** Preserve the upstream arbitrary-JSON extension in generated OpenAPI schemas. */
import fs from "node:fs";

export function normalize(value) {
  if (Array.isArray(value)) return value.map(normalize);
  if (!value || typeof value !== "object") return value;
  if (value["x-json-value"] === true) {
    return {
      description: value.description || "Any valid JSON value.",
      anyOf: [
        { type: "boolean" }, { type: "number" }, { type: "string" },
        { type: "array", items: {} },
        { type: "object", additionalProperties: true,
          ...((value.nullable === false || value["x-nullable"] === false) ? {} : { nullable: true }) },
      ],
    };
  }
  const result = Object.fromEntries(Object.entries(value).map(([key, child]) => [key, normalize(child)]));
  // Public schema descriptions retain behavior, not private tracker references.
  if (typeof result.description === "string") result.description = result.description.replace(/\s*\([T]H-\d+\)/g, "");
  if (result.nullable === true && Array.isArray(result.enum) && !result.enum.includes(null)) result.enum.push(null);
  return result;
}

if (process.argv[1] && import.meta.url === new URL(process.argv[1], "file:").href) {
  const target = process.argv[2];
  fs.writeFileSync(target, JSON.stringify(normalize(JSON.parse(fs.readFileSync(target, "utf8"))), null, 2) + "\n");
}
