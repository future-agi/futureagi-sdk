import { FutureAGIClient } from "../../futureagi-client";
import { BadRequestError, NotFoundError, UnexpectedRedirectError } from "../errors";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";

const rows: Array<Record<string, any>> = JSON.parse(readFileSync(resolve(__dirname, "../../../../../openapi/catalog/operations.json"), "utf8")).operations;
const camel = (text: string) => text.replace(/_([a-z])/g, (_, char: string) => char.toUpperCase());
const make = (handler: (request: Request) => Response, selectors: { workspaceId?: string; organizationId?: string } = {
  workspaceId: "workspace-fixture", organizationId: "organization-fixture",
}) => new FutureAGIClient({
  apiKey: "fixture-api", secretKey: "fixture-secret", baseUrl: "http://localhost:9012", retries: 0, ...selectors,
  fetch: (async (input: RequestInfo | URL, init?: RequestInit) => handler(input instanceof Request ? input : new Request(input, init))) as typeof fetch,
});
const rows5 = (page: number, total = 5, size = 2) => Response.json({ result: {
  table: Array.from({ length: total }, (_, i) => ({ id: i + 1 })).slice((page - 1) * size, page * size),
  metadata: { total_rows: total },
} });

describe("admitted catalog contract smoke", () => {
  test.each(rows)("$public uses the root transport", async (row: any) => {
    const seen: Request[] = [];
    const client = make(request => {
      seen.push(request);
      expect(request.headers.get("x-api-key")).toBe("fixture-api");
      expect(request.headers.get("x-secret-key")).toBe("fixture-secret");
      expect(request.headers.get("x-workspace-id")).toBe("workspace-fixture");
      expect(request.headers.get("x-organization-id")).toBe("organization-fixture");
      const body = row.pagination ? { table: [], results: [], metadata: { total_rows: 0 } } : { id: "answer" };
      return Response.json(row.unwrap ? { result: body } : body);
    });
    const parts = row.public.split(".").map(camel);
    const method = parts.pop();
    let resource: any = client;
    for (const part of parts) resource = resource[part];
    const args = row.path_params.map(() => "sample");
    if (["POST", "PUT", "PATCH"].includes(row.method)) args.push({ name: "smoke" });
    const result = await resource[method](...args);
    expect(seen).toHaveLength(1);
    expect(seen[0].method).toBe(row.method);
    expect(new URL(seen[0].url).pathname).toBe(row.path.replace(/\{[^}]+\}/g, "sample"));
    if (["POST", "PUT", "PATCH"].includes(row.method)) expect(await seen[0].json()).toEqual({ name: "smoke" });
    if (!row.pagination) expect(result).toEqual({ id: "answer" });
  });

  test.each(["widgets", "optimizations"])("%s walks pages without following foreign origins", async kind => {
    const seen: string[] = [];
    const client = make(request => {
      seen.push(request.url);
      const url = new URL(request.url);
      expect(url.hostname).toBe("localhost");
      const page = Number(url.searchParams.get("page"));
      return Response.json(kind === "widgets" ? {
        results: [{ id: page }], next: page === 1 ? "https://untrusted.invalid/steal?page=2" : null,
      } : { status: "success", result: { table: [{ id: page }], metadata: { total_rows: 2 } } });
    });
    const page = kind === "widgets" ? await client.tracing.dashboards.widgets.list("dashboard", { limit: 1 }) :
      await client.optimizations.list({ limit: 1 });
    const items = [];
    for await (const item of page) items.push(item);
    expect(items).toEqual([{ id: 1 }, { id: 2 }]);
    expect(seen).toHaveLength(2);
  });

  test("shares the typed error tree and redirect guard", async () => {
    await expect(make(() => Response.json({ detail: "missing" }, { status: 404 })).workspaces.list()).rejects.toBeInstanceOf(NotFoundError);
    await expect(make(() => new Response(null, { status: 302, headers: { location: "https://untrusted.invalid" } })).workspaces.list()).rejects.toBeInstanceOf(UnexpectedRedirectError);
  });

  test("malformed pages fail instead of returning an empty result", async () => {
    await expect(make(() => Response.json({ result: { unexpected: [] } })).optimizations.list()).rejects.toMatchObject({ code: "invalid_page" });
  });

  test("list supports direct async iteration and server-capped page sizes", async () => {
    const calls: number[] = [];
    const client = make(request => {
      const page = Number(new URL(request.url).searchParams.get("page"));
      calls.push(page);
      const table = page === 1 ? [{ id: 1 }, { id: 2 }] : page === 2 ? [{ id: 3 }, { id: 4 }] : [{ id: 5 }];
      return Response.json({ result: { table, metadata: { total_rows: 5 } } });
    });
    const result = [];
    for await (const item of client.optimizations.list({ limit: 1000 })) result.push(item.id);
    expect(result).toEqual([1, 2, 3, 4, 5]);
    expect(calls).toEqual([1, 2, 3]);
  });

  test.each([[2, 6], [2, 5], [3, 6]])("resumes capped pagination at page %i of %i records", async (start, total) => {
    const calls: number[][] = [];
    const client = make(request => {
      const query = new URL(request.url).searchParams;
      const page = Number(query.get("page"));
      const size = Math.min(Number(query.get("limit")), 2);
      calls.push([page, size]);
      expect(page).toBeLessThanOrEqual(3);
      const table = Array.from({ length: total }, (_, i) => ({ id: i + 1 })).slice((page - 1) * size, page * size);
      return Response.json({ result: { table, metadata: { total_rows: total } } });
    });
    const page = await client.optimizations.list({ page: start, limit: 1000 });
    expect(page.hasMore).toBe(start < 3);
    const result = [];
    for await (const item of page) result.push(item.id);
    expect(result).toEqual(Array.from({ length: total - (start - 1) * 2 }, (_, i) => (start - 1) * 2 + i + 1));
    expect(calls).toEqual(Array.from({ length: 4 - start }, (_, i) => [start + i, 2]));
  });

  test("resuming on a short final page never changes row offsets", async () => {
    const seen: number[] = [];
    const client = make(request => {
      const query = new URL(request.url).searchParams;
      expect(query.get("limit")).toBe("1000");
      const page = Number(query.get("page"));
      seen.push(page);
      expect(page).toBeLessThanOrEqual(4);
      return Response.json({ result: { table: page === 3 ? [{ id: 5 }] : [], metadata: { total_rows: 5 } } });
    });
    const items = [];
    for await (const item of client.optimizations.list({ page: 3, limit: 1000 })) items.push(item);
    expect(items).toEqual([{ id: 5 }]);
    expect(seen).toEqual([3, 4]);
  });

  test("a short last page ends the walk and keeps the raw body", async () => {
    const seen: number[] = [];
    const client = make(request => {
      const page = Number(new URL(request.url).searchParams.get("page"));
      seen.push(page);
      expect(page).toBeLessThanOrEqual(2);
      return Response.json({ result: { table: page === 1 ? [{ id: 1 }, { id: 2 }] : [{ id: 3 }], metadata: { total_rows: 3 } } });
    });
    const page = await client.optimizations.list();
    expect(page.raw).toMatchObject({ metadata: { total_rows: 3 } });
    const items = [];
    for await (const item of page) items.push(item);
    expect(items).toEqual([{ id: 1 }, { id: 2 }, { id: 3 }]);
    expect(seen).toEqual([1, 2]);
  });

  test("withOptions retains namespaces and selected transport", async () => {
    const client = make(() => Response.json({ email: "test@example.invalid" })).withOptions({ timeoutMs: 1234 });
    expect(await client.workspaces.list()).toEqual({ email: "test@example.invalid" });
  });

  test.each([["FI_WORKSPACE_ID", "x-workspace-id"], ["FI_ORGANIZATION_ID", "x-organization-id"]])(
    "an empty %s sends no selector", async (name, header) => {
      const saved = process.env[name];
      process.env[name] = "";
      try {
        const seen: Request[] = [];
        await make(request => { seen.push(request); return Response.json({ id: "answer" }); }, {}).workspaces.list();
        expect(seen[0].headers.has(header)).toBe(false);
      } finally {
        if (saved === undefined) delete process.env[name]; else process.env[name] = saved;
      }
    });

  test.each([400, 404])("an out-of-range probe (%i) after a short resumed page ends the walk", async status => {
    // FA's dataset optimization list answers a page past the end with 400; a plain paginated view with 404.
    const seen: number[] = [];
    const client = make(request => {
      const page = Number(new URL(request.url).searchParams.get("page"));
      seen.push(page);
      return page === 4 ? Response.json({ detail: "Invalid page." }, { status }) : rows5(page);
    });
    const items = [];
    for await (const item of client.optimizations.list({ page: 3, limit: 2 })) items.push(item);
    expect(items).toEqual([{ id: 5 }]);
    expect(seen).toEqual([3, 4]);
  });

  test.each([[400, BadRequestError], [404, NotFoundError]] as const)("a %i on a counted page still raises", async (status, error) => {
    const client = make(request => {
      const page = Number(new URL(request.url).searchParams.get("page"));
      return page === 1 ? rows5(page) : Response.json({ detail: "no" }, { status });
    });
    const walk = async () => {
      const items = [];
      for await (const item of client.optimizations.list({ limit: 2 })) items.push(item);
      return items;
    };
    await expect(walk()).rejects.toBeInstanceOf(error);
  });
});
