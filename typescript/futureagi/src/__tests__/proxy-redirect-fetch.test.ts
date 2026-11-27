// Keyed requests through a proxy: redirects followed by the axios sender, and axios's fetch adapter.
//
// Every listener is on the loopback address. The target and the proxy are addressed by a name that a lookup shim
// resolves to 127.0.0.1, so each counts as a host that is not loopback while its bytes land in a listener of this
// file. The target is an https listener trusted through a scratch CA and records what it reads after TLS; the proxy
// records every request it receives, as CONNECT or in absolute form, with the raw bytes (tunnelled bytes included).
// Keys are random marker strings made per test.

/* eslint-disable @typescript-eslint/no-explicit-any */
import { randomBytes } from "node:crypto";

import { HttpClient } from "../api/auth";

// eslint-disable-next-line @typescript-eslint/no-var-requires
const fx = require("./support/proxy-sinks.cjs");

jest.setTimeout(30_000);

type Target = { port: number; connections: number; requests: string[]; raw(): string; count(markers: string[]): number; close(): Promise<void> };
type Proxy = { port: number; connections: number; connects: string[]; absolute: string[]; raw(): string; count(markers: string[]): number; close(): Promise<void> };

const SHIM: string = fx.SHIM_HOST;

// --- the lookup shim and the scratch CA -----------------------------------------------------------------------

let undoLookup: () => void = () => undefined;
beforeAll(() => {
  fx.certificates();
  undoLookup = fx.shimLookup();
});
afterAll(() => {
  undoLookup();
});

// --- listeners, closed after each test ------------------------------------------------------------------------

const open: Array<{ close(): Promise<void> }> = [];
async function target(respond?: (head: string, index: number) => string | undefined): Promise<Target> {
  const made: Target = await fx.tlsTarget(respond);
  open.push(made);
  return made;
}
async function proxySink(options: Record<string, unknown> = {}): Promise<Proxy> {
  const made: Proxy = await fx.proxySink(options);
  open.push(made);
  return made;
}
afterEach(async () => {
  while (open.length) await open.pop()!.close();
});

// --- environment ----------------------------------------------------------------------------------------------

const ENV_NAMES = [
  "HTTP_PROXY",
  "http_proxy",
  "HTTPS_PROXY",
  "https_proxy",
  "ALL_PROXY",
  "all_proxy",
  "NO_PROXY",
  "no_proxy",
  "npm_config_https_proxy",
  "npm_config_http_proxy",
  "npm_config_proxy",
  "npm_config_no_proxy",
  "FI_ALLOW_INSECURE_HTTP",
];

/** Run `run` with every proxy variable cleared and then `set` applied; restore the environment afterwards. */
async function withEnv<T>(set: Record<string, string>, run: () => Promise<T>): Promise<T> {
  const saved = new Map(ENV_NAMES.map((name) => [name, process.env[name]]));
  for (const name of ENV_NAMES) delete process.env[name];
  Object.assign(process.env, set);
  try {
    return await run();
  } finally {
    for (const [name, value] of saved) {
      if (value === undefined) delete process.env[name];
      else process.env[name] = value;
    }
  }
}

// --- clients and requests -------------------------------------------------------------------------------------

const marker = (tag: string) => `fitest_${tag}_${randomBytes(8).toString("hex")}`;

type AdapterName = "http adapter" | "fetch adapter";
const ADAPTERS: AdapterName[] = ["http adapter", "fetch adapter"];

function client(baseUrl: string, adapter: AdapterName, defaultHeaders: Record<string, string>): HttpClient {
  const made = new HttpClient({ baseUrl, retryAttempts: 1, timeout: 5000, defaultHeaders } as any);
  if (adapter === "fetch adapter") (made as any)._axiosInstance.defaults.adapter = "fetch";
  return made;
}

