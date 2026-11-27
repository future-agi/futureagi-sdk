// A keyed request with a body that is redirected by 307 or 308, which keep the method and the body.
//
// A provider key placed in the body by ProviderAPIKeyClient.set (and any JSON body of a keyed APIKeyAuth.request) is
// part of what the request carries. A 307 or 308 hop of such a request to another origin is not followed: the call
// rejects with an Error whose code is insecure_http_origin, and the other origin receives nothing. A 307 or 308 hop to
// the same origin sends the body again. Through a proxy every hop of a request that started keyed goes inside a
// CONNECT tunnel, so the proxy reads none of the keys and none of the body.
//
// Every listener is on the loopback address. The first target and the other origin are https listeners of
// support/proxy-sinks.cjs on two ports, addressed by a name that a lookup shim resolves to 127.0.0.1 and trusted
// through a scratch CA; each records the bytes it reads after TLS. The proxy is a CONNECT-aware sink on 127.0.0.1
// that records every byte it receives (tunnelled bytes included). Keys are random marker strings made per test.

/* eslint-disable @typescript-eslint/no-explicit-any */
import { randomBytes } from "node:crypto";
import { Readable } from "node:stream";
import * as nodeTls from "node:tls";

import { APIKeyAuth, HttpClient } from "../api/auth";
import { ModelProvider, ProviderAPIKeyClient } from "../api/apikeys";

/** node:tls with the CA functions of Node 22.19+ and 24.5+ (the installed @types/node does not declare them). */
const tls = nodeTls as typeof nodeTls & {
  getCACertificates(kind?: string): string[];
  setDefaultCACertificates(certificates: string[]): void;
};

// eslint-disable-next-line @typescript-eslint/no-var-requires
const fx = require("./support/proxy-sinks.cjs");

jest.setTimeout(30_000);

const CODE = "insecure_http_origin";
const SHIM: string = fx.SHIM_HOST;

type Target = { port: number; connections: number; requests: string[]; raw(): string; count(markers: string[]): number; close(): Promise<void> };
type Sink = { port: number; connections: number; connects: string[]; absolute: string[]; raw(): string; count(markers: string[]): number; close(): Promise<void> };

// --- the lookup shim and the scratch CA -----------------------------------------------------------------------

let undoLookup: () => void = () => undefined;
let caBefore: string[] = [];
beforeAll(() => {
  caBefore = tls.getCACertificates("default");
  fx.certificates();
  undoLookup = fx.shimLookup();
});
afterAll(() => {
  undoLookup();
  tls.setDefaultCACertificates(caBefore);
});

// --- listeners and clients, closed after each test --------------------------------------------------------------

const open: Array<{ close(): Promise<void> }> = [];
async function target(respond?: (head: string, index: number) => string | undefined): Promise<Target> {
  const made: Target = await fx.tlsTarget(respond);
  open.push(made);
  return made;
}
async function proxySink(): Promise<Sink> {
  const made: Sink = await fx.proxySink();
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
  "FI_API_KEY",
  "FI_SECRET_KEY",
  "FI_BASE_URL",
];

let savedEnv = new Map<string, string | undefined>();
beforeEach(() => {
  savedEnv = new Map(ENV_NAMES.map((name) => [name, process.env[name]]));
});
afterEach(() => {
  for (const [name, value] of savedEnv) {
    if (value === undefined) delete process.env[name];
    else process.env[name] = value;
  }
});

/** Clear every variable of ENV_NAMES (the proxy variables and NO_PROXY included), then apply `set`. Restored by the
 * afterEach above. */
function useEnv(set: Record<string, string>): void {
  for (const name of ENV_NAMES) delete process.env[name];
  Object.assign(process.env, set);
}

type Route = "direct" | "through HTTPS_PROXY";
const ROUTES: Route[] = ["direct", "through HTTPS_PROXY"];

/** The proxy for `route` (null when direct) with the environment set for it. */
async function routeFor(route: Route): Promise<Sink | null> {
  if (route === "direct") {
    useEnv({});
    return null;
  }
  const proxy = await proxySink();
  useEnv({ HTTPS_PROXY: `http://127.0.0.1:${proxy.port}` });
  return proxy;
}

