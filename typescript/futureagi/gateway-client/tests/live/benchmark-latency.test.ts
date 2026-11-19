/**
 * @agentcc/client 1.0.1's tests/benchmark-latency.test.ts (the recorded revision), ported against
 * agentcc-gateway the recorded revision over the mock upstream. Same names
 * and counts; the SDK client where 1.0.1 used it. Asserts counts and success;
 * latencies are evidence only (a shared build machine gives no latency claim).
 */
import { expect, it } from "@jest/globals";
import { AgentCC } from "../../src/index.js";
import { authHeaders, chatPost, describeLive, live, marker, MODEL, record, stats, summarize, timeRequests, type Timed, user } from "./_live.js";

const results: Record<string, unknown> = {};
const keep = (label: string, t: Timed) => {
  results[label] = summarize(label, t);
  record("bench_latency", results);
  return t;
};
const client = () => new AgentCC({ apiKey: live.key, baseUrl: live.base, maxRetries: 0 });

async function timedSdk(n: number, parallel: number, prompt: (i: number) => string) {
  const c = client();
  const latencies: number[] = [];
  const contents: (string | null)[] = [];
  for (let start = 0; start < n; start += parallel) {
    await Promise.all(
      Array.from({ length: Math.min(parallel, n - start) }, async (_, j) => {
        const s = performance.now();
        const r = await c.chat.completions.create({ model: MODEL, messages: user(prompt(start + j)), max_tokens: 5 });
        latencies.push(performance.now() - s);
        contents.push(r.choices[0].message.content);
      }),
    );
  }
  return { latencies, contents };
}

describeLive("Benchmark: Sequential Latency", () => {
  it("sends 20 sequential chat completions", async () => {
    const tag = marker();
    const r = await timedSdk(20, 1, (i) => `seq ${i} ${tag}`);
    results.sequential_20 = stats(r.latencies);
    record("bench_latency", results);
    expect(r.latencies).toHaveLength(20);
    expect(r.contents.every((c) => c === "PONG from mock")).toBe(true);
  });
});

describeLive("Benchmark: Concurrent Latency", () => {
  it("sends 30 concurrent chat completions (batches of 10)", async () => {
    const tag = marker();
    const r = await timedSdk(30, 10, (i) => `conc ${i} ${tag}`);
    results.concurrent_30 = stats(r.latencies);
    record("bench_latency", results);
    expect(r.latencies).toHaveLength(30);
    expect(r.contents.every((c) => c === "PONG from mock")).toBe(true);
  });
});

describeLive("Benchmark: Streaming Latency", () => {
  it("measures time-to-first-token and total streaming time (10 requests)", async () => {
    const c = client();
    const ttft: number[] = [];
    const total: number[] = [];
    const tag = marker();
    for (let i = 0; i < 10; i++) {
      const s = performance.now();
      let first: number | null = null;
      let text = "";
      const stream = await c.chat.completions.create({ model: MODEL, messages: user(`stream ${i} ${tag}`), stream: true });
      for await (const chunk of stream) {
        const piece = chunk.choices?.[0]?.delta?.content;
        if (piece && first === null) first = performance.now() - s;
        text += piece ?? "";
      }
      total.push(performance.now() - s);
      if (first !== null) ttft.push(first);
      expect(text).toBe("Hello world");
    }
    results.streaming_ttft = stats(ttft);
    results.streaming_total = stats(total);
    record("bench_latency", results);
    expect(total).toHaveLength(10);
    expect(ttft).toHaveLength(10);
  });
});

describeLive("Benchmark: Gateway Overhead (cached responses)", () => {
  it("measures overhead on cache hits (50 identical requests)", async () => {
    const prompt = `cached ${marker()}`;
    await (await chatPost(prompt)).text();
    const t = keep("cache_hits_50", await timeRequests(50, 1, () => chatPost(prompt)));
    expect(t.latencies).toHaveLength(50);
    expect(t.cache.every((c) => (c ?? "").startsWith("hit"))).toBe(true);
  });
});

describeLive("Benchmark: Models List Latency", () => {
  it("measures /v1/models latency (20 requests)", async () => {
    const t = keep("models_20", await timeRequests(20, 1, () => fetch(`${live.base}/v1/models`, { headers: authHeaders() })));
    expect(t.latencies).toHaveLength(20);
    expect(t.statuses.every((s) => s === 200)).toBe(true);
  });
});

describeLive("Benchmark: Burst Test", () => {
  it("fires 50 requests at once", async () => {
    const tag = marker();
    const t = keep("burst_50", await timeRequests(50, 50, (i) => chatPost(`burst ${i} ${tag}`)));
    expect(t.latencies).toHaveLength(50);
    expect(t.statuses.every((s) => s === 200)).toBe(true);
  });
});
