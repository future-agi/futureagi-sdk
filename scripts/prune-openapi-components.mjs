#!/usr/bin/env node
import fs from "node:fs";

const [inputPath, outputPath = inputPath] = process.argv.slice(2);

if (!inputPath) {
  console.error("Usage: prune-openapi-components.mjs <input> [output]");
  process.exit(1);
}

const spec = JSON.parse(fs.readFileSync(inputPath, "utf8"));
const refs = new Set();
const seen = new Set();

function collectRefs(value) {
  if (!value || typeof value !== "object") {
    return;
  }

  if (typeof value.$ref === "string" && value.$ref.startsWith("#/components/")) {
    refs.add(value.$ref);
  }

  if (Array.isArray(value)) {
    value.forEach(collectRefs);
    return;
  }

  Object.values(value).forEach(collectRefs);
}

function getByRef(ref) {
  const parts = ref
    .replace(/^#\//, "")
    .split("/")
    .map((part) => part.replace(/~1/g, "/").replace(/~0/g, "~"));
  return parts.reduce((current, part) => current?.[part], spec);
}

collectRefs(spec.paths);

while (refs.size > seen.size) {
  for (const ref of [...refs]) {
    if (seen.has(ref)) {
      continue;
    }
    seen.add(ref);
    collectRefs(getByRef(ref));
  }
}

if (spec.components) {
  for (const [section, values] of Object.entries(spec.components)) {
    if (!values || typeof values !== "object") {
      continue;
    }

    if (section === "securitySchemes") {
      continue;
    }

    for (const name of Object.keys(values)) {
      const escapedName = name.replace(/~/g, "~0").replace(/\//g, "~1");
      const ref = `#/components/${section}/${escapedName}`;
      if (!seen.has(ref)) {
        delete values[name];
      }
    }
  }
}

fs.writeFileSync(outputPath, `${JSON.stringify(spec, null, 2)}\n`);
