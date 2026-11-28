/**
 * Run as a child process. The runtime's own copy of undici is loaded first (PROBE_PRELOAD "request": the `Request`
 * global is touched; "env-proxy": the process was started with NODE_USE_ENV_PROXY=1, so the runtime installed its
 * environment-proxy agent at start-up). Then the application puts its own dispatcher in the global dispatcher slot
 * with the `undici` package's `setGlobalDispatcher`, so the slot keeps the form the runtime gives it: an instance of a
 * subclass of the `undici` package's `Agent` whose `dispatch` hands every request to a `ProxyAgent` aimed at the
 * parent's proxy sink. Then the SDK is loaded (PROBE_ORDER "slot-first"; "sdk-first" loads the SDK before the slot is
 * set) and makes a keyed plain-http send, opted in, to a name the shim answers with a loopback address, through the
 * platform client. Prints the outcome, how the SDK judges the dispatcher,
 * and how many times the SDK built the application's class.
 */
import type * as Undici from "undici";

import { installNameShim } from "./name-shim";

const SLOT = Symbol.for("undici.globalDispatcher.1");
const host = globalThis as Record<symbol, unknown>;
const proxyPort = Number(process.env.PROBE_PROXY_PORT ?? "0");
const built = { count: 0 };

/** The application's dispatcher class, made from the `undici` package once the runtime's own copy is loaded. */
function proxyingAgentClass(undici: typeof Undici): new () => Undici.Agent {
  return class ProxyingAgent extends undici.Agent {
    private readonly route: Undici.ProxyAgent;
    constructor(options?: Undici.Agent.Options) {
      super(options);
      built.count += 1;
      this.route = new undici.ProxyAgent(`http://127.0.0.1:${proxyPort}`);
    }
    override dispatch(options: Undici.Agent.DispatchOptions, handler: Parameters<Undici.Agent["dispatch"]>[1]): boolean {
      return this.route.dispatch(options, handler);
    }
  };
}

function slotForm(): string {
  const held = Object.getOwnPropertyDescriptor(globalThis, SLOT);
  if (held === undefined) return "empty";
  const name = (Object.getPrototypeOf(held.value ?? {}) as { constructor?: { name?: string } } | null)?.constructor?.name ?? "unknown";
  return `${name}:${held.configurable === true ? "c" : "-"}${held.enumerable === true ? "e" : "-"}${held.writable === true ? "w" : "-"}`;
}

async function loadSdk(): Promise<{ send: (url: string) => Promise<unknown>; proxies: (dispatcher: unknown, url: string) => boolean }> {
  const { dispatcherProxies } = await import("../http-security");
  const keys = { apiKey: process.env.PROBE_KEY ?? "", secretKey: process.env.PROBE_SECRET ?? "" };
  const { Client } = await import("../../platform/client");
  return {
    send: (url) => {
      const parsed = new URL(url);
      return new Client({ ...keys, baseUrl: parsed.origin, maxRetries: 0, timeout: 3000, allowInsecureHttp: true }).request("GET", parsed.pathname);
    },
    proxies: (dispatcher, url) => dispatcherProxies(dispatcher, url, {}),
  };
}

async function main(): Promise<void> {
  const before = slotForm();
  if (process.env.PROBE_PRELOAD === "request") void Request;
  const preloaded = slotForm();
  // the `undici` package is loaded after the runtime's copy: loaded first, it would fill the empty slot with its own agent
  const loaded = (await import("undici")) as typeof Undici & { default?: typeof Undici };
  const undici = loaded.default ?? loaded;
  const ProxyingAgent = proxyingAgentClass(undici);
  const sdkFirst = process.env.PROBE_ORDER === "sdk-first";
  const early = sdkFirst ? await loadSdk() : undefined;
  undici.setGlobalDispatcher(new ProxyingAgent());
  const installed = host[SLOT];
  const form = slotForm();
  built.count = 0;
  const sdk = early ?? (await loadSdk());
  const shim = installNameShim({ "plain.example.test": "127.0.0.1" });
  const url = `http://plain.example.test:${process.env.PROBE_TARGET_PORT ?? ""}/x`;
  let outcome: string;
  try {
    const answer = (await sdk.send(url)) as { status?: unknown } | undefined;
    outcome = `status:${String(answer?.status ?? "none")}`;
  } catch (error) {
    const code = (error as { code?: unknown }).code;
    outcome = `error:${(error as Error).name}${typeof code === "string" ? `:${code}` : ""}`;
  }
  shim.restore();
  const proxied = sdk.proxies(installed, url);
  const constructed = built.count;
  await (installed as Undici.Agent).close().catch(() => undefined);
  process.stdout.write(`${JSON.stringify({ before, preloaded, form, outcome, proxied, constructed })}\n`);
}
void main();

export {};
