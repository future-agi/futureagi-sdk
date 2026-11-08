/**
 * The public surface of every subpath, values and types (D-21).
 * api-snapshot.json is the checked-in list; a change to any
 * subpath's exports fails here until the snapshot is updated on purpose
 * (GW_UPDATE_SNAPSHOT=1 rewrites it). Every runtime export of @agentcc/client
 * 1.0.1 (the parity golden ts-client-1.0.1-esm/index.json) and of @agentcc/react
 * 1.0.0 (ts-integrations-1.0.0-esm/index.json) is either still exported or
 * listed under "removed" with the delta that removed it.
 */
import { describe, it, expect } from "@jest/globals";
import { readFileSync, writeFileSync } from "node:fs";
import { join } from "node:path";
import ts from "typescript";

const ROOT = join(__dirname, "..", "..");
const SNAPSHOT = join(__dirname, "api-snapshot.json");
const GOLDENS = join(ROOT, "..", "..", "..", "tests", "fixtures", "gateway", "golden");
// @agentcc/client's subpaths against the 1.0.1 golden; @agentcc/react against
// the published 1.0.0 (the ts-integrations golden).
const GOLDEN: Record<string, string> = {
  "./gateway": join(GOLDENS, "ts-client-1.0.1-esm", "index.json"),
  "./gateway/testing": join(GOLDENS, "ts-client-1.0.1-esm", "index.json"),
  "./gateway/express": join(GOLDENS, "ts-client-1.0.1-esm", "index.json"),
  "./gateway/nextjs": join(GOLDENS, "ts-client-1.0.1-esm", "index.json"),
  "./gateway/react": join(GOLDENS, "ts-integrations-1.0.0-esm", "index.json"),
};

export const SUBPATHS: Record<string, string> = {
  "./gateway": "src/index.ts",
  "./gateway/testing": "src/testing.ts",
  "./gateway/express": "src/express.ts",
  "./gateway/nextjs": "src/nextjs.ts",
  "./gateway/react": "src/react/index.ts",
};
const OLD_SPEC: Record<string, string> = {
  "./gateway": "@agentcc/client",
  "./gateway/testing": "@agentcc/client/testing",
  "./gateway/express": "@agentcc/client/express",
  "./gateway/nextjs": "@agentcc/client/nextjs",
  "./gateway/react": "@agentcc/react",
};

interface Snapshot {
  about: string;
  subpaths: Record<string, Record<string, "value" | "type" | "value+type">>;
  removed: Record<string, Record<string, string>>;
}

function surface(): Snapshot["subpaths"] {
  const files = Object.values(SUBPATHS).map((f) => join(ROOT, f));
  const program = ts.createProgram(files, {
    target: ts.ScriptTarget.ES2022,
    module: ts.ModuleKind.ES2022,
    moduleResolution: ts.ModuleResolutionKind.Bundler,
    strict: true,
    skipLibCheck: true,
    types: ["node"],
    noEmit: true,
  });
  const checker = program.getTypeChecker();
  const out: Snapshot["subpaths"] = {};
  for (const [sub, file] of Object.entries(SUBPATHS)) {
    const source = program.getSourceFile(join(ROOT, file));
    if (!source) throw new Error(`no source for ${file}`);
    const mod = checker.getSymbolAtLocation(source);
    const names: Record<string, "value" | "type" | "value+type"> = {};
    for (const sym of checker.getExportsOfModule(mod!)) {
      const target = sym.flags & ts.SymbolFlags.Alias ? checker.getAliasedSymbol(sym) : sym;
      const value = (target.flags & ts.SymbolFlags.Value) !== 0;
      const type = (target.flags & (ts.SymbolFlags.Type | ts.SymbolFlags.Interface | ts.SymbolFlags.TypeAlias)) !== 0;
      names[sym.getName()] = value && type ? "value+type" : value ? "value" : "type";
    }
    out[sub] = Object.fromEntries(Object.entries(names).sort(([a], [b]) => a.localeCompare(b)));
  }
  return out;
}

describe("API snapshot", () => {
  const now = surface();
  const snap = JSON.parse(readFileSync(SNAPSHOT, "utf8")) as Snapshot;
  if (process.env.GW_UPDATE_SNAPSHOT === "1") {
    snap.subpaths = now;
    writeFileSync(SNAPSHOT, JSON.stringify(snap, null, 1) + "\n");
  }

  it.each(Object.keys(SUBPATHS))("%s exports exactly the snapshot", (sub) => {
    expect(now[sub]).toEqual(snap.subpaths[sub]);
  });

  it.each(Object.keys(SUBPATHS))("every 1.0.1 runtime export of %s is kept or removed by a named delta", (sub) => {
    const golden = JSON.parse(readFileSync(GOLDEN[sub], "utf8")) as { loads: Record<string, { exports: string[] } | string[]> };
    const load = golden.loads[OLD_SPEC[sub]];
    const old = Array.isArray(load) ? load : load.exports;
    const removed = snap.removed[sub] ?? {};
    const unaccounted = old.filter((name) => !(name in now[sub]) && !(name in removed));
    expect(unaccounted).toEqual([]);
    const stale = Object.keys(removed).filter((name) => name in now[sub] || !old.includes(name));
    expect(stale).toEqual([]);
    for (const why of Object.values(removed)) expect(why).toMatch(/^D-\d\d/);
  });
});
