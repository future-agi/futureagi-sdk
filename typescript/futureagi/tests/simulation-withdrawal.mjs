/** After `pnpm run build`, run `node tests/simulation-withdrawal.mjs`. No HTTP calls. */
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { createRequire } from "node:module";
import { fileURLToPath, pathToFileURL } from "node:url";

const root = fileURLToPath(new URL("../", import.meta.url));
const manifest = JSON.parse(fs.readFileSync(path.join(root, "package.json"), "utf8"));
const require = createRequire(path.join(root, "package.json"));
const withdrawn = /^Simulations?\w*Client$/;
let checked = 0;
for (const [entry, conditions] of Object.entries(manifest.exports)) {
  for (const mode of ["import", "require"]) {
    const target = path.join(root, conditions[mode].default);
    const module = mode === "import" ? await import(pathToFileURL(target).href) : require(target);
    assert.deepEqual(Object.keys(module).filter(name => withdrawn.test(name)), [], `${entry} ${mode}`);
    if (entry === ".") {
      const client = new module.FutureAGIClient({
        apiKey: "fixture-api", secretKey: "fixture-secret", baseUrl: "http://localhost:9031",
      });
      assert.equal("simulations" in client, false);
      assert.equal("simulations" in client.withOptions({ timeoutMs: 2 }), false);
    }
    const declaration = fs.readFileSync(path.join(root, conditions[mode].types), "utf8");
    assert.equal(/Simulations?\w*Client|\bsimulations\s*:/.test(declaration), false, `${entry} ${mode} declarations`);
    checked += 1;
  }
}
console.log(`PASS: ${checked} emitted public entry/condition pairs omit simulation exports, plus root instances/clones and declarations.`);
