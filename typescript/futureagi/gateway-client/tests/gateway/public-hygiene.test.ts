/**
 * Public hygiene: this directory ships in a public repository and its src/
 * comments ship inside dist/gateway, so nothing here may name a path on a
 * developer's machine, an internal design document, an internal review or
 * release code name, or a build machine's job id, image layout or instance kind.
 *
 * - Everywhere below (src/, tests/ except tests/parity/, which has its own scan,
 *   scripts/, ci/, the toolchain files, an installed
 *   .github/workflows/gateway-client.yml, and the shared parity data in the
 *   repository's tests/fixtures/gateway/: goldens, case catalog, and the
 *   intended-differences list with its reviewer records):
 *   no local paths and no internal document names.
 * - src/ also carries no intended-difference or follow-up ids (D-nn, F-n) and
 *   no section numbers of the 1.x specification: a reader of dist/gateway
 *   has neither document, so a comment says what the code does instead.
 *
 * Every pattern is assembled from pieces, so this file does not match itself;
 * each one has a positive control below.
 */
import { describe, it, expect } from "@jest/globals";
import { existsSync, readdirSync, readFileSync, statSync } from "node:fs";
import { basename, join, relative, sep } from "node:path";

const ROOT = join(__dirname, "..", "..");
const REPO = join(ROOT, "..", "..", "..");
const j = (...parts: string[]) => parts.join("");

/** Local paths and internal document, review and job names: never anywhere here. */
const EVERYWHERE: Array<[string, RegExp]> = [
  ["local path", new RegExp(j("futureagi", "-local"))],
  ["local path", new RegExp(j("/", "Users/"))],
  ["local path", new RegExp(j("/", "Volumes/"))],
  ["local path", new RegExp(j("~/", "\\."))],
  ["internal evidence directory", new RegExp(j("\\.", "omega/"))],
  ["internal design document", new RegExp(j("\\bPL", "AN [0-9\\u00a7]"))],
  ["internal design document", new RegExp(j("AgentCC ", "fold"), "i")],
  ["internal design document", new RegExp(j("GATEWAY", "-ANSWERS"), "i")],
  ["internal design document", new RegExp(j("\\bCRIT", "IQUE\\b"))],
  ["internal design document", new RegExp(j("\\bDESIGN", "-[AB]\\b"))],
  ["internal design document", new RegExp(j("DSX", "-WRITE"), "i")],
  ["internal design document", new RegExp(j("SHARED", "-BASE"))],
  ["internal design document", new RegExp(j("\\bREADI", "NESS\\b"))],
  ["internal design document", new RegExp(j("\\bINVENTORY", "-"))],
  ["internal design document", new RegExp(j("\\bINV", "-[ACFP]\\b"))],
  ["internal design document", new RegExp(j("RESULT", "\\.md"))],
  ["internal design document", new RegExp(j("OWNER", "-RULINGS|MORNING", "-PACKETS"))],
  ["internal decision", new RegExp(j("\\bru", "ling [0-9]"), "i")],
  ["internal decision", new RegExp(j("owner ", "packet"), "i")],
  ["internal lane or packet", new RegExp(j("\\bGW", "-[PL][0-9]"))],
  ["internal lane", new RegExp(j("\\blanes? ", "L[1-9]\\b"), "i")],
  ["internal lane", new RegExp(j("\\bL[1-9]", "('s)? (golden|goldens|recorder|case|cases|lane)\\b"))],
  ["internal release name", new RegExp(j("\\bR", "-GW\\b"))],
  ["internal contract id", new RegExp(j("\\bC", "79\\b"))],
  ["build-machine job id", new RegExp(j("\\bj-20", "[0-9]{6}t[0-9]{4}"))],
  ["build-machine image", new RegExp(j("omega", "-(runner|exec)"), "i")],
  ["build-machine instance kind", new RegExp(j("\\b[Ss]p", "ot (VM|instance)s?\\b"))],
];

/** Ids of documents a reader of dist/gateway does not have: never in src/. */
const SRC_ONLY: Array<[string, RegExp]> = [
  ["intended-difference id", new RegExp(j("\\bD", "-[0-9]{2}[a-z]?\\b"))],
  ["follow-up id", new RegExp(j("\\bF", "-[0-9]{1,2}\\b"))],
  ["1.x specification section", new RegExp(j("\\b[0-9]\\.[0-9]", "[A-Z]\\.[0-9]\\b"))],
];

function walk(dir: string, skip: (path: string) => boolean): string[] {
  return readdirSync(dir).flatMap((name) => {
    const path = join(dir, name);
    if (skip(path)) return [];
    return statSync(path).isDirectory() ? walk(path, skip) : [path];
  });
}

const rel = (file: string) => relative(REPO, file).split(sep).join("/");
const SKIP = new Set(["node_modules", "dist", ".jest-out"].map((d) => join(ROOT, d)));
const SRC = walk(join(ROOT, "src"), () => false);
// Installed or generated, never committed: tests/live/stock/ gets its own node_modules
// on a build machine (npm ci there), and Python writes __pycache__ beside the fixtures'
// helper scripts when a test imports them.
const generated = (p: string) => ["node_modules", "__pycache__", ".pytest_cache"].includes(basename(p));
const TESTS = walk(join(ROOT, "tests"), (p) => p === join(ROOT, "tests", "parity") || generated(p));
const FIXTURES = walk(join(REPO, "tests", "fixtures", "gateway"), generated);
const SCRIPTS = walk(join(ROOT, "scripts"), () => false);
const CI = walk(join(ROOT, "ci"), () => false);
const TOOLCHAIN = readdirSync(ROOT)
  .map((name) => join(ROOT, name))
  .filter((p) => !SKIP.has(p) && statSync(p).isFile());
