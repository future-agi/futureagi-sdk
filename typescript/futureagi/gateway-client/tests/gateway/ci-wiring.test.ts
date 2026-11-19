/**
 * The parity comparator and golden hygiene node tests
 * (tests/parity/compare.test.mjs, hygiene.test.mjs) run in CI, on every
 * path that runs this suite:
 * - ci/gateway-client.yml (installed unchanged as
 *   .github/workflows/gateway-client.yml), on Node 18, 20 and 22, next to
 *   jest, the test-name check and both typechecks;
 * - scripts/run-all-tests.cjs, the `pnpm test` of typescript/futureagi once
 *   the subpaths are registered (sdk-compliance.yml runs `pnpm test`);
 * - scripts/run-suite.sh, the per-Node suite script.
 */
import { describe, it, expect } from "@jest/globals";
import { existsSync, readFileSync } from "node:fs";
import { join } from "node:path";

const ROOT = join(__dirname, "..", "..");
const REPO = join(ROOT, "..", "..", "..");
const read = (...p: string[]) => readFileSync(join(...p), "utf8");
const PARITY = ["tests/parity/compare.test.mjs", "tests/parity/hygiene.test.mjs"];

describe("CI runs the parity node tests", () => {
  it("both parity test files exist", () => {
    for (const f of PARITY) expect(existsSync(join(ROOT, f))).toBe(true);
  });

  it("gateway-client.yml runs them with node --test on Node 18, 20 and 22, after jest and the name check", () => {
    const yml = read(ROOT, "ci", "gateway-client.yml");
    expect(yml).toMatch(/node: \["18", "20", "22"\]/);
    expect(yml).toMatch(/working-directory: typescript\/futureagi\/gateway-client/);
    const steps = [
      "npm ci --ignore-scripts",
      "tsc -p tsconfig.json --noEmit",
      "tsc -p tsconfig.typecheck.json",
      "jest.js -c jest.config.cjs --runInBand --ci --json",
      "node scripts/check-test-names.cjs",
      `node --test ${PARITY.join(" ")}`,
    ];
    let at = -1;
    for (const step of steps) {
      const i = yml.indexOf(step);
      expect(i).toBeGreaterThan(at);
      at = i;
    }
    for (const path of ["typescript/futureagi/gateway-client/**", "tests/fixtures/gateway/**"]) expect(yml).toContain(`"${path}"`);
  });

  it("an installed .github/workflows/gateway-client.yml is ci/gateway-client.yml unchanged", () => {
    const installed = join(REPO, ".github", "workflows", "gateway-client.yml");
    if (existsSync(installed)) expect(read(installed)).toBe(read(ROOT, "ci", "gateway-client.yml"));
    expect(existsSync(join(ROOT, "ci", "gateway-client.yml"))).toBe(true);
  });

  it("root CI forwards Jest flags through pnpm's explicit script runner", () => {
    const yml = read(REPO, ".github", "workflows", "ci.yml");
    const job = yml.slice(yml.indexOf("\n  typescript:\n"), yml.indexOf("\n  packages:\n"));
    expect(job).toMatch(/^\s+run: pnpm run test --runInBand\s*$/m);
    const manifest = JSON.parse(read(ROOT, "..", "package.json"));
    expect(manifest.scripts.test).toBe("node gateway-client/scripts/run-all-tests.cjs");
  });

  it("run-all-tests.cjs runs them after both jest runs and fails when they fail", () => {
    const js = read(ROOT, "scripts", "run-all-tests.cjs");
    expect(js).toContain('["compare.test.mjs", "hygiene.test.mjs"].map((f) => join("gateway-client", "tests", "parity", f))');
    const root = js.indexOf("const root = spawn(");
    const gateway = js.indexOf("const gateway = spawn(");
    const parity = js.indexOf('const parity = spawn("@future-agi/sdk/gateway* parity", ["--test", ...PARITY_TESTS]);');
    expect(root).toBeGreaterThan(0);
    expect(gateway).toBeGreaterThan(root);
    expect(parity).toBeGreaterThan(gateway);
    expect(js).toContain("process.exit([root, gateway, parity].find((code) => code !== 0) ?? 0);");
  });

  it("run-suite.sh runs them on every Node it is given", () => {
    const sh = read(ROOT, "scripts", "run-suite.sh");
    expect(sh).toContain(`step "parity-$V" "$N/node" --test ${PARITY.join(" ")}`);
  });
});
