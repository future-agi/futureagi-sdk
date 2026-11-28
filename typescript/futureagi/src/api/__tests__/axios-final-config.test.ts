/**
 * The final config of a keyed request on axios's http adapter holds the route the SDK gives it: the adapter the SDK
 * judges with, no `transport`, `maxRedirects` 0, no proxy and the SDK's agents, as own properties that caller code run
 * later (a `transformRequest`, a `paramsSerializer`) cannot replace, and that a `transport` or `maxRedirects` on the
 * config's prototype does not shadow. A config the SDK already sent (`response.config`, `error.config`) goes out again
 * through the same instance as it did the first time.
 *
 * Loopback listeners count connections and marker key bytes: an origin at 127.0.0.1 that answers a redirect to another
 * host (the name `localhost`, which the SDK's loopback agent resolves to 127.0.0.1), that redirect target, and a host
 * that answers 200.
 */
import { createRequire } from "node:module";

import axios, { type AxiosInstance, type InternalAxiosRequestConfig } from "axios";

import { APIKeyAuth } from "../auth";
import { HttpMethod } from "../types";
import { ConfigurationError } from "../../_core/errors";
import { MARKER_KEY, MARKER_SECRET, Sink } from "../../_core/__fixtures__/plaintext-sinks";

const VARS = ["HTTP_PROXY", "http_proxy", "HTTPS_PROXY", "https_proxy", "ALL_PROXY", "all_proxy", "NO_PROXY", "no_proxy", "FI_ALLOW_INSECURE_HTTP", "FI_EXTRA_HEADERS"];
const saved = new Map(VARS.map((name) => [name, process.env[name]] as const));

/** The follow-redirects module axios itself depends on, resolved from axios's own location. */
const followRedirects = createRequire(require.resolve("axios"))("follow-redirects") as { http: unknown; https: unknown };

const next = new Sink();
const ok = new Sink();
let origin: Sink;

beforeAll(async () => {
  for (const name of VARS) delete process.env[name];
  await Promise.all([next.listen(), ok.listen()]);
  origin = new Sink("307 Temporary Redirect", `http://localhost:${next.port}/next`);
  await origin.listen();
});
afterAll(() => {
  next.close(); ok.close(); origin.close();
  for (const [name, value] of saved) { if (value === undefined) delete process.env[name]; else process.env[name] = value; }
});
beforeEach(() => { next.reset(); ok.reset(); origin.reset(); });

class Probe extends APIKeyAuth {
  get instance(): AxiosInstance { return this._axiosInstance; }
}
const keyed = (base: string): Probe => new Probe({ fiApiKey: MARKER_KEY, fiSecretKey: MARKER_SECRET, fiBaseUrl: base, retryAttempts: 1 });
const outcome = async (call: () => Promise<unknown>): Promise<unknown> => {
  try { return await call(); } catch (error) { return error; }
};
type Config = InternalAxiosRequestConfig & Record<string, unknown>;
const onRequest = (client: Probe, change: (config: Config) => unknown): void => {
  client.instance.interceptors.request.use((config) => (change(config as Config) ?? config) as InternalAxiosRequestConfig);
};

describe("a config the SDK already sent, sent again through the same instance", () => {
  it("goes out again from response.config, as the first send did", async () => {
    const client = keyed(`http://127.0.0.1:${ok.port}`);
    const first = await client.instance.request({ method: "get", url: "/x" });
    const again = await outcome(() => client.instance.request(first.config));
    process.stdout.write(`re-send of response.config: ${JSON.stringify({ connections: ok.connections, markers: ok.markerBytes })}\n`);
    expect((again as { status?: number }).status).toBe(200);
    expect({ connections: ok.connections, markers: ok.markerBytes }).toEqual({ connections: 2, markers: 4 });
  });

  it("goes out again from a response interceptor that re-sends the config once", async () => {
    const client = keyed(`http://127.0.0.1:${ok.port}`);
    let sends = 0;
    client.instance.interceptors.response.use(async (response) => (sends++ === 0 ? client.instance.request(response.config) : response));
    const result = await outcome(() => client.request({ method: HttpMethod.GET, url: "/y" }));
    expect((result as { status?: number }).status).toBe(200);
    expect({ connections: ok.connections, markers: ok.markerBytes }).toEqual({ connections: 2, markers: 4 });
  });

  it("goes out again from the config of a redirect answer, and stops at the origin again", async () => {
    const client = keyed(`http://127.0.0.1:${origin.port}`);
    const first = await client.instance.request({ method: "get", url: "/start" });
    const again = await outcome(() => client.instance.request(first.config));
    expect((again as { status?: number }).status).toBe(307);
    expect({ connections: origin.connections, markers: origin.markerBytes }).toEqual({ connections: 2, markers: 4 });
    expect({ connections: next.connections, markers: next.markerBytes }).toEqual({ connections: 0, markers: 0 });
  });
});

