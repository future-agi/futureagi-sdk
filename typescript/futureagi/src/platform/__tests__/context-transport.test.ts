import { Client, ClientConfig } from "../client";
import { APIConnectionError, APIError } from "../errors";
import { Auth, FetchLike, operationOptions, RequestOptions } from "../transport";

const BASE = "https://backend.test";
const TOKEN = "11111111-1111-4111-8111-111111111111." + "synthetic-".repeat(5);
const RESOLVE = "/model-hub/skills/contexts/resolve/";
const MANIFEST = "/model-hub/skills/contexts/context-1/versions/7/manifest/";
const auth: Auth = { type: "context", credential: TOKEN };
const ok = (result: unknown = {}) => new Response(JSON.stringify({ status: true, result }), { status: 200, headers: { "content-type": "application/json" } });

function setup(handler: (url: string, init: RequestInit) => Response | Promise<Response> = () => ok(), extra: Partial<ClientConfig> = {}) {
  const calls: Array<{ url: string; init: RequestInit; headers: Headers }> = [];
  const fetch: FetchLike = async (url, init) => {
    calls.push({ url, init, headers: new Headers(init.headers) });
    return handler(url, init);
  };
  const client = new Client({ auth, baseUrl: BASE, fetch, ...extra } as ClientConfig);
  return { client, calls };
}

afterEach(() => jest.restoreAllMocks());

describe("exclusive authentication", () => {
  test.each([false, true])("Context mode ignores stale broad credentials: %s", async stale => {
    const saved = { ...process.env };
    try {
      for (const key of ["FI_API_KEY", "FI_SECRET_KEY", "FI_WORKSPACE_ID"]) {
        delete process.env[key];
        if (stale) process.env[key] = "stale-broad";
      }
      const { client, calls } = setup(() => ok({ resolution_id: "lease-7", resolution_expires_at: "2026-11-07T01:15:00Z" }));
      expect(await client.request("GET", RESOLVE)).toEqual({ resolution_id: "lease-7", resolution_expires_at: "2026-11-07T01:15:00Z" });
      expect(calls[0].headers.get("authorization")).toBe(`Context ${TOKEN}`);
      for (const header of ["x-api-key", "x-secret-key", "x-workspace-id", "cookie"]) expect(calls[0].headers.has(header)).toBe(false);
      expect(calls[0].init.credentials).toBe("omit");
    } finally {
      process.env = saved;
    }
  });

  test.each([{ apiKey: "broad" }, { secretKey: "broad" }, { apiKey: "" }])("mixed config is rejected at runtime", extra => {
    expect(() => setup(undefined, extra)).toThrow(/cannot be combined/);
  });

  test.each(["Authorization", "x-API-key", "X-Secret-Key", "Cookie", "Proxy-Authorization"])("header %s cannot override explicit auth", async header => {
    expect(() => setup(undefined, { defaultHeaders: { [header]: "hidden" } })).toThrow(/authentication header/);
    const { client, calls } = setup();
    await expect(client.request("GET", RESOLVE, {}, { headers: { [header]: "hidden" } })).rejects.toThrow(/authentication header/);
    expect(calls).toHaveLength(0);
  });

  test("only an explicitly configured workspace header is allowed", async () => {
    const { client, calls } = setup(undefined, { workspaceId: "workspace-1" });
    await client.request("GET", RESOLVE, {}, { headers: { "x-workspace-id": "workspace-1" } });
    expect(calls[0].headers.get("x-workspace-id")).toBe("workspace-1");
    await expect(client.request("GET", RESOLVE, {}, { headers: { "X-WORKSPACE-ID": "workspace-2" } })).rejects.toThrow(/workspace header/);
    expect(() => setup(undefined, { defaultHeaders: { "x-workspace-id": "workspace-2" } })).toThrow(/workspace header/);
    expect(calls).toHaveLength(1);
  });

  test("explicit API pair is also exclusive", async () => {
    const { client, calls } = setup(undefined, { auth: { type: "api_key", apiKey: "explicit", secretKey: "pair" } });
    await client.request("GET", RESOLVE);
    expect(calls[0].headers.get("x-api-key")).toBe("explicit");
    expect(calls[0].headers.get("x-secret-key")).toBe("pair");
    expect(calls[0].headers.has("authorization")).toBe(false);
    await expect(client.request("GET", RESOLVE, {}, { headers: { authorization: "other" } })).rejects.toThrow(/authentication header/);
  });

  test.each(["", "secret\r\nInjected: yes", "white space", "é", 1])("invalid secrets have sanitized errors", credential => {
    expect(() => setup(undefined, { auth: { type: "context", credential } as Auth })).toThrow(/ASCII token/);
  });

  test("runtime auth discrimination rejects malformed unions and URL credentials", () => {
    for (const invalid of [null, {}, { type: "unknown" }, { type: "context", credential: TOKEN, apiKey: "broad" }]) {
      expect(() => setup(undefined, { auth: invalid as unknown as Auth })).toThrow();
    }
    expect(() => setup(undefined, { baseUrl: "https://broad:secret@backend.test" })).toThrow(/URL credentials/);
  });
});

