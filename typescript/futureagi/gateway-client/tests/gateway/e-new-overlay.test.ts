/**
 * The entries that classify every difference between this client's recording
 * (scripts/enew/record-enew.sh) and the @agentcc/client 1.0.1 golden: those signed
 * into the shared tests/fixtures/gateway/intended-differences.json ('proven', ids
 * 'D-xx-ts' and 'TS-*') and those still in the overlay,
 * intended-differences-e-new-ts.json ('landed', waiting for a reviewer record).
 * Checked here: their schema, the reviewer rule, overlay ids that clash with neither
 * shared list, rules that pin what they cover, test ids that name tests, and the
 * migration line of each entry that changes what a 1.x caller sends; and that a
 * version bump keeps the release gate: D-03-ts takes any version, no other rule names
 * the current one, and constants.d.ts (pinned by TS-3.2-dts-surface's sha256 rules) is
 * the same text for every version. The comparison itself (scripts/enew/compare-enew.mjs)
 * needs a build and a recording, so it runs on a build machine, where record-enew.sh's
 * bump-* steps also run the gate on a bumped build; this checks the files everywhere.
 */
import { describe, it, expect } from "@jest/globals";
import { createHash } from "node:crypto";
import { existsSync, readdirSync, readFileSync, statSync } from "node:fs";
import { join } from "node:path";
import * as ts from "typescript";
import { assertRetainedReview } from "./retained-review";

const ROOT = join(__dirname, "..", "..");
const REPO = join(ROOT, "..", "..", "..");
type Rule = { path?: string; kind?: string; old?: string; new?: string; top_level?: boolean };
type Entry = {
  id: string;
  lang: string;
  status: string;
  summary: string;
  migration?: string;
  applies_to: string[];
  match: Rule[];
  evidence: string;
  test_id: string;
  reviewer: null | { by: string; record: string; verdict: string };
};
const OVERLAY = JSON.parse(readFileSync(join(__dirname, "intended-differences-e-new-ts.json"), "utf8")) as { recorded_at: string; differences: Entry[] };
const SHARED = JSON.parse(readFileSync(join(REPO, "tests", "fixtures", "gateway", "intended-differences.json"), "utf8")) as { differences: Entry[] };
const TS_LIST = JSON.parse(readFileSync(join(__dirname, "intended-differences-ts.json"), "utf8")) as { differences: Array<{ id: string }> };
// The client's ids, as scripts/enew/compare-enew.mjs PORT_ID reads them from the shared file.
const PORT_ID = /^(D-\d\d[a-z]?-ts|TS-[0-9.]+-[a-z0-9-]+)$/;
const SIGNED = SHARED.differences.filter((e) => PORT_ID.test(e.id));
const PORT = [...SIGNED, ...OVERLAY.differences];
// Entries that change what a 1.x caller sends or may pass carry the line the migration
// guide quotes.
const MIGRATION = ["D-06b-ts", "D-21-ts", "TS-1.5-cache-only-config"];
// Text no recorded value contains: a regex that matches it pins nothing.
const PROBES = ["<<parity probe: no recorded value is this text>>", "\u0000\n"];

