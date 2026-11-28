/**
 * Run as a child process with the runtime's environment proxy on (NODE_USE_ENV_PROXY=1, HTTP_PROXY set): axios's
 * default adapter is set to 'fetch' before the clients are built, then a control `fetch` (which the runtime sends
 * through the proxy) and keyed requests of an `APIKeyAuth` and of an `HttpClient` are made. The listeners are the
 * parent's; this prints what each call answered: a status, or the error class and code.
 */
import axios from "axios";

import { APIKeyAuth, HttpClient } from "../auth";
import { HttpMethod } from "../types";

async function main(): Promise<void> {
  const base = `http://app.localhost:${process.env.PROBE_TARGET_PORT ?? ""}`;
  const key = process.env.PROBE_KEY ?? "";
  const secret = process.env.PROBE_SECRET ?? "";
  axios.defaults.adapter = "fetch";
  const answer = async (call: () => PromiseLike<unknown>): Promise<string> => {
    try { return String(((await call()) as { status?: number }).status); } catch (error) {
      const code = (error as { code?: unknown }).code;
      return `error:${(error as Error).constructor.name}:${typeof code === "string" ? code : ""}`;
    }
  };
  const control = await answer(() => fetch(`${base}/control`));
  const auth = new APIKeyAuth({ fiApiKey: key, fiSecretKey: secret, fiBaseUrl: base, retryAttempts: 1, allowInsecureHttp: true } as never);
  const keyedAuth = await answer(() => auth.request({ method: HttpMethod.GET, url: "/auth" }));
  const client = new HttpClient({ baseUrl: base, retryAttempts: 1, allowInsecureHttp: true });
  const keyedCall = await answer(() => client.request({ method: HttpMethod.GET, url: "/call", headers: { "X-Api-Key": key } as never }));
  process.stdout.write(`${JSON.stringify({ control, keyedAuth, keyedCall })}\n`);
}
void main();
