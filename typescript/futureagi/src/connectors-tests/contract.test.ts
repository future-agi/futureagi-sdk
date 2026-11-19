import { readFileSync } from "node:fs";
import path from "node:path";
import { FutureAGIClient } from "../futureagi-client";
import { FutureAGIAPIError, UnexpectedRedirectError } from "../_core/errors";

const root = path.resolve(__dirname, "../../../..");
const read = (p: string) => JSON.parse(readFileSync(path.join(root, p), "utf8"));
const mapping = read("openapi/connectors/wrapper-map.json").operations;
const features = read("openapi/connectors/features.json");
const surface: Record<string, Record<string, string>> = read("python/tests/connectors/surface.json");
const namespaces: Record<string, string> = { connectors: "mcp_core", integrations: "data_integrations", credentials: "credential_reads" };
const rows: Array<[string, any]> = Object.values(surface).flatMap((methods) => Object.keys(methods).map((name): [string, any] => [name, mapping[name]]));
const camel = (value: string) => value.replace(/_([a-z])/g, (_, letter) => letter.toUpperCase());
function enabled(feature: string): boolean {
  const parent = ({ oauth_connect: "mcp_core", slack_channels: "data_integrations" } as Record<string, string>)[feature];
  return Boolean(features[feature] && (!parent || features[parent]));
}
function expectAbsent(c: any, name: string) {
  const [feature, methods] = Object.entries(surface).find(([, methods]) => name in methods)!;
  expect(enabled(feature)).toBe(false);
  const [namespace, ...parts] = methods[name]!.split(".").map(camel);
  if (!enabled(namespaces[namespace!]!)) expect(namespace! in c).toBe(false);
  else {
    let resource = c[namespace!];
    for (const part of parts.slice(0, -1)) resource = resource[part];
    expect(parts[parts.length - 1]! in resource).toBe(false);
  }
}
function absentWithoutRequest(name: string, row: any): boolean {
  if (enabled(row.feature)) return false;
  expectAbsent(client(() => { throw Error("unexpected request"); }), name);
  return true;
}
const specs = { ee: read("openapi/connectors/ee.json"), fa: read("openapi/connectors/fa.json") };

function contract(row: any) {
  for (const [route, item] of Object.entries(specs[row.source as "ee" | "fa"].paths) as Array<[string, any]>) {
    for (const method of ["get", "post", "put", "patch", "delete"]) {
      if (item[method]?.operationId === row.operation_id) return { route, method: method.toUpperCase(), op: item[method] };
    }
  }
  throw Error("missing operation");
}
function payload(name: string): any {
  if (name === "connectors.connect") return { authorizeUrl: "https://provider.invalid/consent?state=opaque" };
  if (name === "platform.credentials.list") return { credentials: [{ id: "one" }] };
  if (name === "integrations_connections_list") return { result: { connections: [{ id: "one" }], metadata: { total_count: 1 } } };
  if (name === "integrations_sync-logs_list") return { result: { sync_logs: [{ id: "one" }], metadata: { total_count: 1 } } };
  if (name === "integrations_connections_slack_channels_list") return { result: { channels: [{ id: "one" }], next_cursor: null } };
  return name.startsWith("integrations_") ? { result: { id: "one" } } : { id: "one" };
}
function client(handler: (request: Request) => Response | Promise<Response>, retries = 0) {
  return new FutureAGIClient({ apiKey: "test-person-key", secretKey: "test-person-secret", baseUrl: "http://127.0.0.1:9",
    platformBaseUrl: "http://127.0.0.1:9/omega/api", organizationId: "org-a", workspaceId: "ws-a", retries,
    fetch: (async (input: RequestInfo | URL, init?: RequestInit) => handler(new Request(input, init))) as typeof fetch });
}
function invoke(c: FutureAGIClient, row: any) {
  const method = row.methods[0];
  const parts = method.ts.split(".").slice(1);
  let resource: any = c;
  for (const part of parts.slice(0, -1)) resource = resource[part];
  const args: any[] = [], options: Record<string, unknown> = {};
  for (const arg of method.ts_args) {
    const name = arg.replace("options.", "");
    const values: Record<string, unknown> = { body: { display_name: "fixture" }, mine: "1", cursor: "opaque/cursor", pageNumber: 0,
      pageSize: 2, page: 1, limit: 2 };
    const value = values[name] ?? "id /?value";
    if (arg.startsWith("options.")) options[name] = value;
    else args.push(value);
  }
  if (Object.keys(options).length) args.push(options);
  return resource[parts[parts.length - 1]!](...args);
}
let realFetch: typeof fetch;
beforeEach(() => {
  realFetch = globalThis.fetch;
  globalThis.fetch = (async () => { throw Error("unexpected network call"); }) as typeof fetch;
});
afterEach(() => { globalThis.fetch = realFetch; });

test.each(rows)("wire contract %s", async (name, row) => {
  if (absentWithoutRequest(name, row)) return;
  const seen: Request[] = [];
  const value = await invoke(client((r) => { seen.push(r); return Response.json(payload(name)); }), row);
  expect(seen).toHaveLength(1);
  const request = seen[0]!;
  const spec = contract(row);
  expect(request.method).toBe(spec.method);
  const url = new URL(request.url);
  expect(url.pathname).toBe((row.source === "ee" ? "/omega/api" : "") + spec.route.replace(/\{[^}]+\}/g, encodeURIComponent("id /?value")));
  expect(request.headers.get("x-api-key")).toBe("test-person-key");
  expect(request.headers.get("x-secret-key")).toBe("test-person-secret");
  expect(request.headers.get("x-organization-id")).toBe("org-a");
  expect(request.headers.get("x-workspace-id")).toBe("ws-a");
  expect(request.headers.has("idempotency-key")).toBe(false);
  if (name === "connectors.connect") expect(value).toBe(payload(name).authorizeUrl);
  else if (name.endsWith("_list") || name === "platform.credentials.list") expect(value.items).toHaveLength(1);
  else expect(value).toEqual(row.source === "fa" ? payload(name).result : payload(name));
  if (row.methods[0].ts_args.includes("body")) expect(await request.json()).toEqual({ display_name: "fixture" });
  else if (spec.method === "POST") expect(await request.json()).toEqual({});
  else expect(await request.text()).toBe("");
});

