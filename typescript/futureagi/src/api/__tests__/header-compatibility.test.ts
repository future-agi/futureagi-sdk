import { randomUUID } from "node:crypto";
import { createServer, type Server } from "node:http";
import type { AddressInfo } from "node:net";

import type { AxiosRequestConfig } from "axios";

import { Client } from "../../platform/client";
import { HttpClient } from "../auth";
import { HttpMethod } from "../types";

let listener: Server;
let baseUrl: string;
const requests: string[][] = [];
const bodies: string[] = [];

beforeAll(async () => {
  listener = createServer((request, response) => {
    requests.push(request.rawHeaders);
    const chunks: Buffer[] = [];
    request.on("data", (chunk: Buffer) => chunks.push(chunk));
    request.on("end", () => bodies.push(Buffer.concat(chunks).toString("latin1")));
    response.writeHead(200, { "Content-Type": "application/json", Connection: "close" });
    response.end("{}");
  });
  await new Promise<void>((resolve) => listener.listen(0, "127.0.0.1", resolve));
  baseUrl = `http://127.0.0.1:${(listener.address() as AddressInfo).port}`;
});

afterAll(async () => {
  listener.closeAllConnections();
  await new Promise<void>((resolve) => listener.close(() => resolve()));
});

beforeEach(() => { requests.length = 0; bodies.length = 0; });

function values(name: string): string[] {
  expect(requests).toHaveLength(1);
  const [request] = requests;
  const matching: string[] = [];
  for (let at = 0; at < request.length; at += 2) {
    if (request[at].toLowerCase() === name.toLowerCase()) matching.push(request[at + 1]);
  }
  return matching;
}

class AxiosClient extends HttpClient {
  fromAxios(config: AxiosRequestConfig) {
    return this._axiosInstance.request(config);
  }

  setGetContentType(value: string) {
    this._axiosInstance.defaults.headers.get["Content-Type"] = value;
  }
}

const legacy = () => new HttpClient({ baseUrl, retryAttempts: 1, timeout: 3000 });
const platform = () => new Client({ baseUrl, apiKey: randomUUID(), secretKey: randomUUID(), maxRetries: 0, timeout: 3000 });
const legacyCall = (method: HttpMethod, headers: unknown, data?: Record<string, unknown> | string) =>
  legacy().request({ url: "/probe", method, headers: headers as Record<string, string>, ...(data === undefined ? {} : { data: data as Record<string, unknown> }) });
const legacyGet = (headers: unknown) => legacyCall(HttpMethod.GET, headers);
const platformGet = (headers: unknown) => platform().request("GET", "/probe", {}, { headers: headers as Record<string, string> });

it.each(["http", "fetch"])("merges fetch option headers by name on the %s adapter", async (adapter) => {
  const client = new AxiosClient({ baseUrl, timeout: 3000 });
  const response = await client.fromAxios({
    url: "/probe",
    adapter,
    headers: { "X-Trace": "request", "X-Request": "kept" },
    fetchOptions: { headers: new Headers([["x-trace", "option"], ["X-Option", "added"]]) },
  });
  expect(response.status).toBe(200);
  expect(values("X-Trace")).toEqual(["option"]);
  expect(values("X-Request")).toEqual(["kept"]);
  expect(values("X-Option")).toEqual(["added"]);
});

it.each(["http", "fetch"])("uses the last fetch option header across letter cases on the %s adapter", async (adapter) => {
  const client = new AxiosClient({ baseUrl, timeout: 3000 });
  await client.fromAxios({
    url: "/probe",
    adapter,
    fetchOptions: { headers: [["X-Trace", "first"], ["x-trace", "second"], ["X-Trace", "third"]] },
  });
  expect(values("X-Trace")).toEqual(["third"]);
});

it("classifies headers from fetch options before selecting an adapter route", async () => {
  const client = new AxiosClient({ baseUrl, timeout: 3000 });
  await expect(client.fromAxios({
    url: "/probe",
    adapter: "fetch",
    fetchOptions: { headers: { "X-Api-Key": randomUUID() } },
  })).rejects.toMatchObject({ code: "keyed_adapter_unsupported" });
  expect(requests).toHaveLength(0);
});

