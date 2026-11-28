/**
 * A key-carrying platform call that gets a 3xx answer is refused as a redirect (`APIConnectionError`, "not followed") and sends nothing more, also when
 * the redirect stays on the client's own origin. Measured at a loopback listener behind the runtime's own fetch: the
 * marker bytes it receives are those of one request.
 */
import { createServer, type Server } from "node:http";
import { type AddressInfo } from "node:net";

import { Client } from "../client";
import { APIConnectionError } from "../errors";

const MARKER_KEY = ["FIMARK", "ERKEY-", "2b6d90", "e1"].join("");
const MARKER_SECRET = ["FIMARK", "ERSECR", "ET-2b6", "d90e2"].join("");

const servers: Server[] = [];
afterEach(() => { for (const server of servers.splice(0)) server.close(); });

async function listener(status: number): Promise<{ base: string; requests: () => number; markerCount: () => number }> {
  let requests = 0;
  let markers = 0;
  const server = createServer((req, res) => {
    requests += 1;
    for (const value of [req.headers["x-api-key"], req.headers["x-secret-key"]]) if (value === MARKER_KEY || value === MARKER_SECRET) markers += 1;
    req.resume();
    res.writeHead(status, { location: `/second${req.url ?? "/"}` }).end();
  });
  await new Promise<void>((resolve) => { server.listen(0, "127.0.0.1", resolve); });
  servers.push(server);
  return { base: `http://127.0.0.1:${(server.address() as AddressInfo).port}`, requests: () => requests, markerCount: () => markers };
}

describe("a same-origin redirect to a key-carrying platform call", () => {
  it.each([300, 301, 302, 303, 304, 305, 307, 308])("is refused for a %i: one request, the keys sent once", async (status) => {
    const { base, requests, markerCount } = await listener(status);
    const client = new Client({ apiKey: MARKER_KEY, secretKey: MARKER_SECRET, baseUrl: base, maxRetries: 0 });
    const error = await client.request("GET", "/probe").catch((e: unknown) => e);
    expect(error).toBeInstanceOf(APIConnectionError);
    expect((error as Error).message).toMatch(/not followed/);
    expect(requests()).toBe(1);
    expect(markerCount()).toBe(2);
  });
});
