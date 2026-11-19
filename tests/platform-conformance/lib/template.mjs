/**
 * `${a.b.c}` substitution for case data, and filling a manifest path template.
 *
 * A string that is exactly one placeholder takes the value as it is (a number stays a number);
 * a placeholder inside a longer string is stringified. An unknown name throws, so a case never
 * runs with a literal "${...}" in its request.
 */

const WHOLE = /^\$\{([A-Za-z0-9_.\-]+)\}$/;
const PART = /\$\{([A-Za-z0-9_.\-]+)\}/g;

export function lookup(context, dotted) {
  let node = context;
  for (const part of dotted.split(".")) {
    if (node === null || typeof node !== "object" || !(part in node)) {
      throw new Error(`unknown template value \${${dotted}}`);
    }
    node = node[part];
  }
  return node;
}

/** Deep-substitute every placeholder in `value` from `context`. */
export function fill(value, context) {
  if (typeof value === "string") {
    const whole = WHOLE.exec(value);
    if (whole) return lookup(context, whole[1]);
    return value.replace(PART, (_, name) => String(lookup(context, name)));
  }
  if (Array.isArray(value)) return value.map((item) => fill(item, context));
  if (value !== null && typeof value === "object") {
    return Object.fromEntries(Object.entries(value).map(([key, item]) => [key, fill(item, context)]));
  }
  return value;
}

/** The names a value still refers to (for validation without a context). */
export function referencedNames(value, into = new Set()) {
  if (typeof value === "string") for (const match of value.matchAll(PART)) into.add(match[1]);
  else if (Array.isArray(value)) value.forEach((item) => referencedNames(item, into));
  else if (value !== null && typeof value === "object") Object.values(value).forEach((item) => referencedNames(item, into));
  return into;
}

/** The parameter names in a manifest path template, in order. */
export function templateParams(template) {
  return [...template.matchAll(/\{([^}]+)\}/g)].map((match) => match[1]);
}

/**
 * Fill a template. The manifest uses `{id}` more than once in one path, so values are given
 * as a list in order (`params: [..]`) or by name when every name is unique. `filePath` and
 * `rest` keep their slashes; every other segment is percent-encoded.
 */
export function fillPath(template, params = {}) {
  const names = templateParams(template);
  const ordered = Array.isArray(params) ? params : names.map((name) => params[name]);
  if (!Array.isArray(params) && new Set(names).size !== names.length) {
    throw new Error(`${template} repeats a parameter name; give params as a list`);
  }
  if (ordered.length !== names.length || ordered.some((value) => value === undefined || value === null)) {
    throw new Error(`${template} needs ${names.length} parameter(s): ${names.join(", ")}`);
  }
  let index = 0;
  return template.replace(/\{([^}]+)\}/g, (_, name) => {
    const value = String(ordered[index++]);
    if (name === "filePath" || name === "rest") return value.split("/").map(encodeURIComponent).join("/");
    return encodeURIComponent(value);
  });
}
