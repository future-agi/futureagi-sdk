/** Share one structural lockfile projection with the Python scanner. Never skip a whole file. */
import { execFileSync } from "node:child_process";
import path from "node:path";
import { fileURLToPath } from "node:url";

const helper = fileURLToPath(new URL("./hygiene_lockfiles.py", import.meta.url));
const names = new Set(["package-lock.json", "pnpm-lock.yaml", "pnpm-lock.yml", "pnpm-lock", "poetry.lock", "uv.lock"]);

export function lockfileProjection(file, text) {
  if (!names.has(path.basename(file))) return { text, hits: [] };
  try {
    const output = execFileSync("python3", ["-I", helper, file], { input: text, encoding: "utf8", maxBuffer: 64 * 1024 * 1024, timeout: 30000, stdio: ["pipe", "pipe", "pipe"] });
    const result = JSON.parse(output);
    if (typeof result.text !== "string") throw new Error("no structural projection");
    return { text: result.text, hits: [] };
  } catch {
    return { text, hits: [{ rule: "invalid-lockfile", line: 0, text: "lockfile could not be parsed structurally; install scripts/platform/requirements-hygiene.txt" }] };
  }
}
