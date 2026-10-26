// `Client`: one config, every resource hangs off it.
//
// Extending the client
//   - Add methods to a resource in `./resources/<name>.ts` (hand-written, never regenerated).
//   - Swap or add a resource class: `new Client({ resources: { datasets: MyDatasets } })`.
//   - Call an endpoint the catalog lacks: `client.request("GET", "/some/path/", { query })`.
//   - Per call: `client.datasets.get(id, { timeout: 5000, headers: { ... } })`.

import { API_KEY_ENVVAR_NAME, SECRET_KEY_ENVVAR_NAME, get_base_url } from "../utils/constants";
import { createResources, ResourceClasses, Resources } from "./resources";
import { FetchLike, RequestArgs, RequestOptions, ResolvedConfig, Transport } from "./transport";

export interface ClientConfig {
  /** Defaults to FI_API_KEY. */
  apiKey?: string;
  /** Defaults to FI_SECRET_KEY. */
  secretKey?: string;
  /** Defaults to FI_BASE_URL, then https://api.futureagi.com. */
  baseUrl?: string;
  /** Defaults to FI_WORKSPACE_ID. */
  workspaceId?: string;
  /** Per-request timeout in milliseconds (default 60 000). */
  timeout?: number;
  /** Retries for 429 on every call and for timeouts/5xx on calls that are safe to repeat (default 2). */
  maxRetries?: number;
  /** Sent with every request. */
  defaultHeaders?: Record<string, string>;
  /** Replace the global `fetch` (tests, proxies, custom agents). */
  fetch?: FetchLike;
  /** Replace or add resource classes: `{ datasets: MyDatasets }`. */
  resources?: Partial<ResourceClasses>;
}

function resolveConfig(config: ClientConfig): ResolvedConfig {
  const env = typeof process !== "undefined" ? process.env : {};
  const apiKey = config.apiKey ?? env[API_KEY_ENVVAR_NAME];
  const secretKey = config.secretKey ?? env[SECRET_KEY_ENVVAR_NAME];
  if (!apiKey || !secretKey) {
    throw new Error(`pass apiKey and secretKey, or set ${API_KEY_ENVVAR_NAME} and ${SECRET_KEY_ENVVAR_NAME}`);
  }
  if (config.maxRetries !== undefined && config.maxRetries < 0) {
    throw new Error("maxRetries must be >= 0");
  }
  const fetchImpl = config.fetch ?? (typeof fetch === "function" ? fetch : undefined);
  if (!fetchImpl) {
    throw new Error("no global fetch: pass `fetch` in the client config (Node >= 18 has one)");
  }
  return {
    apiKey,
    secretKey,
    baseUrl: (config.baseUrl ?? get_base_url()).replace(/\/+$/, ""),
    workspaceId: config.workspaceId ?? env.FI_WORKSPACE_ID,
    timeout: config.timeout ?? 60_000,
    maxRetries: config.maxRetries ?? 2,
    defaultHeaders: config.defaultHeaders,
    fetch: fetchImpl,
  };
}

/**
 * Future AGI platform client.
 *
 *     import { Client } from "@future-agi/sdk";
 *     const client = new Client();            // FI_API_KEY / FI_SECRET_KEY / FI_BASE_URL
 *     for await (const ds of client.datasets.list()) console.log(ds.name);
 */
export class Client {
  /** The HTTP layer, for hand-written resource methods and tests. */
  readonly transport: Transport;

  constructor(config: ClientConfig = {}) {
    this.transport = new Transport(resolveConfig(config));
    Object.assign(this, createResources(this.transport, config.resources));
  }

  /**
   * Call any endpoint under the base URL with the client's auth, retries and errors, for
   * endpoints the catalog does not describe yet. Resolves to the decoded JSON with the
   * `unwrap` key (the backend's `{status, result}` envelope) removed when present.
   */
  request(method: string, path: string, args: RequestArgs & { unwrap?: string | null; multipart?: boolean } = {}, options?: RequestOptions): Promise<unknown> {
    return this.transport.raw(method, path, args, options);
  }
}

// The generated resources (`client.datasets`, ...) are declared through interface merging, so
// `client.ts` never changes when the catalog does.
// eslint-disable-next-line @typescript-eslint/no-empty-interface
export interface Client extends Resources {}
