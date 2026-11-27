// A proxy chosen by an adapter function of the caller's, after the SDK has judged the request.
//
// A caller may hand axios an adapter function (on the client's axios instance, or as the adapter of one request) that
// receives the request config and sets `proxy` on it before passing it to axios's http adapter; it may add key headers
// as well. The SDK judges the request before that function runs, so the request is read again when Node creates it. A
// keyed https request (or an https hop of one) that would reach such a proxy in absolute form is refused with code
// insecure_http_origin before any byte is written, also when the SDK had chosen a CONNECT tunnel for it. A request
// without a key goes to that proxy as axios sends it, with the proxy's own Basic value, and succeeds, also when the
// function hands axios a copy of the config.
//
// The target is an https listener (scratch CA trusted by this process) on a host name that a lookup shim resolves to
// the loopback address; the proxy is a loopback listener that records every request (CONNECT or absolute form, raw
// bytes included) and answers an absolute-form request itself with 200. No proxy variable applies to the target, so
// the SDK finds no proxy when it judges the request: either every proxy variable is cleared, or NO_PROXY names the
// target host while HTTP_PROXY and HTTPS_PROXY name a second recording proxy. Keys and the proxy password are planted
// markers made per test, and every listener counts the marker bytes it receives.

/* eslint-disable @typescript-eslint/no-explicit-any */
import { randomBytes } from "node:crypto";

import axios from "axios";

import { APIKeyAuth, HttpClient } from "../api/auth";

// eslint-disable-next-line @typescript-eslint/no-var-requires
const fx = require("./support/proxy-sinks.cjs");

jest.setTimeout(30_000);

type Target = { port: number; connections: number; requests: string[]; raw(): string; count(markers: string[]): number; close(): Promise<void> };
type ProxySink = { port: number; connections: number; connects: string[]; absolute: string[]; raw(): string; count(markers: string[]): number; close(): Promise<void> };

const SHIM: string = fx.SHIM_HOST;
const PROXY_USER = "fiproxy";

// --- name lookup and the scratch CA ---------------------------------------------------------------------------

let undoShim: () => void = () => undefined;
beforeAll(() => {
  fx.certificates();
  undoShim = fx.shimLookup();
});
afterAll(() => {
  undoShim();
});

// --- listeners and clients, closed after each test ------------------------------------------------------------

const open: Array<{ close(): Promise<void> }> = [];
const clients: HttpClient[] = [];
afterEach(async () => {
  while (clients.length) {
    const made = clients.pop()!;
    let timer: NodeJS.Timeout | undefined;
    await Promise.race([made.close(), new Promise((resolve) => (timer = setTimeout(resolve, 2000)))]);
    clearTimeout(timer);
  }
  while (open.length) await open.pop()!.close();
});

async function tlsTarget(respond?: (head: string, index: number) => string | undefined): Promise<Target> {
  const made: Target = await fx.tlsTarget(respond);
  open.push(made);
  return made;
}

async function proxySink(): Promise<ProxySink> {
  const made: ProxySink = await fx.proxySink();
  open.push(made);
  return made;
}

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

/** Run `run` with every variable of ENV_NAMES cleared and then `set` applied; restore the environment afterwards. */
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

/** How the environment keeps a proxy variable from applying to the target. `other` is a second recording proxy. */
interface Env {
  name: string;
  vars(other: ProxySink): Record<string, string>;
}

const ENVS: Env[] = [
  { name: "every proxy variable cleared", vars: () => ({}) },
  {
    name: "NO_PROXY naming the target host, HTTP_PROXY and HTTPS_PROXY naming another proxy",
    vars: (other) => ({ HTTP_PROXY: `http://127.0.0.1:${other.port}`, HTTPS_PROXY: `http://127.0.0.1:${other.port}`, NO_PROXY: SHIM }),
  },
];

// --- the adapter function of the caller's ---------------------------------------------------------------------

const marker = (tag: string) => `FIMARK-late-${tag}-${randomBytes(8).toString("hex")}`;

interface ProxyCredentials {
  password: string;
  /** The Proxy-Authorization value axios makes from the proxy's own user name and password. */
  basic: string;
}

