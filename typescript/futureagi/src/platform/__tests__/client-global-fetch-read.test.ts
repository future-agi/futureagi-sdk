/**
 * The platform `Client` built without a `fetch` option reads `globalThis.fetch` once, and keeps the function it read: a
 * getter on the global that answers with another function on a second read changes nothing.
 */
import { Client } from "../client";

const KEY = "marker-globalread-key-0000000000";
const SECRET = "marker-globalread-secret-0000000000";

describe("the platform Client and globalThis.fetch", () => {
  const saved = Object.getOwnPropertyDescriptor(globalThis, "fetch");
  afterEach(() => { if (saved !== undefined) Object.defineProperty(globalThis, "fetch", saved); });

  it("reads the global once when no fetch option is given", () => {
    const first = (async () => new Response("{}")) as typeof fetch;
    const second = (async () => new Response("{}")) as typeof fetch;
    let reads = 0;
    Object.defineProperty(globalThis, "fetch", { configurable: true, get: () => (++reads === 1 ? first : second) });
    const client = new Client({ apiKey: KEY, secretKey: SECRET, baseUrl: "https://api.example.test" });
    process.stdout.write(`globalThis.fetch reads: ${reads}\n`);
    expect(reads).toBe(1);
    expect((client as unknown as { transport: { config: { fetch: unknown } } }).transport.config.fetch).toBe(first);
  });

  it("does not read the global when a fetch option is given", () => {
    let reads = 0;
    const own = (async () => new Response("{}")) as typeof fetch;
    Object.defineProperty(globalThis, "fetch", { configurable: true, get: () => { reads += 1; return own; } });
    new Client({ apiKey: KEY, secretKey: SECRET, baseUrl: "https://api.example.test", fetch: own, customFetchReceivesKeys: true });
    expect(reads).toBe(0);
  });
});
