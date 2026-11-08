/** Retain the recorded lifecycle schemas before legacy Swagger sanitation.
 * Operation selection and routing still come from the newly generated spec.
 */
import fs from "node:fs";
import { normalize } from "./normalize-sdk-json-values.mjs";

const [specPath, convertedPath, extensionPath] = process.argv.slice(2);
const spec = JSON.parse(fs.readFileSync(specPath, "utf8"));
const raw = JSON.parse(fs.readFileSync(convertedPath, "utf8"));
const extension = JSON.parse(fs.readFileSync(extensionPath, "utf8"));
const references = new Set();
function visit(value) {
  if (Array.isArray(value)) return value.forEach(visit);
  if (!value || typeof value !== "object") return;
  if (value.$ref?.startsWith("#/components/")) references.add(value.$ref);
  Object.values(value).forEach(visit);
}
for (const [route, item] of Object.entries(extension.paths)) {
  for (const method of Object.keys(item)) {
    if (!["get", "post", "put", "patch", "delete"].includes(method)) continue;
    const operation = spec.paths[route]?.[method];
    if (!operation) throw new Error(`Missing extension operation: ${method} ${route}`);
    visit(operation);
  }
}
const visited = new Set();
for (const ref of references) {
  if (visited.has(ref)) continue;
  visited.add(ref);
  const [, , section, name] = ref.split("/");
  const source = raw.components?.[section]?.[name];
  if (!source) throw new Error(`Missing extension component: ${ref}`);
  const schema = normalize(source);
  spec.components[section] ??= {};
  spec.components[section][name] = schema;
  visit(schema);
}
fs.writeFileSync(specPath, JSON.stringify(spec, null, 2) + "\n");
