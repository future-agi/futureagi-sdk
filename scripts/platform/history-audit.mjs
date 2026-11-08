/**
 * What a push of an export would make public, audited before any export ref moves and again at
 * push time (`export-verify.mjs`). A clean tip is not enough: every commit under it is published too.
 *
 * The commits audited are those the export adds to the public revisions: `git rev-list <export>
 * --not <public> ...`. A revision that is not named as public (an earlier export, a dry run, a
 * commit id) is never trusted; its commits are audited like new ones. For each commit:
 * - its message is scanned with the checks the export's own messages pass (`scanMessage`);
 * - its author and committer must be the export identity, when one is given;
 * - every entry it introduces is scanned, path name included: an entry whose mode or object differs
 *   from that path in each of its parents (every entry of a root commit). An entry equal to one in a
 *   parent came from that parent, which is public or audited in turn, so nothing reaches the public
 *   history unscanned, and content already public is not scanned again.
 * A shallow boundary in the unpublished range is an error, not a root: the audit needs complete
 * ancestry. Boundaries already reachable from trusted public revisions are excluded with that range.
 * Whole-tree rule-file findings (stale exemptions and reviews) are left to the full scan of the tip.
 * A hit is `{ commit, file, line, rule, text, generated }`; `file` is "message", "author" or
 * "committer" for commit metadata.
 */

import { execFileSync } from "node:child_process";
import { readFileSync } from "node:fs";
import path from "node:path";
import { assertRealHistory } from "./git-history-guard.mjs";
import { scanMessage } from "./hygiene-scan.mjs";
import { scanContext, scanEntries, treeEntries } from "./hygiene-tree.mjs";

function git(cwd, args) {
  return execFileSync("git", args, { cwd, env: { ...process.env, GIT_NO_REPLACE_OBJECTS: "1" }, encoding: "utf8", maxBuffer: 1024 * 1024 * 1024, stdio: ["ignore", "pipe", "pipe"] }).trim();
}

/** The paths that differ between two trees (or commits): `{ path, mode, oid, deleted }`. */
export function changedPaths(cwd, fromTree, toTree) {
  const out = git(cwd, ["diff-tree", "-r", "-z", "--no-renames", "--no-commit-id", fromTree, toTree]);
  const fields = out.split("\0").filter((f) => f !== "");
  const changes = [];
  for (let i = 0; i < fields.length; i += 2) {
    const [, newMode, , newOid, status] = fields[i].slice(1).split(" ");
    changes.push({ path: fields[i + 1], mode: newMode, oid: newOid, deleted: status === "D" });
  }
  return changes;
}

/** Git resolves the shared shallow file for both ordinary and linked worktrees. */
function shallowCommits(cwd) {
  const file = path.resolve(cwd, git(cwd, ["rev-parse", "--git-path", "shallow"]));
  try {
    return new Set(readFileSync(file, "utf8").split(/\s+/u).filter(Boolean));
  } catch (error) {
    if (error.code === "ENOENT") return new Set();
    throw error;
  }
}

/** The commits `head` adds to `publicCommits`, parents before children: `{ commit, parents }`. */
export function newCommits(cwd, head, publicCommits) {
  assertRealHistory(cwd);
  const shallow = shallowCommits(cwd);
  const out = git(cwd, ["rev-list", "--reverse", "--topo-order", "--parents", head, "--not", ...publicCommits]);
  return out
    .split("\n")
    .filter(Boolean)
    .map((line) => {
      const [commit, ...parents] = line.split(" ");
      // rev-list hides every parent of a shallow boundary, even when its objects exist locally.
      // Only boundaries excluded by the trusted public range may remain unaudited.
      if (shallow.has(commit)) {
        throw new Error(`incomplete unpublished ancestry: shallow commit ${commit}; obtain its missing ancestry before exporting or verifying`);
      }
      return { commit, parents };
    });
}

/** The entries `commit` introduces (see above), as `{ mode, type, oid, path }`. */
export function introducedEntries(cwd, commit, parents) {
  if (parents.length === 0) return treeEntries(commit, cwd);
  let introduced = null;
  for (const parent of parents) {
    const changed = new Map(changedPaths(cwd, parent, commit).filter((c) => !c.deleted).map((c) => [c.path, c]));
    introduced = introduced === null ? changed : new Map([...introduced].filter(([p]) => changed.has(p)));
  }
  return [...introduced.values()].map((c) => ({ mode: c.mode, type: c.mode === "160000" ? "commit" : "blob", oid: c.oid, path: c.path }));
}

function metadata(cwd, commit) {
  const [an, ae, cn, ce, message] = git(cwd, ["show", "-s", "--format=%an%x00%ae%x00%cn%x00%ce%x00%B", commit]).split("\0");
  return { author: { name: an, email: ae }, committer: { name: cn, email: ce }, message };
}

/**
 * The audit of everything `head` would publish beyond `publicCommits`, under the rules the qualified
 * revision carries. Returns `{ commits, entries, hits }`; `identity` is `{ name, email }` or null.
 */
export function auditHistory(cwd, { head, publicCommits, platform, tree, identity = null, localOnly }) {
  const commits = newCommits(cwd, head, publicCommits);
  const ctx = scanContext({ cwd, platform, tree, localOnly });
  const hits = [];
  let entries = 0;
  try {
    for (const { commit, parents } of commits) {
      const meta = metadata(cwd, commit);
      for (const h of scanMessage(meta.message, platform, tree)) hits.push({ commit, file: "message", line: h.line, rule: h.rule, text: h.text, generated: false });
      for (const role of identity ? ["author", "committer"] : []) {
        const who = meta[role];
        if (who.name !== identity.name || who.email !== identity.email) {
          hits.push({ commit, file: role, line: 0, rule: "foreign-identity", text: `${who.name} <${who.email}>`, generated: false });
        }
      }
      const introduced = introducedEntries(cwd, commit, parents);
      entries += introduced.length;
      for (const h of scanEntries(introduced, ctx, cwd)) hits.push({ commit, ...h });
    }
  } finally { ctx.verifyProvenance.close(); }
  return { commits: commits.length, entries, hits };
}

/** The report line of one audit hit. */
export const auditLine = (h) => `${h.commit.slice(0, 12)} ${h.file}:${h.line} ${h.rule} ${h.text}`;