// --- keys, clients and outcomes ---------------------------------------------------------------------------------

const marker = (tag: string) => `fi-marker-${tag}-${randomBytes(8).toString("hex")}`;

interface Keys {
  apiKey: string;
  secretKey: string;
  providerKey: string;
}
const newKeys = (): Keys => ({ apiKey: marker("api"), secretKey: marker("secret"), providerKey: marker("provider") });

/** One attempt and a 5 s timeout; the client is closed after the test. */
function tuned<T extends HttpClient>(client: T): T {
  (client as any)._defaultRetryAttempts = 1;
  (client as any)._defaultTimeout = 5000;
  open.push({ close: () => client.close() });
  return client;
}

function providerClient(keys: Keys, base: string): ProviderAPIKeyClient {
  return tuned(new ProviderAPIKeyClient({ provider: ModelProvider.OPENAI, key: keys.providerKey }, keys.apiKey, keys.secretKey, base));
}

function authClient(keys: Keys, base: string): APIKeyAuth {
  return tuned(new APIKeyAuth({ fiApiKey: keys.apiKey, fiSecretKey: keys.secretKey, fiBaseUrl: base, retryAttempts: 1, timeout: 5000 }));
}

/** "(resolved)", or the top-level code of the Error the call rejected with (its message when it has no code). */
async function outcome(run: () => Promise<unknown>): Promise<string> {
  return run().then(
    () => "(resolved)",
    (e: any) => (e instanceof Error ? ((e as { code?: string }).code ?? `message: ${e.message}`) : "(not an Error)"),
  );
}

const redirect = (status: number, location: string) => `HTTP/1.1 ${status} Redirect\r\nLocation: ${location}\r\nContent-Length: 0\r\nConnection: close\r\n\r\n`;
const connectAuthority = (head: string) => head.split("\r\n")[0].split(" ")[1];
const requestTarget = (head: string) => head.split("\r\n")[0].split(" ")[1];

/** The proxy's record: key bytes per kind, requests in absolute form, CONNECT authorities. All zero when direct. */
function proxyRecord(proxy: Sink | null, keys: Keys, otherOrigin: string) {
  if (proxy === null) {
    return { providerKeyBytes: 0, headerKeyBytes: 0, absolute: 0, connectsToOtherOrigin: 0 };
  }
  return {
    providerKeyBytes: proxy.count([keys.providerKey]),
    headerKeyBytes: proxy.count([keys.apiKey, keys.secretKey]),
    absolute: proxy.absolute.length,
    connectsToOtherOrigin: proxy.connects.filter((head) => connectAuthority(head) === otherOrigin).length,
  };
}

const STATUSES = [307, 308];

const CASES = STATUSES.flatMap((status) => ROUTES.map((route) => [status, route] as const));

// --- a cross-origin 307 or 308 of a keyed request with a body ----------------------------------------------------

