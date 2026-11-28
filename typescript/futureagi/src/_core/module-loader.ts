/**
 * How the SDK loads a module at run time without a static import: a `node:` built-in from the runtime, and a package
 * (`undici`) through a `require` that resolves from the SDK's own location, in the CommonJS and the ES module builds.
 */

/**
 * The file this module was loaded from (a path, or a `file:` URL for an ES module), read from the V8 call site of this
 * function (this module sits next to the modules that load through it), or from the first frame of the stack text when
 * the application's `Error.prepareStackTrace` cannot be set aside; `undefined` when the runtime gives no frame (an
 * `Error.stackTraceLimit` of 0 that cannot be raised, say). Both settings are put back as they were.
 */
function ownModuleFile(): string | undefined {
  const holder = Error as unknown as { prepareStackTrace?: unknown; stackTraceLimit?: number };
  const [prepare, limit] = [holder.prepareStackTrace, holder.stackTraceLimit];
  const set = (apply: () => void): void => { try { apply(); } catch { /* a setting that cannot be written stays */ } };
  let stack: unknown;
  try {
    set(() => { holder.prepareStackTrace = (_error: unknown, sites: unknown): unknown => sites; });
    set(() => { holder.stackTraceLimit = 1; });
    stack = (new Error() as { stack?: unknown }).stack;
  } catch {
    stack = undefined;
  } finally {
    set(() => { if (holder.prepareStackTrace !== prepare) holder.prepareStackTrace = prepare; });
    set(() => { if (holder.stackTraceLimit !== limit) holder.stackTraceLimit = limit; });
  }
  try {
    const file = Array.isArray(stack) ? (stack[0] as { getFileName?: () => unknown } | undefined)?.getFileName?.()
      : typeof stack === "string" ? /^\s*at (?:.*\()?((?:file:\/\/)?\/[^()\n]*?):\d+:\d+\)?\s*$/mu.exec(stack)?.[1] : undefined;
    return typeof file === "string" && file !== "" ? file : undefined;
  } catch {
    return undefined;
  }
}

/**
 * A module by its id: a `node:` built-in from the runtime (its `getBuiltinModule`), else through a `require` that
 * resolves from this module's own location (the module's `require`, or one made from its own file in an ES module), so a
 * package such as `undici` is the one installed for the SDK, whatever the working directory. `resolve` only resolves `id`.
 */
export function loadModule(id: string, resolve = false): unknown {
  try {
    const runtime = (globalThis as { process?: { getBuiltinModule?: (id: string) => unknown } }).process;
    const builtin = runtime?.getBuiltinModule;
    if (!resolve && id.startsWith("node:") && typeof builtin === "function") return builtin.call(runtime, id);
    if (typeof require === "function") return resolve ? require.resolve(id) : require(id);
    const create = (runtime?.getBuiltinModule?.("node:module") as { createRequire?: (from: string) => NodeRequire } | undefined)?.createRequire;
    const file = ownModuleFile();
    const load = file === undefined ? undefined : create?.(file);
    return resolve ? load?.resolve(id) : load?.(id);
  } catch {
    return undefined;
  }
}

/**
 * Whether this build loads neither a package nor a `node:` built-in at run time: an ES module build (no `require`) on a
 * runtime without `process.getBuiltinModule`. There the SDK cannot read undici's classes or open a direct transport of its
 * own, so an Agent of the undici package does not clear a dispatcher refusal; an https:// URL or the CommonJS build does.
 */
export function runtimeLoadingUnavailable(): boolean {
  const runtime = (globalThis as { process?: { getBuiltinModule?: unknown } }).process;
  return typeof require !== "function" && typeof runtime?.getBuiltinModule !== "function";
}