it.each(["X-Trace", "Cookie"])("uses the last value across three spellings of platform header %s", async (name) => {
  await platformGet([[name, "v=first"], [name.toLowerCase(), "v=second"], [name, "v=third"]]);
  expect(values(name)).toEqual(["v=third"]);
});

it("reads platform headers from a non-iterable container with forEach and get", async () => {
  await platformGet({
    forEach(append: (value: string, name: string) => void) { append("kept", "X-Trace"); },
    get(name: string) { return name.toLowerCase() === "x-trace" ? "kept" : null; },
  });
  expect(values("X-Trace")).toEqual(["kept"]);
  expect(values("forEach")).toEqual([]);
  expect(values("get")).toEqual([]);
});

it("writes each Set-Cookie value in native Headers on a legacy request", async () => {
  const headers = new Headers();
  headers.append("Set-Cookie", "a=1");
  headers.append("Set-Cookie", "b=2");
  await legacyGet(headers);
  expect(values("Set-Cookie")).toEqual(["a=1", "b=2"]);
});

it.each([
  ["legacy", legacyGet],
  ["platform", platformGet],
] as const)("writes numeric field names on a %s request", async (_client, get) => {
  await get({ 123: "kept" });
  expect(values("123")).toEqual(["kept"]);
});

it("omits Content-Type on a bodyless legacy GET with pair headers", async () => {
  await legacyGet([["X-Trace", "kept"]]);
  expect(values("X-Trace")).toEqual(["kept"]);
  expect(values("Content-Type")).toEqual([]);
});

it("sends an explicit Content-Type on a bodyless legacy GET with pair headers", async () => {
  await legacyGet([["Content-Type", "application/example"]]);
  expect(values("Content-Type")).toEqual(["application/example"]);
});

it("uses the Axios method's explicit content type on a bodyless legacy GET with pair headers", async () => {
  const client = new AxiosClient({ baseUrl, retryAttempts: 1, timeout: 3000 });
  client.setGetContentType("application/method-example");
  await client.request({ url: "/probe", method: HttpMethod.GET, headers: [["X-Trace", "kept"]] as unknown as Record<string, string> });
  expect(values("Content-Type")).toEqual(["application/method-example"]);
});

it.each(["X-Trace", "Cookie"])("keeps the value Axios merges from three spellings of legacy header %s", async (name) => {
  await legacyGet([[name, "v=first"], [name.toLowerCase(), "v=second"], [name, "v=third"]]);
  expect(values(name)).toEqual(["v=second"]);
});

it.each([
  ["X-Trace", ["v=b", "v=c"]],
  ["Cookie", ["v=b; v=c"]],
])("writes each value of a repeated legacy pair name %s", async (name, sent) => {
  await legacyGet([[name, "v=b"], [name, "v=c"]]);
  expect(values(name)).toEqual(sent);
});

it.each([
  ["legacy", legacyGet],
  ["platform", platformGet],
] as const)("reads a numeric field holding a list as a header name on a %s request", async (client, get) => {
  await get({ 123: ["x-probe", "last"] });
  expect(values("x-probe")).toEqual([]);
  if (client === "legacy") expect(values("123")).toEqual(["x-probe", "last"]);
  else expect(values("123")).toEqual(["x-probe,last"]);
});

it("writes a one-item numeric field list on a legacy request", async () => {
  await legacyGet({ 123: ["kept"] });
  expect(values("123")).toEqual(["kept"]);
});

it("writes each Set-Cookie value of an undici package Headers on a legacy request", async () => {
  // eslint-disable-next-line @typescript-eslint/no-require-imports
  const { Headers: PackageHeaders } = require("undici") as { Headers: typeof Headers };
  const headers = new PackageHeaders();
  headers.append("Set-Cookie", "a=1");
  headers.append("Set-Cookie", "b=2");
  await legacyGet(headers);
  expect(values("Set-Cookie")).toEqual(["a=1", "b=2"]);
});