function proxyCredentials(): ProxyCredentials {
  const password = marker("pp");
  return { password, basic: `Basic ${Buffer.from(`${PROXY_USER}:${password}`, "utf8").toString("base64")}` };
}

/** What the caller's adapter function does to the config before it hands it to axios's http adapter. */
interface Late {
  proxyPort: number;
  /** The proxy's own user name and password, as `proxy.auth`. */
  creds?: ProxyCredentials;
  /** Key headers the function adds. */
  keys?: { apiKey: string; secretKey: string };
}

function lateAdapter(late: Late): (config: any) => Promise<any> {
  const httpAdapter = (axios as any).getAdapter("http");
  return (config: any) => {
    config.proxy = {
      protocol: "http",
      host: "127.0.0.1",
      port: late.proxyPort,
      ...(late.creds ? { auth: { username: PROXY_USER, password: late.creds.password } } : {}),
    };
    if (late.keys) {
      config.headers["X-Api-Key"] = late.keys.apiKey;
      config.headers["X-Secret-Key"] = late.keys.secretKey;
    }
    return httpAdapter(config);
  };
}

/** Where the caller puts the adapter function, and how the GET is made. */
interface Placement {
  name: string;
  get(client: HttpClient, adapter: (config: any) => Promise<any>): Promise<any>;
}

const PLACEMENTS: Placement[] = [
  {
    name: "the adapter of the client's axios instance (HttpClient.request)",
    get: (client, adapter) => {
      (client as any)._axiosInstance.defaults.adapter = adapter;
      return client.request({ method: "GET", url: "/v1/probe" } as any);
    },
  },
  {
    name: "the adapter of one request (the client's axios instance)",
    get: (client, adapter) => (client as any)._axiosInstance.request({ method: "GET", url: "/v1/probe", adapter }),
  },
];

// --- helpers --------------------------------------------------------------------------------------------------

function unkeyedClient(baseUrl: string): HttpClient {
  const made = new HttpClient({ baseUrl, retryAttempts: 1, timeout: 5000 });
  clients.push(made);
  return made;
}

function keyedClient(baseUrl: string, apiKey: string, secretKey: string): HttpClient {
  const made = new APIKeyAuth({ fiApiKey: apiKey, fiSecretKey: secretKey, baseUrl, retryAttempts: 1, timeout: 5000 });
  clients.push(made);
  return made;
}

/** "status <n>" for a response, or the codes of what the request rejected with and of its causes. */
async function outcome(run: () => Promise<any>): Promise<string> {
  return run().then(
    (response) => `status ${response?.status}`,
    (error) => {
      const codes: string[] = [];
      const seen = new Set<unknown>();
      for (let current = error; current && typeof current === "object" && !seen.has(current); current = current.cause) {
        seen.add(current);
        if (current.code !== undefined) codes.push(String(current.code));
      }
      return codes.includes("insecure_http_origin") ? "refused insecure_http_origin" : `error ${codes.join(",") || String(error?.message ?? error)}`;
    },
  );
}

const firstLine = (head: string) => head.split("\r\n")[0];
const headerValues = (head: string, name: string) =>
  head
    .split("\r\n")
    .slice(1)
    .filter((line) => line.toLowerCase().startsWith(`${name.toLowerCase()}:`))
    .map((line) => line.slice(line.indexOf(":") + 1).trim());

function record(label: string, data: Record<string, unknown>): void {
  // eslint-disable-next-line no-console
  console.log(`${label}: ${JSON.stringify(data)}`);
}

// --- keys added by the adapter function -----------------------------------------------------------------------

