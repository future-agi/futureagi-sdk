/**
 * Shared walkers over an OpenAPI document, used by the scope filter and the hygiene scan.
 *
 * An extension key (`x-...`) is told apart from a name (a property, header or media type that happens
 * to start with `x-`) by position: the keys of the containers in `rules.nameMaps` are names. An
 * operation-level extension is allowed only on an operation object; a schema-level one anywhere else.
 */

export const METHODS = ["get", "post", "put", "patch", "delete"];

/**
 * Visit every key of `node`. `visit(key, value, ctx)` receives `ctx = { where, isName, path }`, where
 * `where` is "root", "pathItem", "operation" or "other" (the object the key belongs to).
 */
export function walkKeys(node, rules, visit, where = "root", path = "") {
  if (Array.isArray(node)) {
    node.forEach((item, index) => walkKeys(item, rules, visit, "other", `${path}/${index}`));
    return;
  }
  if (node === null || typeof node !== "object") return;
  for (const [key, value] of Object.entries(node)) {
    const here = `${path}/${escapePointer(key)}`;
    visit(key, value, { where, isName: false, path: here });
    if (key === "paths" && where === "root") {
      for (const [name, item] of Object.entries(value ?? {})) {
        visit(name, item, { where: "root", isName: true, path: `${here}/${escapePointer(name)}` });
        walkPathItem(item, rules, visit, `${here}/${escapePointer(name)}`);
      }
    } else if (rules.nameMaps.includes(key) && value !== null && typeof value === "object" && !Array.isArray(value)) {
      for (const [name, child] of Object.entries(value)) {
        const childPath = `${here}/${escapePointer(name)}`;
        visit(name, child, { where: "other", isName: true, path: childPath });
        walkKeys(child, rules, visit, "other", childPath);
      }
    } else {
      walkKeys(value, rules, visit, "other", here);
    }
  }
}

function walkPathItem(item, rules, visit, path) {
  if (item === null || typeof item !== "object") return;
  for (const [key, value] of Object.entries(item)) {
    const here = `${path}/${escapePointer(key)}`;
    visit(key, value, { where: "pathItem", isName: false, path: here });
    if (METHODS.includes(key)) {
      for (const [opKey, opValue] of Object.entries(value ?? {})) {
        const opPath = `${here}/${escapePointer(opKey)}`;
        visit(opKey, opValue, { where: "operation", isName: false, path: opPath });
        if (rules.nameMaps.includes(opKey) && opValue !== null && typeof opValue === "object" && !Array.isArray(opValue)) {
          for (const [name, child] of Object.entries(opValue)) {
            visit(name, child, { where: "other", isName: true, path: `${opPath}/${escapePointer(name)}` });
            walkKeys(child, rules, visit, "other", `${opPath}/${escapePointer(name)}`);
          }
        } else {
          walkKeys(opValue, rules, visit, "other", opPath);
        }
      }
    } else {
      walkKeys(value, rules, visit, "other", here);
    }
  }
}

/** Whether an extension key is allowed where it stands. */
export function extensionAllowed(key, value, ctx, rules) {
  if (ctx.isName || !key.startsWith("x-")) return true;
  if (ctx.where === "operation") return rules.extensions.operation.includes(key);
  if (ctx.where === "pathItem" || ctx.where === "root") return false;
  return rules.extensions.schema.includes(key) && value === true;
}

/** The structural findings for one parsed JSON document: forbidden keys and disallowed extensions. */
export function structuralFindings(doc, rules) {
  const findings = [];
  walkKeys(doc, rules, (key, value, ctx) => {
    if (!ctx.isName && rules.forbiddenKeys.includes(key)) findings.push({ rule: "forbidden-key", at: ctx.path, text: key });
    if (!extensionAllowed(key, value, ctx, rules)) findings.push({ rule: "extension-not-allowed", at: ctx.path, text: key });
    if (!ctx.isName && ctx.where === "operation" && rules.extensions.subkeys[key] && value && typeof value === "object") {
      for (const sub of Object.keys(value)) {
        if (!rules.extensions.subkeys[key].includes(sub)) findings.push({ rule: "extension-subkey-not-allowed", at: `${ctx.path}/${sub}`, text: sub });
      }
    }
  });
  return findings;
}

/** Every `$ref` string under `node`, plus discriminator mapping targets and `x-omega-stream.events`. */
export function collectRefs(node, out = new Set()) {
  if (Array.isArray(node)) {
    for (const item of node) collectRefs(item, out);
    return out;
  }
  if (node === null || typeof node !== "object") return out;
  for (const [key, value] of Object.entries(node)) {
    if (key === "$ref" && typeof value === "string") out.add(value);
    else if (key === "mapping" && value && typeof value === "object") {
      for (const target of Object.values(value)) if (typeof target === "string" && target.startsWith("#/")) out.add(target);
    } else if (key === "x-omega-stream" && value && typeof value.events === "string") out.add(value.events);
    else collectRefs(value, out);
  }
  return out;
}

/** RFC 6901 escaping for one reference token. */
export function escapePointer(token) {
  return String(token).replaceAll("~", "~0").replaceAll("/", "~1");
}

/** Resolve a JSON pointer (`/a/b`) against `doc`; returns `{ parent, key }` for the last token. */
export function pointerParent(doc, pointer) {
  const tokens = pointer.split("/").slice(1).map((t) => t.replaceAll("~1", "/").replaceAll("~0", "~"));
  const key = tokens.pop();
  let parent = doc;
  for (const token of tokens) {
    if (parent === null || typeof parent !== "object" || !(token in parent)) throw new Error(`pointer ${pointer}: no ${token}`);
    parent = parent[token];
  }
  return { parent, key };
}
