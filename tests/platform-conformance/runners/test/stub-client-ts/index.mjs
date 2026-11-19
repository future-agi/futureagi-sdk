// A stub SDK (test fixture only). Three operations over an injected fetch, typed errors, and the
// client-side host guard, so the runner shell's by-path loading and outcome mapping are tested.
const ROUTES = {
  "platform.capabilities.get": () => "/workspace/capabilities",
  "sandboxes.list": () => "/workspace/sandboxes",
  "sandboxes.getInfo": (args) => `/workspace/sandboxes/${encodeURIComponent(args.sandbox)}`,
};

export class StubError extends Error {
  constructor(status, code) {
    super(`stub ${status} ${code}`);
    this.status = status;
    this.code = code;
  }
}

export class StubConfigError extends Error {}

export function isFutureAgiOrLoopback(url) {
  const host = new URL(url).hostname;
  return host === "127.0.0.1" || host === "localhost" || host === "futureagi.com" || host.endsWith(".futureagi.com");
}

export class StubClient {
  constructor({ baseUrl, apiKey, fetch, allowCustomBaseUrl = false }) {
    if (!allowCustomBaseUrl && !isFutureAgiOrLoopback(baseUrl)) throw new StubConfigError("refusing to send a key to a foreign host");
    Object.assign(this, { baseUrl, apiKey, fetch });
  }

  async call(name, args = {}) {
    const route = ROUTES[name];
    if (!route) throw new StubError(0, "unknown_operation");
    const response = await this.fetch(`${this.baseUrl}${route(args)}`, { headers: { authorization: `Bearer ${this.apiKey}` }, redirect: "manual" });
    const body = await response.json().catch(() => null);
    if (!response.ok) throw new StubError(response.status, body?.code ?? body?.error?.code ?? `http_${response.status}`);
    return body;
  }
}
