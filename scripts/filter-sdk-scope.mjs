#!/usr/bin/env node
/** Apply release scope to a built or pinned SDK spec, preserving unrelated contracts. */
import fs from "node:fs";
import { fileURLToPath } from "node:url";

const [specPath, operationsPath] = process.argv.slice(2);
if (!specPath) throw new Error("Usage: filter-sdk-scope.mjs <spec.json> [operations.txt]");
const scope = JSON.parse(fs.readFileSync(fileURLToPath(new URL("../openapi/sdk/scope.json", import.meta.url)), "utf8"));
const spec = JSON.parse(fs.readFileSync(specPath, "utf8"));
const methods = new Set(["get", "post", "put", "patch", "delete", "head", "options", "trace"]);
const removed = {};
for (const [path, item] of Object.entries(spec.paths)) {
  if (scope.excluded_path_prefixes.some(prefix => path.startsWith(prefix))) {
    removed[path] = item;
    delete spec.paths[path];
  }
}

// Only remove components owned exclusively by the withdrawn paths. In particular,
// do not drop shared models or unrelated, intentionally retained extension models.
// Follow local refs and discriminator mappings (both contain component pointers).
function closure(value) {
  const seen = new Set();
  function visit(value) {
    if (typeof value === "string" && value.startsWith("#/components/")) {
      if (seen.has(value)) return;
      seen.add(value);
      const target = value.slice(2).split("/")
        .map(part => part.replace(/~1/g, "/").replace(/~0/g, "~"))
        .reduce((object, key) => object?.[key], spec);
      if (!target) throw new Error(`Unresolved component: ${value}`);
      visit(target);
    } else if (value && typeof value === "object") {
      Object.values(value).forEach(visit);
    }
  }
  visit(value);
  return seen;
}
const withdrawn = closure(removed);
const kept = closure(spec.paths);
// Components outside the withdrawn closure also retain their dependencies.
for (const [section, values] of Object.entries(spec.components ?? {})) {
  for (const [name, schema] of Object.entries(values)) {
    const ref = `#/components/${section}/${name.replace(/~/g, "~0").replace(/\//g, "~1")}`;
    if (!withdrawn.has(ref)) for (const dependency of closure(schema)) kept.add(dependency);
  }
}
const deleted = new Set();
for (const ref of withdrawn) {
  if (kept.has(ref)) continue;
  const [, , section, name] = ref.split("/");
  if (section === "securitySchemes") continue;
  delete spec.components[section][name.replace(/~1/g, "/").replace(/~0/g, "~")];
  deleted.add(ref);
}
const tags = new Set();
const operations = [];
for (const item of Object.values(spec.paths)) {
  for (const [method, operation] of Object.entries(item)) {
    if (!methods.has(method)) continue;
    for (const tag of operation.tags ?? []) tags.add(tag);
    if (operation.operationId) operations.push(operation.operationId);
  }
}
if (spec.tags) spec.tags = spec.tags.filter(tag => tags.has(tag.name));
if (spec["x-updated-components"]) {
  spec["x-updated-components"] = spec["x-updated-components"].filter(ref => !deleted.has(ref));
}
fs.writeFileSync(specPath, `${JSON.stringify(spec, null, 2)}\n`);
if (operationsPath) fs.writeFileSync(operationsPath, `${[...new Set(operations)].sort().join("\n")}\n`);
console.log(`SDK scope: removed ${Object.keys(removed).length} paths and ${deleted.size} exclusive components; kept ${operations.length} operations.`);
