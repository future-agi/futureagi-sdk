// A comparison's label must describe the two recordings it compares. The twin of
// python/tests/gateway/parity/labels.py (read it for the why).
//
// The label "<golden>-><new>" picks the intended-difference rules, so:
//   - the golden side is a golden in catalog.json, and --golden is that committed
//     golden byte for byte (its directory name included);
//   - the new side is either a golden, and --new is then that golden byte for byte
//     (a fresh re-recording is), or a new recording named in catalog.json
//     comparisons.new_recordings, judged only against a baseline listed for it.
import { readFileSync } from "node:fs";
import { basename, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const FIXTURES = fileURLToPath(new URL("../../../../../tests/fixtures/gateway/", import.meta.url));

export class LabelError extends Error {}

const bytes = (file) => readFileSync(file);

// Whether recording a is recording b byte for byte: index.json and every area file.
export function sameRecording(a, b) {
  try {
    const index = bytes(join(b, "index.json"));
    if (!bytes(join(a, "index.json")).equals(index)) return false;
    return Object.keys(JSON.parse(index.toString("utf8")).files ?? {}).every((n) => bytes(join(a, n)).equals(bytes(join(b, n))));
  } catch {
    return false;
  }
}

// Why label does not name the comparison of goldenDir with newDir (empty when it does).
export function labelProblems(label, goldenDir, newDir, goldenRoot = join(FIXTURES, "golden")) {
  const catalog = JSON.parse(readFileSync(join(FIXTURES, "catalog.json"), "utf8"));
  const goldens = new Set(Object.keys(catalog.goldens));
  const baselines = catalog.comparisons.new_recordings;
  const parts = String(label).split("->");
  if (parts.length !== 2 || !parts[0] || !parts[1]) return [`label ${JSON.stringify(label)} is not <golden>-><new>`];
  const [old, fresh] = parts;
  const out = [];
  if (!goldens.has(old)) out.push(`${JSON.stringify(old)} is not a golden (${[...goldens].sort().join(", ")})`);
  else if (basename(resolve(goldenDir)) !== old || !sameRecording(goldenDir, join(goldenRoot, old))) out.push(`--golden ${goldenDir} is not the committed golden ${old}`);
  if (goldens.has(fresh)) {
    if (!sameRecording(newDir, join(goldenRoot, fresh))) out.push(`the new side ${JSON.stringify(fresh)} names a golden, so --new must be that golden byte for byte, and ${newDir} is not`);
  } else if (!(fresh in baselines)) {
    out.push(`the new side ${JSON.stringify(fresh)} is neither a golden nor a new recording named in catalog.json comparisons (${Object.keys(baselines).sort().join(", ")})`);
  } else if (goldens.has(old) && !baselines[fresh].includes(old)) {
    out.push(`${fresh} is judged against ${baselines[fresh].join(" or ")}, not ${old}`);
  }
  return out;
}

export function checkLabel(label, goldenDir, newDir) {
  const problems = labelProblems(label, goldenDir, newDir);
  if (problems.length) throw new LabelError(`label ${JSON.stringify(label)} refused: ${problems.join("; ")}`);
}
