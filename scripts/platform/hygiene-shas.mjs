/**
 * Commit ids in public text. A public reader cannot open a commit that lives only in a private
 * repository or on a local branch, so every commit-like token in a scanned file must be accounted for.
 *
 * A token is a run of 7 to 40 hex characters with at least one digit and at least one letter,
 * bounded by non-alphanumeric characters (including underscores and dashes). Complete UUIDs are
 * excluded, but tagged revisions are not. A token is a hit (`unreviewed-sha`) unless:
 *
 * - it is a provenance value verified against anonymous public-remote ancestry during this scan;
 *   a place-only pin never grants clearance;
 * - it is the value of an exact content-digest key (`shas.digestKeys`: case-insensitive key names
 *   mapped to allowed full hexadecimal lengths). Both the key and the value's length must match,
 *   such as a package's 40-character `shasum`; ambiguous revision keys are not digest keys;
 * - it names a reviewed commit (`shas.reviewed`: the commit, its repository and why it may be named).
 *   A token matches an entry when one is a prefix of the other. A reviewed entry that no scanned file
 *   names is itself a hit (`stale-sha-review`), so the list cannot outlive its uses.
 *
 * Local refs never grant clearance. Provenance uses fresh anonymous public refs; `annotate` only
 * adds a note when a token resolves to a local commit that no remote branch contains.
 *
 *   node scripts/platform/hygiene-shas.mjs classify <scan.json> <clone> [<clone> ...]
 */

import { execFileSync } from "node:child_process";
import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const TOKEN = /(?<![0-9A-Za-z])[0-9a-f]{7,40}(?![0-9A-Za-z])/giu;
const UUID = /(?<![0-9A-Za-z])[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}(?![0-9A-Za-z])/giu;
const DIGIT = /[0-9]/u;
const LETTER = /[a-f]/iu;
const HEX = /^[0-9a-f]{7,40}$/iu;

/** The commit-like tokens of one line, as `{ token, index }`. */
export function shaTokens(line) {
  const out = [];
  const uuids = [...line.matchAll(UUID)].map((m) => [m.index, m.index + m[0].length]);
  for (const m of line.matchAll(TOKEN)) {
    if (uuids.some(([start, end]) => m.index >= start && m.index < end)) continue;
    if (DIGIT.test(m[0]) && LETTER.test(m[0])) out.push({ token: m[0], index: m.index });
  }
  return out;
}

/** A path glob as a regular expression: `**` crosses directories, `*` stays inside one segment. */
export function globRegExp(glob) {
  let re = "";
  for (let i = 0; i < glob.length; i += 1) {
    const c = glob[i];
    if (c === "*" && glob[i + 1] === "*") {
      re += ".*";
      i += 1;
    } else if (c === "*") {
      re += "[^/]*";
    } else {
      re += c.replace(/[.+?^${}()|[\]\\]/gu, "\\$&");
    }
  }
  return new RegExp(`^${re}$`, "u");
}

/** Whether `file` matches one of the globs. */
export function matchesAny(file, globs) {
  return (globs ?? []).some((g) => globRegExp(g).test(file));
}

// Bind exemptions to this occurrence, not another equal token elsewhere on the line.
function valueKey(line, token, index) {
  for (const m of line.matchAll(/(["'])([^"']+)\1\s*:\s*(["'])([0-9a-f]+)\3/giu)) {
    const start = m.index + m[0].length - m[4].length - 1;
    if (start === index && m[4] === token) return m[2];
  }
  return null;
}

const DIGEST_LENGTHS = new Set([32, 40, 64, 96, 128]);
const validDigestLengths = (lengths) => Array.isArray(lengths) && lengths.length > 0 && lengths.every((n) => DIGEST_LENGTHS.has(n));

function isDigest(shas, key, token) {
  if (key === null || !shas?.digestKeys || Array.isArray(shas.digestKeys)) return false;
  return Object.entries(shas.digestKeys).some(([name, lengths]) => name.toLowerCase() === key.toLowerCase() && validDigestLengths(lengths) && lengths.includes(token.length));
}

function reviewedEntry(shas, token) {
  const lower = token.toLowerCase();
  return (shas?.reviewed ?? []).find((e) => typeof e.sha === "string" && (e.sha.toLowerCase().startsWith(lower) || lower.startsWith(e.sha.toLowerCase())));
}

/**
 * The SHA hits of one line of `file`. `used` collects the reviewed entries the line matched, for the
 * stale check.
 */
export function shaHits(file, line, shas, used, verified = new Set()) {
  const hits = [];
  for (const { token, index } of shaTokens(line)) {
    const key = valueKey(line, token, index);
    if (verified.has(index) || isDigest(shas, key, token)) continue;
    const provenance = ["commit", "revision", "backend_revision"].includes(key);
    const entry = provenance ? null : reviewedEntry(shas, token);
    if (entry) {
      used.add(entry);
      continue;
    }
    hits.push({ rule: "unreviewed-sha", text: token });
  }
  return hits;
}

