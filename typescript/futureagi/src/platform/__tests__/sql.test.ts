import { Client } from "../client";
import { APIConnectionError } from "../errors";
import type { SQLCatalog, SQLExecution } from "../models";

// A fake fetch records requests. There is no SQL server or query execution.
test("SQL snapshots, REST defaults, bounded pages and cancellation keep their wire shape", async () => {
  const project_id = "project", id = "personal-job", sql = "mock-only 'input'\n";
  const body = { project_id, sql, start: "2026-01-01T00:00:00Z", end: "2026-01-02T00:00:00Z" };
  const base = { id, ...body, created_at: body.start, expires_at: body.end, finished_at: null, error: "", expired: false, result: {} };
  const replies = [
    { ...base, state: "queued", reused: false },
    { ...base, state: "waiting_for_capacity" },
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
  const state: string | null | undefined = run.state;
  expect(state).toBe("queued");
  expect((await client.sql.getResult(id, { project_id })).state).toBe("waiting_for_capacity");
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


test("SQL retries use the validated body and query overrides for the entire call", async () => {
  const extraBody = { reuse: false as boolean | null };
  const extraQuery = { limit: 1 as number | null, offset: 0 as number | null };
  const sent: unknown[] = [];
  const client = new Client({ apiKey: "example", secretKey: "example", maxRetries: 1, fetch: async (url, init) => {
    sent.push(init.method === "POST" ? JSON.parse(String(init.body)).reuse : Object.fromEntries(new URL(url).searchParams));
    if (sent.length % 2 === 1) {
      if (init.method === "POST") extraBody.reuse = null;
      else extraQuery.limit = extraQuery.offset = null;
      return new Response(null, { status: 429, headers: { "Retry-After": "0" } });
    }
    return new Response("{}", { status: 200 });
  } });
  const project_id = "project";
  await client.sql.run({ project_id, sql: "mock input", start: "start", end: "end" }, { extraBody });
  await client.sql.getResult("job", { project_id }, { extraQuery });
  const page = { project_id, limit: "1", offset: "0" };
  expect(sent).toEqual([false, false, page, page]);
});

test("SQL request timeout is bounded while a retried call keeps validated options", async () => {
  jest.useFakeTimers();
  try {
    const extraBody = { reuse: false as boolean | null };
    let calls = 0;
    const client = new Client({ apiKey: "example", secretKey: "example", maxRetries: 1, fetch: async (_url, init) => {
      calls++;
      if (calls === 1) {
        expect(JSON.parse(String(init.body)).reuse).toBe(false);
        extraBody.reuse = null;
        return new Response(null, { status: 429, headers: { "Retry-After": "0" } });
      }
      expect(JSON.parse(String(init.body)).reuse).toBe(false);
      await new Promise<never>((_resolve, reject) => {
        init.signal?.addEventListener("abort", () => reject(new Error("request aborted")), { once: true });
      });
      throw new Error("unreachable");
    } });
    const request = client.sql.run(
      { project_id: "project", sql: "mock input", start: "start", end: "end" },
      { extraBody, timeout: 25, maxRetries: 1 },
    );
    await Promise.resolve();
    await jest.advanceTimersByTimeAsync(0);
    expect(calls).toBe(2);
    await jest.advanceTimersByTimeAsync(24);
    expect(calls).toBe(2);
    await jest.advanceTimersByTimeAsync(1);
    await expect(request).rejects.toBeInstanceOf(APIConnectionError);
    expect(calls).toBe(2);
  } finally {
    jest.useRealTimers();
  }
});


test("SQL validates the same values it sends without losing request option getters", async () => {
  let reads = 0;
  class RunParams {
    project_id = "project"; sql = "mock input"; start = "start"; end = "end";
    get reuse(): boolean { ++reads; return true; }
  }
  class Options {
    #token = "scoped";
    get extraBody() { return { reuse: false }; }
    get headers() { return { "X-Test": this.#token }; }
  }
  const client = new Client({ apiKey: "example", secretKey: "example", fetch: async (_url, init) => {
    expect(new Headers(init.headers).get("x-test")).toBe("scoped");
    expect(JSON.parse(String(init.body)).reuse).toBe(false);
    return new Response("{}", { status: 202 });
  } });
  await client.sql.run(new RunParams(), Object.freeze(new Options()));
  expect(reads).toBe(1);
});
