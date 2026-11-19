/**
 * @agentcc/client 1.0.1's tests/benchmark-deep.test.ts (the recorded revision), ported against
 * agentcc-gateway the recorded revision over the mock upstream. Same test
 * names and request counts. 1.0.1 printed latencies and asserted only the counts;
 * this port asserts the counts, that every answer succeeded and, for the cache
 * cases, that the cache answered. Latencies go to the evidence directory only:
 * a shared build machine gives no latency claim.
 */
import { expect, it } from "@jest/globals";
import { authHeaders, chatPost, describeLive, live, marker, record, summarize, timeRequests, type Timed } from "./_live.js";

const results: Record<string, ReturnType<typeof summarize>> = {};
const keep = (label: string, t: Timed) => {
  results[label] = summarize(label, t);
  record("bench_deep", results);
  return t;
};
const ok = (t: Timed, n: number) => {
  expect(t.latencies).toHaveLength(n);
  expect(t.statuses.every((s) => s === 200)).toBe(true);
};
const healthz = () => fetch(`${live.base}/healthz`);
const models = () => fetch(`${live.base}/v1/models`, { headers: authHeaders() });

describeLive("Deep Benchmark: /healthz overhead", () => {
  it("100 sequential /healthz calls", async () => {
    ok(keep("healthz_seq_100", await timeRequests(100, 1, healthz)), 100);
  });
  it("200 concurrent /healthz calls (50 parallel)", async () => {
    ok(keep("healthz_par_200", await timeRequests(200, 50, healthz)), 200);
  });
});

describeLive("Deep Benchmark: /v1/models overhead", () => {
  it("100 sequential /v1/models calls", async () => {
    ok(keep("models_seq_100", await timeRequests(100, 1, models)), 100);
  });
});

describeLive("Deep Benchmark: Cache hit overhead (full pipeline)", () => {
  it("200 cached chat completions (sequential)", async () => {
    const prompt = `What is 2+2? ${marker()}`;
    for (let i = 0; i < 3; i++) await (await chatPost(prompt)).text();
    const t = keep("cache_seq_200", await timeRequests(200, 1, () => chatPost(prompt)));
    ok(t, 200);
    expect(t.cache.every((c) => (c ?? "").startsWith("hit"))).toBe(true);
  });
  it("500 cached chat completions (50 parallel)", async () => {
    const prompt = `What is 2+2? ${marker()}`;
    await (await chatPost(prompt)).text();
    const t = keep("cache_par_500", await timeRequests(500, 50, () => chatPost(prompt)));
    ok(t, 500);
    expect(t.cache.every((c) => (c ?? "").startsWith("hit"))).toBe(true);
  });
});

describeLive("Deep Benchmark: Fresh requests (provider round-trip)", () => {
  it("20 sequential fresh completions", async () => {
    const tag = marker();
    const t = keep("fresh_seq_20", await timeRequests(20, 1, (i) => chatPost(`Return exactly the number ${i + 1000} ${tag}`)));
    ok(t, 20);
    expect(t.cache.some((c) => (c ?? "").startsWith("hit"))).toBe(false);
  });
  it("50 concurrent fresh completions (10 parallel)", async () => {
    const tag = marker();
    const t = keep("fresh_par_50", await timeRequests(50, 10, (i) => chatPost(`Return exactly the number ${i + 2000} ${tag}`)));
    ok(t, 50);
    expect(t.cache.some((c) => (c ?? "").startsWith("hit"))).toBe(false);
  });
});

describeLive("Deep Benchmark: Auth overhead isolation", () => {
  it("compares /healthz (no auth) vs /v1/models (auth required)", async () => {
    ok(keep("auth_healthz_100", await timeRequests(100, 1, healthz)), 100);
    ok(keep("auth_models_100", await timeRequests(100, 1, models)), 100);
    const noKey = await fetch(`${live.base}/v1/models`);
    expect(noKey.status).toBe(401);
  });
});

describeLive("Deep Benchmark: Plugin pipeline overhead", () => {
  it("compares /v1/models vs cache hit (shows plugin pipeline cost)", async () => {
    const prompt = `pipeline ${marker()}`;
    await (await chatPost(prompt)).text();
    ok(keep("pipeline_models_100", await timeRequests(100, 1, models)), 100);
    const t = keep("pipeline_cache_100", await timeRequests(100, 1, () => chatPost(prompt)));
    ok(t, 100);
    expect(t.cache.every((c) => (c ?? "").startsWith("hit"))).toBe(true);
  });
});

describeLive("Deep Benchmark: Full summary table", () => {
  it("prints a comparison summary", async () => {
    const prompt = `summary ${marker()}`;
    await (await chatPost(prompt)).text();
    ok(keep("summary_healthz_50", await timeRequests(50, 1, healthz)), 50);
    ok(keep("summary_models_50", await timeRequests(50, 1, models)), 50);
    ok(keep("summary_cache_50", await timeRequests(50, 1, () => chatPost(prompt))), 50);
    expect(Object.keys(results).length).toBeGreaterThanOrEqual(3);
  });
});