/** Problems with the `shas` block itself, and reviewed entries no scanned file used. */
export function shaFindings(shas, used) {
  const out = [];
  if (shas?.digestKeys !== undefined) {
    if (!shas.digestKeys || typeof shas.digestKeys !== "object" || Array.isArray(shas.digestKeys)) {
      out.push({ rule: "invalid-digest-keys", text: "digestKeys must map exact key names to full hexadecimal lengths" });
    } else {
      for (const [key, lengths] of Object.entries(shas.digestKeys)) {
        if (!key || !validDigestLengths(lengths)) out.push({ rule: "invalid-digest-keys", text: "a digest key needs a name and full hexadecimal lengths (32, 40, 64, 96 or 128)" });
      }
    }
  }
  for (const pin of shas?.pins ?? []) {
    if (typeof pin.path !== "string" || !Array.isArray(pin.keys) || pin.keys.length === 0 || !pin.why) {
      out.push({ rule: "invalid-sha-pin", text: "a pin needs path, keys and why" });
    }
  }
  for (const e of shas?.reviewed ?? []) {
    if (typeof e.sha !== "string" || !HEX.test(e.sha) || !e.repository || !e.why) {
      out.push({ rule: "invalid-sha-review", text: "a reviewed commit needs sha (7 to 40 hex), repository and why" });
    } else if (!used.has(e)) {
      out.push({ rule: "stale-sha-review", text: `${e.sha.slice(0, 12)} (${e.repository}) is named by no scanned file` });
    }
  }
  return out;
}

/**
 * Commits of the local repository that no remote-tracking branch contains, as a lookup by prefix.
 * Used only to annotate hits; an empty set when `cwd` is not a repository.
 */
export function localOnlyCommits(cwd) {
  try {
    const out = execFileSync("git", ["rev-list", "--all", "--not", "--remotes"], {
      cwd,
      env: { ...process.env, GIT_NO_REPLACE_OBJECTS: "1" },
      encoding: "utf8",
      stdio: ["ignore", "pipe", "ignore"],
      maxBuffer: 64 * 1024 * 1024
    });
    return out.split("\n").filter(Boolean);
  } catch {
    return [];
  }
}

/** The note for a hit: whether the token names a local-only commit of this repository. */
export function annotate(token, localOnly) {
  return localOnly.some((sha) => sha.toLowerCase().startsWith(token.toLowerCase())) ? `${token} (a commit no remote branch contains)` : token;
}

/**
 * Classify the unreviewed commit ids of a scan against local clones, to help a reviewer: `public` when a
 * remote branch of that clone contains the commit (the clone's remote names the repository), `local-only`
 * when the clone has the commit but no remote branch does, `unknown` when no clone has it. A suggestion
 * only: the gate still passes a commit id only by a reviewed entry in the rule file.
 */
export function classifyTokens(tokens, repos) {
  const run = (cwd, args) => {
    try {
      return execFileSync("git", args, { cwd, encoding: "utf8", stdio: ["ignore", "pipe", "ignore"] }).trim();
    } catch {
      return "";
    }
  };
  return [...new Set(tokens)].sort().map((token) => {
    for (const repo of repos) {
      const sha = run(repo, ["rev-parse", "--verify", "--quiet", `${token}^{commit}`]);
      if (!sha) continue;
      const url = run(repo, ["remote", "get-url", "origin"]);
      const repository = url.replace(/^.*github\.com[:/]/u, "").replace(/\.git$/u, "");
      const remote = run(repo, ["branch", "-r", "--contains", sha]).split("\n").filter(Boolean);
      return { token, sha, repository, state: remote.length > 0 ? "public" : "local-only" };
    }
    return { token, sha: null, repository: null, state: "unknown" };
  });
}

function classifyMain(argv) {
  const [scanFile, ...repos] = argv;
  if (!scanFile || repos.length === 0) {
    process.stderr.write("usage: hygiene-shas.mjs classify <scan.json from hygiene-tree.mjs --json> <clone> [<clone> ...]\n");
    return 2;
  }
  const scan = JSON.parse(readFileSync(scanFile, "utf8"));
  const tokens = scan.hits.filter((h) => h.rule === "unreviewed-sha").map((h) => h.text.split(" ")[0]);
  const rows = classifyTokens(tokens, repos);
  for (const r of rows) process.stdout.write(`${r.state.padEnd(10)} ${r.token} ${r.repository ?? ""}\n`);
  const suggested = rows.filter((r) => r.state === "public").map((r) => ({ sha: r.sha, repository: r.repository, why: "" }));
  process.stdout.write(`${JSON.stringify(suggested, null, 2)}\n`);
  return 0;
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url) && process.argv[2] === "classify") {
  process.exit(classifyMain(process.argv.slice(3)));
}
