// client.simulation.calls.workers, against a fake fetch (no backend).

import { Client } from "../client";
import type { FetchLike } from "../transport";

const BASE = "http://backend.test";
const CALL = "22222222-2222-4222-8222-22222222222b";
const PATH = `/simulate/v3/call-executions/${CALL}/workers/`;

function answering(status: number, body?: unknown): { fetch: FetchLike; seen: URL[] } {
  const seen: URL[] = [];
  const fetch: FetchLike = async (url) => {
    seen.push(new URL(url));
    return body === undefined
      ? new Response(null, { status })
      : new Response(JSON.stringify(body), { status, headers: { "content-type": "application/json" } });
  };
  return { fetch, seen };
}

const client = (fetch: FetchLike) => new Client({ apiKey: "k", secretKey: "s", baseUrl: BASE, fetch, maxRetries: 0 });

describe("simulation call workers", () => {
  test("reads one trial's workers, optionally an earlier attempt", async () => {
    const workers = { workers: [{ name: "dispatcher" }, { name: "billing" }], state: "complete" };
    const { fetch, seen } = answering(200, { status: true, result: workers });

    const result = await client(fetch).simulation.calls.workers(CALL, { attempt: "a1" });

    expect(seen[0].pathname).toBe(PATH);
    expect(seen[0].searchParams.get("attempt")).toBe("a1");
    expect(result.workers?.map((w) => w?.name)).toEqual(["dispatcher", "billing"]);
  });

  test("traces still being collected answer pending", async () => {
    const pending = { pending: true, next_read_at: "2026-11-26T10:00:00Z", participants_declared: true };
    const { fetch } = answering(202, { status: true, result: pending });

    const result = await client(fetch).simulation.calls.workers(CALL);

    expect(result.pending).toBe(true);
    expect(result.next_read_at).toBe("2026-11-26T10:00:00Z");
  });

  test("a trial without a hand-off answers nothing", async () => {
    const { fetch } = answering(204);

    expect(await client(fetch).simulation.calls.workers(CALL)).toBeFalsy();
  });
});
