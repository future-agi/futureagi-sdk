/**
 * Run as a child process (tsx), with no proxy variable set and no dispatcher set by the application. Loads the SDK in
 * the way PROBE_MODE names, then makes one keyed plain-http send per sender to 127.0.0.1 and to localhost (the parent's
 * target sinks), and prints what each send answered, how each part was loaded (an ES module namespace or a CommonJS
 * exports object), and how many times the SDK built the application's dispatcher class.
 *
 * PROBE_MODE, a list of steps joined by ",":
 *   "esm:root": an ES module graph that imports the root and platform entries;
 *   "cjs:root": `require` of those entries;
 *   "fetch" / "request": the application's first `fetch` runs, or the `Request` global is touched, at that point.
 * PROBE_UNDICI "unresolvable": the resolver refuses `undici` (an application that does not install it).
 * PROBE_SLOT "forged": before the SDK is loaded, the application puts a `ProxyingAgent` (a subclass of the `undici`
 * package's `Agent` whose `dispatch` hands every request to a `ProxyAgent` aimed at the parent's proxy sink) in the
 * global dispatcher slot with the `undici` package's `setGlobalDispatcher`.
 */
import Module, { createRequire } from "node:module";
import { mkdtempSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const src = join(here, "..", "..");
const packageRoot = join(src, "..");
const requireHere = createRequire(import.meta.url);
const SLOT = Symbol.for("undici.globalDispatcher.1");
const steps = (process.env.PROBE_MODE ?? "").split(",").filter((step) => step !== "");
const targets = JSON.parse(process.env.PROBE_TARGETS ?? "{}");
const keys = JSON.parse(process.env.PROBE_KEYS ?? "{}");
const proxyPort = Number(process.env.PROBE_PROXY_PORT ?? "0");
const scratch = mkdtempSync(join(tmpdir(), "keyed-loopback-load-"));
const built = { count: 0 };

/** The resolver refuses `undici` and every path inside it. */
function refuseUndici() {
  const resolve = Module._resolveFilename;
  Module._resolveFilename = function resolveFilename(request, ...rest) {
    if (request === "undici" || request.startsWith("undici/")) {
      const error = new Error(`Cannot find module '${request}'`);
      error.code = "MODULE_NOT_FOUND";
      throw error;
    }
    return resolve.call(this, request, ...rest);
  };
}

/** The application's `ProxyingAgent`, built from its own copy of the `undici` package and put in the global slot. */
function forgeSlot() {
  const undici = createRequire(join(packageRoot, "package.json"))("undici");
  class ProxyingAgent extends undici.Agent {
    constructor(options) {
      super(options);
      built.count += 1;
      this.route = new undici.ProxyAgent(`http://127.0.0.1:${proxyPort}`);
    }
    dispatch(options, handler) { return this.route.dispatch(options, handler); }
  }
  undici.setGlobalDispatcher(new ProxyingAgent());
  built.count = 0;
  const held = globalThis[SLOT];
  return () => held.close().catch(() => undefined);
}

const ROOT_PARTS = { root: join(src, "index.ts"), platform: join(src, "platform", "index.ts") };

/** One ES module graph that imports the root and platform entries statically. */
async function loadEsm(loaded) {
  const names = Object.keys(ROOT_PARTS);
  const text = names.map((name) => `import * as ${name} from ${JSON.stringify(pathToFileURL(ROOT_PARTS[name]).href)};`).join("\n") + `\nexport { ${names.join(", ")} };\n`;
  const entry = join(scratch, "entry.mjs");
  writeFileSync(entry, text);
  Object.assign(loaded, await import(pathToFileURL(entry).href));
}

function loadCjs(loaded) {
  for (const [name, file] of Object.entries(ROOT_PARTS)) loaded[name] = requireHere(file);
}

const formOf = (namespace) => (namespace === undefined ? "absent" : Object.prototype.toString.call(namespace) === "[object Module]" ? "esm" : "cjs");

function senders(loaded) {
  const pair = (name) => ({ apiKey: keys[name][0], secretKey: keys[name][1] });
  const list = {};
  if (loaded.root !== undefined) {
    list.platform = (base) => new loaded.platform.Client({ ...pair("platform"), baseUrl: base, maxRetries: 0, timeout: 3000 }).request("GET", "/probe");
  }
  return list;
}

async function main() {
  globalThis[Symbol.for("futureagi.insecureHttpWarned")] = true;
  const before = globalThis[SLOT] === undefined ? "empty" : "held";
  const closeForged = process.env.PROBE_SLOT === "forged" ? forgeSlot() : undefined;
  if (process.env.PROBE_UNDICI === "unresolvable") refuseUndici();
  const loaded = {};
  for (const step of steps) {
    if (step === "fetch") await fetch("http://127.0.0.1:9/").catch(() => undefined);
    else if (step === "request") void Request;
    else if (step === "esm:root") await loadEsm(loaded);
    else if (step === "cjs:root") loadCjs(loaded);
  }
  const outcomes = {};
  for (const [name, send] of Object.entries(senders(loaded))) {
    for (const host of ["127.0.0.1", "localhost"]) {
      const row = `${name}@${host}`;
      try {
        await send(`http://${host}:${targets[name][host]}`);
        outcomes[row] = { outcome: "sent" };
      } catch (error) {
        const code = typeof error?.code === "string" ? `:${error.code}` : "";
        outcomes[row] = { outcome: `error:${error?.name}${code}`, message: String(error?.message ?? error).slice(0, 600) };
      }
    }
  }
  const constructed = built.count;
  await closeForged?.();
  const forms = { root: formOf(loaded.root) };
  rmSync(scratch, { recursive: true, force: true });
  process.stdout.write(`${JSON.stringify({ before, forms, constructed, outcomes })}\n`);
  process.exit(0);
}
main().catch((error) => {
  rmSync(scratch, { recursive: true, force: true });
  process.stderr.write(`${String(error?.stack ?? error)}\n`);
  process.exit(1);
});
