/**
 * The strict tree scan as a machine-readable findings list, for the step that rewrites or removes
 * what the scan found. Written by `hygiene-tree.mjs <rev> --findings <file>`; always the strict
 * result, with no debt baseline applied, so every entry still has to be resolved before export.
 *
 * Each finding is `{ path, line, target, class, rule, reason, match, lineSha256, generated, fix }`:
 * `line` is 0 for a finding about a whole file or a path name; `target` is "content", "path" or
 * "file"; `lineSha256` is the sha256 of the stripped line (the key an exact-line exemption uses);
 * `match` is the matched text, so keep the list outside the repository. `class` groups the rules:
 *
 *   internal-reference   names and ids of the private build and its documents
 *   encoded-text         printable text hidden behind an escape
 *   local-path           paths of one machine or account
 *   private-source-path  paths into sources that are not published
 *   secret               credentials (remove and rotate)
 *   placeholder-host     hosts that must not reach a public file
 *   commit-id            commit ids a public reader may not be able to open
 *   unreviewed-file      binaries, submodules and files that are not text
 *   invalid-file         platform JSON that does not parse
 *   openapi-structure    OpenAPI keys and extensions outside the allowlist
 *   rule-file            rule-file entries that are malformed or match nothing
 *   history              commit metadata that is not the export identity
 *   other                a rule this table does not know (add it here)
 */

const CLASSES = {
  "internal-reference": [
    "stream-id", "ticket-id", "team-ref", "review-ref", "internal-doc", "decision-ref", "run-id", "process-word",
    "internal-id", "internal-review", "plan-reference", "owner-question", "internal-plan", "ee-only-marker", "gcp-project", "rig"
  ],
  "encoded-text": ["ascii-escape"],
  "local-path": ["volumes-path", "home-path", "tmp-path", "local-state"],
  "private-source-path": ["source-ts-path", "ee-source-path"],
  secret: ["private-key", "aws-key", "github-token", "slack-token", "google-key", "openai-style-key"],
  "placeholder-host": ["placeholder-host"],
  "commit-id": ["unreviewed-sha", "consumer-revision"],
  "unreviewed-file": ["binary-unreviewed", "submodule", "not-text"],
  "invalid-file": ["invalid-json", "invalid-lockfile"],
  "openapi-structure": ["forbidden-key", "extension-not-allowed", "extension-subkey-not-allowed"],
  "rule-file": [
    "invalid-names", "invalid-binary-review", "stale-binary-review", "invalid-glob", "invalid-exemption", "stale-exemption",
    "invalid-digest-keys", "invalid-sha-pin", "invalid-sha-review", "stale-sha-review", "stale-baseline"
  ],
  history: ["foreign-identity"]
};

export const CLASS_OF = new Map(Object.entries(CLASSES).flatMap(([name, rules]) => rules.map((rule) => [rule, name])));

/** Reasons for the rules whose rule file carries no `about` of its own. */
const REASONS = {
  "volumes-path": "an absolute path on a local volume names one machine's layout",
  "home-path": "a home-directory path names a local account",
  "tmp-path": "a local temporary path",
  "internal-id": "an internal tracker or work-item id a public reader cannot open",
  "internal-review": "private process vocabulary a public reader has no context for",
  "plan-reference": "a numbered section reference into a private document",
  "owner-question": "a numbered private question id",
  "source-ts-path": "a TypeScript source path inside a platform file, which names sources that are not published",
  "ee-source-path": "a path into private server sources",
  "internal-plan": "the name of a private planning document",
  "ee-only-marker": "a private-edition marker",
  "gcp-project": "a cloud project name",
  "local-state": "the name of a local state directory",
  "placeholder-host": "a placeholder host that must not reach a public file",
  rig: "the name of private build infrastructure",
  "unreviewed-sha": "a commit id a public reader may not be able to open",
  "consumer-revision": "a consumer repository's commit id recorded in the evaluation census fixture",
  "binary-unreviewed": "a file that is not UTF-8 text and has no reviewed path and sha256",
  submodule: "a submodule entry is not published as files",
  "not-text": "a file that is not UTF-8 text cannot be scanned",
  "invalid-json": "a JSON file under the platform paths does not parse",
  "invalid-lockfile": "a lockfile cannot be parsed structurally with the required parsers",
  "forbidden-key": "an OpenAPI key the platform contract never publishes",
  "extension-not-allowed": "an OpenAPI extension outside the allowlist",
  "extension-subkey-not-allowed": "an OpenAPI extension field outside the allowlist",
  "stale-baseline": "a counted debt entry no longer occurs",
  "foreign-identity": "a commit's author or committer is not the export identity"
};
const SECRET = "a credential in a published file";
const RULE_FILE = "a rule-file entry is malformed, or matches nothing scanned";

/** The class of a rule id ("other" for one the table does not list). */
export const classOf = (rule) => CLASS_OF.get(rule) ?? "other";

/** Why a rule fails: the rule file's own `about` when it has one, else the reason recorded here. */
export function reasonFor(rule, rules = {}) {
  const about = [...(rules.tree?.patterns ?? []), ...(rules.platform?.patterns ?? [])].find((p) => p.id === rule)?.about;
  if (about) return about;
  if (REASONS[rule]) return REASONS[rule];
  if (classOf(rule) === "secret") return SECRET;
  if (classOf(rule) === "rule-file") return RULE_FILE;
  return "a rule without a recorded reason";
}

/** What resolves a finding. */
function fixFor(finding) {
  if (finding.generated) return "fix the generator's input and regenerate; never edit the file";
  switch (finding.class) {
    case "secret":
      return "remove the value and rotate the credential";
    case "commit-id":
      return "remove the id, or list a public commit as reviewed";
    case "unreviewed-file":
      return "remove the file, or list it by path and the sha256 of its bytes after a review";
    case "rule-file":
      return "correct or remove the rule-file entry";
    case "history":
      return "cut the export onto a public base again";
    default:
      return finding.target === "path" ? "rename the path" : "rewrite or remove the text";
  }
}

/** The findings list of one strict scan result (`scanTree`), sorted by path, line and rule. */
export function findingsList(scan, rules = {}) {
  const findings = scan.hits.map((h) => {
    const finding = {
      path: h.file,
      line: h.line,
      target: h.target ?? (h.line === 0 ? "file" : "content"),
      class: classOf(h.rule),
      rule: h.rule,
      reason: reasonFor(h.rule, rules),
      match: h.text,
      lineSha256: h.contentSha256 ?? null,
      generated: Boolean(h.generated)
    };
    return { ...finding, fix: fixFor(finding) };
  });
  findings.sort((a, b) => (a.path < b.path ? -1 : a.path > b.path ? 1 : a.line - b.line || (a.rule < b.rule ? -1 : a.rule > b.rule ? 1 : 0)));
  const byClass = {};
  for (const f of findings) byClass[f.class] = (byClass[f.class] ?? 0) + 1;
  return { version: 1, kind: "hygiene-findings", mode: "strict", commit: scan.commit ?? null, tree: scan.tree, files: scan.files, total: findings.length, byClass, findings };
}
