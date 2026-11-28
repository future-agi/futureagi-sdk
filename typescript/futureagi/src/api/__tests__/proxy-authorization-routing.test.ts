import { randomUUID } from "node:crypto";
import { createServer, type Server } from "node:http";
import type { AddressInfo } from "node:net";

import type { AxiosRequestConfig } from "axios";

import { APIKeyAuth, HttpClient } from "../auth";
import { HttpMethod } from "../types";

interface Seen { line: string; headers: string[] }

let origin: Server;
let proxy: Server;
let originPort: number;
let proxyPort: number;
const atOrigin: Seen[] = [];
const atProxy: Seen[] = [];
let proxyAnswer: (url: string) => { status: number; location?: string } = () => ({ status: 200 });

const record = (into: Seen[]) => (request: { method?: string; url?: string; rawHeaders: string[] }) =>
  into.push({ line: `${request.method} ${request.url}`, headers: request.rawHeaders });

beforeAll(async () => {
  origin = createServer((request, response) => {
    record(atOrigin)(request);
    response.writeHead(200, { "Content-Type": "application/json", Connection: "close" });
    response.end("{}");
  });
  proxy = createServer((request, response) => {
    record(atProxy)(request);
    const answer = proxyAnswer(request.url ?? "");
    response.writeHead(answer.status, { "Content-Type": "application/json", Connection: "close", ...(answer.location ? { Location: answer.location } : {}) });
    response.end("{}");
  });
  await new Promise<void>((resolve) => origin.listen(0, "127.0.0.1", resolve));
  await new Promise<void>((resolve) => proxy.listen(0, "127.0.0.1", resolve));
  originPort = (origin.address() as AddressInfo).port;
  proxyPort = (proxy.address() as AddressInfo).port;
});

afterAll(async () => {
  for (const server of [origin, proxy]) {
    server.closeAllConnections();
    await new Promise<void>((resolve) => server.close(() => resolve()));
  }
});

const PROXY_NAMES = ["HTTP_PROXY", "http_proxy", "HTTPS_PROXY", "https_proxy", "ALL_PROXY", "all_proxy", "NO_PROXY", "no_proxy"];
let saved: Record<string, string | undefined>;

beforeEach(() => {
  atOrigin.length = 0;
  atProxy.length = 0;
  proxyAnswer = () => ({ status: 200 });
  saved = Object.fromEntries(PROXY_NAMES.map((name) => [name, process.env[name]]));
});

afterEach(() => {
  for (const [name, value] of Object.entries(saved)) {
    if (value === undefined) delete process.env[name];
    else process.env[name] = value;
  }
});

function useProxyEnv(noProxy: string): void {
  for (const name of PROXY_NAMES) delete process.env[name];
  process.env.HTTP_PROXY = `http://127.0.0.1:${proxyPort}`;
  process.env.NO_PROXY = noProxy;
}

const markerCount = (seen: Seen[], marker: string): number =>
  seen.reduce((count, request) => count + request.headers.filter((field) => field.includes(marker)).length, 0);

const named = (seen: Seen[], name: string): string[] =>
  seen.flatMap((request) => request.headers.filter((_field, at) => at % 2 === 1 && request.headers[at - 1].toLowerCase() === name.toLowerCase()));

class AxiosClient extends HttpClient {
  fromAxios(config: AxiosRequestConfig) {
    return this._axiosInstance.request(config);
  }

  addInterceptor(name: string, value: string) {
    this._axiosInstance.interceptors.request.use((config) => { config.headers.set(name, value); return config; });
  }
}

class KeyedAxiosClient extends APIKeyAuth {
  fromAxios(config: AxiosRequestConfig) {
    return this._axiosInstance.request(config);
  }
}

const baseUrl = () => `http://127.0.0.1:${originPort}`;
const legacy = (keyed: boolean) => keyed
  ? new APIKeyAuth({ baseUrl: baseUrl(), fiApiKey: `api-${randomUUID()}`, fiSecretKey: `secret-${randomUUID()}`, retryAttempts: 1, timeout: 3000 })
  : new HttpClient({ baseUrl: baseUrl(), retryAttempts: 1, timeout: 3000 });

