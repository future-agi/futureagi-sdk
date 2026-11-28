/**
 * The platform transport decides plain HTTP on the host as the base URL writes it (tests/fixtures/loopback/hosts.json,
 * "request_urls"): 127.0.0.1. and 127.1 and 0x7f.0.0.1 and 2130706433 are not loopback.
 */
import { readFileSync } from "node:fs";
import { join } from "node:path";

import { Client } from "../client";
import { setRuntimeFetch } from "../transport";

const ROWS = (JSON.parse(readFileSync(join(__dirname, "../../../../../tests/fixtures/loopback/hosts.json"), "utf8")) as {
  request_urls: { url: string; loopback: boolean }[];
}).request_urls;
const ROW_PAIRS = ROWS.map((row) => [row.url, row.loopback] as const);

const SAVED = process.env.FI_ALLOW_INSECURE_HTTP;
beforeEach(() => { delete process.env.FI_ALLOW_INSECURE_HTTP; });
let afterEachRestore: jest.SpyInstance | undefined;
afterEach(() => { setRuntimeFetch(); afterEachRestore?.mockRestore(); afterEachRestore = undefined; if (SAVED === undefined) delete process.env.FI_ALLOW_INSECURE_HTTP; else process.env.FI_ALLOW_INSECURE_HTTP = SAVED; });

describe("the platform transport reads the written host", () => {
  it.each(ROW_PAIRS)("keys to %s: loopback is %s", async (url, loopback) => {
    const calls: string[] = [];
    // the SDK's own transport over the runtime's fetch, replaced here so no request leaves the process
    const runtime = jest.spyOn(globalThis, "fetch").mockImplementation((async (target: string) => {
      calls.push(target);
      return new Response("{}", { status: 200, headers: { "content-type": "application/json" } });
    }) as never);
    afterEachRestore = runtime;
    setRuntimeFetch(globalThis.fetch);
    const client = new Client({ apiKey: "k", secretKey: "s", baseUrl: url.replace(/\/$/u, ""), maxRetries: 0 });
    const sent = Promise.resolve().then(() => client.request("GET", "/probe"));
    if (loopback) {
      await expect(sent).resolves.toBeDefined();
      expect(calls).toHaveLength(1);
    } else {
      await expect(sent).rejects.toThrow(/http/iu);
      expect(calls).toHaveLength(0);
    }
  });
});
