/**
 * Run as a child process with the runtime's environment proxy on (NODE_USE_ENV_PROXY=1, HTTP_PROXY set), from the
 * package directory. PROBE_ADAPTER names the adapter function set as the client's instance default:
 * - "other-build-fetch": axios's 'fetch' adapter from the axios build the SDK did not load (the CommonJS build when the
 *   SDK runs as an ES module, the ES module build otherwise);
 * - "global-fetch": a third-party adapter function that calls the global `fetch`.
 * A control `fetch` (which the runtime sends through the proxy) and keyed requests of an `APIKeyAuth` and of an
 * `HttpClient` are made. The listeners are the parent's; this prints what each call answered: a status, or the error
 * class and code, and the build and adapterName of the adapter.
 */
import { createRequire } from "node:module";
import { join } from "node:path";

import axios, { type AxiosAdapter } from "axios";

import { APIKeyAuth, HttpClient } from "../auth";
import { HttpMethod } from "../types";
import { globalFetchAdapter } from "./global-fetch-adapter";

async function otherBuildFetch(): Promise<[AxiosAdapter, string]> {
  const own = axios.getAdapter("fetch");
  const cjs = (createRequire(join(process.cwd(), "package.json"))("axios") as { default: typeof axios }).default;
  if (cjs.getAdapter("fetch") !== own) return [cjs.getAdapter("fetch"), "commonjs"];
  const esm = ((await import("axios")) as unknown as { default: typeof axios }).default;
  if (esm.getAdapter("fetch") !== own) return [esm.getAdapter("fetch"), "es module"];
  throw new Error("both axios builds share the SDK's fetch adapter");
}

async function main(): Promise<void> {
  const base = `http://app.localhost:${process.env.PROBE_TARGET_PORT ?? ""}`;
  const key = process.env.PROBE_KEY ?? "";
  const secret = process.env.PROBE_SECRET ?? "";
  const [adapter, build] = process.env.PROBE_ADAPTER === "global-fetch" ? [globalFetchAdapter().adapter, "third party"] : await otherBuildFetch();
  const answer = async (call: () => PromiseLike<unknown>): Promise<string> => {
    try { return String(((await call()) as { status?: number }).status); } catch (error) {
      const code = (error as { code?: unknown }).code;
      return `error:${(error as Error).constructor.name}:${typeof code === "string" ? code : ""}`;
    }
  };
  const control = await answer(() => fetch(`${base}/control`));
  const auth = new APIKeyAuth({ fiApiKey: key, fiSecretKey: secret, fiBaseUrl: base, retryAttempts: 1, allowInsecureHttp: true });
  (auth as unknown as { _axiosInstance: { defaults: { adapter: unknown } } })._axiosInstance.defaults.adapter = adapter;
  const keyedAuth = await answer(() => auth.request({ method: HttpMethod.GET, url: "/auth" }));
  const client = new HttpClient({ baseUrl: base, retryAttempts: 1, allowInsecureHttp: true });
  (client as unknown as { _axiosInstance: { defaults: { adapter: unknown } } })._axiosInstance.defaults.adapter = adapter;
  const keyedCall = await answer(() => client.request({ method: HttpMethod.GET, url: "/call", headers: { "X-Api-Key": key } }));
  process.stdout.write(`${JSON.stringify({ control, keyedAuth, keyedCall, build, adapterName: (adapter as { adapterName?: string }).adapterName ?? "" })}\n`);
}
void main();
