/** Refuse repository-local history overlays before inspecting objects or moving an export ref. */
import { execFileSync } from "node:child_process";
import { lstatSync } from "node:fs";
import path from "node:path";

export function assertRealHistory(cwd) {
  if (Object.hasOwn(process.env, "GIT_REPLACE_REF_BASE")) {
    throw new Error("history overrides are not allowed: GIT_REPLACE_REF_BASE is set");
  }
  const git = (...args) => execFileSync("git", args, {
    cwd, encoding: "utf8", env: { ...process.env, GIT_NO_REPLACE_OBJECTS: "1" },
    stdio: ["ignore", "pipe", "pipe"]
  }).trim();
  if (git("for-each-ref", "--format=%(refname)", "refs/replace/")) {
    throw new Error("history overrides are not allowed: refs/replace is non-empty");
  }
  // Git resolves common-dir paths for linked worktrees. Even an empty file or dangling symlink is refused.
  const grafts = path.resolve(cwd, git("rev-parse", "--git-path", "info/grafts"));
  try {
    lstatSync(grafts);
  } catch (error) {
    if (error.code === "ENOENT") return;
    throw error;
  }
  throw new Error("history overrides are not allowed: info/grafts exists");
}
