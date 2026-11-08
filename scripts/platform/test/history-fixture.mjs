import { execFileSync, spawnSync } from "node:child_process";
import { mkdirSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { verifyRecord } from "../export-verify.mjs";
import { loadRules, RULES_FILE } from "../hygiene-scan.mjs";
import { loadTreeRules, TREE_RULES_FILE } from "../hygiene-tree.mjs";
import { exportHistory } from "../public-history.mjs";

export const here = path.dirname(fileURLToPath(import.meta.url));
export const sample = JSON.parse(readFileSync(path.join(here, "hygiene-tree-cases.json"), "utf8")).text.find((c) => c.rules.includes("stream-id")).text;
export const platform = loadRules();
const policy = loadTreeRules();
export const tree = { ...policy, binaries: [], exemptions: [], shas: { ...policy.shas, reviewed: [] } };
export const map = {
  author: { name: "Example Maintainers", email: "maintainers@example.com" },
  date: "2026-01-02T03:04:05Z",
  modules: [{ paths: ["**"], message: "docs: the release tree" }]
};
export const forgeClean = (r) => ({ ...r, mode: "strict", dryRun: false, hygiene: { hits: 0, allowed: false }, ancestry: { ...r.ancestry, hits: 0 } });

export function fixture(t) {
  const dir = mkdtempSync(path.join(tmpdir(), "history-guard-"));
  t.after(() => rmSync(dir, { recursive: true, force: true }));
  const git = (...args) => execFileSync("git", [
    "-c", `user.name=${map.author.name}`, "-c", `user.email=${map.author.email}`,
    "-c", "commit.gpgsign=false", ...args
  ], {
    cwd: dir, encoding: "utf8", stdio: ["ignore", "pipe", "pipe"],
    env: { ...Object.fromEntries(Object.entries(process.env).filter(([key]) => key !== "GIT_NO_REPLACE_OBJECTS")), GIT_CONFIG_GLOBAL: "/dev/null", GIT_CONFIG_NOSYSTEM: "1" }
  }).trim();
  const write = (file, text) => {
    mkdirSync(path.dirname(path.join(dir, file)), { recursive: true });
    writeFileSync(path.join(dir, file), text);
  };
  git("init", "-qb", "main");
  write("README.md", "base\n");
  git("add", "-A");
  git("commit", "-qm", "public base");
  const base = git("rev-parse", "HEAD");
  for (const name of ["main", "dev"]) git("update-ref", `refs/remotes/origin/${name}`, base);
  git("checkout", "-qb", "qualified");
  write("docs/guide.md", "guide\n");
  git("add", "-A");
  git("commit", "-qm", "candidate");
  const cut = (extra = {}) => exportHistory(dir, {
    qualified: "qualified", onto: "origin/dev", main: "origin/main", publicRevs: ["origin/dev"], map, platform, tree, ...extra
  });
  const verify = (record, extra = {}) => verifyRecord(dir, record, { platform, tree, localOnly: [], ...extra });
  const mergeSide = (first) => {
    git("checkout", "-qb", "side", base);
    write("hidden.txt", `${sample}\n`);
    git("add", "-A");
    git("commit", "-qm", "side notes");
    const leaking = git("rev-parse", "HEAD");
    git("rm", "-q", "hidden.txt");
    git("commit", "-qm", "remove side notes");
    const side = git("rev-parse", "HEAD");
    git("checkout", "-qb", "onto", first.export.commit);
    git("merge", "--no-ff", "-qm", "merge side", "side");
    return { side, leaking };
  };
  const cli = (publicRev) => {
    write(RULES_FILE, JSON.stringify(platform));
    write(TREE_RULES_FILE, JSON.stringify(tree));
    write("map.json", JSON.stringify(map));
    return spawnSync(process.execPath, [path.join(here, "../public-history.mjs"),
      "--qualified", "qualified", "--onto", "origin/dev", "--main", "origin/main",
      "--public", "origin/dev", "--public", publicRev, "--modules", "map.json", "--ref", "export/cli"
    ], { cwd: dir, encoding: "utf8" });
  };
  return { dir, git, write, base, cut, verify, mergeSide, cli };
}
