/**
 * @agentcc/client 1.0.1's tests/benchmark-v3.test.ts (the recorded revision), ported against
 * agentcc-gateway the recorded revision. 1.0.1 compared two hand-started
 * gateways (a Docker build on 8090 and a "v3" build on 8092) and asserted the v3
 * mean was under twice the Docker mean. There is one gateway build here, the pin,
 * so each test measures it alone (200 iterations after 5 warm-ups, as 1.0.1) and
 * asserts success and, for cache cases, cache hits; the cross-build ratio is not
 * reproducible and is dropped (tests/live/manifest.json). Latencies are evidence only.
 */
import { expect, test } from "@jest/globals";
import { authHeaders, chatPost, describeLive, live, marker, record, summarize, timeRequests, type Timed } from "./_live.js";

const WARMUP = 5;
const ITERATIONS = 200;
const results: Record<string, unknown> = {};
const keep = (label: string, t: Timed) => {
  results[label] = summarize(label, t);
  record("bench_v3", results);
  return t;
};

async function bench(make: () => Promise<Response>): Promise<Timed> {
  for (let i = 0; i < WARMUP; i++) await (await make()).text();
  return timeRequests(ITERATIONS, 1, make);
}

describeLive("Gateway v3 Benchmark", () => {
  test("healthz endpoint", async () => {
    const t = keep("healthz", await bench(() => fetch(`${live.base}/healthz`)));
    expect(t.statuses.every((s) => s === 200)).toBe(true);
  });

  test("GET /v1/models (static route)", async () => {
    const t = keep("models", await bench(() => fetch(`${live.base}/v1/models`, { headers: authHeaders() })));
    expect(t.statuses.every((s) => s === 200)).toBe(true);
  });

  test("cache hit latency (POST /v1/chat/completions)", async () => {
    const prompt = `Say the word benchmark for cache test ${marker()}`;
    const t = keep("cache_hit", await bench(() => chatPost(prompt)));
    expect(t.statuses.every((s) => s === 200)).toBe(true);
    expect(t.cache.every((c) => (c ?? "").startsWith("hit"))).toBe(true);
  });

  test("burst throughput (50 concurrent cache hits)", async () => {
    const prompt = `Say the word burst for throughput test ${marker()}`;
    await (await chatPost(prompt)).text();
    const rounds: number[] = [];
    for (let r = 0; r < 5; r++) {
      const t = await timeRequests(50, 50, () => chatPost(prompt));
      expect(t.statuses.every((s) => s === 200)).toBe(true);
      expect(t.cache.every((c) => (c ?? "").startsWith("hit"))).toBe(true);
      rounds.push(t.wallMs);
    }
    const meanRound = rounds.reduce((a, b) => a + b, 0) / rounds.length;
    results.burst = { rounds_ms: rounds.map(Math.round), rps: Math.round((50 / meanRound) * 1000) };
    record("bench_v3", results);
    expect(meanRound).toBeGreaterThan(0);
  });

  test("summary table", async () => {
    expect(Object.keys(results).length).toBeGreaterThanOrEqual(1);
  });
});
