#!/usr/bin/env node
/** Content-addressed provenance for a private input. Repository revisions never enter public output. */
import { createHash } from "node:crypto";
import { readFileSync, writeFileSync } from "node:fs";
import { pathToFileURL } from "node:url";

const LABEL = "enterprise customer contract";
const KEYS = new Set(["contract", "source_label", "source_digest", "pinned", "scope", "scoped"]);
export function sourceProvenance(source) {
  if (Object.keys(source).some((key) => !KEYS.has(key)) || source.source_label !== LABEL ||
      !/^sha256:[a-f0-9]{64}$/.test(source.source_digest ?? "")) {
    throw new Error("source provenance must contain only a neutral label and SHA256 content digest");
  }
  return { source_label: LABEL, source_digest: source.source_digest };
}
export const contentDigest = (bytes) => `sha256:${createHash("sha256").update(bytes).digest("hex")}`;
export function verifyInput(source, bytes) {
  sourceProvenance(source);
  if (contentDigest(bytes) !== source.source_digest) throw new Error("source input content digest mismatch");
}

// Migration and rebuild both verify exact input bytes before writing. Only the known
// metadata keys are projected: legacy revision, repository and source path are not copied.
export function pinInput(source, input, scoped) {
  const expected = source.source_digest ?? `sha256:${source.sha256}`;
  if (!/^sha256:[a-f0-9]{64}$/.test(expected) || contentDigest(input) !== expected) {
    throw new Error("source input content digest mismatch");
  }
  return {
    contract: "Future AGI platform customer contract (OpenAPI 3.1)",
    source_label: LABEL,
    source_digest: contentDigest(input),
    pinned: source.pinned,
    scope: "openapi/platform/scope.json",
    scoped: { path: "openapi/platform/generated/futureagi-platform.openapi.json", sha256: contentDigest(scoped).slice(7) },
  };
}

export function main(argv) {
  const [mode, sourcePath, inputPath, scopedPath] = argv;
  const source = JSON.parse(readFileSync(sourcePath, "utf8"));
  const input = readFileSync(inputPath);
  if (mode === "verify") verifyInput(source, input);
  else if (mode === "pin" && scopedPath) writeFileSync(sourcePath, `${JSON.stringify(pinInput(source, input, readFileSync(scopedPath)), null, 2)}\n`);
  else throw new Error("usage: source-pin.mjs verify|pin source.json input.json [scoped.json]");
}
if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) main(process.argv.slice(2));
