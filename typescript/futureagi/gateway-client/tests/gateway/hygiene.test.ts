/**
 * The build root's own rules:
 *
 * - Import boundary: src/** imports only its own files, plus `react` and only
 *   under src/react/. No node:* module, no openai, axios, winston, form-data
 *   or uuid, nothing from the root package (typescript/futureagi/src), so
 *   every subpath runs in browsers and edge runtimes and installs nothing.
 *   The esbuild metafiles of the packed tarball check the built output too
 *   (scripts/consumer/check-metafile.cjs).
 * - process.env is read in one place, behind a typeof process guard.
 * - Every module is 400 lines or fewer.
 */
import { describe, it, expect } from "@jest/globals";
import { readdirSync, readFileSync, statSync } from "node:fs";
import { dirname, join, relative, resolve, sep } from "node:path";
import ts from "typescript";

const SRC = resolve(__dirname, "..", "..", "src");

function walk(dir: string): string[] {
  return readdirSync(dir).flatMap((name) => {
    const path = join(dir, name);
    return statSync(path).isDirectory() ? walk(path) : /\.tsx?$/.test(name) ? [path] : [];
  });
}

const FILES = walk(SRC);
const rel = (file: string) => relative(SRC, file).split(sep).join("/");

function specifiers(file: string): string[] {
  const info = ts.preProcessFile(readFileSync(file, "utf8"), true, true);
  return info.importedFiles.map((f) => f.fileName);
}

describe("gateway-client hygiene", () => {
  it("finds the sources", () => {
    expect(FILES.length).toBeGreaterThan(40);
    expect(FILES.map(rel)).toContain("react/index.ts");
  });

  it.each(FILES.map(rel))("%s imports only files inside src (and react under src/react/)", (name) => {
    const file = join(SRC, name);
    const bad: string[] = [];
    for (const spec of specifiers(file)) {
      if (spec.startsWith(".")) {
        const target = resolve(dirname(file), spec);
        if (!target.startsWith(SRC + sep)) bad.push(`${spec} leaves src/`);
        else if (!/\.js$/.test(spec)) bad.push(`${spec} has no .js suffix (ES module resolution needs it)`);
      } else if (spec === "react") {
        if (!name.startsWith("react/")) bad.push(`react outside src/react/`);
      } else {
        bad.push(`bare import ${spec}`);
      }
    }
    expect(bad).toEqual([]);
  });

  it("process.env is read only in env.ts, behind a typeof process guard", () => {
    const readers = FILES.filter((f) => /\bprocess\./.test(readFileSync(f, "utf8"))).map(rel);
    expect(readers).toEqual(["env.ts"]);
    expect(readFileSync(join(SRC, "env.ts"), "utf8")).toMatch(/typeof process === "undefined"/);
  });

  it.each(FILES.map(rel))("%s is 400 lines or fewer", (name) => {
    const lines = readFileSync(join(SRC, name), "utf8").split("\n").length - 1;
    expect(lines).toBeLessThanOrEqual(400);
  });
});