describe.each(PLACEMENTS.map((placement) => [placement.name, placement] as const))("an adapter function set as %s", (_name, placement) => {
  test("HttpClient: a function that sets an http proxy and adds X-Api-Key and X-Secret-Key to an https request gets insecure_http_origin, and the proxy receives no byte", async () => {
    const target = await tlsTarget();
    const proxy = await proxySink();
    const keys = { apiKey: marker("ak"), secretKey: marker("sk") };
    const client = unkeyedClient(`https://${SHIM}:${target.port}`);
    const result = await withEnv({}, () => outcome(() => placement.get(client, lateAdapter({ proxyPort: proxy.port, keys }))));
    const seen = {
      result,
      connects: proxy.connects.length,
      absolute: proxy.absolute.length,
      proxyConnections: proxy.connections,
      proxyKeyBytes: proxy.count([keys.apiKey, keys.secretKey]),
      targetConnections: target.connections,
    };
    record(`keys added late, ${placement.name}`, seen);
    expect(seen).toEqual({
      result: "refused insecure_http_origin",
      connects: 0,
      absolute: 0,
      proxyConnections: 0,
      proxyKeyBytes: 0,
      targetConnections: 0,
    });
  });
});

// --- the client's own keys, the proxy set by the adapter function ---------------------------------------------

const KEYED_CASES = PLACEMENTS.flatMap((placement) =>
  ENVS.flatMap((env) =>
    [false, true].map((withAuth) => [placement.name, env.name, withAuth ? "with" : "without", { placement, env, withAuth }] as const),
  ),
);

describe("APIKeyAuth with its own keys and an adapter function that sets an http proxy", () => {
  test.each(KEYED_CASES)(
    "adapter function on %s, %s, a proxy %s a user name and password of its own: the https request gets insecure_http_origin, and no key byte reaches either proxy",
    async (_placementName, _envName, _auth, { placement, env, withAuth }) => {
      const target = await tlsTarget();
      const proxy = await proxySink();
      const other = await proxySink();
      const [apiKey, secretKey] = [marker("ka"), marker("ks")];
      const creds = withAuth ? proxyCredentials() : undefined;
      const client = keyedClient(`https://${SHIM}:${target.port}`, apiKey, secretKey);
      const result = await withEnv(env.vars(other), () => outcome(() => placement.get(client, lateAdapter({ proxyPort: proxy.port, creds }))));
      const seen = {
        result,
        connects: proxy.connects.length,
        absolute: proxy.absolute.length,
        proxyConnections: proxy.connections,
        proxyKeyBytes: proxy.count([apiKey, secretKey]),
        otherProxyConnections: other.connections,
        targetConnections: target.connections,
      };
      record(`client keys, ${placement.name}, ${env.name}, own auth ${withAuth}`, seen);
      expect(seen).toEqual({
        result: "refused insecure_http_origin",
        connects: 0,
        absolute: 0,
        proxyConnections: 0,
        proxyKeyBytes: 0,
        otherProxyConnections: 0,
        targetConnections: 0,
      });
    },
  );
});

// --- a request without a key ----------------------------------------------------------------------------------

describe.each(PLACEMENTS.map((placement) => [placement.name, placement] as const))("an adapter function set as %s", (_name, placement) => {
  test("HttpClient without a key: an https request through the proxy the function sets, with a user name and password of its own, goes in absolute form with the proxy's own Basic value and succeeds with 200", async () => {
    const target = await tlsTarget();
    const proxy = await proxySink();
    const creds = proxyCredentials();
    const base = `https://${SHIM}:${target.port}`;
    const client = unkeyedClient(base);
    const result = await withEnv({}, () => outcome(() => placement.get(client, lateAdapter({ proxyPort: proxy.port, creds }))));
    const seen = {
      result,
      connects: proxy.connects.length,
      absolute: proxy.absolute.map(firstLine),
      proxyAuthorization: proxy.absolute.map((head) => headerValues(head, "proxy-authorization")),
      keyHeaders: proxy.absolute.map((head) => [...headerValues(head, "x-api-key"), ...headerValues(head, "x-secret-key"), ...headerValues(head, "authorization")]),
      targetConnections: target.connections,
    };
    record(`unkeyed, ${placement.name}`, seen);
    expect(seen).toEqual({
      result: "status 200",
      connects: 0,
      absolute: [`GET ${base}/v1/probe HTTP/1.1`],
      proxyAuthorization: [[creds.basic]],
      keyHeaders: [[]],
      targetConnections: 0,
    });
  });
});

// --- a copy of the config, a proxy chosen by the SDK, and a redirect hop ---------------------------------------

