// client.simulation.environments.actors, against a fake fetch (no backend).

import { Client } from "../client";
import type { FetchLike } from "../transport";

const BASE = "https://backend.test";
const ENV = "11111111-1111-4111-8111-11111111111a";
const H = `/simulate/api/harness-environments/${ENV}/`;
const ACTORS = { status: true, result: { actors: [], limits: {}, revision: 3 } };

type Seen = { method: string; path: string; query: URLSearchParams; body: unknown; key?: string | null };

function recording(): { fetch: FetchLike; seen: Seen[] } {
  const seen: Seen[] = [];
  const fetch: FetchLike = async (url, init) => {
    const u = new URL(url);
    const raw = init?.body ? String(init.body) : "";
    const key = new Headers(init?.headers).get("idempotency-key");
    seen.push({ method: init?.method ?? "GET", path: u.pathname, query: u.searchParams, body: raw ? JSON.parse(raw) : undefined, key });
    return new Response(JSON.stringify(ACTORS), { status: 200, headers: { "content-type": "application/json" } });
  };
  return { fetch, seen };
}

const client = (fetch: FetchLike) => new Client({ apiKey: "k", secretKey: "s", baseUrl: BASE, fetch, customFetchReceivesKeys: true, maxRetries: 0 });

describe("simulation environment actors", () => {
  test("list, get and validate read; create and update write the draft", async () => {
    const { fetch, seen } = recording();
    const actors = client(fetch).simulation.environments.actors;

    await actors.list(ENV);
    await actors.get(ENV, "caller", { scenario_key: "refund-flow" });
    await actors.validate(ENV, { op: "delete", actor_id: "caller" });
    await actors.create(ENV, { actor: { name: "Dispatcher" }, id: "dispatcher" });
    await actors.update(ENV, "caller", { changes: { goal: "Book a ride" } });

    expect(seen.map((s) => [s.method, s.path])).toEqual([
      ["GET", H + "actors/"],
      ["GET", H + "actors/caller/"],
      ["POST", H + "actor-validation/"],
      ["POST", H + "actors/"],
      ["PUT", H + "actors/caller/"],
    ]);
    expect(seen[1].query.get("scenario_key")).toBe("refund-flow");
    expect(seen[2].body).toEqual({ op: "delete", actor_id: "caller" });
    expect(seen[3].body).toEqual({ actor: { name: "Dispatcher" }, id: "dispatcher" });
  });

  test("delete, setLimits and acceptUnresolved", async () => {
    const { fetch, seen } = recording();
    const actors = client(fetch).simulation.environments.actors;

    await actors.delete(ENV, "coworker", { expected_revision: 3 });
    await actors.setLimits(ENV, { limits: { max_active: 2, actor_seconds_per_call: null } });
    await actors.acceptUnresolved(ENV, { policy: "refunds over 500 need a manager" });

    expect(seen.map((s) => [s.method, s.path])).toEqual([
      ["DELETE", H + "actors/coworker/"],
      ["PUT", H + "actor-limits/"],
      ["POST", H + "actor-unresolved/accept/"],
    ]);
    expect(seen[0].query.get("expected_revision")).toBe("3");
    expect(seen[1].body).toEqual({ limits: { max_active: 2, actor_seconds_per_call: null } });
    expect(seen[2].body).toEqual({ policy: "refunds over 500 need a manager" });
  });

  test("an environment refusal carries its code", async () => {
    const fetch: FetchLike = async () =>
      new Response(JSON.stringify({ error: "unresolved_not_found", message: "gone", retryable: false }), {
        status: 404,
        headers: { "content-type": "application/json" },
      });

    await expect(client(fetch).simulation.environments.actors.acceptUnresolved(ENV, { policy: "gone" })).rejects.toMatchObject({
      status: 404,
      code: "unresolved_not_found",
    });
  });

  test("a run sends an idempotency key, the one given or a new one", async () => {
    const { fetch, seen } = recording();
    const environments = client(fetch).simulation.environments;

    await environments.run(ENV, { scenario_ids: ["refund-flow"], idempotencyKey: "run-1" });
    await environments.run(ENV, { scenario_ids: ["refund-flow"] });
    await environments.run(ENV, { scenario_ids: ["refund-flow"] });

    expect(seen[0].key).toBe("run-1");
    expect(seen[1].key).toBeTruthy();
    expect(seen[1].key).not.toBe(seen[2].key);
    expect(seen[0].body).toEqual({ scenario_ids: ["refund-flow"] });
  });

  test("an empty path value is refused before any request", async () => {
    const { fetch, seen } = recording();

    await expect(client(fetch).simulation.environments.actors.get(ENV, " ")).rejects.toThrow(/is empty/);
    expect(seen).toEqual([]);
  });

  test("a run sends its seed", async () => {
    const { fetch, seen } = recording();

    await client(fetch).simulation.environments.run(ENV, { scenario_ids: ["refund-flow"], trials: 1, seed: "7" });

    expect([seen[0].method, seen[0].path]).toEqual(["POST", H + "run/"]);
    expect(seen[0].body).toEqual({ scenario_ids: ["refund-flow"], trials: 1, seed: "7" });
  });
});
