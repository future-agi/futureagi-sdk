/**
 * Internal names, matched by sha256, so that the public rule file never spells them.
 *
 * A line is lower-cased and split into words (runs of `[a-z0-9_]`). Words joined only by `.` or `-`
 * form a run, and every sequence of 1 to `maxWords` consecutive words of a run, taken with the
 * separators between them, is a candidate. A candidate whose sha256 is listed under "names" in
 * `hygiene-rules.json` is a hit for the rule the entry names. So a listed name is found in any case,
 * inside a longer dotted or hyphenated name and as a path segment, but not inside a longer word.
 *
 * `hygiene_scan.py` implements the same steps, and `test/hygiene-cases.json` holds the cases both
 * scanners must agree on. The plain list of names is kept outside this repository; `checkNameList`
 * checks it against the hashes both ways (`hygiene-scan.mjs --names <file>`).
 */

import { createHash } from "node:crypto";

const WORD = /[a-z0-9_]+/gu;
const SEPARATOR = /^[.-]+$/u;
const HEX64 = /^[0-9a-f]{64}$/u;
const digests = new Map();

/** The sha256 of a text, as lower-case hex (memoised: a scan hashes the same words many times). */
export function sha256(text) {
  let digest = digests.get(text);
  if (digest === undefined) {
    digest = createHash("sha256").update(text, "utf8").digest("hex");
    digests.set(text, digest);
  }
  return digest;
}

/** Every candidate of one line, in order of its first word, then length. */
export function nameCandidates(line, maxWords) {
  const lower = line.toLowerCase();
  const words = [...lower.matchAll(WORD)].map((m) => [m.index, m.index + m[0].length]);
  const out = [];
  for (let i = 0; i < words.length; i += 1) {
    for (let j = i; j < words.length && j < i + maxWords; j += 1) {
      if (j > i && !SEPARATOR.test(lower.slice(words[j - 1][1], words[j][0]))) break;
      out.push(lower.slice(words[i][0], words[j][1]));
    }
  }
  return out;
}

/** The hits of one line: the first candidate per rule, as `{ rule, text }`. */
export function nameHits(line, names) {
  const table = names?.sha256 ?? {};
  if (Object.keys(table).length === 0) return [];
  const hits = new Map();
  for (const candidate of nameCandidates(line, names.maxWords)) {
    const rule = table[sha256(candidate)];
    if (rule !== undefined && !hits.has(rule)) hits.set(rule, { rule, text: candidate });
  }
  return [...hits.values()];
}

/** Problems with the "names" block itself: a bad hash, a rule id without a name, a bad word limit. */
export function namesFindings(names) {
  const out = [];
  if (names === undefined) return out;
  if (!Number.isInteger(names.maxWords) || names.maxWords < 1) out.push("names.maxWords must be a positive integer");
  for (const [digest, rule] of Object.entries(names.sha256 ?? {})) {
    if (!HEX64.test(digest)) out.push(`names.sha256: "${digest.slice(0, 12)}..." is not a lower-case sha256`);
    if (typeof rule !== "string" || rule === "") out.push(`names.sha256: ${digest.slice(0, 12)} has no rule id`);
  }
  return out;
}

/**
 * Check a plain name list (`<rule id> <name>` per line, `#` comments) against the hashes, both ways:
 * every name must hash to an entry with its rule and be found when it stands alone in a line, and
 * every entry must have a name in the list. Returns the problems (empty when the two agree).
 */
export function checkNameList(text, names) {
  const problems = [];
  const covered = new Set();
  text.split("\n").forEach((raw, index) => {
    const line = raw.trim();
    if (line === "" || line.startsWith("#")) return;
    const [rule, name, ...rest] = line.split(/\s+/u);
    const where = `line ${index + 1}`;
    if (!name || rest.length > 0) {
      problems.push(`${where}: expected "<rule id> <name>"`);
      return;
    }
    if (name !== name.toLowerCase()) problems.push(`${where}: names are listed in lower case`);
    const digest = sha256(name.toLowerCase());
    covered.add(digest);
    const listed = names?.sha256?.[digest];
    if (listed === undefined) problems.push(`${where}: no hash for this name (node scripts/platform/hygiene-scan.mjs --hash ${rule} <name>)`);
    else if (listed !== rule) problems.push(`${where}: the hash is listed for ${listed}, not ${rule}`);
    else if (!nameHits(`see ${name} here`, names).some((h) => h.rule === rule)) {
      problems.push(`${where}: the name is not one run of at most ${names.maxWords} words, so the scan cannot find it`);
    }
  });
  for (const digest of Object.keys(names?.sha256 ?? {})) {
    if (!covered.has(digest)) problems.push(`hash ${digest.slice(0, 12)} (${names.sha256[digest]}) has no name in the list`);
  }
  return problems;
}
