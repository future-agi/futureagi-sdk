/** The shared platform surface: withResponse, pages, handles and the one waiter. */
import { json, makeCore, Script } from "../__fixtures__/platform";
import { APITimeoutError } from "../errors";
import { ASYNC_DISPOSE, Handle, pollUntil } from "../handles";
import { listPage } from "../pagination";

describe("withResponse", () => {
  it("returns the data and the final response's metadata; plain awaits stay plain", async () => {
    const script = new Script([
      json(
        201,
        { id: "c1" },
        { "x-request-id": "req-3", "x-ratelimit-remaining": "9", "x-omega-idempotent-replayed": "true", "set-cookie": "s=secret" },
      ),
    ]);
    const raw = await makeCore(script).call("runs.create", { body: {} }).withResponse();
    expect(raw.data).toEqual({ id: "c1" });
    expect([raw.requestId, raw.idempotencyKey, raw.meta.idempotentReplay]).toEqual(["req-3", script.keys[0], true]);
    expect(raw.meta.rateLimit).toEqual({ "x-ratelimit-remaining": "9" });
    expect(raw.meta.headers["set-cookie"]).toBe("[redacted]");
    await expect(makeCore(new Script([json(200, { id: "c2" })])).call("runs.get", { path: { id: "c2" } })).resolves.toEqual({ id: "c2" });
  });

  it("map keeps the metadata", async () => {
    const raw = await makeCore(new Script([json(200, { id: "c1" }, { "x-request-id": "r" })]))
      .call<{ id: string }>("runs.get", { path: { id: "c1" } })
      .map((d) => d.id)
      .withResponse();
    expect([raw.data, raw.requestId]).toEqual(["c1", "r"]);
  });
});

describe("pages", () => {
  const pages: Record<string, unknown> = {
    first: { conversations: [1, 2], nextCursor: "c2" },
    c2: { conversations: [3], nextCursor: "c3" },
    c3: { conversations: [4], nextCursor: "c3" },
  };
  const script = () => new Script([(req) => json(200, pages[new URL(req.url).searchParams.get("cursor") ?? "first"])]);

  it("await gives the first page; for await walks every item and stops on a repeated cursor", async () => {
    const s = script();
    const core = makeCore(s);
    const page = await listPage<number>(core, "runs.list", { query: { agentId: "a" } });
    expect([page.items, page.hasMore, page.nextCursor]).toEqual([[1, 2], true, "c2"]);
    const all: number[] = [];
    for await (const item of listPage<number>(core, "runs.list", { query: { agentId: "a" } })) all.push(item);
    expect(all).toEqual([1, 2, 3, 4]);
    expect(s.requests.every((r) => new URL(r.url).searchParams.get("agentId") === "a")).toBe(true);
    expect((await page.nextPage())?.items).toEqual([3]);
  });

  it("a single-page list has the same interface", async () => {
    const core = makeCore(new Script([json(200, { sandboxes: [{ id: "s1" }] })]));
    const page = await listPage(core, "sandboxes.list", {}, { transform: (d) => (d as { id: string }).id });
    expect([page.items, page.hasMore, await page.nextPage()]).toEqual([["s1"], false, undefined]);
  });
});

class Thing extends Handle<{ id: string; status: string }> {
  protected readonly noun = "thing";
  disposed = false;
  constructor(
    data: { id: string; status: string },
    private readonly statuses: string[],
  ) {
    super(data);
  }
  protected async fetchData() {
    return { id: this.data.id, status: this.statuses.shift() ?? "ready" };
  }
  protected isDone(): boolean {
    return this.data.status === "ready" || this.data.status === "failed";
  }
  async dispose(): Promise<void> {
    this.disposed = true;
  }
}

describe("handles", () => {
  it("read fields, copy, refresh and wait with one waiter", async () => {
    const thing = new Thing({ id: "t1", status: "new" }, ["starting", "ready"]);
    expect([thing.id, thing.status]).toEqual(["t1", "new"]);
    const copy = thing.toJSON();
    copy.status = "x";
    expect(thing.status).toBe("new");
    const sleeps: number[] = [];
    await expect(thing.wait({ sleep: async (ms) => void sleeps.push(ms) })).resolves.toBe(thing);
    expect([thing.status, sleeps]).toEqual(["ready", [500]]);
    await thing[ASYNC_DISPOSE as unknown as "dispose"]();
    expect(thing.disposed).toBe(true);
  });

  it("a wait past its timeout throws APITimeoutError", async () => {
    let t = 0;
    const err = await pollUntil(async () => undefined, {
      timeoutMs: 12_000,
      sleep: async () => undefined,
      now: () => (t += 5_000),
      label: "waiting for thing t1",
    }).then(undefined, (e: unknown) => e);
    expect(err).toBeInstanceOf(APITimeoutError);
    expect((err as Error).message).toBe("waiting for thing t1 did not finish within 12 s");
  });
});
