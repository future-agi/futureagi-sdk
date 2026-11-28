import { randomBytes } from "node:crypto";
import { createServer, type AddressInfo, type Server } from "node:net";
import { Client } from "../client";

const marker = () => `PAMARK-${randomBytes(12).toString("hex")}`;
const credentials = { apiKey: marker(), secretKey: marker() };
const caller = marker();
const duplicate = marker();
const custom = "origin-probe";
const proxyHeader = "pRoXy-AuThOrIzAtIoN";
const probeHeader = "X-Origin-Probe";
const pairs: [string, string][] = [[proxyHeader, `Basic ${caller}`], [probeHeader, custom]];
const mixedPairs: [string, string][] = [...pairs, ["PROXY-AUTHORIZATION", `Bearer ${duplicate}`]];
const forms = [
  ["record", () => Object.fromEntries(pairs)],
  ["Headers", () => new Headers(pairs)],
  ["Map", () => new Map(pairs)],
  ["pairs", () => pairs.slice()],
  ["mixed-case duplicate pairs", () => mixedPairs.slice()],
] as const;

// The runtime accepts iterable headers on SDK entry points with record-only types.
const record = (input: unknown) => input as Record<string, string>;
let server: Server;
let origin: string;
const observed: Buffer[] = [];
const json = "{}";

beforeAll(async () => {
  server = createServer((socket) => {
    let bytes = Buffer.alloc(0);
    const read = (chunk: Buffer) => {
      bytes = Buffer.concat([bytes, chunk]);
      const end = bytes.indexOf("\r\n\r\n");
      if (end < 0) return;
      socket.off("data", read);
      const headers = bytes.subarray(0, end + 4);
      observed.push(headers);
      const status = headers.includes("/retry ") && observed.length === 1 ? "503 Service Unavailable\r\nRetry-After: 0" : "200 OK";
      socket.end(`HTTP/1.1 ${status}\r\nContent-Type: application/json\r\nContent-Length: ${Buffer.byteLength(json)}\r\nConnection: close\r\n\r\n${json}`);
    };
    socket.on("data", read);
  });
  await new Promise<void>((resolve, reject) => {
    server.once("error", reject);
    server.listen(0, "127.0.0.1", resolve);
  });
  origin = `http://127.0.0.1:${(server.address() as AddressInfo).port}`;
});

afterAll(async () => {
  await new Promise<void>((resolve, reject) => server.close((error) => error ? reject(error) : resolve()));
});

beforeEach(() => {
  observed.length = 0;
  jest.replaceProperty(process, "env", {
    HTTP_PROXY: "http://127.0.0.1:9",
    HTTPS_PROXY: "http://127.0.0.1:9",
    ALL_PROXY: "http://127.0.0.1:9",
    NO_PROXY: "localhost,127.0.0.1,::1",
  });
});
afterEach(() => jest.restoreAllMocks());

function platform(defaultHeaders?: Record<string, string>) {
  return new Client({ ...credentials, baseUrl: origin, maxRetries: 0, defaultHeaders });
}

function expectOrigin(configured?: string, count = 1) {
  expect(observed).toHaveLength(count);
  for (const bytes of observed) {
    expect(bytes.indexOf(caller)).toBe(-1);
    expect(bytes.indexOf(duplicate)).toBe(-1);
    const lines = bytes.toString("latin1").split("\r\n");
    expect(lines.map((line) => line.toLowerCase())).toContain(`${probeHeader.toLowerCase()}: ${custom}`);
    const received = lines.filter((line) => /^proxy-authorization:/i.test(line)).map((line) => line.slice(line.indexOf(":") + 2));
    expect(received).toEqual(configured === undefined ? [] : [configured]);
  }
}

describe.each(forms)("origin headers with %s input", (_form, headers) => {
  it("platform Client excludes credentials from default headers", async () => {
    await platform(record(headers())).request("GET", "/probe");
    expectOrigin();
  });

  it("platform Transport excludes credentials from call headers", async () => {
    await platform().transport.raw("GET", "/probe", {}, { headers: record(headers()) });
    expectOrigin();
  });
});
it("platform transport omits caller proxy credentials on each retry", async () => {
  const client = new Client({ ...credentials, baseUrl: origin, maxRetries: 1, defaultHeaders: record(mixedPairs) });
  await client.request("GET", "/retry");
  expectOrigin(undefined, 2);
});
