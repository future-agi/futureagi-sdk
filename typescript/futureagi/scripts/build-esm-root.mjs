import { writeFile } from "node:fs/promises";

// Linking the full static graph can initialize Node's HTTP dependencies before the first import runs.
// Keep only provenance in the entry's static graph and load the client graph after it evaluates.
const api = await import("../dist/esm/public-api.js");
const names = Object.keys(api).join(",\n  ");
await writeFile(new URL("../dist/esm/index.js", import.meta.url),
  `import "./_core/dispatcher-provenance.js";\nexport const {\n  ${names}\n} = await import("./public-api.js");\n`);