describe("a keyed request with a body redirected by 307 or 308 to another https origin", () => {
  test.each(CASES)(
    "ProviderAPIKeyClient.set, %d, %s: rejects with code insecure_http_origin, and neither the other origin nor the proxy receives the provider key or the key headers",
    async (status, route) => {
      const keys = newKeys();
      const proxy = await routeFor(route);
      const other = await target();
      const otherOrigin = `${SHIM}:${other.port}`;
      const first = await target((_head, index) => (index === 0 ? redirect(status, `https://${otherOrigin}/model-hub/api-keys/`) : undefined));
      const result = await outcome(() => providerClient(keys, `https://${SHIM}:${first.port}`).set());
      expect({
        result,
        firstHopReceivedProviderKey: first.count([keys.providerKey]) > 0,
        proxy: proxyRecord(proxy, keys, otherOrigin),
        otherOriginConnections: other.connections,
        otherOriginProviderKeyBytes: other.count([keys.providerKey]),
        otherOriginHeaderKeyBytes: other.count([keys.apiKey, keys.secretKey]),
      }).toEqual({
        result: CODE,
        firstHopReceivedProviderKey: true,
        proxy: { providerKeyBytes: 0, headerKeyBytes: 0, absolute: 0, connectsToOtherOrigin: 0 },
        otherOriginConnections: 0,
        otherOriginProviderKeyBytes: 0,
        otherOriginHeaderKeyBytes: 0,
      });
    },
  );

  test.each(ROUTES)(
    "APIKeyAuth.request, a POST with a JSON body, 308, %s: rejects with code insecure_http_origin, and neither the other origin nor the proxy receives the body or the key headers",
    async (route) => {
      const keys = newKeys();
      const proxy = await routeFor(route);
      const other = await target();
      const otherOrigin = `${SHIM}:${other.port}`;
      const first = await target((_head, index) => (index === 0 ? redirect(308, `https://${otherOrigin}/v1/items`) : undefined));
      const client = authClient(keys, `https://${SHIM}:${first.port}`);
      const result = await outcome(() => client.request({ method: "POST", url: "/v1/items", json: { note: keys.providerKey } } as any));
      expect({
        result,
        firstHopReceivedBody: first.count([keys.providerKey]) > 0,
        proxy: proxyRecord(proxy, keys, otherOrigin),
        otherOriginConnections: other.connections,
        otherOriginBodyBytes: other.count([keys.providerKey]),
        otherOriginHeaderKeyBytes: other.count([keys.apiKey, keys.secretKey]),
      }).toEqual({
        result: CODE,
        firstHopReceivedBody: true,
        proxy: { providerKeyBytes: 0, headerKeyBytes: 0, absolute: 0, connectsToOtherOrigin: 0 },
        otherOriginConnections: 0,
        otherOriginBodyBytes: 0,
        otherOriginHeaderKeyBytes: 0,
      });
    },
  );
});

// --- a same-origin 307 or 308 (control) ---------------------------------------------------------------------------

describe("a keyed request with a body redirected by 307 or 308 to the same origin", () => {
  test.each(CASES)(
    "ProviderAPIKeyClient.set, %d, %s: the body and the key headers are sent again on the second hop and the call succeeds, with no key bytes at the proxy",
    async (status, route) => {
      const keys = newKeys();
      const proxy = await routeFor(route);
      const site = await target((_head, index) => (index === 0 ? redirect(status, "/model-hub/api-keys/next/") : undefined));
      const origin = `${SHIM}:${site.port}`;
      const result = await outcome(() => providerClient(keys, `https://${origin}`).set());
      const hops = site.requests.map(requestTarget);
      expect({
        result,
        hops,
        providerKeyBytesAtTarget: site.count([keys.providerKey]),
        apiKeyBytesAtTarget: site.count([keys.apiKey]),
        proxy:
          proxy === null
            ? null
            : {
                keyBytes: proxy.count([keys.providerKey, keys.apiKey, keys.secretKey]),
                absolute: proxy.absolute.length,
                tunnelledHops: proxy.connects.filter((head) => connectAuthority(head) === origin).length,
              },
      }).toEqual({
        result: "(resolved)",
        hops: ["/model-hub/api-keys/", "/model-hub/api-keys/next/"],
        providerKeyBytesAtTarget: 2 * keys.providerKey.length,
        apiKeyBytesAtTarget: 2 * keys.apiKey.length,
        proxy: proxy === null ? null : { keyBytes: 0, absolute: 0, tunnelledHops: 2 },
      });
    },
  );
});

// --- the other hops of a request that started keyed go through the tunnel ---------------------------------------

