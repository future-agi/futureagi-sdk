/**
 * Root client and core-namespace error behavior:
 * every status on a core namespace throws the same class a platform namespace throws, with the body's
 * fields kept on the error; a fetch failure is APIConnectionError / APITimeoutError; withOptions; the
 * platform options reach the origin, and a bad platform setting never breaks a core namespace.
 */
import { FutureAGIClient } from "../../futureagi-client";
import { SDKException } from "../../utils/errors";
import { CoreServerError, json, netError, STATUS_CLASSES } from "../__fixtures__/platform";
import * as E from "../errors";

const KEYS = { apiKey: "k-test-1234", secretKey: "s-test-1234", baseUrl: "http://api.test", retries: 0 };

function client(answer: (request: Request) => Response | Promise<Response>, extra: Record<string, unknown> = {}) {
  const requests: Request[] = [];
  const fetchMock = (async (input: RequestInfo | URL, init?: RequestInit) => {
    const request = new Request(input as RequestInfo, init);
    requests.push(request);
    return answer(request);
  }) as typeof fetch;
  const c = new FutureAGIClient({ ...KEYS, fetch: fetchMock, ...extra });
  return { c, requests };
}

const calls = (c: FutureAGIClient) => ({
  core: () => c.annotationQueues.list({ limit: 1 }),
  "core typed": () => c.datasets.versions.list("d1"),
  platform: () => c._platform.call("platform.capabilities.get"),
});

describe("core namespaces throw the platform's classes", () => {
  it.each(STATUS_CLASSES)("%i is %p on core and platform", async (status, cls) => {
    const { c } = client((request) => json(status, {
      detail: "nope",
      // The Console resource 404 has an EE envelope; plain FA/core 404s remain unchanged.
      ...(status === 404 && new URL(request.url).pathname.startsWith("/omega/api/workspace/") ? { code: "not_found" } : {}),
    }, { "x-request-id": "req-7" }));
    for (const [path, call] of Object.entries(calls(c))) {
      const err = (await Promise.resolve(call()).then(undefined, (e: unknown) => e)) as E.FutureAGIAPIError & { detail?: string };
      expect([path, err.constructor]).toEqual([path, cls]);
      expect([path, err.statusCode, err.requestId]).toEqual([path, status, "req-7"]);
      expect(err).toBeInstanceOf(SDKException);
      if (path !== "platform") expect([path, err.detail]).toEqual([path, "nope"]); // body fields kept (Object.assign)
    }
  });

  it("a non-JSON 503 from a proxy is still CoreServerError", async () => {
    const { c } = client(() => new Response("<html>busy</html>", { status: 503 }));
    await expect(c.annotationQueues.list({ limit: 1 })).rejects.toBeInstanceOf(CoreServerError);
  });

  it.each([
    ["ECONNREFUSED", E.APIConnectionError],
    ["UND_ERR_CONNECT_TIMEOUT", E.APITimeoutError],
    ["ECONNRESET", E.APIConnectionError],
  ] as const)("%s is %p on core and platform", async (code, cls) => {
    const { c } = client(() => {
      throw netError(code);
    });
    for (const [path, call] of Object.entries(calls(c))) {
      const err = await Promise.resolve(call()).then(undefined, (e: unknown) => e);
      expect([path, (err as object).constructor]).toEqual([path, cls]);
    }
  });

  it("a timeout on a core call is APITimeoutError; missing keys stay CredentialsMissingError", async () => {
    const hang = (req: Request) =>
      new Promise<Response>((_, reject) => req.signal.addEventListener("abort", () => reject(req.signal.reason)));
    const { c } = client(hang, { timeoutMs: 20 });
    await expect(c.annotationQueues.list({ limit: 1 })).rejects.toBeInstanceOf(E.APITimeoutError);
    const prev = { a: process.env.FI_API_KEY, s: process.env.FI_SECRET_KEY };
    delete process.env.FI_API_KEY;
    delete process.env.FI_SECRET_KEY;
    try {
      const bare = new FutureAGIClient({ baseUrl: "http://api.test", fetch: (async () => json(200, {})) as typeof fetch });
      const err = await bare.annotationQueues.list({ limit: 1 }).then(undefined, (e: unknown) => e);
      expect(err).toBeInstanceOf(E.CredentialsMissingError);
      expect(String((err as Error).message)).toMatch(/requires credentials/u);
    } finally {
      if (prev.a !== undefined) process.env.FI_API_KEY = prev.a;
      if (prev.s !== undefined) process.env.FI_SECRET_KEY = prev.s;
    }
  });
});

