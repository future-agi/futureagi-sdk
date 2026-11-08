/**
 * scripts/consumer/check-install-logs.cjs, the packed-tarball rig's
 * peer-dependency check: an ERESOLVE line in any install log fails it, even
 * when npm exited 0 ("npm warn ERESOLVE overriding peer dependency"), and
 * pack-checks.sh counts it as a failed step.
 */
import { describe, it, expect, afterEach } from "@jest/globals";
import { spawnSync } from "node:child_process";
import { mkdtempSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

const ROOT = join(__dirname, "..", "..");
const SCRIPT = join(ROOT, "scripts", "consumer", "check-install-logs.cjs");
const dirs: string[] = [];
afterEach(() => {
  for (const d of dirs.splice(0)) rmSync(d, { recursive: true, force: true });
});

function outDir(logs: Record<string, string>): string {
  const dir = mkdtempSync(join(tmpdir(), "gw-install-logs-"));
  dirs.push(dir);
  for (const [name, text] of Object.entries(logs)) writeFileSync(join(dir, name), text);
  return dir;
}

function run(dir: string) {
  const r = spawnSync(process.execPath, [SCRIPT, dir], { encoding: "utf8" });
  return { status: r.status, out: r.status === 2 && !r.stdout ? null : JSON.parse(r.stdout) };
}

const CLEAN = "added 3 packages in 2s\n";
const OVERRIDE = [
  "npm warn ERESOLVE overriding peer dependency",
  "npm warn While resolving: consumer@0.0.0",
  "added 5 packages in 3s",
].join("\n");

describe("install-log peer check", () => {
  it("clean install logs pass", () => {
    const dir = outDir({ "install-v20.20.2.log": CLEAN, "matrix-install-react17-v20.20.2.log": CLEAN, "tsc-install.log": CLEAN });
    expect(run(dir)).toEqual({ status: 0, out: { logs: ["install-v20.20.2.log", "matrix-install-react17-v20.20.2.log", "tsc-install.log"], eresolve: [] } });
  });

  it("an ERESOLVE override warning in an install that exited 0 fails, naming the log and line", () => {
    const dir = outDir({ "matrix-install-react19-v18.20.8.log": OVERRIDE, "install-v18.20.8.log": CLEAN });
    const { status, out } = run(dir);
    expect(status).toBe(1);
    expect(out.eresolve).toEqual([{ log: "matrix-install-react19-v18.20.8.log", line: "npm warn ERESOLVE overriding peer dependency" }]);
  });

  it("an ERESOLVE error, in the existing-tree setup or the tsc consumer, fails too", () => {
    for (const name of ["matrix-tree-existing17-v22.23.3.log", "tsc-install.log", "install-v22.23.3.log"]) {
      const dir = outDir({ [name]: "npm error code ERESOLVE\nnpm error ERESOLVE unable to resolve dependency tree\n" });
      const { status, out } = run(dir);
      expect(status).toBe(1);
      expect(out.eresolve.map((e: { log: string }) => e.log)).toEqual([name, name]);
    }
  });

  it("other logs are not install logs: an ERESOLVE in a smoke or tsc log is not read", () => {
    const dir = outDir({ "install-v20.20.2.log": CLEAN, "smoke-esm-v20.20.2.log": "ERESOLVE", "tsc-node16.log": "ERESOLVE", "eresolve.log": "ERESOLVE" });
    expect(run(dir).status).toBe(0);
  });

  it("no install log at all is a failure, not a pass", () => {
    const dir = outDir({ "steps.txt": "" });
    expect(run(dir).status).toBe(2);
  });

  it("pack-checks.sh runs it as a counted step after every install", () => {
    const sh = readFileSync(join(ROOT, "scripts", "pack-checks.sh"), "utf8");
    const at = sh.indexOf('step eresolve node "$C/check-install-logs.cjs" "$OUT"');
    expect(at).toBeGreaterThan(0);
    for (const install of ["step \"install-$V\"", "step \"matrix-install-$CASE-$V\"", "step \"matrix-tree-$CASE-$V\"", "step tsc-install"]) {
      const i = sh.indexOf(install);
      expect(i).toBeGreaterThan(0);
      expect(i).toBeLessThan(at);
    }
    expect(sh).toMatch(/\[ \$rc -eq 0 \] \|\| fails=\$\(\(fails\+1\)\)/);
    expect(sh.trimEnd().endsWith("exit $fails")).toBe(true);
  });
});
