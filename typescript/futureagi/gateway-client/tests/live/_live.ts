/**
 * Helpers of the live wire suite: the running stack as the
 * tests see it. The stack (agentcc-gateway built at the recorded revision, the mock
 * upstream, the wire tap, minted virtual keys) is started by
 * python/tests/gateway/live/stack/run-wire-suite.sh on a build machine, which sets:
 *
 * - FI_GATEWAY_LIVE_BASE_URL  the gateway origin (every suite is skipped without it)
 * - FI_GATEWAY_LIVE_TAP_URL   the recording proxy in front of the gateway
 * - FI_GATEWAY_LIVE_MOCK_URL  the mock upstream
 * - FI_GATEWAY_LIVE_KEYS      a JSON file with this run's keys
 * - FI_GATEWAY_LIVE_EVIDENCE  where observations are written (JSON; tokens hashed)
 * - FI_GATEWAY_LIVE_BLOCK_WORD the word the gateway's keyword guardrail blocks
 */
import { describe } from "@jest/globals";
import { createHash, randomUUID } from "node:crypto";
import { mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { join } from "node:path";

export const LIVE = (process.env.FI_GATEWAY_LIVE_BASE_URL ?? "").replace(/\/+$/, "");
export const describeLive = LIVE ? describe : describe.skip;
export const MODEL = "gpt-4o-mini";

const env = (name: string): string => (process.env[name] ?? "").replace(/\/+$/, "");

export const live = {
  get base(): string {
    return LIVE;
  },
  get tap(): string {
    return env("FI_GATEWAY_LIVE_TAP_URL");
  },
  get mock(): string {
    return env("FI_GATEWAY_LIVE_MOCK_URL");
  },
  get blockWord(): string {
    return process.env.FI_GATEWAY_LIVE_BLOCK_WORD ?? "";
  },
  keys(): { plain: { key: string }; override: { key: string }; fallback: { key: string } } {
    return JSON.parse(readFileSync(process.env.FI_GATEWAY_LIVE_KEYS as string, "utf8"));
  },
  get key(): string {
    return this.keys().plain.key;
  },
  get overrideKey(): string {
    return this.keys().override.key;
  },
  /** org-fallback's key: its org config turns failover and the mock-fails chain on. */
  get fallbackKey(): string {
    return this.keys().fallback.key;
  },
};

export interface WireRecord {
  seq: number;
  method: string;
  path: string;
  headers: Record<string, string>;
  header_names?: string[];
  body: unknown;
}

/** A unique tag a test puts in its prompt, to find its requests in the records. */
export const marker = (): string => `[[id:${randomUUID().replace(/-/g, "").slice(0, 12)}]]`;

export const sha12 = (value: string): string => createHash("sha256").update(value).digest("hex").slice(0, 12);

async function records(base: string, route: string, tag?: string): Promise<WireRecord[]> {
  const rows = (await (await fetch(`${base}${route}`)).json()) as WireRecord[];
  return tag ? rows.filter((r) => JSON.stringify(r.body ?? null).includes(tag)) : rows;
}

/** What the gateway forwarded to the upstream. */
export const mockRecords = (tag?: string): Promise<WireRecord[]> => records(live.mock, "/__mock/requests", tag);

/** What a client sent through the wire tap. */
export const tapRecords = (tag?: string): Promise<WireRecord[]> => records(live.tap, "/__tap/requests", tag);

/** Write an observation to the evidence directory (never a raw key). */
export function record(name: string, data: unknown): void {
  const dir = join(process.env.FI_GATEWAY_LIVE_EVIDENCE ?? "/tmp/gw-live-evidence", "ts");
  mkdirSync(dir, { recursive: true });
  writeFileSync(join(dir, `${name}.json`), JSON.stringify(data, null, 1));
}

export const user = (content: string) => [{ role: "user" as const, content }];

/** POST a stream request with fetch: status, headers and the raw SSE body. */
export async function rawStream(path: string, body: unknown, headers: Record<string, string> = {}) {
  const resp = await fetch(`${live.base}${path}`, {
    method: "POST",
    headers: { "content-type": "application/json", authorization: `Bearer ${live.key}`, ...headers },
    body: JSON.stringify(body),
  });
  const text = await resp.text();
  return {
    status: resp.status,
    headers: Object.fromEntries(resp.headers.entries()),
    frames: text.split("\n").filter((l) => l.startsWith("data: ")).map((l) => l.slice(6)),
    text,
  };
}

/** Latency statistics, recorded as evidence only: no latency is asserted on a shared build machine. */
export function stats(latencies: number[]) {
  const s = [...latencies].sort((a, b) => a - b);
  const pick = (p: number) => s[Math.max(0, Math.ceil((p / 100) * s.length) - 1)];
  const mean = s.reduce((a, b) => a + b, 0) / (s.length || 1);
  return { count: s.length, min: s[0], max: s[s.length - 1], mean: Math.round(mean * 100) / 100, median: pick(50), p90: pick(90), p95: pick(95), p99: pick(99) };
}

export interface Timed {
  latencies: number[];
  statuses: number[];
  cache: (string | null)[];
  wallMs: number;
}

/**
 * Run `n` requests made by `make(i)`, `parallel` at a time; returns every
 * latency, status and x-agentcc-cache value. The benchmark ports assert counts and
 * statuses only, and record the latencies without asserting on them: timings from a
 * shared test machine say nothing about the gateway's own speed.
 */
export async function timeRequests(n: number, parallel: number, make: (i: number) => Promise<Response>): Promise<Timed> {
  const out: Timed = { latencies: [], statuses: [], cache: [], wallMs: 0 };
  const t0 = performance.now();
  for (let start = 0; start < n; start += parallel) {
    await Promise.all(
      Array.from({ length: Math.min(parallel, n - start) }, async (_, j) => {
        const s = performance.now();
        const resp = await make(start + j);
        await resp.text();
        out.latencies.push(performance.now() - s);
        out.statuses.push(resp.status);
        out.cache.push(resp.headers.get("x-agentcc-cache"));
      }),
    );
  }
  out.wallMs = performance.now() - t0;
  return out;
}

export const authHeaders = (): Record<string, string> => ({ authorization: `Bearer ${live.key}`, "content-type": "application/json" });

/** POST /v1/chat/completions with a fixed or per-index prompt. */
export const chatPost = (content: string, extra: Record<string, unknown> = {}): Promise<Response> =>
  fetch(`${live.base}/v1/chat/completions`, {
    method: "POST",
    headers: authHeaders(),
    body: JSON.stringify({ model: MODEL, messages: user(content), max_tokens: 5, temperature: 0, ...extra }),
  });

export function summarize(label: string, t: Timed) {
  return { label, wall_ms: Math.round(t.wallMs), throughput_rps: Math.round((t.statuses.length / (t.wallMs / 1000)) * 10) / 10, ...stats(t.latencies), statuses: [...new Set(t.statuses)], cache: [...new Set(t.cache)] };
}
