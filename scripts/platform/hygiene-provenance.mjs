/** Anonymous public-ref ancestry checks. No local refs, credentials or persisted clearance. */
import { execFileSync } from "node:child_process";
import { mkdtempSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import path from "node:path";

export function publicRemote(repository) {
  if (typeof repository !== "string") return null;
  const match = /^(?:https:\/\/github\.com\/)?([A-Za-z0-9_.-]+\/[A-Za-z0-9_.-]+?)(?:\.git)?\/?$/u.exec(repository);
  return match ? `https://github.com/${match[1]}.git` : null;
}

/** The injection is only for deterministic tests of the anonymous git protocol. */
export function createProvenanceVerifier(run = execFileSync) {
  const checked = new Map();
  const directories = [];
  function verify(repository, token) {
    const remote = publicRemote(repository);
    if (!remote || !/^[a-f0-9]{7,40}$/iu.test(token)) return false;
    if (!checked.has(remote)) {
      const dir = mkdtempSync(path.join(tmpdir(), "public-provenance-"));
      directories.push(dir);
      // A fresh HOME and no git config also disable .netrc, URL rewrites, helpers,
      // HTTP headers, replace objects and inherited repository environment variables.
      const env = { PATH: process.env.PATH, HOME: dir, TMPDIR: dir,
        GIT_CONFIG_NOSYSTEM: "1", GIT_CONFIG_GLOBAL: "/dev/null", GIT_CONFIG_COUNT: "0",
        GIT_TERMINAL_PROMPT: "0", GIT_ASKPASS: "/usr/bin/false", GIT_NO_REPLACE_OBJECTS: "1", GIT_ALLOW_PROTOCOL: "https" };
      const git = (args) => run("git", ["-c", "credential.helper=", "-c", "http.extraHeader=", "-c", "http.followRedirects=false", ...args], {
        cwd: dir, env, encoding: "utf8", stdio: ["ignore", "pipe", "pipe"], timeout: 60000, maxBuffer: 64 * 1024 * 1024
      }).trim();
      try {
        const advertised = git(["ls-remote", "--symref", remote, "HEAD", "refs/heads/*", "refs/tags/*"]);
        const refs = advertised.split("\n").map((line) => line.split(/\s+/u)).filter(([sha, ref]) => /^[a-f0-9]{40}$/u.test(sha) && /^refs\/(heads|tags)\//u.test(ref) && !ref.endsWith("^{}"));
        if (!refs.length) throw new Error("no anonymous public refs");
        git(["init", "--bare", "-q"]);
        git(["fetch", "--quiet", "--filter=tree:0", "--no-tags", remote, ...refs.map(([, ref]) => `${ref}:${ref}`)]);
        // The object graph is obtained only from advertised public refs, never by
        // fetching the candidate id (some hosts permit unreachable object fetches).
        const commits = new Set(git(["rev-list", "--all"]).split("\n"));
        checked.set(remote, commits);
      } catch {
        checked.set(remote, new Set());
      }
    }
    return [...checked.get(remote)].filter((sha) => sha.startsWith(token.toLowerCase())).length === 1;
  }
  verify.close = () => directories.forEach((dir) => rmSync(dir, { recursive: true, force: true }));
  return verify;
}

/** Exact JSON value occurrences only: an equal id in prose on the same line is still scanned. */
export function provenanceOccurrences(file, text, verify) {
  const allowed = new Set();
  if (!file.endsWith(".json")) return allowed;
  let doc;
  try { doc = JSON.parse(text); } catch { return allowed; }
  if (!doc || Array.isArray(doc) || typeof doc !== "object") return allowed;
  // Provenance documents use a sibling source identity and revision. Other nested
  // objects and arbitrary string content never inherit that source's authority.
  const source = doc.source ?? doc.repository ?? doc.backend_repository;
  for (const key of ["revision", "commit", "backend_revision"]) {
    const value = doc[key];
    if (typeof value !== "string" || !/^[a-f0-9]{7,40}$/iu.test(value) || !source) continue;
    let proven = false;
    try { proven = verify(source, value) === true; } catch { proven = false; }
    if (!proven) continue;
    // Walk JSON tokens to bind the span to the top-level member, including minified files.
    const tokens = /"(?:[^"\\]|\\.)*"|[{}\[\]:,]/gu;
    let depth = 0;
    let pending = null;
    let expectingValue = false;
    for (const match of text.matchAll(tokens)) {
      const token = match[0];
      if (token === "{" || token === "[") { depth += 1; continue; }
      if (token === "}" || token === "]") { depth -= 1; continue; }
      if (depth !== 1) continue;
      if (token === ",") { pending = null; expectingValue = false; continue; }
      if (token === ":") { expectingValue = true; continue; }
      if (!token.startsWith('"')) continue;
      if (!expectingValue) pending = JSON.parse(token);
      else if (pending === key && token === JSON.stringify(value)) allowed.add(match.index + 1);
    }
  }
  return allowed;
}
