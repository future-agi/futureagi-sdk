#!/usr/bin/env node
/**
 * TSDoc on every public symbol of the platform TypeScript modules (the docs pages are written from it).
 * Loads each entry with the package's own TypeScript compiler, walks every export, and for classes and
 * interfaces every public member declared in the module's own sources; each must carry a doc comment.
 * A member is reported once, under the class or interface that declares it (an inherited member is the
 * base's gap, not every subclass's).
 *
 * `tsdoc-baseline.json` lists the gaps known when a module landed, by module directory under `src/`
 * (`_core`, `deployments`, ...). They are reported but do not fail; a new gap fails, and so does a
 * listed gap that is now documented or gone, so the list can only shrink.
 *
 *   node scripts/platform/lint/tsdoc-coverage.mjs [entry.ts ...]
 *
 * Default entries: `typescript/futureagi/src/<namespace>/index.ts` and `src/_core/index.ts` where they
 * exist. TypeScript is loaded from `typescript/futureagi/node_modules` (run `npm ci` there first).
 */

import { existsSync, readFileSync } from "node:fs";
import { createRequire } from "node:module";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { NAMESPACES, REPO } from "./roots.mjs";

const PACKAGE = path.join(REPO, "typescript/futureagi");
const BASELINE = new URL("./tsdoc-baseline.json", import.meta.url);

export function coverage(entryFile, ts) {
  const program = ts.createProgram([entryFile], {
    module: ts.ModuleKind.CommonJS,
    moduleResolution: ts.ModuleResolutionKind.Node10,
    target: ts.ScriptTarget.ES2022,
    strict: true,
    noEmit: true,
    skipLibCheck: true
  });
  const checker = program.getTypeChecker();
  const source = program.getSourceFile(entryFile);
  const ownRoot = path.dirname(entryFile);
  const ownDecl = (d) => path.resolve(d.getSourceFile().fileName).startsWith(ownRoot);
  const hasDoc = (sym) => sym.getDocumentationComment(checker).length > 0 || sym.getJsDocTags(checker).length > 0;
  const missing = new Set();
  let checked = 0;
  for (const exported of checker.getExportsOfModule(checker.getSymbolAtLocation(source))) {
    const sym = exported.flags & ts.SymbolFlags.Alias ? checker.getAliasedSymbol(exported) : exported;
    if ((sym.declarations ?? []).filter(ownDecl).length === 0) continue;
    checked += 1;
    if (!hasDoc(sym)) missing.add(exported.name);
    if (sym.flags & (ts.SymbolFlags.Class | ts.SymbolFlags.Interface)) {
      for (const member of checker.getPropertiesOfType(checker.getDeclaredTypeOfSymbol(sym))) {
        const decls = (member.declarations ?? []).filter(ownDecl);
        if (decls.length === 0) continue;
        const hidden = decls.some(
          (d) => (ts.getCombinedModifierFlags(d) & (ts.ModifierFlags.Private | ts.ModifierFlags.Protected)) !== 0 || d.name?.kind === ts.SyntaxKind.PrivateIdentifier
        );
        if (hidden) continue;
        checked += 1;
        const owner = decls[0].parent?.name?.text ?? exported.name;
        // a well-known symbol member (`[Symbol.asyncIterator]`) has a compiler-numbered internal name
        const name = member.name.replace(/^__@(\w+)@\d+$/u, "[Symbol.$1]");
        if (!hasDoc(member)) missing.add(`${owner}.${name}`);
      }
    }
  }
  return { checked, missing: [...missing].sort() };
}

/**
 * Split the gaps of each entry by the baseline: `failures` (new gaps), `known` (listed gaps still
 * open) and `stale` (listed gaps that are documented or gone now; they fail too).
 */
export function applyBaseline(missingByEntry, baseline) {
  const failures = [];
  const known = [];
  const stale = [];
  for (const [entry, missing] of Object.entries(missingByEntry)) {
    const listed = new Set(baseline[entry] ?? []);
    for (const name of missing) (listed.has(name) ? known : failures).push(`${entry}: ${name}`);
    for (const name of listed) if (!missing.includes(name)) stale.push(`${entry}: ${name}`);
  }
  return { failures, known, stale };
}

export function defaultEntries() {
  return ["_core", ...NAMESPACES].map((n) => path.join(PACKAGE, "src", n, "index.ts")).filter((f) => existsSync(f));
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const given = process.argv.slice(2).map((f) => path.resolve(REPO, f));
  const entries = given.length > 0 ? given : defaultEntries();
  if (entries.length === 0) {
    process.stdout.write("tsdoc-coverage: no platform TypeScript entry exists yet; 0 symbols checked\n");
    process.exit(0);
  }
  const ts = createRequire(path.join(PACKAGE, "package.json"))("typescript");
  const baseline = JSON.parse(readFileSync(BASELINE, "utf8")).known;
  let total = 0;
  const missingByEntry = {};
  for (const entry of entries) {
    const result = coverage(entry, ts);
    total += result.checked;
    // keyed by the module directory under src/ (`_core`, `deployments`, ...): the entry is its index
    missingByEntry[path.relative(path.join(PACKAGE, "src"), path.dirname(entry))] = result.missing;
  }
  const { failures, known, stale } = applyBaseline(missingByEntry, baseline);
  for (const name of failures) process.stderr.write(`tsdoc-coverage: no doc comment on ${name}\n`);
  for (const name of stale) process.stderr.write(`tsdoc-coverage: documented or gone now, remove it from tsdoc-baseline.json: ${name}\n`);
  process.stdout.write(
    `tsdoc-coverage: ${total} public symbols checked, ${failures.length} new gap(s), ${stale.length} stale baseline entr(ies), ${known.length} known gap(s) listed in tsdoc-baseline.json\n`
  );
  process.exit(failures.length === 0 && stale.length === 0 ? 0 : 1);
}