const forms: Array<[string, (marker: string) => unknown]> = [
  ["a record", (marker) => ({ "Proxy-Authorization": `Basic ${marker}`, "X-Other": "kept" })],
  ["a record with two spellings", (marker) => ({ "proxy-authorization": `Basic ${marker}-a`, "Proxy-Authorization": `Basic ${marker}-b`, "X-Other": "kept" })],
  ["a Headers", (marker) => new Headers([["Proxy-Authorization", `Basic ${marker}`], ["X-Other", "kept"]])],
  ["a Map", (marker) => new Map([["Proxy-Authorization", `Basic ${marker}`], ["X-Other", "kept"]])],
  ["pairs", (marker) => [["Proxy-Authorization", `Basic ${marker}`], ["X-Other", "kept"]]],
  ["pairs with mixed spellings", (marker) => [["Proxy-Authorization", `Basic ${marker}-a`], ["PROXY-AUTHORIZATION", `Basic ${marker}-b`], ["proxy-authorization", `Basic ${marker}-c`], ["X-Other", "kept"]]],
];

describe.each([["an unkeyed", false], ["a keyed", true]] as const)("Proxy-Authorization on %s direct request", (_kind, keyed) => {
  it.each(forms)("is withheld from the host when the call headers are %s", async (_form, make) => {
    const marker = randomUUID();
    await legacy(keyed).request({ url: "/probe", method: HttpMethod.GET, headers: make(marker) as Record<string, string> });
    expect(atOrigin).toHaveLength(1);
    expect(markerCount(atOrigin, marker)).toBe(0);
    expect(named(atOrigin, "X-Other")).toEqual(["kept"]);
  });

  it("is withheld from the host when the client default headers hold it", async () => {
    const marker = randomUUID();
    const defaultHeaders = { "Proxy-Authorization": `Basic ${marker}`, "X-Other": "kept" };
    const client = keyed
      ? new APIKeyAuth({ baseUrl: baseUrl(), fiApiKey: `api-${randomUUID()}`, fiSecretKey: `secret-${randomUUID()}`, retryAttempts: 1, timeout: 3000, defaultHeaders })
      : new HttpClient({ baseUrl: baseUrl(), retryAttempts: 1, timeout: 3000, defaultHeaders });
    await client.request({ url: "/probe", method: HttpMethod.GET });
    expect(markerCount(atOrigin, marker)).toBe(0);
    expect(named(atOrigin, "X-Other")).toEqual(["kept"]);
  });

  it("is withheld from the host on a NO_PROXY match", async () => {
    useProxyEnv("127.0.0.1");
    const marker = randomUUID();
    await legacy(keyed).request({ url: "/probe", method: HttpMethod.GET, headers: { "Proxy-Authorization": `Basic ${marker}` } });
    expect(atProxy).toHaveLength(0);
    expect(atOrigin).toHaveLength(1);
    expect(markerCount(atOrigin, marker)).toBe(0);
  });
});

describe.each(forms)("Proxy-Authorization in fetch option headers held in %s", (_form, make) => {
  it.each(["http", "fetch"])("is withheld from the host on the %s adapter", async (adapter) => {
    const marker = randomUUID();
    const client = new AxiosClient({ baseUrl: baseUrl(), timeout: 3000 });
    await client.fromAxios({ url: "/probe", adapter, fetchOptions: { headers: make(marker) } });
    expect(atOrigin).toHaveLength(1);
    expect(markerCount(atOrigin, marker)).toBe(0);
    expect(named(atOrigin, "X-Other")).toEqual(["kept"]);
  });
});

it.each(["http", "fetch"])("withholds a Proxy-Authorization an interceptor adds from the host on the %s adapter", async (adapter) => {
  const marker = randomUUID();
  const client = new AxiosClient({ baseUrl: baseUrl(), timeout: 3000 });
  client.addInterceptor("Proxy-Authorization", `Basic ${marker}`);
  await client.fromAxios({ url: "/probe", adapter });
  expect(atOrigin).toHaveLength(1);
  expect(markerCount(atOrigin, marker)).toBe(0);
});

it("withholds fetch option Proxy-Authorization from the host on a keyed http adapter request", async () => {
  const marker = randomUUID();
  const client = new KeyedAxiosClient({ baseUrl: baseUrl(), fiApiKey: `api-${randomUUID()}`, fiSecretKey: `secret-${randomUUID()}`, timeout: 3000 });
  await client.fromAxios({ url: "/probe", adapter: "http", fetchOptions: { headers: { "Proxy-Authorization": `Basic ${marker}` } } });
  expect(atOrigin).toHaveLength(1);
  expect(markerCount(atOrigin, marker)).toBe(0);
});

