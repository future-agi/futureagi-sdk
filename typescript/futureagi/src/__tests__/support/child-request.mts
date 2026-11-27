// One keyed request from a fresh process; prints the outcome as one JSON line.
//
// The SDK modules are loaded after the process-wide setup below, so a case can replace the global fetch before or
// after they are imported, and install a global dispatcher before the client is made.
import { createRequire } from "node:module";

const spec = JSON.parse(process.env.FI_CHILD_CASE ?? "{}") as {
  /** "probe-unkeyed": one plain http.get without a key, outside the SDK. "axios-http-client": an axios HttpClient with
   * only the given default headers (the client key and secret are not used). */
  kind: "axios" | "fetch" | "probe-unkeyed" | "axios-http-client";
  baseUrl: string;
  apiKey: string;
  secretKey: string;
  defaultHeaders?: Record<string, string>;
  allowInsecureHttp?: boolean;
  /** Directory of an undici package, and the proxy its dispatchers should send to. */
  undici?: string;
  proxyAgent?: string;
  /** The global dispatcher to install (default: a ProxyAgent when `proxyAgent` is given). */
  dispatcher?: "proxy-agent" | "named-agent" | "proxy-wrapped-agent" | "compose-proxy" | "pool" | "composed-pool";
  /** Replace the global fetch with one that drops the dispatcher it is given and sends through `proxyAgent`. */
  fetchWrapper?: "before-import" | "after-import";
  /** Return from main instead of calling process.exit, so the time the process takes to exit can be measured. */
  noExit?: boolean;
  /** Before the SDK is imported, wrap http.request and http.get so that every request uses an agent that sends it to
   * `proxyAgent` in absolute form, whatever agent the caller gave (as a process-wide proxy bootstrap does). */
  forcedHttpAgent?: boolean;
  /** Like `forcedHttpAgent`, with the call shape of global-agent under forceGlobalAgent: http.request and http.get are
   * replaced before the SDK is imported by functions that copy the options, set their agent to one that sends every
   * request to `proxyAgent` in absolute form, and pass the caller's callback on. */
  globalAgentWrapper?: boolean;
  /** Set axios.defaults.adapter before the client is made. */
  axiosAdapter?: "fetch" | "http";
};

const load = createRequire(import.meta.url);

function makeDispatcher(undici: any, kind: NonNullable<typeof spec.dispatcher>, proxy: string): unknown {
  switch (kind) {
    case "proxy-agent":
      return new undici.ProxyAgent(proxy);
    case "named-agent": {
      // A dispatcher class named Agent that sends every request through the proxy.
      const Base = undici.ProxyAgent;
      const Named = { Agent: class extends Base {} }.Agent;
      return new Named(proxy);
    }
    case "proxy-wrapped-agent":
      // A JavaScript Proxy around a proxying dispatcher, reporting the constructor of a plain Agent.
      return new Proxy(new undici.ProxyAgent(proxy), {
        get(target, name) {
          if (name === "constructor") return undici.Agent;
          const value = Reflect.get(target, name, target);
          return typeof value === "function" ? value.bind(target) : value;
        },
      });
    case "compose-proxy": {
      // An Agent composed with an interceptor that hands every request to a ProxyAgent.
      const via = new undici.ProxyAgent(proxy);
      return new undici.Agent().compose(() => (options: unknown, handler: unknown) => via.dispatch(options, handler));
    }
    case "pool":
      return new undici.Pool(proxy);
    case "composed-pool":
      return new undici.Pool(proxy).compose((dispatch: any) => (options: unknown, handler: unknown) => dispatch(options, handler));
  }
}

function installForcedHttpAgent(proxy: string): void {
  const http = load("node:http");
  const via = new URL(proxy);
  class ForcedProxyAgent extends http.Agent {
    addRequest(request: any, options: any): void {
      request.path = `http://${options.host}:${options.port}${request.path}`;
      super.addRequest(request, { ...options, host: via.hostname, port: Number(via.port) });
    }
  }
  const forced = new ForcedProxyAgent();
  for (const name of ["request", "get"] as const) {
    const original = http[name];
    http[name] = function (input: any, options?: any, callback?: any) {
      if (typeof options === "function") {
        callback = options;
        options = undefined;
      }
      if (typeof input === "object" && !(input instanceof URL)) {
        return original.call(http, { ...input, agent: forced }, options);
      }
      return original.call(http, input, { ...(options ?? {}), agent: forced }, callback);
    };
  }
  load("node:module").syncBuiltinESMExports();
}

