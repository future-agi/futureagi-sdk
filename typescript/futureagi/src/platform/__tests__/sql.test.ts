import { Client } from "../client";
import type { SQLCatalog, SQLExecution } from "../models";

// A fake fetch records requests. There is no SQL server or query execution.
test("SQL snapshots, REST defaults, bounded pages and cancellation keep their wire shape", async () => {
  const project_id = "project", id = "personal-job", sql = "mock-only 'input'\n";
  const body = { project_id, sql, start: "2026-01-01T00:00:00Z", end: "2026-01-02T00:00:00Z" };
  const base = { id, ...body, created_at: body.start, expires_at: body.end, finished_at: null, error: "", expired: false, result: {} };
  const replies = [
    { ...base, state: "queued", reused: false },
    { ...base, state: "running" },
    { ...base, state: "succeeded", result: { rows: [[1, false, "cell", null]], next_offset: null, has_more: false } },
    { ...base, state: "cancelled" },
    { version: 1, identity_semantics: "project", datasets: [], examples: [], max_rows: 10000, max_window_days: 31, can_save: false },
  ];
  const calls: unknown[] = [];
  const client = new Client({ apiKey: "example", secretKey: "example", baseUrl: "http://mock.invalid", fetch: async (url, init) => {
    const target = new URL(url);
    calls.push([init.method, target.pathname, Object.fromEntries(target.searchParams), init.body ? JSON.parse(String(init.body)) : null]);
    return new Response(JSON.stringify(replies[calls.length - 1]), { status: calls.length === 1 ? 202 : 200 });
  } });
  const run: SQLExecution = await client.sql.run(body);
  const state: "queued" | "running" | "succeeded" | "failed" | "cancelled" | null | undefined = run.state;
  expect(state).toBe("queued");
  expect((await client.sql.getResult(id, { project_id })).state).toBe("running");
  const page = await client.sql.getResult(id, { project_id, limit: 1000, offset: 0 });
  expect(page.result?.rows).toEqual([[1, false, "cell", null]]);
  expect((await client.sql.cancel(id, { project_id })).state).toBe("cancelled");
  const catalog: SQLCatalog = await client.sql.getCatalog({ project_id });
  expect(catalog.max_window_days).toBe(31);
  const root = "/tracer/sql-query/";
  expect(calls).toEqual([
    ["POST", root + "run/", {}, body],
    ["GET", `${root}${id}/`, { project_id }, null],
    ["GET", `${root}${id}/`, { project_id, limit: "1000", offset: "0" }, null],
    ["POST", `${root}${id}/cancel/`, {}, { project_id }],
    ["GET", root + "catalog/", { project_id }, null],
  ]);
});

test("optional SQL fields allow omission, not null", async () => {
  const bodies: unknown[] = [];
  const client = new Client({ apiKey: "example", secretKey: "example", fetch: async (_url, init) => {
    bodies.push(JSON.parse(String(init.body)));
    return new Response("{}", { status: 202 });
  } });
  const body = { project_id: "project", sql: "mock input", start: "start", end: "end" };
  await client.sql.run(body);
  await client.sql.run({ ...body, reuse: false });
  // @ts-expect-error Optional boolean does not accept null.
  await expect(client.sql.run({ ...body, reuse: null })).rejects.toThrow("reuse cannot be null");
  // @ts-expect-error Optional limit does not accept null.
  await expect(client.sql.getResult("id", { project_id: "project", limit: null })).rejects.toThrow("limit cannot be null");
  // @ts-expect-error Optional offset does not accept null.
  await expect(client.sql.getResult("id", { project_id: "project", offset: null })).rejects.toThrow("offset cannot be null");
  await expect(client.sql.run(body, { extraBody: { reuse: null } })).rejects.toThrow("reuse cannot be null");
  await expect(client.sql.getResult("id", { project_id: "project" }, { extraQuery: { limit: null } })).rejects.toThrow("limit cannot be null");
  expect(bodies).toEqual([body, { ...body, reuse: false }]);
});
