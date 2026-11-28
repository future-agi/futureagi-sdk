/**
 * An axios adapter function of a third party that sends through the runtime's global `fetch`: it reads none of the
 * `proxy`, agent or `maxRedirects` settings of the request, so `fetch` follows a redirect on its own and goes through
 * the runtime's environment proxy when that is on. Each call is counted, so a test can tell whether the request was
 * handed to it.
 */
import axios, { type AxiosAdapter, type AxiosResponse, type InternalAxiosRequestConfig } from "axios";

export interface CountingAdapter {
  readonly adapter: AxiosAdapter;
  readonly calls: number;
}

export function globalFetchAdapter(): CountingAdapter {
  let calls = 0;
  const adapter: AxiosAdapter = async (config: InternalAxiosRequestConfig): Promise<AxiosResponse> => {
    calls += 1;
    const headers: Record<string, string> = {};
    for (const [name, value] of Object.entries(config.headers.toJSON())) {
      if (value !== undefined && value !== null && value !== false) headers[name] = String(value);
    }
    const response = await fetch(axios.getUri(config), { method: String(config.method ?? "get").toUpperCase(), headers });
    const data = await response.text();
    const answered: Record<string, string> = {};
    response.headers.forEach((value, name) => { answered[name] = value; });
    return { data, status: response.status, statusText: response.statusText, headers: answered, config, request: {} };
  };
  return { adapter, get calls() { return calls; } };
}
