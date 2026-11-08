/** The only publication boundary: the remote-tracking origin/main and origin/dev tips at cut time. */
import { execFileSync } from "node:child_process";

const REQUIRED = ["refs/remotes/origin/main", "refs/remotes/origin/dev"];
const EXPECTED = "public revisions must be exactly remote-tracking origin/main and origin/dev under refs/remotes/";
const git = (cwd, args) => execFileSync("git", args, {
  cwd, encoding: "utf8", env: { ...process.env, GIT_NO_REPLACE_OBJECTS: "1" },
  stdio: ["ignore", "pipe", "pipe"]
}).trim();

export function remoteRevision(cwd, rev) {
  try {
    if (typeof rev !== "string" || !/^(?:refs\/remotes\/)?origin\/(?:main|dev)$/u.test(rev)) throw new Error("not a public name");
    // Do not silently prefer a remote ref when a short name is shadowed by a local branch or tag.
    const ref = git(cwd, ["rev-parse", "--symbolic-full-name", "--verify", "--end-of-options", rev]);
    if (!REQUIRED.includes(ref)) throw new Error("not a remote-tracking ref");
    const commit = git(cwd, ["rev-parse", "--verify", `${ref}^{commit}`]);
    return { rev, ref, commit };
  } catch {
    throw new Error(`${EXPECTED}; refused ${JSON.stringify(rev)}`);
  }
}

export function publicRevisions(cwd, revs) {
  if (!Array.isArray(revs) || revs.length !== REQUIRED.length) throw new Error(EXPECTED);
  const resolved = revs.map((rev) => remoteRevision(cwd, rev));
  if (REQUIRED.some((ref) => !resolved.some((p) => p.ref === ref))) throw new Error(EXPECTED);
  return resolved;
}

export function publicRevisionProblems(cwd, record) {
  let resolved;
  try {
    resolved = publicRevisions(cwd, record.public.map((p) => p.rev));
  } catch (error) {
    return [error.message];
  }
  const problems = [];
  resolved.forEach((p, i) => {
    if (p.commit !== record.public[i].commit) {
      problems.push(`${p.rev} is at ${p.commit}, not ${record.public[i].commit} as recorded: cut the export again and requalify`);
    }
  });
  const main = resolved.find((p) => p.ref === REQUIRED[0]);
  const recordedMain = record.public[resolved.indexOf(main)].commit;
  if (record.main.commit !== recordedMain) problems.push("the record's main commit is not its remote-tracking origin/main revision");
  return problems;
}