describe("immutable continuation", () => {
  test("label movement cannot alter a caller's leased immutable requests", async () => {
    const { client, calls } = setup((url, init) => {
      if (new URL(url).pathname === RESOLVE) return ok({ version: 7, version_id: "v7", digest: "digest-7", resolution_id: "lease-7" });
      expect(new URL(url).pathname).toBe(MANIFEST);
      expect(new Headers(init.headers).get("x-context-resolution")).toBe("lease-7");
      return ok({ version: 7, digest: "digest-7" }); // production has advanced to v8
    });
    const resolved = await client.request("GET", RESOLVE, { query: { name: "demo", label: "production" } }) as { resolution_id: string };
    for (const offset of [25, 50]) {
      expect(await client.request("GET", MANIFEST, { query: { file_offset: offset } }, { resolutionId: resolved.resolution_id })).toEqual({ version: 7, digest: "digest-7" });
    }
    expect(calls).toHaveLength(3);
  });

  test.each([401, 403, 410, 422, 304])("denial %s is never retried or replaced by a label resolve", async status => {
    const { client, calls } = setup(() => new Response(status === 304 ? null : JSON.stringify({ code: "denied" }), { status }));
    await expect(client.request("GET", MANIFEST, { decode: "bytes" }, { resolutionId: "lease" })).rejects.toMatchObject({ status });
    expect(calls).toHaveLength(1);
  });

  test("429 retries preserve the exact caller operation and lease", async () => {
    let attempts = 0;
    const { client, calls } = setup(() => ++attempts === 1 ? new Response(null, { status: 429, headers: { "retry-after": "0" } }) : ok());
    await client.request("POST", "/model-hub/skills/contexts/bindings/b/receipts/", { body: { event_id: "event" } }, { resolutionId: "lease", idempotencyKey: "original-key" });
    expect(calls).toHaveLength(2);
    expect(calls[0].init.body).toBe(calls[1].init.body);
    for (const { headers } of calls) {
      expect(headers.get("idempotency-key")).toBe("original-key");
      expect(headers.get("x-context-resolution")).toBe("lease");
    }
  });

  test("unknown POST is never automatically replayed", async () => {
    const { client, calls } = setup(() => { throw new Error("lost response"); });
    await expect(client.request("POST", RESOLVE, {}, { idempotencyKey: "original-key" })).rejects.toBeInstanceOf(APIConnectionError);
    expect(calls).toHaveLength(1);
  });

  test.each(["/other/", "https://evil.test/token", "https://user:pass@backend.test/other/"])("redirect %s cannot move a credential or lease", async location => {
    const { client, calls } = setup(() => new Response(null, { status: 307, headers: { location } }));
    await expect(client.request("GET", RESOLVE)).rejects.toThrow(/cannot follow redirects/);
    expect(calls).toHaveLength(1);
  });

  test("ZIP and empty bytes remain byte-identical; download errors remain typed", async () => {
    for (const raw of [new Uint8Array([80, 75, 0, 255, 254, 128, 13, 10]), new Uint8Array()]) {
      const { client } = setup(() => new Response(raw, { headers: { "content-type": "application/zip" } }));
      expect(await client.request("GET", MANIFEST, { decode: "bytes" }, { resolutionId: "lease" })).toEqual(raw);
    }
    const { client } = setup(() => new Response(JSON.stringify({ code: "context_quarantined" }), { status: 422 }));
    await expect(client.request("GET", MANIFEST, { decode: "bytes" })).rejects.toBeInstanceOf(APIError);
  });

  test("concurrent immutable reads never share a mutable lease header", async () => {
    const { client, calls } = setup();
    await Promise.all(Array.from({ length: 8 }, (_, i) => client.request("GET", MANIFEST, {}, { resolutionId: `lease-${i}` })));
    expect(new Set(calls.map(c => c.headers.get("x-context-resolution")))).toEqual(new Set(Array.from({ length: 8 }, (_, i) => `lease-${i}`)));
    await client.request("GET", RESOLVE);
    expect(calls[8].headers.has("x-context-resolution")).toBe(false);
  });

  test("typed headers cannot hide conflicting defaults", async () => {
    const { client } = setup(undefined, { defaultHeaders: { "x-context-resolution": "old" } });
    await expect(client.request("GET", RESOLVE, {}, { resolutionId: "new" })).rejects.toThrow(/conflicting X-Context-Resolution/);
  });
});

test("generated headers are allowlisted and cannot replace an operation identity", () => {
  const original: RequestOptions = { resolutionId: "lease", headers: { "X-Trace": "trace" } };
  const merged = operationOptions(original, { "X-Context-Resolution": "lease", "Idempotency-Key": "key" });
  expect(merged.headers).toEqual({ "X-Trace": "trace", "X-Context-Resolution": "lease", "Idempotency-Key": "key" });
  expect(original.headers).toEqual({ "X-Trace": "trace" });
  expect(() => operationOptions(original, { "x-context-resolution": "other" })).toThrow(/conflicting/);
  expect(() => operationOptions(undefined, { "Authorization": "hidden" })).toThrow(/may only carry/);
  expect(() => operationOptions(undefined, { "Idempotency-Key": undefined }, ["Idempotency-Key"])).toThrow(/required/);
});
