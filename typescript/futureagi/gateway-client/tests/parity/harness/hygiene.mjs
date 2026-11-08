// Refuse a golden that carries a local path. The twin of
// python/tests/gateway/parity/_hygiene.py; both pass tests/fixtures/gateway/hygiene-cases.json.
//
// A recording holds what the SDK does. A path of the checkout, an install or a
// temp directory says where it was recorded: the golden then reproduces from
// that one directory only, and a machine's layout lands in the repository.
// Two rules find one:
//   - the static rule, which needs no context (a committed golden's recording
//     place is unknown): any "file://" URL, and an absolute path under a home,
//     volume or temp root that does not continue a word or URL path;
//   - the recorder's own roots (its checkout, the install, the working, home,
//     temp and output directories), passed in. Any absolute directory other than
//     the filesystem root is usable, including a single-component checkout.
// Text after a "<path>" placeholder is relative to it and is never checked.
import { mkdirSync, realpathSync, writeFileSync } from "node:fs";
import { homedir, tmpdir } from "node:os";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { dump } from "./observe.mjs";

const PLACEHOLDER = /<path>[^\s"'()]*/g;
const STATIC = /file:\/\/|(?<![\w.@+~-])\/(?:Users|Volumes|home|tmp|private|root|var\/folders)\//g;

const usable = (root) => typeof root === "string" && /^\/[^/]/.test(root);

function variants(roots) {
  const out = new Set();
  for (const root of roots) {
    if (!usable(root)) continue;
    out.add(root.replace(/\/+$/, ""));
    try {
      out.add(realpathSync(root).replace(/\/+$/, ""));
    } catch {
      // a root that does not exist here is still checked as given
    }
  }
  return [...out].filter(usable).sort();
}

// The local paths in one string: each static token, then each root it contains.
export function leaks(text, roots = []) {
  const body = String(text).replace(PLACEHOLDER, "<path>");
  const found = [...body.matchAll(STATIC)].map((m) => m[0]);
  for (const root of variants(roots)) if (body.includes(root)) found.push(root);
  return found;
}

// Every string in a JSON-able value, keys included, with its JSON path.
export function leaksIn(value, roots = [], at = "") {
  const out = [];
  const visit = (v, path) => {
    if (typeof v === "string") {
      for (const token of leaks(v, roots)) out.push({ at: path, token });
    } else if (Array.isArray(v)) {
      v.forEach((item, i) => visit(item, `${path}/${i}`));
    } else if (v && typeof v === "object") {
      for (const key of Object.keys(v).sort()) {
        for (const token of leaks(key, roots)) out.push({ at: `${path}/${key}`, token });
        visit(v[key], `${path}/${key}`);
      }
    }
  };
  visit(value, at);
  return out;
}

// The directories a recorder process knows it runs from.
export function recorderRoots(...extra) {
  const checkout = fileURLToPath(new URL("../../../../../../", import.meta.url));
  return [checkout, process.cwd(), homedir(), tmpdir(), ...extra.map((p) => resolve(p))];
}

export class LocalPathError extends Error {}

// Write dump(data) to file, or refuse (nothing written) if any string leaks.
export function writeChecked(file, data, roots) {
  const found = leaksIn(data, roots);
  if (found.length) {
    const shown = found.slice(0, 5).map((f) => `${f.at || "/"}: ${f.token}`).join("; ");
    throw new LocalPathError(`refusing to write ${file}: ${found.length} local path(s) (${shown})`);
  }
  const text = dump(data);
  mkdirSync(dirname(file), { recursive: true });
  writeFileSync(file, text);
  return text;
}
