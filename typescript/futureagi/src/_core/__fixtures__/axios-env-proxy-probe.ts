/**
 * Run as a child process with the runtime's environment proxy on (NODE_USE_ENV_PROXY=1, HTTP_PROXY set) and the plain-HTTP
 * opt-in on: first a control `fetch`, which the runtime sends through the proxy, then keyed requests of an `HttpClient`
 * and of an `APIKeyAuth`, which go straight to their host. The listeners are the parent's; this prints what
 * each call answered.
 */
import { APIKeyAuth, HttpClient } from "../../api/auth";
import { HttpMethod } from "../../api/types";

async function main(): Promise<void> {
  const base = `http://app.localhost:${process.env.PROBE_TARGET_PORT ?? ""}`;
  const key = process.env.PROBE_KEY ?? "";
  const answer = async (call: () => PromiseLike<unknown>): Promise<string> => {
    try { return String(((await call()) as { status?: number }).status); } catch (error) { return `error:${String(error)}`; }
  };
  const get = (client: HttpClient, path: string, headers?: Record<string, unknown>) =>
    client.request({ method: HttpMethod.GET, url: path, ...(headers === undefined ? {} : { headers: headers as never }) });
  const open = { baseUrl: base, retryAttempts: 1, allowInsecureHttp: true };
  const control = await answer(() => fetch(`${base}/control`));
  const keyedDefault = await answer(() => get(new HttpClient({ ...open, defaultHeaders: { "X-Api-Key": key } }), "/default"));
  const keyedCall = await answer(() => get(new HttpClient(open), "/call", { "X-Secret-Key": key }));
  const keyedLayer = await answer(() => get(new HttpClient(open), "/layer", { common: { Authorization: `Bearer ${key}` } }));
  const auth = new APIKeyAuth({ fiApiKey: key, fiSecretKey: key, fiBaseUrl: base, retryAttempts: 1, allowInsecureHttp: true } as never);
  const keyedAuth = await answer(() => get(auth, "/auth"));
  // the same request with a control character before the scheme, which the URL parser drops
  const keyedPrefixed = await answer(() => get(new HttpClient({ ...open, baseUrl: `\u001c${base}`, defaultHeaders: { "X-Api-Key": key } }), "/prefixed"));
  process.stdout.write(`${JSON.stringify({ control, keyedDefault, keyedCall, keyedLayer, keyedAuth, keyedPrefixed })}\n`);
}
void main();
