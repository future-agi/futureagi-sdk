/**
 * The platform source roots the lints read, relative to the repository root. A root that does not exist
 * yet (a namespace whose module is not written yet) is skipped and named in the lint's output.
 */

import path from "node:path";
import { fileURLToPath } from "node:url";

export const REPO = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../../..");
export const NAMESPACES = ["deployments", "sandboxes", "agents", "environments", "workspace", "gateway", "connectors"];

/** Hand-written platform modules, both languages (no generated code, no tests). */
export const SOURCE_ROOTS = [
  "python/fi/_core",
  ...NAMESPACES.map((n) => `python/fi/${n}`),
  "typescript/futureagi/src/_core",
  ...NAMESPACES.map((n) => `typescript/futureagi/src/${n}`)
];

/** Everything the 400-line rule covers: the sources plus the platform tooling and tests. */
export const SIZE_ROOTS = [...SOURCE_ROOTS, "python/fi/evals", "python/tests/evals", "scripts/platform", "python/tests/platform", "python/tests/core", "tests/platform-conformance"];
