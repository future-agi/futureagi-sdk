// Scenario lifecycle, validation and run readiness on client.simulation, against a fake fetch (no backend).

import { Client } from "../client";
import type { FetchLike } from "../transport";

const BASE = "http://backend.test";
const ENV = "11111111-1111-4111-8111-11111111111a";
const H = `/simulate/api/harness-environments/${ENV}/`;

type Seen = { method: string; path: string; query: URLSearchParams; body: unknown };

function recording(result: unknown = {}, status = 200): { fetch: FetchLike; seen: Seen[] } {
  const seen: Seen[] = [];
  const fetch: FetchLike = async (url, init) => {
    const u = new URL(url);
    const raw = init?.body ? String(init.body) : "";
    seen.push({ method: init?.method ?? "GET", path: u.pathname, query: u.searchParams, body: raw ? JSON.parse(raw) : undefined });
    return new Response(JSON.stringify({ status: true, result }), { status, headers: { "content-type": "application/json" } });
  };
  return { fetch, seen };
}

const client = (fetch: FetchLike) => new Client({ apiKey: "k", secretKey: "s", baseUrl: BASE, fetch, maxRetries: 0 });

describe("scenario lifecycle", () => {
  test("validate, follow, archive, restore, revisions and records", async () => {
    const { fetch, seen } = recording({ state: "validating", job_id: "j1" }, 202);
    const scenarios = client(fetch).simulation.environments.scenarios;

    const started = await scenarios.validate(ENV, { keys: ["refund-flow"] });
    await scenarios.validationStatus(ENV, { job_id: started.job_id as string });
    await scenarios.runningValidation(ENV);
    await scenarios.archive(ENV, "refund-flow", { reason: "duplicate" });
    await scenarios.restore(ENV, "refund-flow");
    await scenarios.revisions(ENV, "refund-flow");
    await scenarios.records(ENV, "refund-flow", { table: "orders" });

    expect(seen.map((s) => [s.method, s.path])).toEqual([
      ["POST", H + "scenarios/validate/"],
      ["GET", H + "scenarios/validate/"],
      ["GET", H + "scenarios/validate/running/"],
      ["POST", H + "scenarios/refund-flow/archive/"],
      ["POST", H + "scenarios/refund-flow/restore/"],
      ["GET", H + "scenarios/refund-flow/revisions/"],
      ["GET", H + "scenarios/refund-flow/records/"],
    ]);
    expect(seen[0].body).toEqual({ keys: ["refund-flow"] });
    expect(seen[1].query.get("job_id")).toBe("j1");
    expect(seen[3].body).toEqual({ reason: "duplicate" });
    expect(seen[6].query.get("table")).toBe("orders");
  });

  test("the scenario list filters by lifecycle", async () => {
    const { fetch, seen } = recording({ results: [], lifecycle_counts: {} });

    await client(fetch).simulation.jobs.scenarios.list(ENV, { lifecycle: "archived" });

    expect(seen[0].path).toBe(`/simulate/api/harness-jobs/${ENV}/scenarios/`);
    expect(seen[0].query.get("lifecycle")).toBe("archived");
  });
});

describe("run readiness", () => {
  test("get, getForScenarios, cases, recheck, history and source changes", async () => {
    const { fetch, seen } = recording();
    const env = client(fetch).simulation.environments;

    await env.readiness.get(ENV, { suite_version_id: "s1", keys: ["a", "b"], trials: 3 });
    await env.readiness.getForScenarios(ENV, { scenario_ids: ["a", "b"], trials: 2 });
    await env.readiness.cases(ENV, { bucket: "blocked", cursor: 10 });
    await env.readiness.recheck(ENV, { agent_version_id: "av1" });
    await env.readiness.history(ENV, { cursor: 2 });
    await env.versions.sourceChanges(ENV, "v9");

    expect(seen.map((s) => [s.method, s.path])).toEqual([
      ["GET", H + "capabilities/"],
      ["POST", H + "capabilities/"],
      ["GET", H + "capabilities/cases/"],
      ["POST", H + "capabilities/recheck/"],
      ["GET", H + "capabilities/history/"],
      ["GET", H + "versions/environment/v9/source-changes/"],
    ]);
    expect(seen[0].query.getAll("keys")).toEqual(["a", "b"]);
    expect(seen[1].body).toEqual({ scenario_ids: ["a", "b"], trials: 2 });
    expect(seen[2].query.get("bucket")).toBe("blocked");
    expect(seen[3].body).toEqual({ agent_version_id: "av1" });
  });

  test("save the validated candidates and plan a selection", async () => {
    const { fetch, seen } = recording();
    const env = client(fetch).simulation.environments;

    await env.drafts.save(ENV, { idempotency_key: "save-1", candidates: { agent_version_id: "a1" }, expected_review_digest: "d1" });
    await env.runPlan(ENV, { scenario_keys: "refund-flow,book-ride" });

    expect(seen[0].body).toEqual({ idempotency_key: "save-1", candidates: { agent_version_id: "a1" }, expected_review_digest: "d1" });
    expect(seen[1].query.get("scenario_keys")).toBe("refund-flow,book-ride");
  });
});