describe("a keyed request redirected to another https origin through HTTPS_PROXY, with no body on the second hop", () => {
  const HOPS: Array<[string, number, (keys: Keys, base: string) => Promise<unknown>]> = [
    ["ProviderAPIKeyClient.set answered by 303", 303, (keys, base) => providerClient(keys, base).set()],
    ["ProviderAPIKeyClient.get answered by 307", 307, (keys, base) => providerClient(keys, base).get()],
  ];

  test.each(HOPS.map(([name, status]) => [name, status] as const))(
    "%s: the second hop reaches the other origin through a CONNECT tunnel with no key, and the proxy receives no request in absolute form",
    async (name, status) => {
      const call = HOPS.find(([entry]) => entry === name)![2];
      const keys = newKeys();
      const proxy = (await routeFor("through HTTPS_PROXY"))!;
      const other = await target();
      const otherOrigin = `${SHIM}:${other.port}`;
      const first = await target((_head, index) => (index === 0 ? redirect(status, `https://${otherOrigin}/model-hub/api-keys/`) : undefined));
      const result = await outcome(() => call(keys, `https://${SHIM}:${first.port}`));
      expect({
        result,
        keyBytesAtProxy: proxy.count([keys.providerKey, keys.apiKey, keys.secretKey]),
        absolute: proxy.absolute.map(requestTarget),
        connectsToOtherOrigin: proxy.connects.filter((head) => connectAuthority(head) === otherOrigin).length,
        otherOriginRequests: other.requests.length,
        otherOriginKeyBytes: other.count([keys.providerKey, keys.apiKey, keys.secretKey]),
      }).toEqual({
        result: "(resolved)",
        keyBytesAtProxy: 0,
        absolute: [],
        connectsToOtherOrigin: 1,
        otherOriginRequests: 1,
        otherOriginKeyBytes: 0,
      });
    },
  );
});

// --- a cross-origin hop that keeps the body: 300, and 301 or 302 of a method other than POST ---------------------

describe("a keyed APIKeyAuth.request with a JSON body redirected to another https origin by a status that keeps the method and the body", () => {
  const KEPT: Array<[number, string]> = [
    [300, "POST"],
    [301, "PUT"],
    [302, "PATCH"],
    [301, "DELETE"],
  ];
  const KEPT_CASES = KEPT.flatMap(([status, method]) => ROUTES.map((route) => [status, method, route] as const));

  test.each(KEPT_CASES)(
    "%d answering a %s, %s: rejects with code insecure_http_origin, and neither the other origin nor the proxy receives the body or the key headers",
    async (status, method, route) => {
      const keys = newKeys();
      const proxy = await routeFor(route);
      const other = await target();
      const otherOrigin = `${SHIM}:${other.port}`;
      const first = await target((_head, index) => (index === 0 ? redirect(status, `https://${otherOrigin}/v1/items/1`) : undefined));
      const client = authClient(keys, `https://${SHIM}:${first.port}`);
      const result = await outcome(() => client.request({ method, url: "/v1/items/1", json: { note: keys.providerKey } } as any));
      expect({
        result,
        firstHopMethod: first.requests.map((head) => head.split(" ")[0]),
        firstHopReceivedBody: first.count([keys.providerKey]) > 0,
        proxy: proxyRecord(proxy, keys, otherOrigin),
        otherOriginConnections: other.connections,
        otherOriginBodyBytes: other.count([keys.providerKey]),
        otherOriginHeaderKeyBytes: other.count([keys.apiKey, keys.secretKey]),
      }).toEqual({
        result: CODE,
        firstHopMethod: [method],
        firstHopReceivedBody: true,
        proxy: { providerKeyBytes: 0, headerKeyBytes: 0, absolute: 0, connectsToOtherOrigin: 0 },
        otherOriginConnections: 0,
        otherOriginBodyBytes: 0,
        otherOriginHeaderKeyBytes: 0,
      });
    },
  );

  test.each(ROUTES)(
    "a chain A -(302 to a PUT)-> B -(302)-> C, %s: rejects with code insecure_http_origin at the first hop, and B and C receive no connection and no byte",
    async (route) => {
      const keys = newKeys();
      const proxy = await routeFor(route);
      const third = await target();
      const thirdOrigin = `${SHIM}:${third.port}`;
      const second = await target((_head, index) => (index === 0 ? redirect(302, `https://${thirdOrigin}/v1/items/3`) : undefined));
      const secondOrigin = `${SHIM}:${second.port}`;
      const first = await target((_head, index) => (index === 0 ? redirect(302, `https://${secondOrigin}/v1/items/2`) : undefined));
      const client = authClient(keys, `https://${SHIM}:${first.port}`);
      const result = await outcome(() => client.request({ method: "PUT", url: "/v1/items/1", json: { note: keys.providerKey } } as any));
      expect({
        result,
        firstHopRequests: first.requests.length,
        secondConnections: second.connections,
        secondBytes: second.raw().length,
        thirdConnections: third.connections,
        thirdBytes: third.raw().length,
        proxy: proxyRecord(proxy, keys, secondOrigin),
        connectsToThird: proxy === null ? 0 : proxy.connects.filter((head) => connectAuthority(head) === thirdOrigin).length,
      }).toEqual({
        result: CODE,
        firstHopRequests: 1,
        secondConnections: 0,
        secondBytes: 0,
        thirdConnections: 0,
        thirdBytes: 0,
        proxy: { providerKeyBytes: 0, headerKeyBytes: 0, absolute: 0, connectsToOtherOrigin: 0 },
        connectsToThird: 0,
      });
    },
  );
});