const ROUTES: Array<[string, (client: Probe) => void]> = [
  ["a transformRequest assigns axios's fetch adapter to this.adapter", (client) => {
    const fetchAdapter = axios.getAdapter("fetch");
    onRequest(client, (config) => { config.transformRequest = [function (this: InternalAxiosRequestConfig, data: unknown) { (this as Config).adapter = fetchAdapter; return data; }]; });
  }],
  ["an instance default transformRequest assigns 'fetch' to this.adapter", (client) => {
    client.instance.defaults.transformRequest = [function (this: InternalAxiosRequestConfig, data: unknown) { (this as Config).adapter = "fetch"; return data; }];
  }],
  ["a transformRequest assigns 'http' to this.adapter and sets this.transport", (client) => {
    onRequest(client, (config) => { config.transformRequest = [function (this: InternalAxiosRequestConfig, data: unknown) { (this as Config).adapter = "http"; (this as Config).transport = followRedirects.http; return data; }]; });
  }],
  ["an interceptor installs an accessor for adapter that answers axios's fetch adapter", (client) => {
    const fetchAdapter = axios.getAdapter("fetch");
    onRequest(client, (config) => { Object.defineProperty(config, "adapter", { get: () => fetchAdapter, set: () => undefined, configurable: true, enumerable: true }); });
  }],
  ["the transport is a value on the config's prototype", (client) => {
    onRequest(client, (config) => { Object.setPrototypeOf(config, { transport: followRedirects.http }); });
  }],
  ["the transport is a getter on the config's prototype", (client) => {
    onRequest(client, (config) => { Object.setPrototypeOf(config, Object.create(Object.prototype, { transport: { get: () => followRedirects.http } })); });
  }],
  ["a paramsSerializer sets the transport inside the http adapter", (client) => {
    onRequest(client, (config) => { config.params = { a: 1 }; config.paramsSerializer = { serialize: () => { config.transport = followRedirects.http; return "a=1"; } }; });
  }],
  ["a paramsSerializer restores maxRedirects and sets the transport inside the http adapter", (client) => {
    onRequest(client, (config) => {
      config.params = { a: 1 };
      config.paramsSerializer = { serialize: () => { config.maxRedirects = 5; config.beforeRedirect = () => undefined; config.transport = followRedirects.http; return "a=1"; } };
    });
  }],
  ["an interceptor returns a Proxy whose transport is the follow-redirects module", (client) => {
    onRequest(client, (config) => new Proxy(config, { get: (target, name, receiver) => (name === "transport" ? followRedirects.http : Reflect.get(target, name, receiver)) }));
  }],
];

describe.each(ROUTES)("a keyed request when %s", (route, change) => {
  it("puts no marker key byte at the host the origin redirects to, and does not resolve as a success", async () => {
    const client = keyed(`http://127.0.0.1:${origin.port}`);
    change(client);
    const result = await outcome(() => client.request({ method: HttpMethod.GET, url: "/start" }));
    const atTarget = { connections: next.connections, markers: next.markerBytes };
    process.stdout.write(`redirect target when ${route}: ${JSON.stringify(atTarget)}\n`);
    expect(atTarget).toEqual({ connections: 0, markers: 0 });
    expect(result).toBeInstanceOf(Error);
  });
});

describe("a keyed request whose config refuses the SDK's settings", () => {
  it("is refused before any connection when an interceptor makes adapter a non-configurable accessor", async () => {
    const client = keyed(`http://127.0.0.1:${origin.port}`);
    const fetchAdapter = axios.getAdapter("fetch");
    onRequest(client, (config) => { Object.defineProperty(config, "adapter", { get: () => fetchAdapter, set: () => undefined, configurable: false }); });
    const result = await outcome(() => client.request({ method: HttpMethod.GET, url: "/start" }));
    expect(result).toBeInstanceOf(ConfigurationError);
    expect((result as ConfigurationError).code).toBe("keyed_config_unsupported");
    expect(origin.connections + next.connections).toBe(0);
  });

  it("is refused before any connection when an interceptor makes transport non-configurable", async () => {
    const client = keyed(`http://127.0.0.1:${origin.port}`);
    onRequest(client, (config) => { Object.defineProperty(config, "transport", { value: followRedirects.http, configurable: false, enumerable: true }); });
    const result = await outcome(() => client.request({ method: HttpMethod.GET, url: "/start" }));
    expect(result).toBeInstanceOf(ConfigurationError);
    expect((result as ConfigurationError).code).toBe("keyed_config_unsupported");
    expect(origin.connections + next.connections).toBe(0);
  });

  it("is refused before any connection when the final config is a Proxy", async () => {
    const client = keyed(`http://127.0.0.1:${ok.port}`);
    onRequest(client, (config) => new Proxy(config, {}));
    const result = await outcome(() => client.request({ method: HttpMethod.GET, url: "/start" }));
    expect(result).toBeInstanceOf(ConfigurationError);
    expect((result as ConfigurationError).code).toBe("keyed_config_unsupported");
    expect(ok.connections).toBe(0);
  });
});
