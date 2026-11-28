/**
 * The platform `Client` sends its keys through a fetch other than the runtime's own only with
 * `customFetchReceivesKeys: true` (the boolean, not a truthy value), whether that fetch is passed in or is the global
 * `fetch` somebody replaced before the client was built. The URL-shape rule applies on both routes. Measured at
 * loopback listeners: raw marker bytes at a CONNECT-aware proxy sink and at the target.
 */
import net from "node:net";

import { ProxyAgent } from "undici";

import { ConfigurationError } from "../../_core/errors";
import { Client } from "../client";
import { Transport } from "../transport";

const MARKER_KEY = ["FIMARK", "ERKEY-", "4f10c9", "b1"].join("");
const MARKER_SECRET = ["FIMARK", "ERSECR", "ET-4f1", "0c9b2"].join("");
const CODE = "custom_fetch_not_opted_in";

class Sink {
  readonly server: net.Server;
  port = 0;
  received = Buffer.alloc(0);
  constructor() {
    this.server = net.createServer((socket) => {
      socket.on("error", () => undefined);
      socket.setTimeout(300, () => socket.destroy());
      let tunnel = false;
      let head = "";
      socket.on("data", (chunk) => {
        this.received = Buffer.concat([this.received, chunk]);
        head += chunk.toString("latin1");
        if (!head.includes("\r\n\r\n")) return;
        if (!tunnel && head.startsWith("CONNECT ")) { tunnel = true; head = ""; socket.write("HTTP/1.1 200 Connection established\r\n\r\n"); return; }
        socket.end("HTTP/1.1 502 Bad Gateway\r\nContent-Length: 0\r\nConnection: close\r\n\r\n");
      });
    });
  }
  async listen(): Promise<void> {
    await new Promise<void>((resolve) => this.server.listen(0, "127.0.0.1", resolve));
    this.port = (this.server.address() as net.AddressInfo).port;
  }
  reset(): void { this.received = Buffer.alloc(0); }
  get markerBytes(): number {
    const blob = this.received.toString("latin1");
    return [MARKER_KEY, MARKER_SECRET].reduce((n, m) => n + (blob.split(m).length - 1), 0);
  }
}
const proxySink = new Sink();
const targetSink = new Sink();
const realFetch = globalThis.fetch;
beforeAll(async () => { await Promise.all([proxySink.listen(), targetSink.listen()]); });
afterAll(() => { proxySink.server.close(); targetSink.server.close(); });
beforeEach(() => { proxySink.reset(); targetSink.reset(); });
afterEach(() => { globalThis.fetch = realFetch; });

const viaProxy = ((input: RequestInfo | URL, init?: RequestInit) =>
  realFetch(input, { ...init, dispatcher: new ProxyAgent(`http://127.0.0.1:${proxySink.port}`) } as RequestInit)) as typeof fetch;
const target = (): string => `http://127.0.0.1:${targetSink.port}`;
const base = (): { apiKey: string; secretKey: string; baseUrl: string; maxRetries: number } => ({ apiKey: MARKER_KEY, secretKey: MARKER_SECRET, baseUrl: target(), maxRetries: 0 });

async function refusal(run: () => Promise<unknown>): Promise<ConfigurationError> {
  try { await run(); } catch (error) {
    if (error instanceof ConfigurationError) return error;
    throw error;
  }
  throw new Error("expected a ConfigurationError");
}

describe("a global fetch replaced before the platform Client is built", () => {
  it("is refused without the opt-in: the replacement is not called and the sinks see 0 marker bytes", async () => {
    const replacement = jest.fn(viaProxy);
    globalThis.fetch = replacement as typeof fetch;
    const error = await refusal(() => new Client(base()).request("GET", "/probe"));
    expect(error.code).toBe(CODE);
    expect(replacement).not.toHaveBeenCalled();
    expect(proxySink.markerBytes).toBe(0);
    expect(targetSink.markerBytes).toBe(0);
  });

  it("is used with the opt-in", async () => {
    globalThis.fetch = viaProxy;
    await new Client({ ...base(), customFetchReceivesKeys: true }).request("GET", "/probe").catch(() => undefined);
    expect(proxySink.markerBytes).toBeGreaterThan(0);
  });

  it("leaves the runtime's own fetch unrestricted for a loopback base URL", async () => {
    await new Client(base()).request("GET", "/probe").catch(() => undefined);
    expect(targetSink.markerBytes).toBeGreaterThan(0);
  });
});

describe("the opt-in for a fetch passed to the platform Client", () => {
  it.each([1, "true", {}, [true]])("is not satisfied by %j: 0 marker bytes", async (value) => {
    const error = await refusal(() => new Client({ ...base(), fetch: viaProxy, customFetchReceivesKeys: value as never }).request("GET", "/probe"));
    expect(error.code).toBe(CODE);
    expect(proxySink.markerBytes).toBe(0);
  });

  it.each([1, "true", {}, [true]])("is not satisfied by %j in the transport's own configuration", async (value) => {
    const transport = new Transport({ apiKey: MARKER_KEY, secretKey: MARKER_SECRET, baseUrl: target(), timeout: 1000, maxRetries: 0, fetch: viaProxy, customFetchReceivesKeys: value as never });
    const error = await refusal(() => transport.raw("GET", "/probe"));
    expect(error.code).toBe(CODE);
    expect(proxySink.markerBytes).toBe(0);
  });
});

describe("the URL-shape rule of the platform Client", () => {
  // a backslash before an @ writes one host that readers of the URL split into two
  const ambiguous = (): string => `http://127.0.0.1:${targetSink.port}\\@other.example`;

  it("refuses an ambiguous base URL for a fetch passed in with the opt-in: the fetch is not called", async () => {
    const calls: string[] = [];
    const counting = (async (input: RequestInfo | URL) => { calls.push(String(input)); return new Response("{}"); }) as typeof fetch;
    const error = await refusal(() => new Client({ ...base(), baseUrl: ambiguous(), fetch: counting, customFetchReceivesKeys: true }).request("GET", "/probe"));
    expect(error.message).toMatch(/backslash/u);
    expect(calls).toHaveLength(0);
  });

  it("refuses an ambiguous base URL for the runtime's own fetch: the target sees 0 marker bytes", async () => {
    const error = await refusal(() => new Client({ ...base(), baseUrl: ambiguous() }).request("GET", "/probe"));
    expect(error.message).toMatch(/backslash/u);
    expect(targetSink.markerBytes).toBe(0);
  });
});