/** X-Api-Key, X-Secret-Key and an Authorization Bearer header, each with its own marker. */
function allKeys(): { headers: Record<string, string>; markers: string[] } {
  const [apiKey, secretKey, token] = [marker("pa"), marker("ps"), marker("pz")];
  return { headers: { "X-Api-Key": apiKey, "X-Secret-Key": secretKey, Authorization: `Bearer ${token}` }, markers: [apiKey, secretKey, token] };
}

/** Resolve to "(resolved)", or to the code (or message) of what the request rejected with. */
async function outcome(run: () => Promise<unknown>): Promise<string> {
  return run().then(
    () => "(resolved)",
    (e: any) => (e instanceof Error ? ((e as { code?: string }).code ?? e.message) : "(not an Error)"),
  );
}

const get = (c: HttpClient, url = "/v1/probe") => c.request({ method: "GET", url } as any);

const KEY_HEADER = /^(x-api-key|x-secret-key|authorization|cookie)\s*:/im;
const connectAuthority = (head: string) => head.split("\r\n")[0].split(" ")[1];
const connectsWithKeyHeaders = (proxy: Proxy) => proxy.connects.filter((head) => KEY_HEADER.test(head.split("\r\n").slice(1).join("\r\n"))).length;
const redirect = (status: number, location: string) => `HTTP/1.1 ${status} Redirect\r\nLocation: ${location}\r\nContent-Length: 0\r\nConnection: close\r\n\r\n`;
const requestPath = (head: string) => head.split("\r\n")[0].split(" ")[1];

// --- redirects --------------------------------------------------------------------------------------------------

describe("a keyed https request through HTTPS_PROXY that is redirected", () => {
  test.each(ADAPTERS)(
    "%s: a 302 to a path on the same origin reaches the proxy only as CONNECT on both hops, and the key reaches the target on both hops",
    async (adapter) => {
      const { headers, markers } = allKeys();
      const site = await target((_head, index) => (index === 0 ? redirect(302, "/v1/next") : undefined));
      const proxy = await proxySink();
      const result = await withEnv({ HTTPS_PROXY: `http://${SHIM}:${proxy.port}` }, () => outcome(() => get(client(`https://${SHIM}:${site.port}`, adapter, headers))));
      expect({
        result,
        proxyKeyBytes: proxy.count(markers),
        absolute: proxy.absolute.length,
        tunnelledHops: proxy.connects.length >= 2,
        connectAuthorities: [...new Set(proxy.connects.map(connectAuthority))],
        connectsWithKeyHeaders: connectsWithKeyHeaders(proxy),
        targetPaths: site.requests.map(requestPath),
        keyedHops: site.requests.map((head) => markers.every((m) => head.includes(m))),
      }).toEqual({
        result: "(resolved)",
        proxyKeyBytes: 0,
        absolute: 0,
        tunnelledHops: true,
        connectAuthorities: [`${SHIM}:${site.port}`],
        connectsWithKeyHeaders: 0,
        targetPaths: ["/v1/probe", "/v1/next"],
        keyedHops: [true, true],
      });
    },
  );

  test.each(ADAPTERS)(
    "%s: a 307 to another https origin tunnels the first hop, the second hop carries no key, and the proxy reads none of the key over the chain",
    async (adapter) => {
      const { headers, markers } = allKeys();
      const second = await target();
      const first = await target((_head, index) => (index === 0 ? redirect(307, `https://${SHIM}:${second.port}/v1/next`) : undefined));
      const proxy = await proxySink();
      const result = await withEnv({ HTTPS_PROXY: `http://${SHIM}:${proxy.port}` }, () => outcome(() => get(client(`https://${SHIM}:${first.port}`, adapter, headers))));
      const firstOrigin = `${SHIM}:${first.port}`;
      expect({
        result,
        proxyKeyBytes: proxy.count(markers),
        firstHopTunnelled: proxy.connects.length >= 1 && connectAuthority(proxy.connects[0]) === firstOrigin,
        absoluteToFirstOrigin: proxy.absolute.filter((head) => requestPath(head).includes(`//${firstOrigin}/`)).length,
        connectsWithKeyHeaders: connectsWithKeyHeaders(proxy),
        firstHopKeyed: first.requests.length === 1 && markers.every((m) => first.requests[0].includes(m)),
        secondHopMade: second.requests.length > 0 || proxy.absolute.some((head) => requestPath(head).includes(`//${SHIM}:${second.port}/v1/next`)),
        secondOriginKeyBytes: second.count(markers),
      }).toEqual({
        result: "(resolved)",
        proxyKeyBytes: 0,
        firstHopTunnelled: true,
        absoluteToFirstOrigin: 0,
        connectsWithKeyHeaders: 0,
        firstHopKeyed: true,
        secondHopMade: true,
        secondOriginKeyBytes: 0,
      });
    },
  );
});