it("withholds Proxy-Authorization from a request that the proxy environment routes", async () => {
  useProxyEnv("");
  const marker = randomUUID();
  await legacy(false).request({ url: "/probe", method: HttpMethod.GET, headers: [["Proxy-Authorization", `Basic ${marker}`]] as unknown as Record<string, string> });
  expect(atOrigin).toHaveLength(0);
  expect(atProxy).toHaveLength(1);
  expect(atProxy[0].line).toBe(`GET http://127.0.0.1:${originPort}/probe`);
  expect(markerCount(atProxy, marker)).toBe(0);
});

const proxyOption = () => ({ protocol: "http", host: "127.0.0.1", port: proxyPort });

it("sends Proxy-Authorization to the proxy named by the Axios proxy option", async () => {
  const marker = randomUUID();
  const client = new AxiosClient({ baseUrl: baseUrl(), timeout: 3000 });
  await client.fromAxios({
    url: "/probe",
    proxy: proxyOption(),
    fetchOptions: { headers: new Headers([["Proxy-Authorization", `Basic ${marker}`]]) },
  });
  expect(atOrigin).toHaveLength(0);
  expect(atProxy).toHaveLength(1);
  expect(markerCount(atProxy, marker)).toBe(1);
});

it("withholds Proxy-Authorization from an https URL sent through the Axios proxy option", async () => {
  const marker = randomUUID();
  const client = new AxiosClient({ baseUrl: `https://127.0.0.1:${originPort}`, timeout: 3000 });
  await client.fromAxios({ url: "/probe", proxy: proxyOption(), headers: { "Proxy-Authorization": `Basic ${marker}` } }).catch(() => undefined);
  expect(markerCount(atProxy, marker)).toBe(0);
  expect(markerCount(atOrigin, marker)).toBe(0);
});

it("withholds Proxy-Authorization from a redirect hop to an https URL through the same proxy", async () => {
  proxyAnswer = (url) => (url.endsWith("/probe") ? { status: 302, location: `https://127.0.0.1:${originPort}/landing` } : { status: 200 });
  const marker = randomUUID();
  const client = new AxiosClient({ baseUrl: baseUrl(), timeout: 3000 });
  await client.fromAxios({ url: "/probe", proxy: proxyOption(), headers: { "Proxy-Authorization": `Basic ${marker}` } }).catch(() => undefined);
  expect(atProxy.length).toBeGreaterThanOrEqual(1);
  expect(atProxy[0].line).toBe(`GET http://127.0.0.1:${originPort}/probe`);
  expect(markerCount(atProxy.slice(0, 1), marker)).toBe(1);
  expect(markerCount(atProxy.slice(1), marker)).toBe(0);
  expect(markerCount(atOrigin, marker)).toBe(0);
});

it("withholds Proxy-Authorization from each hop of a direct redirect", async () => {
  proxyAnswer = () => ({ status: 302, location: `${baseUrl()}/landing` });
  const marker = randomUUID();
  const client = new HttpClient({ baseUrl: `http://127.0.0.1:${proxyPort}`, retryAttempts: 1, timeout: 3000 });
  await client.request({ url: "/probe", method: HttpMethod.GET, headers: { "Proxy-Authorization": `Basic ${marker}` } });
  expect(atProxy).toHaveLength(1);
  expect(atOrigin).toHaveLength(1);
  expect(markerCount(atProxy, marker) + markerCount(atOrigin, marker)).toBe(0);
});

it("does not send a Proxy-Authorization set by extraHeaders to a forward proxy", async () => {
  const marker = randomUUID();
  const client = new AxiosClient({ baseUrl: baseUrl(), timeout: 3000, extraHeaders: { "Proxy-Authorization": `Bearer ${marker}` } });
  await client.fromAxios({ url: "/probe", proxy: proxyOption() });
  expect(atProxy).toHaveLength(1);
  expect(markerCount(atProxy, marker)).toBe(0);
});

it("sends a Proxy-Authorization set by extraHeaders to a URL under the base URL", async () => {
  const marker = randomUUID();
  const client = new HttpClient({ baseUrl: baseUrl(), retryAttempts: 1, timeout: 3000, extraHeaders: { "Proxy-Authorization": `Bearer ${marker}` } });
  await client.request({ url: "/probe", method: HttpMethod.GET, headers: { "Proxy-Authorization": "Basic call-value" } });
  expect(named(atOrigin, "Proxy-Authorization")).toEqual([`Bearer ${marker}`]);
});
