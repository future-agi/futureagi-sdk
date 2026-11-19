// CommonJS consumer: require() each @future-agi/sdk gateway subpath from the
// installed tarball and use it. Prints one JSON document.
"use strict";
const { SUBPATHS, exportKeys, exercise } = require("./smoke-lib.cjs");
const { renderReact } = require("./react-render.cjs");

(async () => {
  const loads = {};
  const mods = {};
  for (const sub of SUBPATHS) {
    try {
      const mod = require(`@future-agi/sdk/${sub}`);
      mods[sub] = mod;
      loads[sub] = { ok: true, exports: exportKeys(mod), file: require.resolve(`@future-agi/sdk/${sub}`).replace(/^.*node_modules\//, "node_modules/") };
    } catch (err) {
      loads[sub] = { ok: false, code: err.code || null, message: String(err.message).split("\n")[0] };
    }
  }
  const used = await exercise(mods);
  if (mods["gateway/react"]) used.react = renderReact(mods["gateway/react"], mods["gateway"], require("react"), require("react-dom/server"));
  process.stdout.write(JSON.stringify({ format: "cjs", node: process.version, loads, used }) + "\n");
})().catch((err) => {
  process.stdout.write(JSON.stringify({ format: "cjs", node: process.version, fatal: String(err && err.stack || err) }) + "\n");
  process.exit(1);
});