for (const status of [400, 401, 403, 404, 409, 413, 422, 429, 500, 503]) {
  test.each(rows)(`typed ${status} for %s`, async (name, row) => {
    if (absentWithoutRequest(name, row)) return;
    const seen: Request[] = [];
    const c = client((r) => { seen.push(r); return Response.json({ code: "scope_denied", message: "not permitted" }, { status }); });
    const expected: Record<number, string> = {400: "BadRequestError", 401: "AuthenticationError", 403: "PermissionDeniedError", 404: "NotFoundError",
      409: "ConflictError", 413: "PayloadTooLargeError", 422: "UnprocessableEntityError", 429: "CoreRateLimitError"};
    await expect(invoke(c, row)).rejects.toMatchObject({name: expected[status] ?? "CoreServerError", code: "scope_denied"});
    expect(seen).toHaveLength(1);
  });
}
test.each(rows)("redirect refusal %s", async (name, row) => {
  if (absentWithoutRequest(name, row)) return;
  const seen: Request[] = [];
  const c = client((r) => { seen.push(r); return new Response(null, { status: 302, headers: { Location: "https://provider.invalid/callback" } }); });
  await expect(invoke(c, row)).rejects.toBeInstanceOf(UnexpectedRedirectError);
  expect(seen).toHaveLength(1);
});

test("unsafe sign-in is not retried after a service failure", async () => {
  const seen: Request[] = [];
  const c = client((r) => { seen.push(r); return Response.json({ code: "unavailable" }, { status: 503 }); }, 2);
  if (enabled("oauth_connect")) {
    await expect((c as any).connectors.connectApp("app")).rejects.toBeInstanceOf(FutureAGIAPIError);
    expect(seen).toHaveLength(1);
  } else {
    expectAbsent(c, "connectors.connect");
    expect(seen).toHaveLength(0);
  }
});

test("human-only credential mutations and OAuth completion are not exposed", () => {
  const c = client(() => { throw Error("unexpected request"); });
  for (const [namespace, methods] of Object.entries({ credentials: ["create", "delete", "revoke", "rotate"],
      connectors: ["completeOAuth"], integrations: ["slackInstall"] })) {
    if (enabled(namespaces[namespace]!)) for (const method of methods) expect(method in (c as any)[namespace]).toBe(false);
    else expect(namespace in c).toBe(false);
  }
});

test.each([
  [404, "product_not_admitted", "ProductNotAvailableError"],
  [409, "idempotency_key_in_progress", "IdempotencyKeyInProgressError"],
  [422, "idempotency_key_reused", "IdempotencyKeyReusedError"],
] as const)("narrow error code %s %s", async (status, code, name) => {
  for (const namespace of ["connectors", "integrations"]) {
    const c: any = client(() => Response.json({status: false, code}, {status}));
    if (enabled(namespaces[namespace]!)) await expect(c[namespace].get("one")).rejects.toMatchObject({name, code});
    else expect(namespace in c).toBe(false);
  }
});

test("numbered pages and opaque channel cursors", async () => {
  const seen: Request[] = [];
  const c = client((r) => {
    seen.push(r);
    const url = new URL(r.url);
    if (url.pathname.includes("slack/channels")) {
      const cursor = url.searchParams.get("cursor");
      return Response.json({ result: { channels: [{ id: cursor ? "two" : "one" }], next_cursor: cursor ? null : "opaque/next" } });
    }
    const page = url.searchParams.get("page_number");
    return Response.json({ result: { connections: [{ id: page }], metadata: { total_count: 2 } } });
  });
  if (enabled("data_integrations")) {
    const items: any[] = [];
    for await (const item of await (c as any).integrations.list({ pageSize: 50 })) items.push(item);
    expect(items.map((x) => x.id)).toEqual(["0", "1"]);
  } else expectAbsent(c, "integrations_connections_list");
  if (enabled("slack_channels")) {
    const channels: any[] = [];
    for await (const item of await (c as any).integrations.slackChannels("connection")) channels.push(item);
    expect(channels.map((x) => x.id)).toEqual(["one", "two"]);
  } else expectAbsent(c, "integrations_connections_slack_channels_list");
  expect(seen).toHaveLength(2 * (Number(enabled("data_integrations")) + Number(enabled("slack_channels"))));
});

test("every declared operation has a complete ON or OFF disposition", () => {
  expect(Object.entries(mapping).filter(([, row]: [string, any]) => row.feature).map(([name]) => name).sort())
    .toEqual(rows.map(([name]) => name).sort());
  for (const [feature, methods] of Object.entries(surface)) {
    for (const [name, method] of Object.entries(methods)) {
      const row = mapping[name];
      expect(row.feature).toBe(feature);
      if (enabled(feature)) {
        expect(row.methods.map((m: any) => m.ts)).toEqual(["client." + method.split(".").map(camel).join(".")]);
        expect(row.unwrapped).toBeUndefined();
      } else {
        expect(row.methods).toBeUndefined();
        expect(row.unwrapped).toBeTruthy();
        expect(row.languages).toEqual({py: "NOT-OFFERED", ts: "NOT-OFFERED"});
      }
    }
  }
});