describe.each(PLACEMENTS.map((placement) => [placement.name, placement] as const))("an adapter function set as %s", (_name, placement) => {
  test("HttpClient without a key: a function that hands axios a copy of the config with a proxy of its own user name and password gets 200 through that proxy in absolute form", async () => {
    const target = await tlsTarget();
    const proxy = await proxySink();
    const creds = proxyCredentials();
    const base = `https://${SHIM}:${target.port}`;
    const client = unkeyedClient(base);
    const httpAdapter = (axios as any).getAdapter("http");
    const copying = (config: any) =>
      httpAdapter({ ...config, proxy: { protocol: "http", host: "127.0.0.1", port: proxy.port, auth: { username: PROXY_USER, password: creds.password } } });
    const result = await withEnv({}, () => outcome(() => placement.get(client, copying)));
    const seen = {
      result,
      absolute: proxy.absolute.map(firstLine),
      proxyAuthorization: proxy.absolute.map((head) => headerValues(head, "proxy-authorization")),
      targetConnections: target.connections,
    };
    record(`unkeyed copy, ${placement.name}`, seen);
    expect(seen).toEqual({ result: "status 200", absolute: [`GET ${base}/v1/probe HTTP/1.1`], proxyAuthorization: [[creds.basic]], targetConnections: 0 });
  });

  test.each([
    ["an https proxy", { protocol: "https" }],
    ["an http proxy", { protocol: "http" }],
    ["a proxy given by host and port only", {}],
  ])(
    "APIKeyAuth through a CONNECT tunnel to the proxy of HTTPS_PROXY: a function that sets %s gets insecure_http_origin, and neither proxy receives a byte",
    async (_kind, shape) => {
      const target = await tlsTarget();
      const chosen = await proxySink();
      const late = await proxySink();
      const [apiKey, secretKey] = [marker("ta"), marker("ts")];
      const client = keyedClient(`https://${SHIM}:${target.port}`, apiKey, secretKey);
      const httpAdapter = (axios as any).getAdapter("http");
      const setting = (config: any) => {
        config.proxy = { ...shape, host: "127.0.0.1", port: late.port };
        return httpAdapter(config);
      };
      const result = await withEnv({ HTTPS_PROXY: `http://127.0.0.1:${chosen.port}` }, () => outcome(() => placement.get(client, setting)));
      const seen = {
        result,
        chosenConnections: chosen.connections,
        lateConnections: late.connections,
        keyBytes: chosen.count([apiKey, secretKey]) + late.count([apiKey, secretKey]),
        targetConnections: target.connections,
      };
      record(`tunnel chosen, late ${_kind}, ${placement.name}`, seen);
      expect(seen).toEqual({ result: "refused insecure_http_origin", chosenConnections: 0, lateConnections: 0, keyBytes: 0, targetConnections: 0 });
    },
  );

  test("APIKeyAuth: a redirect to another origin whose hop a function sends to a proxy it sets gets insecure_http_origin, and the proxy receives no byte", async () => {
    const other = await tlsTarget();
    const first = await tlsTarget(() => `HTTP/1.1 302 Found\r\nLocation: https://localhost:${other.port}/v1/next\r\nContent-Length: 0\r\nConnection: close\r\n\r\n`);
    const proxy = await proxySink();
    const [apiKey, secretKey] = [marker("ra"), marker("rs")];
    const client = keyedClient(`https://${SHIM}:${first.port}`, apiKey, secretKey);
    const httpAdapter = (axios as any).getAdapter("http");
    const onHop = (config: any) => {
      if (String(config.url).includes("localhost")) {
        config.proxy = { protocol: "http", host: "127.0.0.1", port: proxy.port };
      }
      return httpAdapter(config);
    };
    const result = await withEnv({}, () => outcome(() => placement.get(client, onHop)));
    const seen = {
      result,
      firstRequests: first.requests.length,
      proxyConnections: proxy.connections,
      proxyKeyBytes: proxy.count([apiKey, secretKey]),
      otherConnections: other.connections,
    };
    record(`hop to another origin, ${placement.name}`, seen);
    expect(seen).toEqual({ result: "refused insecure_http_origin", firstRequests: 1, proxyConnections: 0, proxyKeyBytes: 0, otherConnections: 0 });
  });
});