it("sends the last Set-Cookie of fetch option Headers on the fetch adapter", async () => {
  const client = new AxiosClient({ baseUrl, timeout: 3000 });
  const headers = new Headers();
  headers.append("Set-Cookie", "a=1");
  headers.append("Set-Cookie", "b=2");
  await client.fromAxios({ url: "/probe", adapter: "fetch", fetchOptions: { headers } });
  expect(values("Set-Cookie")).toEqual(["b=2"]);
});

function* pairs(): Generator<[string, string]> { yield ["X-Trace", "kept"]; }
const forms: Array<[string, () => unknown]> = [
  ["pairs", () => [["X-Trace", "kept"]]],
  ["a Map", () => new Map([["X-Trace", "kept"]])],
  ["a Set", () => new Set([["X-Trace", "kept"]])],
  ["a generator", () => pairs()],
  ["a Headers", () => new Headers([["X-Trace", "kept"]])],
  ["null", () => null],
];

describe.each(forms)("legacy headers in %s", (_form, make) => {
  it.each([HttpMethod.GET, HttpMethod.DELETE, "HEAD", "OPTIONS"])("omits Content-Type on a bodyless %s", async (method) => {
    await legacyCall(method as HttpMethod, make());
    expect(values("Content-Type")).toEqual([]);
  });

  it("sends a string POST body as given with the Axios form content type", async () => {
    await legacyCall(HttpMethod.POST, make(), "plain text body");
    expect(values("Content-Type")).toEqual(["application/x-www-form-urlencoded"]);
    expect(bodies).toEqual(["plain text body"]);
  });

  it("sends an object POST body as JSON", async () => {
    await legacyCall(HttpMethod.POST, make(), { name: "value" });
    expect(values("Content-Type")).toEqual(["application/json"]);
    expect(bodies).toEqual(['{"name":"value"}']);
  });
});

it("keeps Content-Type on a bodyless legacy GET with record headers", async () => {
  await legacyGet({ "X-Trace": "kept" });
  expect(values("Content-Type")).toEqual(["application/json"]);
});

it.each([
  ["forEach", { forEach(append: (value: string, name: string) => void) { append("kept", "X-Trace"); } }],
  ["get", { get(name: string) { return name; } }],
] as const)("refuses a legacy container with a %s method alone before any connection", async (method, container) => {
  await expect(legacyGet(container)).rejects.toMatchObject({ code: "unreadable_headers", message: expect.stringContaining(`a ${method} method`) });
  await expect(platformGet(container)).rejects.toMatchObject({ code: "unreadable_headers" });
  expect(requests).toHaveLength(0);
});

it.each([
  [[["X-Api-Key", "planted-marker-value"], ["x-api-key", ""]]],
  [[["X-Api-Key", ""], ["X-Api-Key", "planted-marker-value"]]],
])("refuses a key header given once empty and once with a value before any connection", async (headers) => {
  await expect(legacyGet(headers)).rejects.toMatchObject({ code: "unreadable_headers" });
  await expect(platformGet(headers)).rejects.toMatchObject({ code: "unreadable_headers" });
  expect(requests).toHaveLength(0);
});

it("keeps a repeated legacy pair name whose first value is empty", async () => {
  await legacyGet([["X-Trace", ""], ["X-Trace", "second"]]);
  expect(values("X-Trace")).toEqual(["", "second"]);
});

it("keeps Content-Type on a bodyless legacy GET with a record from another realm", async () => {
  // eslint-disable-next-line @typescript-eslint/no-require-imports
  const { runInNewContext } = require("node:vm") as typeof import("node:vm");
  await legacyGet(runInNewContext('({ "X-Trace": "kept" })'));
  expect(values("X-Trace")).toEqual(["kept"]);
  expect(values("Content-Type")).toEqual(["application/json"]);
});

it("keeps Content-Type on a bodyless legacy GET with a plain forEach and get object", async () => {
  await legacyGet({
    forEach(append: (value: string, name: string) => void) { append("kept", "X-Trace"); },
    get(name: string) { return name.toLowerCase() === "x-trace" ? "kept" : null; },
  });
  expect(values("X-Trace")).toEqual(["kept"]);
  expect(values("Content-Type")).toEqual(["application/json"]);
});
