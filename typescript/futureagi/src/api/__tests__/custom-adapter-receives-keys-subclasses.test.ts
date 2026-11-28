/**
 * `customAdapterReceivesKeys: true` reaches the HttpClient of every APIKeyAuth client the SDK exports: Annotation,
 * KnowledgeBase, APIKeyManager (its own requests and the provider key calls it hands to ProviderAPIKeyClient) and
 * ProviderAPIKeyClient. A keyed request through an adapter function of the caller's (set as axios's global default
 * while the client is built) goes through that adapter when the client carries the opt-in, and is refused before any
 * connection with `keyed_adapter_unsupported` when it does not.
 *
 * The adapter sends through the global `fetch` to a loopback listener that counts connections and planted marker key
 * bytes; each row prints its counts.
 */
import axios, { type AxiosAdapter } from "axios";

import { Annotation } from "../../annotations/annotation";
import type { AnnotationOptions } from "../../annotations/types";
import { KnowledgeBase } from "../../kb/client";
import type { KnowledgeBaseOptions } from "../../kb/types";
import { APIKeyManager, ProviderAPIKeyClient } from "../apikeys";
import { HttpMethod, ModelProvider } from "../types";
import { ConfigurationError } from "../../_core/errors";
import { MARKER_KEY, MARKER_SECRET, Sink } from "../../_core/__fixtures__/plaintext-sinks";
import { proxyEnvironment } from "../../_core/__fixtures__/proxy-sink";
import { globalFetchAdapter } from "../__fixtures__/global-fetch-adapter";

const ENV = ["FI_API_KEY", "FI_SECRET_KEY", "FI_BASE_URL", "FI_ALLOW_INSECURE_HTTP", "FI_EXTRA_HEADERS"];
const saved = new Map(ENV.map((name) => [name, process.env[name]] as const));
const sink = new Sink();
let restoreProxy: (() => void) | undefined;

beforeAll(async () => {
  restoreProxy = proxyEnvironment();
  await sink.listen();
});
afterAll(() => {
  sink.close();
  restoreProxy?.();
  for (const [name, value] of saved) { if (value === undefined) delete process.env[name]; else process.env[name] = value; }
});
beforeEach(() => {
  sink.reset();
  for (const name of ENV) delete process.env[name];
  // APIKeyManager and the provider key calls it makes read the keys and the base URL from the environment
  process.env.FI_API_KEY = MARKER_KEY;
  process.env.FI_SECRET_KEY = MARKER_SECRET;
  process.env.FI_BASE_URL = `http://127.0.0.1:${sink.port}`;
  APIKeyManager.resetInstance();
});
afterEach(() => { APIKeyManager.resetInstance(); });

/** Runs `step` with `adapter` as axios's global default, so every client built inside it takes that adapter. */
const withDefaultAdapter = async <T>(adapter: AxiosAdapter, step: () => Promise<T>): Promise<T> => {
  const before = axios.defaults.adapter;
  axios.defaults.adapter = adapter;
  try { return await step(); } finally { axios.defaults.adapter = before; }
};
const outcome = async (call: () => Promise<unknown>): Promise<unknown> => {
  try { return await call(); } catch (error) { return error; }
};
const keys = (): { fiApiKey: string; fiSecretKey: string; fiBaseUrl: string } =>
  ({ fiApiKey: MARKER_KEY, fiSecretKey: MARKER_SECRET, fiBaseUrl: `http://127.0.0.1:${sink.port}` });
const opt = (on: boolean): { customAdapterReceivesKeys?: boolean } => (on ? { customAdapterReceivesKeys: true } : {});

type ManagerFactory = (options?: { customAdapterReceivesKeys?: boolean }) => APIKeyManager;
const manager = (on: boolean): APIKeyManager =>
  on ? (APIKeyManager.getInstance as unknown as ManagerFactory)(opt(true)) : APIKeyManager.getInstance();
type ProviderOptions = Parameters<typeof ProviderAPIKeyClient.listApiKeys>[0];