function installGlobalAgentWrapper(proxy: string): void {
  const http = load("node:http");
  const via = new URL(proxy);
  class ProxyOnlyAgent extends http.Agent {
    addRequest(request: any, options: any): void {
      request.path = `http://${options.host}:${options.port}${request.path}`;
      super.addRequest(request, { ...options, host: via.hostname, port: Number(via.port) });
    }
  }
  const agent = new ProxyOnlyAgent();
  for (const name of ["request", "get"] as const) {
    const original = http[name];
    http[name] = function (...args: any[]) {
      if (typeof args[0] === "string" || args[0] instanceof URL) {
        const [options, callback] = typeof args[1] === "function" ? [{}, args[1]] : [{ ...(args[1] ?? {}) }, args[2]];
        return original.call(http, args[0], { ...options, agent }, callback);
      }
      return original.call(http, { ...(args[0] ?? {}), agent }, args[1]);
    };
  }
  load("node:module").syncBuiltinESMExports();
}

function installFetchWrapper(undici: any, proxy: string): void {
  const original = globalThis.fetch;
  const via = new undici.ProxyAgent(proxy);
  globalThis.fetch = ((input: any, init: any = {}) => original(input, { ...init, dispatcher: via })) as typeof fetch;
}

async function main(): Promise<void> {
  try {
    const undici = spec.undici !== undefined ? load(spec.undici) : undefined;
    if (spec.fetchWrapper === "before-import") installFetchWrapper(undici, spec.proxyAgent!);
    if (spec.forcedHttpAgent) installForcedHttpAgent(spec.proxyAgent!);
    if (spec.globalAgentWrapper) installGlobalAgentWrapper(spec.proxyAgent!);
    const { APIKeyAuth } = await import("../../api/auth");
    const { Client } = await import("../../platform/client");
    if (spec.fetchWrapper === "after-import") installFetchWrapper(undici, spec.proxyAgent!);
    if (spec.fetchWrapper === undefined && undici !== undefined && spec.proxyAgent !== undefined) {
      undici.setGlobalDispatcher(makeDispatcher(undici, spec.dispatcher ?? "proxy-agent", spec.proxyAgent));
    }
    if (spec.axiosAdapter !== undefined) {
      const axios = (await import("axios")).default;
      axios.defaults.adapter = spec.axiosAdapter;
    }
    if (spec.kind === "probe-unkeyed") {
      const http = load("node:http");
      await new Promise<void>((resolve, reject) => {
        http.get(`${spec.baseUrl}/v1/probe`, (response: any) => response.resume().on("end", resolve)).on("error", reject);
      });
    } else if (spec.kind === "axios-http-client") {
      const { HttpClient } = await import("../../api/auth");
      const http = new HttpClient({ baseUrl: spec.baseUrl, retryAttempts: 1, timeout: 5000, defaultHeaders: spec.defaultHeaders, allowInsecureHttp: spec.allowInsecureHttp } as any);
      await http.request({ method: "GET", url: "/v1/probe" });
    } else if (spec.kind === "axios") {
      const http = new APIKeyAuth({ fiApiKey: spec.apiKey, fiSecretKey: spec.secretKey, baseUrl: spec.baseUrl, retryAttempts: 1, timeout: 5000, defaultHeaders: spec.defaultHeaders, allowInsecureHttp: spec.allowInsecureHttp } as any);
      await http.request({ method: "GET", url: "/v1/probe" });
    } else {
      const client = new Client({ apiKey: spec.apiKey, secretKey: spec.secretKey, baseUrl: spec.baseUrl, maxRetries: 0, timeout: 5000, defaultHeaders: spec.defaultHeaders, allowInsecureHttp: spec.allowInsecureHttp } as any);
      await client.request("GET", "/v1/probe/");
    }
    console.log("RESULT:" + JSON.stringify({ ok: true }));
  } catch (error) {
    const e = error as { code?: string; message?: string };
    console.log("RESULT:" + JSON.stringify({ ok: false, code: e.code ?? null }));
  }
  if (!spec.noExit) process.exit(0);
}

void main();
