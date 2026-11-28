/**
 * Run as a child process (tsx), with no proxy variable set. Sets up what PROBE_CASE names, loads the SDK in the way
 * PROBE_MODE names, then sends keyed plain HTTP requests with the platform Client to the target sinks at 127.0.0.1
 * and localhost. Prints each outcome, how the root was loaded, and how many times the application's `ProxyingAgent`
 * was built after the application built its own.
 *
 * PROBE_MODE: "esm:root" (an ES module graph that imports the root) or "cjs:root" (`require` of the root).
 * PROBE_UNDICI "unresolvable": the resolver refuses `undici` once the application holds its own copy of the package.
 * PROBE_CASE, before the SDK is loaded:
 *   "record" / "record-named": the application puts its `ProxyingAgent` (a subclass of the `undici` package's `Agent`
 *     whose `dispatch` hands every request to a `ProxyAgent` aimed at the proxy sink; "record-named" names the subclass
 *     `Agent`) in the global dispatcher slot, defines the runtime-undici record with that class as its `Agent` and the
 *     package's `Pool` and `Client`, and touches the `Request` global (the runtime's undici is loaded then);
 * PROBE_CASE, after the SDK is loaded, a dispatcher of the `undici` package put in the global slot:
 *   "mock-accessor": a `MockAgent()` whose own `agent` slot is a getter that returns its genuine `Agent` when the call
 *     stack names dispatcher-provenance and the `ProxyingAgent` otherwise;
 *   "dispatch-accessor": an `Agent` whose own `dispatch` is such a getter (`Agent`'s dispatch, or the `ProxyingAgent`'s);
 *   "factory-accessor" / "proto-factory-accessor": an `Agent` whose `factory` slot, its own or (with its own deleted) one
 *     on a prototype put between it and `Agent.prototype`, is such a getter (`Agent`'s factory, or one that hands every
 *     origin the `ProxyingAgent`);
 *   "socket-path" / "connect-socket-path" / "connect-path": an `Agent` built with `socketPath`, `connect.socketPath` or
 *     `connect.path` naming the parent's Unix socket sink (PROBE_SOCKET).
 */
import Module, { createRequire } from "node:module";
import { mkdtempSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const packageRoot = join(here, "..", "..", "..");
const src = join(packageRoot, "src");
const requireHere = createRequire(import.meta.url);
const RECORD = Symbol.for("@future-agi/sdk.runtime-undici");
const mode = process.env.PROBE_MODE;
const probeCase = process.env.PROBE_CASE;
const targets = JSON.parse(process.env.PROBE_TARGETS ?? "{}");
const keys = JSON.parse(process.env.PROBE_KEYS ?? "{}");
const proxyPort = Number(process.env.PROBE_PROXY_PORT ?? "0");
const socket = process.env.PROBE_SOCKET ?? "";
const scratch = mkdtempSync(join(tmpdir(), "runtime-undici-record-"));
const built = { count: 0 };
const opened = [];

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

let undiciPackage;
const undici = () => (undiciPackage ??= createRequire(join(packageRoot, "package.json"))("undici"));

/** The application's `ProxyingAgent` class: every request it is handed goes to a `ProxyAgent` aimed at the proxy sink. */
function proxyingClass(named) {
  const { Agent, ProxyAgent } = undici();
  const classes = {
    ProxyingAgent: class ProxyingAgent extends Agent {
      constructor(options) {
        super(options);
        built.count += 1;
        this.route = new ProxyAgent(`http://127.0.0.1:${proxyPort}`);
        opened.push(this.route);
      }
      dispatch(options, handler) { return this.route.dispatch(options, handler); }
    },
  };
  if (!named) return classes.ProxyingAgent;
  const Named = { Agent: class extends classes.ProxyingAgent {} }.Agent;
  return Named;
}

const fromProvenance = () => (new Error().stack ?? "").includes("dispatcher-provenance");

/** The global slot's dispatcher the case names, built from the application's copy of the `undici` package. */
function caseDispatcher() {
  if (probeCase.startsWith("record")) return undefined;
  const { Agent, MockAgent } = undici();
  if (probeCase.endsWith("-accessor")) {
    const proxying = new (proxyingClass(false))();
    if (probeCase.includes("factory")) {
      const agent = new Agent();
      const slot = Object.getOwnPropertySymbols(agent).find((symbol) => symbol.description === "factory");
      const genuine = agent[slot];
      const getter = { configurable: true, get: () => (fromProvenance() ? genuine : () => proxying) };
      if (probeCase === "factory-accessor") return Object.defineProperty(agent, slot, getter);
      delete agent[slot];
      return Object.setPrototypeOf(agent, Object.create(Agent.prototype, { [slot]: getter }));
    }
    if (probeCase === "dispatch-accessor") {
      const agent = new Agent();
      const genuine = Agent.prototype.dispatch;
      Object.defineProperty(agent, "dispatch", { configurable: true, get: () => (fromProvenance() ? genuine : (options, handler) => proxying.dispatch(options, handler)) });
      return agent;
    }
    const mock = new MockAgent();
    const slot = Object.getOwnPropertySymbols(mock).find((symbol) => symbol.description === "agent");
    const genuine = mock[slot];
    Object.defineProperty(mock, slot, { configurable: true, get: () => (fromProvenance() ? genuine : proxying) });
    return mock;
  }
  if (probeCase === "socket-path") return new Agent({ socketPath: socket });
  if (probeCase === "connect-socket-path") return new Agent({ connect: { socketPath: socket } });
  if (probeCase === "connect-path") return new Agent({ connect: { path: socket } });
  return undefined;
}

const ROOT_PARTS = { root: join(src, "index.ts"), platform: join(src, "platform", "index.ts") };

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
  const list = {};
  if (loaded.platform !== undefined && targets.platform !== undefined) {
    list.platform = (base) => new loaded.platform.Client({ apiKey: keys.platform[0], secretKey: keys.platform[1], baseUrl: base, maxRetries: 0, timeout: 3000 }).request("GET", "/probe");
  }
  return list;
}

async function main() {
  globalThis[Symbol.for("futureagi.insecureHttpWarned")] = true;
  if (probeCase === "record" || probeCase === "record-named") {
    const { Pool, Client, setGlobalDispatcher } = undici();
    const ProxyingAgent = proxyingClass(probeCase === "record-named");
    setGlobalDispatcher(new ProxyingAgent());
    Object.defineProperty(globalThis, RECORD, { value: Object.freeze({ Agent: ProxyingAgent, Pool, Client, EnvHttpProxyAgent: undefined }) });
    void Request;
  }
  if (process.env.PROBE_UNDICI === "unresolvable") {
    undici();
    refuseUndici();
  }
  const loaded = {};
  if (mode === "esm:root") await loadEsm(loaded);
  else if (mode === "cjs:root") loadCjs(loaded);
  else throw new Error(`Unknown load mode: ${mode}`);
  const placed = caseDispatcher();
  if (placed !== undefined) {
    undici().setGlobalDispatcher(placed);
    opened.push(placed);
  }
  built.count = 0;
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
  await Promise.all(opened.map((dispatcher) => dispatcher.close?.().catch(() => undefined)));
  const forms = { root: formOf(loaded.root) };
  rmSync(scratch, { recursive: true, force: true });
  process.stdout.write(`${JSON.stringify({ forms, constructed, outcomes })}\n`);
  process.exit(0);
}
main().catch((error) => {
  rmSync(scratch, { recursive: true, force: true });
  process.stderr.write(`${String(error?.stack ?? error)}\n`);
  process.exit(1);
});
