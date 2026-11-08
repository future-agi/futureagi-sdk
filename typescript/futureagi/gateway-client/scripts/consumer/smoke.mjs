// ES module consumer: import() each @future-agi/sdk gateway subpath from the
// installed tarball and use it. Prints one JSON document.
import { createRequire } from "node:module";
const require = createRequire(import.meta.url);
const { SUBPATHS, exportKeys, exercise } = require("./smoke-lib.cjs");
const { renderReact } = require("./react-render.cjs");

const loads = {};
const mods = {};
try {
  for (const sub of SUBPATHS) {
    try {
      const mod = await import(`@future-agi/sdk/${sub}`);
      mods[sub] = mod;
      loads[sub] = { ok: true, exports: exportKeys(mod), file: import.meta.resolve ? String(import.meta.resolve(`@future-agi/sdk/${sub}`)).replace(/^.*node_modules\//, "node_modules/") : null };
    } catch (err) {
      loads[sub] = { ok: false, code: err.code || null, message: String(err.message).split("\n")[0] };
    }
  }
  const used = await exercise(mods);
  if (mods["gateway/react"]) {
    // The renderer comes through require(): react-dom 17 has no exports map,
    // so Node's ES module loader cannot resolve react-dom/server. It is the
    // same React instance the subpath's import of "react" loaded (Node keeps
    // one module per CommonJS file for both loaders).
    used.react = renderReact(mods["gateway/react"], mods["gateway"], require("react"), require("react-dom/server"));
  }
  process.stdout.write(JSON.stringify({ format: "esm", node: process.version, loads, used }) + "\n");
} catch (err) {
  process.stdout.write(JSON.stringify({ format: "esm", node: process.version, fatal: String((err && err.stack) || err) }) + "\n");
  process.exit(1);
}
