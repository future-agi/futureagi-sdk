import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { FutureAGIClient } from "../../futureagi-client";
import { ConfigurationError, FutureAGIAPIError, UnexpectedRedirectError } from "../../_core/errors";

const rows: Array<Record<string, any>> = JSON.parse(readFileSync(resolve(__dirname, "../../../../../openapi/tracing/wrapper-map.json"), "utf8")).operations;
const make = (handler: (request: Request) => Response) => new FutureAGIClient({
  apiKey: "fixture-api", secretKey: "fixture-secret", baseUrl: "http://localhost:9012", retries: 0,
  workspaceId: "workspace", organizationId: "organization",
  fetch: (async (input: RequestInfo | URL, init?: RequestInit) => handler(input instanceof Request ? input : new Request(input, init))) as typeof fetch,
});

test.each(rows)("$py follows the pinned operation", async row => {
  const seen: Request[] = [];
  const payload = { status: true, result: { id: "child", parent_span_id: "parent" }, query_complete: false };
  const client = make(request => {
    seen.push(request);
    expect(request.headers.get("x-api-key")).toBe("fixture-api");
    expect(request.headers.get("x-secret-key")).toBe("fixture-secret");
    expect(request.headers.get("x-workspace-id")).toBe("workspace");
    expect(request.headers.get("x-organization-id")).toBe("organization");
    expect(request.headers.has("idempotency-key")).toBe(false);
    expect(new URL(request.url).hostname).toBe("localhost");
    return Response.json(payload);
  });
  const args: any[] = Object.keys(row.args).map(() => "identifier");
  const body = ["POST", "PUT", "PATCH"].includes(row.method);
  if (body) args.push({ tags: ["tag"], optional: null });
  expect(await (client.tracing as any)[row.ts](...args)).toEqual(payload);
  expect(seen).toHaveLength(1);
  expect(seen[0].method).toBe(row.method);
  expect(new URL(seen[0].url).pathname).toBe(row.path.replace(/\{[^}]+\}/g, "identifier"));
  if (body) expect(await seen[0].json()).toEqual(args[args.length - 1]);
});

test("trace filter is additive, preserves identity and returns only the requested page", async () => {
  const seen: Request[] = [];
  const payload = { status: true, result: { table: [{ span_id: "child", trace_id: "trace", parent_span_id: "parent" }], metadata: { has_more: true, next_cursor: "next", query_complete: false } } };
  const client = make(request => { seen.push(request); return Response.json(payload); });
  const filters = [{ column_id: "created_at", filter_config: { filter_type: "datetime", filter_op: "between", filter_value: ["2026-01-01", "2026-01-02"] } }];
  const before = JSON.stringify(filters);
  expect(await client.tracing.spansByTrace("trace", { project_id: "project", filters, cursor: "resume", cursor_mode: true })).toEqual(payload);
  expect(JSON.stringify(filters)).toBe(before);
  expect(seen).toHaveLength(1);
  const query = new URL(seen[0].url).searchParams;
  expect(query.get("project_id")).toBe("project");
  expect(query.get("cursor")).toBe("resume");
  expect(query.get("cursor_mode")).toBe("true");
  expect(JSON.parse(query.get("filters")!)).toEqual([...filters, { column_id: "trace_id", filter_config: {
    col_type: "SYSTEM_METRIC", filter_type: "text", filter_op: "in", filter_value: ["trace"],
  } }]);
});

test.each([400, 401, 403, 404, 429, 500, 503])("status %i raises a typed error", async status => {
  const client = make(() => Response.json({ detail: "denied" }, { status }));
  await expect(client.tracing.spans({ project_id: "foreign-project" })).rejects.toBeInstanceOf(FutureAGIAPIError);
});

test("invalid selectors cannot dispatch", () => {
  const client = make(() => { throw new Error("must not send"); });
  expect(() => client.tracing.spansByTrace("", { project_id: "project" })).toThrow(ConfigurationError);
  expect(() => client.tracing.spansByTrace("trace", { project_id: "" })).toThrow(ConfigurationError);
  expect(() => client.tracing.spansByTrace("trace", { project_id: "project", filters: [null] } as any)).toThrow(ConfigurationError);
});

test("redirects, traversal and undeclared parameters fail closed", async () => {
  const seen: Request[] = [];
  const client = make(request => { seen.push(request); return new Response(null, { status: 302, headers: { location: "https://untrusted.invalid" } }); });
  await expect(client.tracing.getSpan("span")).rejects.toBeInstanceOf(UnexpectedRedirectError);
  await expect(client.tracing.getSpan("..")).rejects.toBeInstanceOf(ConfigurationError);
  await expect(client.tracing.spans({ undeclared: true })).rejects.toBeInstanceOf(ConfigurationError);
  expect(seen).toHaveLength(1);
});

test("copies retain Observe methods, query selectors and escaped identifiers", async () => {
  const seen: Request[] = [];
  const client = make(request => { seen.push(request); return Response.json({ ok: true }); }).withOptions({ timeoutMs: 2000 });
  await client.tracing.projects({ name: "my project", page_size: 10 });
  expect(new URL(seen[0].url).searchParams.get("name")).toBe("my project");
  await client.tracing.issue("cluster/one", { project_id: "project" });
  expect(seen[1].url).toContain("cluster%2Fone");
  expect(new URL(seen[1].url).searchParams.get("project_id")).toBe("project");
  expect(await client.tracing.dashboards.list()).toEqual({ ok: true });
});