const WORKFLOW = join(REPO, ".github", "workflows", "gateway-client.yml");
const ALL = [...SRC, ...TESTS, ...SCRIPTS, ...CI, ...TOOLCHAIN, ...FIXTURES, ...(existsSync(WORKFLOW) ? [WORKFLOW] : [])];

function leaks(text: string, rules: Array<[string, RegExp]>): string[] {
  const found: string[] = [];
  text.split("\n").forEach((line, i) => {
    for (const [what, re] of rules) {
      const m = re.exec(line);
      if (m) found.push(`${i + 1}: ${what} "${m[0]}"`);
    }
  });
  return found;
}

describe("public hygiene", () => {
  it("finds the files it checks", () => {
    expect(SRC.length).toBeGreaterThan(40);
    expect(TESTS.length).toBeGreaterThan(40);
    expect(SCRIPTS.length).toBeGreaterThan(5);
    expect(CI.map(rel)).toEqual(["typescript/futureagi/gateway-client/ci/gateway-client.yml"]);
    expect(TOOLCHAIN.map((p) => relative(ROOT, p))).toEqual(
      expect.arrayContaining(["jest.config.cjs", "package.json", "registration-fragment.json", "tsconfig.json"]),
    );
    expect(TESTS.some((p) => p.includes(`${sep}tests${sep}parity${sep}`))).toBe(false);
    expect(TESTS.map(rel)).toEqual(
      expect.arrayContaining([
        "typescript/futureagi/gateway-client/tests/live/wire.test.ts",
        "typescript/futureagi/gateway-client/tests/live/manifest.json",
        "typescript/futureagi/gateway-client/tests/live/stock/package.json",
      ]),
    );
    expect(FIXTURES.map(rel)).toEqual(
      expect.arrayContaining([
        "tests/fixtures/gateway/intended-differences.json",
        "tests/fixtures/gateway/catalog.json",
        "tests/fixtures/gateway/README.md",
        "tests/fixtures/gateway/golden/ts-client-1.0.1-esm/index.json",
      ]),
    );
  });

  it.each(ALL.map(rel))("%s names no local path or internal document", (name) => {
    const file = join(REPO, name);
    expect([...leaks(name, EVERYWHERE).map((l) => `path ${l}`), ...leaks(readFileSync(file, "utf8"), EVERYWHERE)]).toEqual([]);
  });

  it.each(SRC.map(rel))("%s cites no intended-difference, follow-up or specification id", (name) => {
    expect(leaks(readFileSync(join(REPO, name), "utf8"), SRC_ONLY)).toEqual([]);
  });

  it("every rule catches what it is for (positive controls)", () => {
    const samples = [
      j("see futureagi", "-local/x"),
      j("see ~/", ".config/x"),
      j("/", "Users/someone/x"),
      j("/", "Volumes/disk/x"),
      j("evidence in .", "omega/program"),
      j("PL", "AN 2.1"),
      j("PL", "AN §3"),
      j("AgentCC ", "fold"),
      j("GATEWAY", "-ANSWERS 3(a)"),
      j("gateway", "-answers-map.json"),
      j("CRIT", "IQUE B4"),
      j("DESIGN", "-A"),
      j("DSX", "-WRITE-MAP"),
      j("SHARED", "-BASE"),
      j("READI", "NESS section 3"),
      j("INVENTORY", "-AGENTCC"),
      j("INV", "-A §4"),
      j("RESULT", ".md:359"),
      j("OWNER", "-RULINGS"),
      j("ru", "ling 234"),
      j("owner ", "packet 32"),
      j("GW", "-P4"),
      j("GW", "-L3"),
      j("lane ", "L4"),
      j("L1", "'s golden"),
      j("R", "-GW"),
      j("the C", "79 contract"),
      j("j-20", "261024t0813-a06316"),
      j("/opt/omega", "-runner/playwright"),
      j("image omega", "-exec-v20261021"),
      j("no latency claim from a S", "pot VM"),
      j("ran on s", "pot instances"),
    ];
    for (const s of samples) expect([s, leaks(s, EVERYWHERE).length]).toEqual([s, 1]);
    for (const s of [j("(D", "-18)"), j("D", "-06b"), j("F", "-3"), j("(8.1", "E.5)")]) expect([s, leaks(s, SRC_ONLY).length]).toEqual([s, 1]);
  });

  it("ordinary text passes (negative controls)", () => {
    const clean = [
      "the plan for a request",
      "D-18 in real browsers",
      "@agentcc/client 1.0.1 and 2.0",
      "gateway at live-gateway-source",
      "ES2022 and node16",
      "x-agentcc-metadata",
      "a 1.2.3 version",
      "the L1 cache",
      "no x-omega- header",
      "/opt/ms-playwright",
      "a spot check of the cache on a VM, and the hot spot",
    ];
    for (const s of clean) expect([s, leaks(s, EVERYWHERE)]).toEqual([s, []]);
    expect(leaks("version 0.1.2 and HTTP/1.1", SRC_ONLY)).toEqual([]);
  });
});