// --- a keyed streamed body over the copy limit redirected by 307 to another origin --------------------------------

describe("a keyed APIKeyAuth.request with an 11 MiB streamed body redirected by 307 to another https origin", () => {
  const MiB = 1024 * 1024;

  test.each(ROUTES)(
    "%s: rejects with code insecure_http_origin (not ERR_FR_MAX_BODY_LENGTH_EXCEEDED), and the other origin receives no connection",
    async (route) => {
      const keys = newKeys();
      const proxy = await routeFor(route);
      const other = await target();
      const otherOrigin = `${SHIM}:${other.port}`;
      const first = await target((_head, index) => (index === 0 ? redirect(307, `https://${otherOrigin}/v1/upload`) : undefined));
      const client = authClient(keys, `https://${SHIM}:${first.port}`);
      const head = Buffer.from(keys.providerKey);
      const filler = Buffer.alloc(MiB, 0x61);
      const source = Readable.from([head, ...Array.from({ length: 11 }, () => filler)]);
      const result = await outcome(() =>
        client.request({ method: "POST", url: "/v1/upload", data: source, headers: { "Content-Type": "application/octet-stream" }, timeout: 20_000 } as any),
      );
      expect({
        result,
        firstHopRequests: first.requests.length,
        proxy: proxyRecord(proxy, keys, otherOrigin),
        otherOriginConnections: other.connections,
        otherOriginBytes: other.raw().length,
      }).toEqual({
        result: CODE,
        firstHopRequests: 1,
        proxy: { providerKeyBytes: 0, headerKeyBytes: 0, absolute: 0, connectsToOtherOrigin: 0 },
        otherOriginConnections: 0,
        otherOriginBytes: 0,
      });
    },
  );
});

// --- a cross-origin 302 of a keyed POST, followed as a GET without a body (control) ------------------------------

describe("a keyed APIKeyAuth.request POST with a JSON body redirected by 302 to another https origin", () => {
  test.each(ROUTES)(
    "%s: the hop is followed as a GET, and the other origin receives no body bytes and no key headers",
    async (route) => {
      const keys = newKeys();
      const proxy = await routeFor(route);
      const other = await target();
      const otherOrigin = `${SHIM}:${other.port}`;
      const first = await target((_head, index) => (index === 0 ? redirect(302, `https://${otherOrigin}/v1/items/2`) : undefined));
      const client = authClient(keys, `https://${SHIM}:${first.port}`);
      const result = await outcome(() => client.request({ method: "POST", url: "/v1/items", json: { note: keys.providerKey } } as any));
      expect({
        result,
        firstHopReceivedBody: first.count([keys.providerKey]) > 0,
        otherOriginRequests: other.requests.map((head) => head.split("\r\n")[0].split(" ").slice(0, 2).join(" ")),
        otherOriginBodyBytes: other.count([keys.providerKey]),
        otherOriginHeaderKeyBytes: other.count([keys.apiKey, keys.secretKey]),
        keyBytesAtProxy: proxy === null ? 0 : proxy.count([keys.providerKey, keys.apiKey, keys.secretKey]),
      }).toEqual({
        result: "(resolved)",
        firstHopReceivedBody: true,
        otherOriginRequests: ["GET /v1/items/2"],
        otherOriginBodyBytes: 0,
        otherOriginHeaderKeyBytes: 0,
        keyBytesAtProxy: 0,
      });
    },
  );
});
