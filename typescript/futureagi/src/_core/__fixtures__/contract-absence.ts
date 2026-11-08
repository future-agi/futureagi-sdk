import { publicPath } from "./contract-public";

type Case = Record<string, any>;

function partsOf(path: unknown): string[] {
  if (typeof path !== "string" || !/^[A-Za-z_$][\w$]*(\.[A-Za-z_$][\w$]*)+$/.test(path)) {
    throw new Error(`invalid public absence path: ${String(path)}`);
  }
  return path.split(".");
}

/** Comparison spellings only; offered calls must use their declared public path. */
export function unavailableTypeScriptPaths(row: Case): string[] {
  const wrappers = row.wrappers ?? (row.wrapper ? [row.wrapper] : undefined);
  if (!wrappers) {
    const path = publicPath(row);
    partsOf(path);
    return [path];
  }
  if (!Array.isArray(wrappers) || !wrappers.length) throw new Error(`missing wrappers for ${row.id}`);
  return wrappers.map((wrapper: Case) => {
    if (wrapper.ts !== undefined) {
      partsOf(wrapper.ts);
      return wrapper.ts;
    }
    const absent = wrapper.not_offered?.ts;
    if (absent?.status !== "NOT-OFFERED" || !absent.reason) {
      throw new Error(`missing TypeScript path without a valid language declaration: ${row.id}`);
    }
    const [root, ...parts] = partsOf(wrapper.py);
    const converted = parts.map(part => {
      if (!/^[a-z][a-z0-9]*(_[a-z][a-z0-9]*)*$/.test(part)) {
        throw new Error(`cannot derive TypeScript absence path from ${wrapper.py}`);
      }
      return part.replace(/_([a-z])/g, (_, c: string) => c.toUpperCase());
    });
    return [root, ...converted].join(".");
  });
}

/** A missing namespace is absence; accessor failures and malformed paths are not. */
export function publicValueAt(client: any, path: string, handles: Record<string, any> = {}): unknown {
  const [root, ...parts] = partsOf(path);
  if (root !== "client" && !Object.hasOwn(handles, root)) {
    throw new Error(`public handle fixture required for ${path}`);
  }
  let value = root === "client" ? client : handles[root];
  for (const part of parts) {
    if (value === undefined) return undefined;
    if (value === null || !["object", "function"].includes(typeof value)) {
      throw new Error(`invalid public namespace in ${path}`);
    }
    value = value[part];
  }
  return value;
}

/** Without a real handle fixture, prove every mapped root factory is absent.
 * An empty handle-fixture dictionary alone says nothing about the SDK surface.
 */
export function absenceCandidates(row: Case, inventory: Case[], handles: Record<string, any> = {}): string[] {
  if (row.public_absence) return row.public_absence.ts;
  return unavailableTypeScriptPaths(row).flatMap(path => {
    const [root] = partsOf(path);
    if (root === "client" || Object.hasOwn(handles, root)) return [path];
    const factories = inventory.flatMap(candidate => (candidate.wrappers ?? []).flatMap((wrapper: Case) => {
      if (![root, `Page[${root}]`].includes(wrapper.returns)) return [];
      return unavailableTypeScriptPaths({ ...candidate, wrappers: [wrapper] }).filter(factory => factory.startsWith("client."));
    }));
    if (!factories.length) throw new Error(`cannot resolve public handle absence for ${path}`);
    return factories;
  });
}