describe("core edge cases", () => {
  it("an unparsable success body is FutureAGIAPIError invalid_json, made once", async () => {
    const { c, requests } = client(() => new Response("not-json", { status: 201, headers: { "Content-Type": "application/json" } }));
    const err = (await c.datasets.versions.create("d1", { items: [] } as never).then(undefined, (e: unknown) => e)) as E.FutureAGIAPIError;
    expect(err).toBeInstanceOf(E.FutureAGIAPIError);
    expect([err.code, err.statusCode]).toEqual(["invalid_json", 201]);
    expect(requests).toHaveLength(1);
  });

  it("the fiApiKey / fiSecretKey aliases reach the platform origin too", async () => {
    const requests: Request[] = [];
    const c = new FutureAGIClient({
      fiApiKey: "k-alias-1234",
      fiSecretKey: "s-alias-1234",
      baseUrl: "http://api.test",
      fetch: (async (input: RequestInfo | URL, init?: RequestInit) => {
        requests.push(new Request(input as RequestInfo, init));
        return json(200, {});
      }) as typeof fetch,
    });
    await c._platform.call("platform.capabilities.get");
    expect(requests[0]!.headers.get("x-api-key")).toBe("k-alias-1234");
  });
});

describe("a split key pair never reaches the platform", () => {
  const ENV_NAMES = ["FI_API_KEY", "FI_SECRET_KEY", "FI_PLATFORM_BASE_URL"] as const;
  let saved: Record<string, string | undefined>;
  beforeEach(() => {
    saved = Object.fromEntries(ENV_NAMES.map((n) => [n, process.env[n]]));
    for (const n of ENV_NAMES) delete process.env[n];
  });
  afterEach(() => {
    for (const n of ENV_NAMES) {
      if (saved[n] === undefined) delete process.env[n];
      else process.env[n] = saved[n];
    }
  });

  it.each([
    [
      "apiKey + platformBaseUrl arguments, FI_SECRET_KEY in env",
      { apiKey: "k-arg-1234", platformBaseUrl: "http://127.0.0.1:9/omega/api" },
      { FI_SECRET_KEY: "s-env-1234" },
    ],
    [
      "secretKey argument, FI_API_KEY + FI_PLATFORM_BASE_URL in env",
      { secretKey: "s-arg-1234" },
      { FI_API_KEY: "k-env-1234", FI_PLATFORM_BASE_URL: "https://evil.example/omega/api" },
    ],
  ] as const)("%s: CredentialsMissingError and nothing is sent", async (_name, options, env) => {
    Object.assign(process.env, env);
    const sent: Request[] = [];
    const c = new FutureAGIClient({
      ...options,
      baseUrl: "https://api.futureagi.com",
      retries: 0,
      fetch: (async (input: RequestInfo | URL, init?: RequestInit) => {
        sent.push(new Request(input as RequestInfo, init));
        return json(200, {});
      }) as typeof fetch,
    });
    await expect(c._platform.call("platform.capabilities.get")).rejects.toBeInstanceOf(E.CredentialsMissingError);
    expect(sent).toHaveLength(0);
  });
});

describe("the client's platform options", () => {
  it("reach the origin, and the platform origin derives from baseUrl", async () => {
    const { c, requests } = client(() => json(200, { ok: true }), { workspaceId: "ws-2" });
    await c._platform.call("platform.capabilities.get");
    expect(requests[0]!.url).toBe("http://api.test/omega/api/workspace/capabilities");
    expect(requests[0]!.headers.get("x-workspace-id")).toBe("ws-2");
  });

  it("a bad platform setting never breaks a core namespace", async () => {
    const { c } = client(() => json(200, { count: 0, results: [] }), {
      platformBaseUrl: "https://evil.example/omega/api",
      platformToken: undefined,
    });
    await expect(c.annotationQueues.list({ limit: 1 })).resolves.toEqual({ count: 0, results: [] });
    const prev = process.env.FI_PLATFORM_BASE_URL;
    process.env.FI_PLATFORM_BASE_URL = "https://evil.example/omega/api";
    try {
      const { c: fromEnv } = client(() => json(200, {}));
      await expect(fromEnv._platform.call("platform.capabilities.get")).rejects.toBeInstanceOf(E.HostNotAllowedError);
    } finally {
      if (prev === undefined) delete process.env.FI_PLATFORM_BASE_URL;
      else process.env.FI_PLATFORM_BASE_URL = prev;
    }
  });

  it("withOptions changes the timeout and retries of a copy that shares the origin", async () => {
    let n = 0;
    const { c, requests } = client(() => (n++ === 0 ? json(503) : json(200, {})), { retries: 2 });
    const quick = c.withOptions({ retries: 0, timeoutMs: 5_000 });
    await expect(quick._platform.call("runs.get", { path: { id: "c" } })).rejects.toBeInstanceOf(CoreServerError);
    expect(requests).toHaveLength(1);
    expect(quick._platform.settings.timeoutMs).toBe(5_000);
    expect(quick._platform.shared).toBe(c._platform.shared);
    expect(c._platform.settings.timeoutMs).toBe(30_000);
  });
});