// --- the axios fetch adapter ------------------------------------------------------------------------------------

describe("axios fetch adapter", () => {
  const FORMS: Array<[string, () => { headers: Record<string, string>; markers: string[] }]> = [
    [
      "X-Api-Key and X-Secret-Key",
      () => {
        const [apiKey, secretKey] = [marker("fa"), marker("fs")];
        return { headers: { "X-Api-Key": apiKey, "X-Secret-Key": secretKey }, markers: [apiKey, secretKey] };
      },
    ],
    [
      "Authorization Bearer",
      () => {
        const token = marker("fz");
        return { headers: { Authorization: `Bearer ${token}` }, markers: [token] };
      },
    ],
  ];

  test.each(FORMS.map(([name]) => name))("a keyed https request (%s) through HTTPS_PROXY reaches the proxy only as CONNECT and the key reaches the target", async (form) => {
    const { headers, markers } = FORMS.find(([name]) => name === form)![1]();
    const site = await target();
    const proxy = await proxySink();
    const result = await withEnv({ HTTPS_PROXY: `http://${SHIM}:${proxy.port}` }, () => outcome(() => get(client(`https://${SHIM}:${site.port}`, "fetch adapter", headers))));
    expect({
      result,
      proxyKeyBytes: proxy.count(markers),
      absolute: proxy.absolute.length,
      tunnelled: proxy.connects.length >= 1,
      connectAuthorities: [...new Set(proxy.connects.map(connectAuthority))],
      connectsWithKeyHeaders: connectsWithKeyHeaders(proxy),
      targetKeyed: site.count(markers) > 0,
    }).toEqual({
      result: "(resolved)",
      proxyKeyBytes: 0,
      absolute: 0,
      tunnelled: true,
      connectAuthorities: [`${SHIM}:${site.port}`],
      connectsWithKeyHeaders: 0,
      targetKeyed: true,
    });
  });

  test("with no proxy variable set, a keyed https request is sent by the fetch adapter directly to the target", async () => {
    const { headers, markers } = allKeys();
    const site = await target();
    const proxy = await proxySink();
    const result = await withEnv({}, () => outcome(() => get(client(`https://${SHIM}:${site.port}`, "fetch adapter", headers))));
    expect({
      result,
      proxyConnections: proxy.connections,
      targetKeyed: site.count(markers) > 0,
      // fetch marks its requests with sec-fetch-mode; axios's http adapter does not send it
      sentByFetch: site.requests.length === 1 && /^sec-fetch-mode\s*:/im.test(site.requests[0]),
    }).toEqual({ result: "(resolved)", proxyConnections: 0, targetKeyed: true, sentByFetch: true });
  });

  test("a request without a key through HTTPS_PROXY is sent by the fetch adapter directly to the target", async () => {
    const site = await target();
    const proxy = await proxySink();
    const result = await withEnv({ HTTPS_PROXY: `http://${SHIM}:${proxy.port}` }, () => outcome(() => get(client(`https://${SHIM}:${site.port}`, "fetch adapter", {}))));
    expect({
      result,
      proxyConnections: proxy.connections,
      sentByFetch: site.requests.length === 1 && /^sec-fetch-mode\s*:/im.test(site.requests[0]),
    }).toEqual({ result: "(resolved)", proxyConnections: 0, sentByFetch: true });
  });
});
