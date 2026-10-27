// The hand-written transport, against an injected `fetch` (no backend, no mocking framework).

import { mkdtemp, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";

import { Client } from "../client";
import { APIConnectionError, APIError, BadRequestError, InternalServerError, NotFoundError } from "../errors";
import { OP_DATASETS_CREATE } from "../_operations";
import type { FetchLike } from "../transport";

const BASE = "http://backend.test";

interface Seen {
  url: string;
  method: string;
  headers: Record<string, string>;
  body: RequestInit["body"];
  signal: AbortSignal | null | undefined;
}

function json(status: number, data: unknown, headers: Record<string, string> = {}): Response {
  return new Response(JSON.stringify(data), { status, headers: { "content-type": "application/json", ...headers } });
}

const dataset = () => json(200, { status: true, result: { message: "ok", dataset_id: "d1", dataset_name: "x" } });

/** A fetch that records every call and answers with the given responses in order (the last one repeats). */
function fake(...responses: Array<Response | Error | ((seen: Seen) => Response | Error)>): { fetch: FetchLike; calls: Seen[] } {
  const calls: Seen[] = [];
  const fetch: FetchLike = async (url, init) => {
    const seen: Seen = { url, method: init.method ?? "GET", headers: init.headers as Record<string, string>, body: init.body, signal: init.signal };
    calls.push(seen);
    const next = responses[Math.min(calls.length, responses.length) - 1];
    const answer = typeof next === "function" ? next(seen) : next;
    if (answer instanceof Error) {
      throw answer;
    }
    return answer.clone(); // the same Response may answer several calls
  };
  return { fetch, calls };
}

function client(fetch: FetchLike, extra: ConstructorParameters<typeof Client>[0] = {}): Client {
  return new Client({ apiKey: "k", secretKey: "s", baseUrl: BASE, fetch, maxRetries: 0, ...extra });
}

describe("requests", () => {
  test("sends auth headers, encodes path params and drops unset query fields", async () => {
    const { fetch, calls } = fake(json(200, { status: true, result: { table: [] } }));
    await client(fetch, { workspaceId: "w1" }).datasets.get("a/b c");
    expect(calls[0].url).toBe(`${BASE}/model-hub/develops/a%2Fb%20c/get-dataset-table/`);
    expect(calls[0].headers).toMatchObject({ "X-Api-Key": "k", "X-Secret-Key": "s", "X-Workspace-Id": "w1" });
    expect(calls[0].body).toBeUndefined();
  });

  test("json bodies drop unset fields, keep lists, and merge the escape hatches", async () => {
    const { fetch, calls } = fake(dataset());
    await client(fetch).datasets.create({ new_dataset_name: "x", model_type: undefined }, { extraBody: { tag: "t" }, extraQuery: { dry_run: true, ids: [1, 2] } });
    expect(JSON.parse(calls[0].body as string)).toEqual({ new_dataset_name: "x", tag: "t" });
    expect(calls[0].headers["Content-Type"]).toBe("application/json");
    expect(calls[0].url).toBe(`${BASE}/model-hub/develops/create-empty-dataset/?dry_run=true&ids=1&ids=2`);
  });

  test("the {status, result} envelope is removed, with or without the contract saying so", async () => {
    const { fetch } = fake(json(200, { status: true, result: { email: "me@x" } }));
    expect(await client(fetch).account.whoami()).toEqual({ email: "me@x" }); // contract: no envelope
    const bare = fake(json(200, { status: true, result: { ids: ["s1"] }, message: "created" }));
    expect(await client(bare.fetch).request("POST", "/x/")).toEqual({ ids: ["s1"] });
    expect(await client(bare.fetch).request("POST", "/x/", { unwrap: null })).toEqual({ status: true, result: { ids: ["s1"] }, message: "created" });
  });

  test("empty and non-JSON responses", async () => {
    expect(await client(fake(new Response(null, { status: 204 })).fetch).request("DELETE", "/x/")).toBeNull();
    const html = fake(new Response("<html>maintenance</html>", { status: 200, headers: { "content-type": "text/html" } }));
    await expect(client(html.fetch).datasets.create({ new_dataset_name: "x" })).rejects.toThrow(/non-JSON/);
  });

  test("raw requests reject relative paths and files on JSON operations", async () => {
    const c = client(fake(dataset()).fetch);
    expect(() => c.request("GET", "relative/")).toThrow(/start with/);
    await expect(c.transport.request(OP_DATASETS_CREATE, { body: {}, files: { file: new Uint8Array([1]) } })).rejects.toThrow(/multipart/);
  });
});

describe("errors", () => {
  test("are typed by status and carry the backend envelope", async () => {
    const { fetch } = fake(json(404, { status: false, type: "not_found", code: "E404", detail: "nope" }, { "x-request-id": "r1" }));
    const error = await client(fetch).datasets.get("missing").catch((e) => e);
    expect(error).toBeInstanceOf(NotFoundError);
    expect(error).toBeInstanceOf(APIError);
    expect(error).toMatchObject({ status: 404, message: "404 nope", type: "not_found", code: "E404", detail: "nope", requestId: "r1" });
  });

  test("field errors appear in the message", async () => {
    const { fetch } = fake(json(400, { status: false, detail: { new_dataset_name: ["This field may not be blank."] } }));
    const error = await client(fetch).datasets.create({ new_dataset_name: "" }).catch((e) => e);
    expect(error).toBeInstanceOf(BadRequestError);
    expect(error.message).toContain("new_dataset_name");
    expect(error.detail).toEqual({ new_dataset_name: ["This field may not be blank."] });
  });

  test("an unfollowed redirect is an error, not an empty result", async () => {
    const { fetch } = fake(new Response(null, { status: 301, headers: { location: "https://api.futureagi.com/" } }));
    const error = await client(fetch).datasets.list().firstPage().catch((e) => e);
    expect(error).toBeInstanceOf(APIError);
    expect(error.status).toBe(301);
  });
});

describe("retries", () => {
  test("a write is not retried on 5xx but a read is", async () => {
    const write = fake(json(503, { detail: "busy" }), dataset());
    await expect(client(write.fetch, { maxRetries: 2 }).datasets.create({ new_dataset_name: "x" })).rejects.toBeInstanceOf(InternalServerError);
    expect(write.calls).toHaveLength(1);
    const read = fake(json(503, { detail: "busy" }, { "retry-after": "0" }), json(200, { status: true, result: { datasets: [], total_pages: 1 } }));
    await client(read.fetch, { maxRetries: 2 }).datasets.list().firstPage();
    expect(read.calls).toHaveLength(2);
  });

  test("429 is retried for any method, honouring retry-after", async () => {
    const { fetch, calls } = fake(json(429, {}, { "retry-after": "0" }), dataset());
    expect((await client(fetch, { maxRetries: 1 }).datasets.create({ new_dataset_name: "x" })).dataset_id).toBe("d1");
    expect(calls).toHaveLength(2);
  });

  test("a connection error is not retried for a write and becomes APIConnectionError", async () => {
    const { fetch, calls } = fake(new TypeError("fetch failed"));
    await expect(client(fetch, { maxRetries: 2 }).datasets.create({ new_dataset_name: "x" })).rejects.toBeInstanceOf(APIConnectionError);
    expect(calls).toHaveLength(1);
  });

  test("requests carry a timeout signal", async () => {
    const { fetch, calls } = fake(dataset());
    await client(fetch, { timeout: 1234 }).datasets.create({ new_dataset_name: "x" });
    expect(calls[0].signal).toBeInstanceOf(AbortSignal);
  });
});

describe("per-call options", () => {
  test("override headers, timeout and retries for one call only", async () => {
    const { fetch, calls } = fake(json(503, {}, { "retry-after": "0" }), json(200, { status: true, result: { datasets: [], total_pages: 1 } }), dataset());
    const c = client(fetch, { defaultHeaders: { "X-Team": "sdk", "User-Agent": "mine" } });
    await c.datasets.list({}, { headers: { "X-Trace": "t1", "X-Team": "override" }, maxRetries: 1 }).firstPage();
    expect(calls).toHaveLength(2); // the per-call maxRetries allowed one retry of the GET
    expect(calls[1].headers).toMatchObject({ "X-Trace": "t1", "X-Team": "override", "User-Agent": "mine", "X-Api-Key": "k" });
    await c.datasets.create({ new_dataset_name: "x" });
    expect(calls[2].headers).toMatchObject({ "X-Team": "sdk" });
    expect(calls[2].headers["X-Trace"]).toBeUndefined();
  });
});

describe("pagination", () => {
  const page = (items: unknown[], extra: Record<string, unknown>) => json(200, { status: true, result: { datasets: items, ...extra } });

  test("walks total_pages pages starting at the catalog's first page", async () => {
    const { fetch, calls } = fake(page([{ name: "a" }], { total_pages: 2 }), page([{ name: "b" }], { total_pages: 2 }));
    const names: string[] = [];
    for await (const ds of client(fetch).datasets.list({ page_size: 1 })) {
      names.push(ds.name as string);
    }
    expect(names).toEqual(["a", "b"]);
    expect(calls.map((c) => new URL(c.url).searchParams.get("page"))).toEqual(["0", "1"]);
    expect(new URL(calls[0].url).searchParams.get("page_size")).toBe("1");
  });

  test("stops on an empty `next`, respects toArray limits, and firstPage fetches once", async () => {
    const results = (items: unknown[], next: string | null) => json(200, { results: items, next });
    const pages = () => fake(results([{ id: 1 }, { id: 2 }], "more"), results([{ id: 3 }], null));
    const all = pages();
    expect(await client(all.fetch).prompts.list().toArray()).toEqual([{ id: 1 }, { id: 2 }, { id: 3 }]);
    expect(all.calls).toHaveLength(2);
    const limited = pages();
    expect(await client(limited.fetch).prompts.list().toArray(1)).toEqual([{ id: 1 }]);
    expect(limited.calls).toHaveLength(1);
    const once = pages();
    const first = await client(once.fetch).prompts.list().firstPage();
    expect(first.number).toBe(1);
    expect(first.items).toHaveLength(2);
    expect(once.calls).toHaveLength(1);
  });

  test("a page without its items list is an error, never an empty result", async () => {
    const { fetch } = fake(json(200, { status: true, result: { nope: [] } }));
    await expect(client(fetch).datasets.list().firstPage()).rejects.toThrow(/page has no 'datasets' list/);
  });
});

describe("multipart", () => {
  test("sends form fields and files from bytes, named data and paths", async () => {
    const dir = await mkdtemp(join(tmpdir(), "fi-sdk-"));
    const path = join(dir, "notes.txt");
    await writeFile(path, "from a path");
    const { fetch, calls } = fake(json(200, { status: true, result: { kb_id: "kb1", kb_name: "x", file_ids: ["f1", "f2", "f3"] } }));
    const result = await client(fetch).knowledgeBases.create({ name: "x", file: [path, { name: "inline.txt", data: "from a string" }, new Uint8Array([104, 105])] }, { extraBody: { public: false } });
    expect(result.kb_id).toBe("kb1");
    const form = calls[0].body as FormData;
    expect(form).toBeInstanceOf(FormData);
    expect(calls[0].headers["Content-Type"]).toBeUndefined(); // fetch adds the boundary itself
    expect(form.get("name")).toBe("x");
    expect(form.get("public")).toBe("false");
    const files = form.getAll("file") as File[];
    expect(files.map((f) => f.name)).toEqual(["notes.txt", "inline.txt", "upload"]);
    expect(await Promise.all(files.map((f) => f.text()))).toEqual(["from a path", "from a string", "hi"]);
  });
});
