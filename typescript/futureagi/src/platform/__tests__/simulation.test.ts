// client.simulation's hand-written wait helpers, against a fake fetch (no backend).

import { Client } from "../client";
import { openQuestion, WaitTimeoutError } from "../index";
import type { FetchLike } from "../transport";

const BASE = "http://backend.test";
const JOB = "/simulate/api/harness-jobs/j1/";
const VERSIONS = "/simulate/api/harness-environments/e1/versions/";
const FAST = { pollIntervalMs: 1 };

const ok = (result: unknown) => ({ status: true, result });
const job = (state: string, extra: Record<string, unknown> = {}) => ({ job: { job_id: "j1" }, status: { state }, ...extra });

/** routes: path -> bodies, answered in order; the last one repeats. Records the paths. */
function scripted(routes: Record<string, unknown[]>): { fetch: FetchLike; seen: string[] } {
  const seen: string[] = [];
  const fetch: FetchLike = async (url) => {
    const path = new URL(url).pathname;
    seen.push(path);
    const queue = routes[path];
    const body = queue.length > 1 ? queue.shift() : queue[0];
    return new Response(JSON.stringify(body), { status: 200, headers: { "content-type": "application/json" } });
  };
  return { fetch, seen };
}

const client = (fetch: FetchLike) => new Client({ apiKey: "k", secretKey: "s", baseUrl: BASE, fetch, maxRetries: 0 });

describe("simulation wait helpers", () => {
  test("waitForJob polls until a terminal state", async () => {
    const { fetch, seen } = scripted({ [JOB]: [ok(job("running")), ok(job("running")), ok(job("completed"))] });
    const result = await client(fetch).simulation.waitForJob("j1", FAST);
    expect((result.status as { state: string }).state).toBe("completed");
    expect(seen).toEqual([JOB, JOB, JOB]);
  });

  test("waitForJob stops at an open question, not at one already answered", async () => {
    const question = { message_id: "q1", prompt: "Docker or Python?" };
    const asked = job("running", { conversation: { blocking_input: question, messages: [] } });
    const answered = job("running", { conversation: { blocking_input: question, messages: [{ reply_to: "q1" }] } });
    const { fetch, seen } = scripted({ [JOB]: [ok(answered), ok(asked)] });
    const result = await client(fetch).simulation.waitForJob("j1", FAST);
    expect(openQuestion(result)).toEqual(question);
    expect(seen).toHaveLength(2);
    expect(openQuestion(answered)).toBeNull();
  });

  test("waitForJob times out with WaitTimeoutError and rejects a non-positive timeout", async () => {
    const { fetch } = scripted({ [JOB]: [ok(job("running"))] });
    await expect(client(fetch).simulation.waitForJob("j1", { timeoutMs: 5, pollIntervalMs: 5 })).rejects.toBeInstanceOf(WaitTimeoutError);
    await expect(client(fetch).simulation.waitForJob("j1", { timeoutMs: 0 })).rejects.toBeInstanceOf(RangeError);
  });

  test("waitForRun waits for grading after the job, and not after a failed job", async () => {
    const te = "/simulate/test-executions/te1/";
    const graded = scripted({ [JOB]: [ok(job("completed"))], [te]: [{ status: "evaluating" }, { status: "completed" }] });
    const run = await client(graded.fetch).simulation.waitForRun("j1", { ...FAST, testExecutionId: "te1" });
    expect(run.executionStatus).toBe("completed");
    expect(graded.seen).toEqual([JOB, te, te]);

    const failed = scripted({ [JOB]: [ok(job("failed"))] });
    const result = await client(failed.fetch).simulation.waitForRun("j1", { ...FAST, testExecutionId: "te1" });
    expect(result.executionStatus).toBeNull();
    expect(failed.seen).toEqual([JOB]);
  });

  test("waitForAgentVersion polls until the check leaves pending, and fails if the version vanishes", async () => {
    const versions = (check: string) => ok({ agent: [{ id: "v1", preflight_status: "passed" }, { id: "v2", preflight_status: check }], environment: [], suite: [] });
    const { fetch, seen } = scripted({ [VERSIONS]: [versions("pending"), versions("failed")] });
    const version = await client(fetch).simulation.waitForAgentVersion("e1", "v2", FAST);
    expect(version.preflight_status).toBe("failed");
    expect(seen).toHaveLength(2);

    const gone = scripted({ [VERSIONS]: [ok({ agent: [], environment: [], suite: [] })] });
    await expect(client(gone.fetch).simulation.waitForAgentVersion("e1", "v2", FAST)).rejects.toThrow(/no longer listed/);
  });

  test("waitForInsights polls until terminal", async () => {
    const path = "/simulate/test-executions/te1/debug-analysis/";
    const { fetch, seen } = scripted({ [path]: [ok({ test_execution_id: "te1", status: "running" }), ok({ test_execution_id: "te1", status: "completed" })] });
    const analysis = await client(fetch).simulation.waitForInsights("te1", FAST);
    expect(analysis.status).toBe("completed");
    expect(seen).toHaveLength(2);
  });
});