// The version this tree ships, and the VERSION line scripts/build.cjs requires for it.
const PKG_VERSION = (JSON.parse(readFileSync(join(ROOT, "..", "package.json"), "utf8")) as { version: string }).version;
const CONSTANTS = join(ROOT, "src", "constants.ts");
const typedLine = (v: string) => `export const VERSION: string = "${v}";`;
const literalLine = (v: string) => `export const VERSION = "${v}";`;
const nextMinor = (v: string) => `${v.split(".")[0]}.${Number(v.split(".")[1]) + 1}.0`;
// What tests/parity/harness/dts.mjs hashes: the text without source-map comments.
const DTS_NORMALISE = String.raw`.replace(/^\/\/# sourceMappingURL=.*$/gm, "").trimEnd() + "\n"`;
const dtsSha = (text: string) => createHash("sha256").update(text.replace(/^\/\/# sourceMappingURL=.*$/gm, "").trimEnd() + "\n").digest("hex");
const libFiles = new Map<string, ts.SourceFile | undefined>();

/**
 * src/constants.ts's declaration file as tsc emits it under one of the build's configs
 * (tsconfig.esm.json or tsconfig.cjs.json), with the source's VERSION line replaced by
 * `line(version)`.
 */
function emitConstantsDts(config: string, version: string, line: (v: string) => string = typedLine): string {
  const fail = (d: ts.Diagnostic) => {
    throw new Error(ts.flattenDiagnosticMessageText(d.messageText, "\n"));
  };
  const parsed = ts.getParsedCommandLineOfConfigFile(join(ROOT, config), {}, { ...ts.sys, onUnRecoverableConfigFileDiagnostic: fail });
  if (!parsed) throw new Error(`${config}: not read`);
  parsed.errors.forEach(fail);
  const source = readFileSync(CONSTANTS, "utf8");
  if (source.split(typedLine(PKG_VERSION)).length !== 2) throw new Error(`src/constants.ts has no single line: ${typedLine(PKG_VERSION)}`);
  const text = source.replace(typedLine(PKG_VERSION), line(version));
  const host = ts.createCompilerHost(parsed.options);
  const read = host.getSourceFile.bind(host);
  host.getSourceFile = (name, target, onError, fresh) => {
    if (name === CONSTANTS.split("\\").join("/")) return ts.createSourceFile(name, text, target);
    const key = `${name}|${JSON.stringify(target)}`;
    if (!libFiles.has(key)) libFiles.set(key, read(name, target, onError, fresh));
    return libFiles.get(key);
  };
  const program = ts.createProgram({ rootNames: [CONSTANTS], options: parsed.options, host });
  ts.getPreEmitDiagnostics(program).forEach(fail);
  const out: string[] = [];
  const result = program.emit(undefined, (name, data) => name.endsWith("/constants.d.ts") && out.push(data), undefined, true);
  if (result.emitSkipped || out.length !== 1) throw new Error(`${config}: constants.d.ts not emitted`);
  return out[0];
}

function walk(dir: string): string[] {
  return readdirSync(dir).flatMap((name) => (statSync(join(dir, name)).isDirectory() ? walk(join(dir, name)) : [join(dir, name)]));
}

const pins = (regex: string) => !PROBES.some((p) => new RegExp(regex).test(p));
const pinned = (rule: Rule) => !/[*?]/.test(rule.path ?? "*") || (["old", "new"] as const).some((s) => s in rule && pins(rule[s] as string));

describe("TypeScript E-NEW entries (signed and overlay)", () => {
  it("the client has entries, every one in exactly one of the two files", () => {
    expect(SIGNED.length).toBeGreaterThanOrEqual(13);
    const ids = PORT.map((e) => e.id);
    expect(new Set(ids).size).toBe(ids.length);
    expect(OVERLAY.recorded_at).toBe("typescript-overlay-source");
    expect(SIGNED.every((e) => e.status === "proven")).toBe(true);
    expect(OVERLAY.differences.every((e) => e.status === "landed")).toBe(true);
  });

  it("every entry is well formed, for the two TypeScript client comparisons only", () => {
    for (const e of PORT) {
      expect(e.id).toMatch(PORT_ID);
      expect([e.id, e.lang, e.applies_to]).toEqual([e.id, "ts", ["ts-client-1.0.1-*->e-new-ts-*"]]);
      expect(e.summary.length).toBeGreaterThan(40);
      expect(e.evidence.length).toBeGreaterThan(40);
      expect(["landed", "proven"]).toContain(e.status);
      if (e.status === "landed") expect(e.reviewer).toBeNull();
      else {
        for (const k of ["by", "record", "verdict"] as const) expect(String(e.reviewer?.[k] ?? "").trim()).not.toBe("");
        expect(() => assertRetainedReview(e)).not.toThrow();
      }
      expect(e.match.length).toBeGreaterThan(0);
      for (const rule of e.match) {
        expect(Object.keys(rule).every((k) => ["path", "kind", "old", "new", "top_level"].includes(k))).toBe(true);
        expect(["any", "changed", "added", "removed"]).toContain(rule.kind ?? "any");
        for (const s of ["old", "new"] as const) if (s in rule) expect(() => new RegExp(rule[s] as string)).not.toThrow();
      }
    }
  });

  it("a retained review rejects different metadata or comparison rules", () => {
    const original = SIGNED[0];
    expect(() => assertRetainedReview({ ...original, reviewer: { ...original.reviewer!, record: "unrelated-review" } })).toThrow();
    expect(() => assertRetainedReview({ ...original, match: [...original.match, { path: "*" }] })).toThrow();
    expect(() => assertRetainedReview({ ...original, reviewer: null })).toThrow();
  });

  it("no overlay id is in the shared list or in intended-differences-ts.json", () => {
    const taken = new Set([...SHARED.differences, ...TS_LIST.differences].map((d) => d.id));
    expect(OVERLAY.differences.filter((e) => taken.has(e.id)).map((e) => e.id)).toEqual([]);
    const listed = new Set(TS_LIST.differences.map((d) => d.id));
    expect(SIGNED.filter((e) => listed.has(e.id)).map((e) => e.id)).toEqual([]);
  });

  it("the id rule bites", () => {
    for (const id of ["D-03-ts", "D-11b-ts", "TS-1.5-cache-only-config", "TS-3.2-dts-surface"]) expect(id).toMatch(PORT_ID);
    for (const id of ["D-03", "D-03-py", "PY-1.3-new-names", "D-11b", "TS-x", "ts-1.5-a"]) expect(id).not.toMatch(PORT_ID);
  });

  it("every rule names an exact path, or pins a value with a regex that pins", () => {
    const loose = PORT.flatMap((e) => e.match.filter((r) => !pinned(r)).map((r) => [e.id, r.path]));
    expect(loose).toEqual([]);
  });

  it("the pinning check bites", () => {
    expect(pinned({ path: "stream.*" })).toBe(false);
    expect(pinned({ path: "*", new: ".*" })).toBe(false);
    expect(pinned({ path: "*/headers/*", new: "\\s*" })).toBe(false);
    expect(pinned({ path: "env.base_url.x/requests/0/path" })).toBe(true);
    expect(pinned({ path: "*/headers/user-agent", new: "^futureagi-typescript/" })).toBe(true);
  });

  it("D-03-ts pins the new version values by the version's shape, the 1.0.1 values exactly", () => {
    const d03 = SIGNED.find((e) => e.id === "D-03-ts");
    expect(d03).toBeDefined();
    for (const rule of d03!.match) {
      const re = new RegExp(rule.new as string);
      const value = rule.path?.toLowerCase().endsWith("user-agent") ? (v: string) => `futureagi-typescript/${v}` : (v: string) => v;
      for (const v of ["0.1.2", "0.2.0", "1.0.0-rc.1"]) expect([rule.path, v, re.test(value(v))]).toEqual([rule.path, v, true]);
      for (const v of ["1.0", "x.y.z", "0.1.2 extra"]) expect([rule.path, v, re.test(value(v))]).toEqual([rule.path, v, false]);
      expect(rule.old).toMatch(/1\\\.0\\\.1\$$/);
    }
  });

  it("no other rule of the client names the version this tree ships", () => {
    // The version shape D-03-ts's new-value rules take (a pre-release suffix included).
    expect(PKG_VERSION).toMatch(/^\d+\.\d+\.\d+[^"' ]*$/);
    const named = PORT.flatMap((e) =>
      e.match.flatMap((r, i) => (["old", "new"] as const).filter((s) => String(r[s] ?? "").split("\\").join("").includes(PKG_VERSION)).map((s) => `${e.id}: rule ${i} ${s}`)),
    );
    expect(named).toEqual([]);
  });

  it("no source file but src/constants.ts holds the version, which it declares string", () => {
    const literal = new RegExp(`(?<![0-9.])${PKG_VERSION.split(".").join("\\.")}(?![0-9])`);
    const holders = walk(join(ROOT, "src")).filter((f) => literal.test(readFileSync(f, "utf8")));
    expect(holders).toEqual([CONSTANTS]);
    expect(readFileSync(CONSTANTS, "utf8").split(typedLine(PKG_VERSION)).length).toBe(2);
    expect(readFileSync(join(ROOT, "scripts", "build.cjs"), "utf8")).toContain("export const VERSION: string = \"${pkgVersion}\";");
  });

  it("a version bump leaves constants.d.ts, and TS-3.2-dts-surface's sha256 pins of it, as they are", () => {
    expect(readFileSync(join(ROOT, "tests", "parity", "harness", "dts.mjs"), "utf8")).toContain(DTS_NORMALISE);
    const ts32 = SIGNED.find((e) => e.id === "TS-3.2-dts-surface");
    for (const [format, config] of [["esm", "tsconfig.esm.json"], ["cjs", "tsconfig.cjs.json"]]) {
      const pin = ts32?.match.find((r) => r.path === `<index>/dts/@agentcc/client/dist/${format}/constants.d.ts/sha256`);
      expect([format, pin?.kind, typeof pin?.new]).toEqual([format, "changed", "string"]);
      const texts = [PKG_VERSION, nextMinor(PKG_VERSION), "10.0.0-rc.1"].map((v) => emitConstantsDts(config, v));
      expect([format, new Set(texts).size]).toEqual([format, 1]);
      expect(texts[0]).toContain("export declare const VERSION: string;");
      expect([format, texts[0].includes(PKG_VERSION)]).toEqual([format, false]);
      expect([format, dtsSha(texts[0]), new RegExp(pin!.new as string).test(dtsSha(texts[0]))]).toEqual([format, dtsSha(texts[0]), true]);
    }
  });

  it("the bump check bites: with a literal-typed VERSION, the declaration file changes with the version", () => {
    const [a, b] = [PKG_VERSION, nextMinor(PKG_VERSION)].map((v) => emitConstantsDts("tsconfig.esm.json", v, literalLine));
    expect(a).toContain(`export declare const VERSION = "${PKG_VERSION}";`);
    expect(dtsSha(a)).not.toBe(dtsSha(b));
  });

  it("entries that change what a 1.x caller sends carry a migration line", () => {
    const byId = new Map(PORT.map((e) => [e.id, e]));
    for (const id of MIGRATION) {
      const e = byId.get(id);
      expect([id, typeof e?.migration === "string" && e.migration.length > 40]).toEqual([id, true]);
      expect([id, e?.summary.includes("Migration:")]).toEqual([id, true]);
    }
    expect(PORT.filter((e) => "migration" in e).map((e) => e.id).sort()).toEqual([...MIGRATION].sort());
  });

  it("every entry's test id names a test in the tree", () => {
    for (const e of PORT) {
      const [file, name] = e.test_id.split("::");
      expect([e.id, file.startsWith("typescript/futureagi/gateway-client/tests/")]).toEqual([e.id, true]);
      expect([e.id, existsSync(join(REPO, file))]).toEqual([e.id, true]);
      const source = readFileSync(join(REPO, file), "utf8");
      for (const title of name.split(" > ")) expect([e.id, title, source.includes(JSON.stringify(title))]).toEqual([e.id, title, true]);
    }
  });
});
