/**
 * Run as a child process. Before the SDK is loaded, a dispatcher written here is put in the runtime's global dispatcher
 * slot: classes named `Agent` and `Pool` with a `factory` slot, whose `dispatch` writes every request it is handed to
 * the parent's proxy sink. Then the SDK is loaded and makes a keyed plain-http send with the platform client (opted in) to a name the shim
 * answers with a loopback address. Prints what the send answered and whether the SDK counts the dispatcher as proxied.
 * PROBE_SLOT picks how the dispatcher is put in the slot: "assign" (a plain assignment) or "define" (a non-configurable property).
 */
import net from "node:net";

import { installNameShim } from "./name-shim";

const SLOT = Symbol.for("undici.globalDispatcher.1");
const FACTORY = Symbol("factory");
const proxyPort = Number(process.env.PROBE_PROXY_PORT ?? "0");

function toProxy(options: { origin?: unknown; path?: unknown; method?: unknown; headers?: unknown }, handler: Record<string, unknown>): boolean {
  const socket = net.connect(proxyPort, "127.0.0.1", () => {
    socket.end(`${String(options.method)} ${String(options.origin)}${String(options.path)} HTTP/1.1\r\nx-carried: ${JSON.stringify(options.headers)}\r\n\r\n`);
  });
  socket.on("error", () => undefined);
  socket.on("close", () => {
    const failure = new Error("closed");
    try {
      if (typeof handler.onResponseError === "function") (handler.onResponseError as (c: unknown, e: Error) => void)({}, failure);
      else if (typeof handler.onError === "function") (handler.onError as (e: Error) => void)(failure);
    } catch { /* the runtime's handler may refuse a second answer */ }
  });
  return true;
}

class Pool { dispatch(options: object, handler: Record<string, unknown>): boolean { return toProxy(options, handler); } close(): Promise<void> { return Promise.resolve(); } }
const factory = (): Pool => new Pool();
class Agent {
  [FACTORY] = factory;
  dispatch(options: object, handler: Record<string, unknown>): boolean { return toProxy(options, handler); }
  close(): Promise<void> { return Promise.resolve(); }
}

async function main(): Promise<void> {
  if (process.env.PROBE_SLOT === "define") Object.defineProperty(globalThis, SLOT, { value: new Agent(), writable: true, enumerable: false, configurable: false });
  else (globalThis as Record<symbol, unknown>)[SLOT] = new Agent();
  const installed = (globalThis as Record<symbol, unknown>)[SLOT];
  const shim = installNameShim({ "plain.example.test": "127.0.0.1" });
  const { Client } = await import("../../platform/client");
  const { dispatcherProxies } = await import("../http-security");
  const baseUrl = `http://plain.example.test:${process.env.PROBE_TARGET_PORT ?? ""}`;
  const url = `${baseUrl}/x`;
  const client = new Client({ apiKey: process.env.PROBE_KEY ?? "", secretKey: process.env.PROBE_SECRET ?? "", baseUrl, maxRetries: 0, timeout: 3000, allowInsecureHttp: true });
  let outcome: string;
  try { await client.request("GET", "/x"); outcome = "status:ok"; } catch (error) { outcome = `error:${(error as Error).name}`; }
  shim.restore();
  const kept = (globalThis as Record<symbol, unknown>)[SLOT] === installed;
  process.stdout.write(`${JSON.stringify({ outcome, proxied: dispatcherProxies(installed, url, {}), kept })}\n`);
}
void main();

export {};