/** Each row builds its client with the adapter in place and returns the keyed call it makes. */
const ROWS: Array<[string, (on: boolean) => Promise<unknown>]> = [
  ["Annotation", async (on) => {
    const client = new Annotation({ ...keys(), ...opt(on) } as AnnotationOptions);
    return client.request({ method: HttpMethod.GET, url: "/annotation" });
  }],
  ["KnowledgeBase", async (on) => {
    const client = new KnowledgeBase(undefined, { ...keys(), ...opt(on) } as KnowledgeBaseOptions);
    return client.request({ method: HttpMethod.GET, url: "/knowledge-base" });
  }],
  ["APIKeyManager.request", async (on) => manager(on).request({ method: HttpMethod.GET, url: "/manager" })],
  ["APIKeyManager.setProviderApiKey", async (on) => manager(on).setProviderApiKey(ModelProvider.OPENAI, "marker-provider-key-0000000000")],
  ["APIKeyManager.listProviderApiKeys", async (on) => manager(on).listProviderApiKeys()],
  ["ProviderAPIKeyClient.listApiKeys", async (on) => ProviderAPIKeyClient.listApiKeys({ ...keys(), ...opt(on) } as ProviderOptions)],
];

const report = (row: string, setting: string, counting: { calls: number }, result: unknown): void => {
  const refused = result instanceof ConfigurationError ? result.code : "sent";
  process.stdout.write(`[custom adapter] ${row} ${setting}: adapter calls ${counting.calls}, sink connections ${sink.connections}, ` +
    `sink markers ${sink.markerBytes}, outcome ${refused}\n`);
};

describe.each(ROWS)("%s", (row, call) => {
  it("with customAdapterReceivesKeys: true, a keyed request goes through the caller's adapter, which carries the keys to the listener", async () => {
    const counting = globalFetchAdapter();
    const result = await withDefaultAdapter(counting.adapter, () => outcome(() => call(true)));
    report(row, "opt-in", counting, result);
    expect(result instanceof ConfigurationError ? result.code : "sent").toBe("sent");
    expect({ calls: counting.calls, connections: sink.connections, markers: sink.markerBytes }).toEqual({ calls: 1, connections: 1, markers: 2 });
  });

  it("without the option, the keyed request is refused with keyed_adapter_unsupported before any connection", async () => {
    const counting = globalFetchAdapter();
    const result = await withDefaultAdapter(counting.adapter, () => outcome(() => call(false)));
    report(row, "no opt-in", counting, result);
    expect(result).toBeInstanceOf(ConfigurationError);
    expect((result as ConfigurationError).code).toBe("keyed_adapter_unsupported");
    expect({ calls: counting.calls, connections: sink.connections, markers: sink.markerBytes }).toEqual({ calls: 0, connections: 0, markers: 0 });
  });
});

describe("APIKeyManager is one instance per process", () => {
  it("refuses a second getInstance call that asks for another customAdapterReceivesKeys setting", () => {
    const first = (APIKeyManager.getInstance as unknown as ManagerFactory)(opt(true));
    expect((APIKeyManager.getInstance as unknown as ManagerFactory)(opt(true))).toBe(first);
    expect(APIKeyManager.getInstance()).toBe(first);
    let result: unknown;
    try { (APIKeyManager.getInstance as unknown as ManagerFactory)({ customAdapterReceivesKeys: false }); } catch (error) { result = error; }
    expect(result).toBeInstanceOf(ConfigurationError);
  });
});

const providerClient = (setting?: boolean) => new ProviderAPIKeyClient({}, MARKER_KEY, MARKER_SECRET, keys().fiBaseUrl, setting);

it.each([{ allowInsecureHttp: true }, {}, "true", 1, null, new Boolean(true), new Boolean(false)])("rejects a non-boolean provider adapter option %j", (setting) => {
  const construct = () => providerClient(setting as unknown as boolean);
  expect(construct).toThrow(TypeError);
  expect(construct).toThrow(/customAdapterReceivesKeys.*pass true/i);
});

it.each([true, false, undefined])("delivers provider keys according to the constructor option %s", async (setting) => {
  const counting = globalFetchAdapter();
  const result = await withDefaultAdapter(counting.adapter, () => outcome(() => providerClient(setting).request({ method: HttpMethod.GET, url: "/provider" })));
  if (setting) expect(result).toMatchObject({ status: 200 });
  else expect(result).toMatchObject({ code: "keyed_adapter_unsupported" });
  expect(counting.calls).toBe(setting ? 1 : 0);
  expect(sink.markerBytes).toBe(setting ? 2 : 0);
});
