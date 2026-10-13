/** Add a reviewed operation closure while preserving the existing SDK surface. */
import fs from "node:fs";

const [baselinePath, currentPath, rawPath, scopePath, outputPath] = process.argv.slice(2);
const baseline = JSON.parse(fs.readFileSync(baselinePath, "utf8"));
const current = JSON.parse(fs.readFileSync(currentPath, "utf8"));
const raw = JSON.parse(fs.readFileSync(rawPath, "utf8"));
const scope = JSON.parse(fs.readFileSync(scopePath, "utf8"));
const result = structuredClone(baseline);
const references = new Set();

function transform(value) {
  if (Array.isArray(value)) return value.map(transform);
  if (!value || typeof value !== "object") return value;
  if (value.$ref?.startsWith("#/components/")) references.add(value.$ref);
  if (value.nullable === true && Array.isArray(value.enum)) {
    return { ...value, enum: [...value.enum, null] };
  }
  if (value["x-json-value"] === true) {
    return {
      description: value.description || "Any valid JSON value.",
      anyOf: [
        { type: "boolean" }, { type: "number" }, { type: "string" },
        { type: "array", items: {} },
        { type: "object", additionalProperties: true, ...((value.nullable === false || value["x-nullable"] === false) ? {} : { nullable: true }) },
      ],
    };
  }
  return Object.fromEntries(Object.entries(value).map(([key, child]) => [key, transform(child)]));
}

for (const key of scope.operations) {
  const [method, path] = key.split(" ");
  const operation = current.paths[path]?.[method.toLowerCase()];
  if (!operation) throw new Error(`Missing operation: ${key}`);
  result.paths[path] ??= {};
  result.paths[path][method.toLowerCase()] = transform(operation);
  if (current.paths[path].parameters) result.paths[path].parameters = transform(current.paths[path].parameters);
}
const visited = new Set();
const owned = new Set(baseline["x-updated-components"] || []);
const updatedComponents = new Set();
while ([...references].some((ref) => !visited.has(ref))) {
  const ref = [...references].find((value) => !visited.has(value));
  visited.add(ref);
  const [, , section, name] = ref.split("/");
  const source = raw.components?.[section]?.[name] ?? current.components?.[section]?.[name];
  if (!source) throw new Error(`Missing component: ${ref}`);
  const converted = transform(source);
  result.components[section] ??= {};
  const existing = result.components[section][name];
  // Shared components must remain identical. A cross-feature change needs its
  // own reviewed SDK refresh instead of being smuggled into this overlay.
  if (existing && !owned.has(ref) && JSON.stringify(existing) !== JSON.stringify(converted)) {
    const currentExisting = current.components?.[section]?.[name];
    if (JSON.stringify(existing) !== JSON.stringify(currentExisting)) {
      throw new Error(`Existing SDK component changed: ${ref}`);
    }
    continue;
  }
  result.components[section][name] = converted;
  if (!existing || owned.has(ref)) updatedComponents.add(ref);
}
result["x-backend-source"] = scope.backend_repository;
result["x-backend-revision"] = scope.backend_revision;
result["x-updated-operations"] = scope.operations;
result["x-updated-components"] = [...updatedComponents].sort();
fs.writeFileSync(outputPath, `${JSON.stringify(result, null, 2)}\n`);
console.log(`Updated ${scope.operations.length} SDK operations and ${visited.size} referenced components.`);
