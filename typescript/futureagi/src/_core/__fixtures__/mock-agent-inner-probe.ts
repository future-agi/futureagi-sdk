/**
 * Run as a child process. An undici `MockAgent` is put in the runtime's global dispatcher slot, and the SDK makes keyed
 * plain-http sends through the platform client, to `127.0.0.1`, to `localhost` and, opted in,
 * to a name the shim answers with a loopback address. The proxy and target listeners run in this process, so the
 * marker count of each send is read on its own.
 *
 * PROBE_MODE picks the load order: "sdk-first" (the SDK is loaded first, then the slot is set), "request" (the `Request`
 * global is touched, the slot is set, then the SDK is loaded), "env-proxy" (the process was started with
 * NODE_USE_ENV_PROXY=1, then as "request"), "slot-first" (the slot is set, then the SDK is loaded).
 * PROBE_FORM picks how the slot is set: "setGlobalDispatcher" (the `undici` package's), "assign" (a plain assignment) or
 * "define" (a non-configurable, read-only property).
 * PROBE_INNER picks the mock: "proxying" (`MockAgent({ agent })` whose agent is an `Agent` subclass handing every request
 * to a `ProxyAgent` aimed at the proxy listener) or "genuine" (`MockAgent()`, with an interceptor answering every
 * request, so a send through it reaches no listener).
 * Prints one JSON line: the slot form and the rows.
 */
import type * as Undici from "undici";

import { installNameShim } from "./name-shim";
import { CountingSink } from "./proxy-sink";

const SLOT = Symbol.for("undici.globalDispatcher.1");
const KEY = process.env.PROBE_KEY ?? "";
const SECRET = process.env.PROBE_SECRET ?? "";
const HOST = "plain.example.test";

interface Row { sender: string; host: string; outcome: string; proxyMarkers: number; proxyTunnels: number; targetMarkers: number; targetConnections: number; mockAnswers: number }

function slotForm(): string {
  const held = Object.getOwnPropertyDescriptor(globalThis, SLOT);
  if (held === undefined) return "empty";
  const name = (Object.getPrototypeOf(held.value ?? {}) as { constructor?: { name?: string } } | null)?.constructor?.name ?? "unknown";
  return `${name}:${held.configurable === true ? "c" : "-"}${held.enumerable === true ? "e" : "-"}${held.writable === true ? "w" : "-"}`;
}

type Send = (base: string, path: string) => Promise<unknown>;

async function loadSenders(): Promise<Array<[string, Send]>> {
  const { Client } = await import("../../platform/client");
  const keys = { apiKey: KEY, secretKey: SECRET };
  return [
    ["platform Client", (base, path) => new Client({ ...keys, baseUrl: base, maxRetries: 0, timeout: 3000, allowInsecureHttp: true }).request("GET", path)],
  ];
}

function install(dispatcher: object, undici: typeof Undici): void {
  const form = process.env.PROBE_FORM;
  if (form === "setGlobalDispatcher") undici.setGlobalDispatcher(dispatcher as Undici.Dispatcher);
  else if (form === "define") Object.defineProperty(globalThis, SLOT, { value: dispatcher, writable: false, enumerable: false, configurable: false });
  else (globalThis as Record<symbol, unknown>)[SLOT] = dispatcher;
}

async function main(): Promise<void> {
  const proxy = new CountingSink([KEY, SECRET]);
  const target = new CountingSink([KEY, SECRET]);
  await Promise.all([proxy.listen(), target.listen()]);
  const mode = process.env.PROBE_MODE ?? "slot-first";
  const early = mode === "sdk-first" ? await loadSenders() : undefined;
  if (mode === "request" || mode === "env-proxy") void Request;
  const loaded = (await import("undici")) as typeof Undici & { default?: typeof Undici };
  const undici = loaded.default ?? loaded;
  const counter = { answers: 0 };
  let mock: Undici.MockAgent;
  if (process.env.PROBE_INNER === "genuine") {
    mock = new undici.MockAgent();
    const bases = [`http://127.0.0.1:${target.port}`, `http://localhost:${target.port}`, `http://${HOST}:${target.port}`];
    for (const base of bases) {
      mock.get(base).intercept({ path: () => true, method: () => true }).reply(200, () => { counter.answers += 1; return { items: [], results: [] }; }).persist();
    }
  } else {
    class ProxyingAgent extends undici.Agent {
      private readonly route = new undici.ProxyAgent(`http://127.0.0.1:${proxy.port}`);
      override dispatch(options: Undici.Agent.DispatchOptions, handler: Parameters<Undici.Agent["dispatch"]>[1]): boolean {
        return this.route.dispatch(options, handler);
      }
    }
    mock = new undici.MockAgent({ agent: new ProxyingAgent() });
  }
  install(mock, undici);
  const form = slotForm();
  const senders = early ?? (await loadSenders());
  const shim = installNameShim({ [HOST]: "127.0.0.1" });
  const rows: Row[] = [];
  for (const [sender, send] of senders) {
    for (const host of ["127.0.0.1", "localhost", HOST]) {
      proxy.reset();
      target.reset();
      counter.answers = 0;
      let outcome: string;
      try {
        const answer = (await send(`http://${host}:${target.port}`, "/probe")) as { status?: unknown } | undefined;
        outcome = `sent:${String(answer?.status ?? "ok")}`;
      } catch (error) {
        const code = (error as { code?: unknown }).code;
        outcome = `error:${(error as Error).name}${typeof code === "string" ? `:${code}` : ""}`;
      }
      rows.push({ sender, host, outcome, proxyMarkers: proxy.markerCount, proxyTunnels: proxy.tunnels, targetMarkers: target.markerCount, targetConnections: target.connections, mockAnswers: counter.answers });
    }
  }
  shim.restore();
  void mock.close().catch(() => undefined);
  process.stdout.write(`${JSON.stringify({ form, rows })}\n`);
  process.exit(0);
}
void main();

export {};
