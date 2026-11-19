import { Ratings, Run, Runs } from "..";
import { FutureAGIClient } from "../../../futureagi-client";
import { PLATFORM_OPERATIONS } from "../../../generated/platform/policy.gen";
import { CoreServerError, Script, json, sse, dropped, makeCore, keysOrigin } from "../../../_core/__fixtures__/platform";
import { APITimeoutError, ConfigurationError, MixedCredentialsError, PermissionDeniedError, StreamInterruptedError } from "../../../_core/errors";

const raw = (status = "active", id = "run-a") => ({ conversation: { id, status, managedExecution: { taskId: "task-a" } }, receipt: { auditEntryId: "audit-a" }, future: true });
const setup = (script: Script, retries = 0) => new Runs(makeCore(script, {
  table: PLATFORM_OPERATIONS, resolveOrigin: () => keysOrigin("http://127.0.0.1:9000/omega/api"), retries,
}));
const DONE: [undefined, string, unknown] = [undefined, "done", { type: "done" }];
const status = (seq: number, value: string): [string, string, unknown] => [String(seq), "status", { seq, status: value }];

type Case = [string, (runs: Runs, run: Run, ratings: Ratings) => unknown];
const cases: Case[] = [
  ["runs.create", r => r.create({ input: "hello", idempotencyKey: "stable-run-key" })],
  ["runs.list", r => r.list({ agentId: "a", status: "active", agentVersion: 1, deploymentVersion: 2, channelId: "c", providerEventId: "p", externalCorrelationId: "e", limit: 2, cursor: "opaque" })],
  ["runs.get", r => r.get("run-a")], ["runs.delete", r => r.delete("run-a")],
  ["runs.send", (_, r) => r.send({ input: "next", idempotencyKey: "stable-run-key" })],
  ["runs.cancel", (_, r) => r.cancel()], ["runs.interrupt", (_, r) => r.interrupt()],
  ["runs.continue", (_, r) => r.resume({ idempotencyKey: "stable-run-key" })],
  ["runs.retry", (_, r) => r.retry({ reason: "retry", idempotencyKey: "stable-run-key" })],
  ["runs.fork", (_, r) => r.fork({ upToMessageId: "message-a", idempotencyKey: "stable-run-key" })],
  ["runs.tree", (_, r) => r.tree()],
  ["runs.observations", (_, r) => r.observations({ taskId: "task-a", kind: "tool.started", limit: 20 })],
  ["runs.evidence", (_, r) => r.evidence()], ["runs.proofPack", (_, r) => r.proofPack()],
  ["runs.controlStatus", (_, r) => r.controlStatus()], ["runs.approvals", (_, r) => r.approvals()],
  ["runs.rating.get", (_, r) => r.rating.get()], ["runs.rating.set", (_, r) => r.rating.set({ rating: null, messageId: "message-a" })],
  ["platform.approvals.list", r => r.listApprovals({ conversationId: "run-a", state: "decided", limit: 2, cursor: "opaque" })],
  ["platform.ratings.summary", (_, __, r) => r.summary()], ["platform.ratings.trajectory", (_, __, r) => r.trajectory()],
];

test.each(cases)("%s uses the generated wire policy", async (name, invoke) => {
  const script = new Script([json(200, { ...raw(), conversations: [], approvals: [] })]);
  const runs = setup(script), run = new Run(runs, raw());
  const result = await invoke(runs, run, new Ratings(runs.core));
  const request = script.requests[0]!;
  const policy = runs.core.operation(name);
  expect(request.method).toBe(policy.method);
  expect(new URL(request.url).pathname).toBe("/omega/api" + policy.path.replace("{id}", "run-a"));
  expect(request.headers.get("Idempotency-Key")).toBe(policy.idempotent === true ? "stable-run-key" : null);
  expect(request.headers.get("X-Api-Key")).toBe("k-test-1234");
  expect(request.headers.get("X-Secret-Key")).toBe("s-test-1234");
  const bodies: Record<string, unknown> = {
    "runs.create": { input: "hello" }, "runs.send": { input: "next" },
    "runs.retry": { reason: "retry" }, "runs.fork": { upToMessageId: "message-a" },
    "runs.rating.set": { rating: null, messageId: "message-a" },
  };
  if (name in bodies) expect(await request.json()).toEqual(bodies[name]);
  if (name === "runs.observations") expect(Object.fromEntries(new URL(request.url).searchParams)).toEqual({ taskId: "task-a", kind: "tool.started", limit: "20" });
  if (["runs.create", "runs.get", "runs.fork"].includes(name)) expect(result).toBeInstanceOf(Run);
});

test("the cases cover every run, rating and approval-read operation", () => {
  expect([...cases.map(c => c[0]), "runs.events"].sort()).toEqual(Object.keys(PLATFORM_OPERATIONS).filter(n => n.startsWith("runs.") || n.startsWith("platform.ratings.") || n === "platform.approvals.list").sort());
  expect("decide" in Run.prototype || "approve" in Run.prototype || "deny" in Run.prototype).toBe(false);
});

test("create body, waiter, envelope and identity survive refresh", async () => {
  const script = new Script([json(201, raw()), json(200, raw("done"))]);
  const runs = setup(script);
  const run = await runs.create({ input: "hello", agentId: "a", modelId: "fixture-model", metadata: { channelId: "c" }, wait: true, timeout: 0 });
  expect(run.status).toBe("done"); expect(run.identity).toEqual({ taskId: "task-a" });
  expect(run.response).toMatchObject({ receipt: { auditEntryId: "audit-a" }, future: true });
  expect(await script.requests[0]!.json()).toEqual({ input: "hello", agentId: "a", modelId: "fixture-model", metadata: { channelId: "c" } });
  expect(script.keys[0]).toBeTruthy(); expect(script.requests).toHaveLength(2);
});

test.each(["waiting_approval", "new-server-state"])("%s is not terminal", async state => {
  const script = new Script([json(200, raw(state))]); const runs = setup(script);
  await expect(new Run(runs, raw(state)).wait({ timeout: 0 })).rejects.toBeInstanceOf(APITimeoutError);
  expect(script.requests).toHaveLength(1);
});

const reactivating: [string, (run: Run) => Promise<unknown>][] = [
  ["send", run => run.send({ input: "next" })],
  ["retry", run => run.retry()],
  ["resume", run => run.resume()],
];

test.each(reactivating)("wait after %s observes the new turn rather than cached completion", async (_, invoke) => {
  for (const state of ["done", "error", "canceled"]) {
    const receipt = { accepted: true, receipt: { id: "new-turn" } };
    const fresh = { ...raw("done"), messages: [{ id: "new-message" }] };
    const script = new Script([json(200, raw(state)), json(202, receipt), json(200, raw("active")), json(200, fresh)]);
    const run = await setup(script).get("run-a");
    expect(await invoke(run)).toEqual(receipt);
    expect(run.status).toBe(state); expect(run.response).toEqual(raw(state));
    expect(await run.wait({ timeout: 1, sleep: async () => {} })).toBe(run);
    expect(run.response).toEqual(fresh); expect(run.status).toBe("done");
    expect(script.requests.map(r => r.method)).toEqual(["GET", "POST", "GET", "GET"]);
    expect(await run.wait({ timeout: 0 })).toBe(run);
    expect(script.requests).toHaveLength(4);
  }
});

test.each(reactivating)("failed %s preserves a valid terminal snapshot", async (_, invoke) => {
  const script = new Script([json(403, { error: "scope_denied" })]);
  const run = new Run(setup(script), raw("done"));
  await expect(invoke(run)).rejects.toBeInstanceOf(PermissionDeniedError);
  expect(await run.wait({ timeout: 0 })).toBe(run);
  expect(run.response).toEqual(raw("done"));
  expect(script.requests.map(r => r.method)).toEqual(["POST"]);
});

test("a failed refresh and timeout after reactivation never reuse old completion", async () => {
  const script = new Script([json(202, { accepted: true }), json(403, { error: "scope_denied" }), json(200, raw("active")), json(200, raw("done"))]);
  const run = new Run(setup(script), raw("done"));
  await run.send({ input: "next" });
  await expect(run.wait({ timeout: 0 })).rejects.toBeInstanceOf(PermissionDeniedError);
  await expect(run.wait({ timeout: 0 })).rejects.toBeInstanceOf(APITimeoutError);
  expect(await run.wait({ timeout: 0 })).toBe(run);
  expect(script.requests.map(r => r.method)).toEqual(["POST", "GET", "GET", "GET"]);
});

test("opaque cursors retain filters and repeated cursors stop iteration", async () => {
  const script = new Script([json(200, { conversations: [raw().conversation], nextCursor: "opaque+/=" }), json(200, { conversations: [raw("done", "run-b").conversation], nextCursor: "opaque+/=" })]);
  const ids: string[] = [];
  for await (const run of setup(script).list({ agentId: "a", limit: 1 })) ids.push(run.id);
  expect(ids).toEqual(["run-a", "run-b"]);
  expect(new URL(script.requests[1]!.url).searchParams.get("cursor")).toBe("opaque+/=");
  expect(new URL(script.requests[1]!.url).searchParams.get("agentId")).toBe("a");
});

test("events resume without repeats after a disconnect and wait for the done frame", async () => {
  const script = new Script([() => dropped('id: 2\nevent: status\ndata: {"seq":2,"status":"active"}\n\n'), () => sse([status(2, "active"), status(3, "done"), DONE])]);
  const runs = setup(script), events = [];
  for await (const event of new Run(runs, raw()).events({ after: 1 })) events.push(event as Record<string, unknown>);
  expect(events.map(e => e.seq)).toEqual([2, 3, undefined]);
  expect(script.requests.map(r => r.headers.get("Last-Event-ID"))).toEqual(["1", "2"]);
});

test("events enforce idle and reconnect bounds, and terminal authorization refusals", async () => {
  const script = new Script([() => new Response(new ReadableStream({ start(c) { c.enqueue(new TextEncoder().encode(": heartbeat\n\n")); } }), { headers: { "content-type": "text/event-stream" } })]);
  const run = new Run(setup(script), raw());
  const collect = async () => { for await (const _ of run.events({ after: 0, bounds: { idleTimeoutMs: 5, maxReconnects: 0 } })) {} };
  await expect(collect()).rejects.toBeInstanceOf(StreamInterruptedError);
  expect(script.requests).toHaveLength(1);
  const denied = new Run(setup(new Script([json(403, { error: "scope_denied" })])), raw());
  await expect(denied.events().next()).rejects.toBeInstanceOf(PermissionDeniedError);
});

test("explicit keys survive retries but cancellation and interruption are not replayed", async () => {
  const script = new Script([json(503, { error: "unavailable" }), json(201, raw())]);
  await setup(script, 1).create({ input: "hello", idempotencyKey: "stable-run-key" });
  expect(script.keys).toEqual(["stable-run-key", "stable-run-key"]);
  for (const method of ["cancel", "interrupt"] as const) {
    const s = new Script([json(503, { error: "unavailable" })]);
    await expect(new Run(setup(s, 1), raw())[method]()).rejects.toBeInstanceOf(CoreServerError);
    expect(s.requests).toHaveLength(1);
  }
});

test("approvals are reads and dispose cancels a still-active run", async () => {
  const script = new Script([json(200, { approvals: [{ approval: { id: "approval-a" } }] }), json(200, raw()), json(202, { accepted: true })]);
  const run = new Run(setup(script), raw());
  await run.waitForApproval({ timeout: 0 }); await run.dispose();
  expect(script.requests.map(r => r.method)).toEqual(["GET", "GET", "POST"]);
  for (const after of [-1, "01", "1\n", "", "1.0", Number.MAX_SAFE_INTEGER + 1]) expect(() => run.events({ after })).toThrow(ConfigurationError);
});

test("root registration, copied options and mixed authentication fail before transport", async () => {
  const script = new Script([json(201, raw("done"))]);
  const client = new FutureAGIClient({ apiKey: "fixture-api", secretKey: "fixture-secret", baseUrl: "http://127.0.0.1:9000", fetch: script.fetch });
  expect(client.agents.runs).toBeInstanceOf(Runs);
  await client.withOptions({ retries: 0 }).agents.runs.create({ input: "hello" });
  expect(script.requests).toHaveLength(1);
  const mixed = new FutureAGIClient({ apiKey: "fixture-api", secretKey: "fixture-secret", platformToken: "fixture-token", baseUrl: "http://127.0.0.1:9000", fetch: script.fetch });
  await expect(mixed.agents.runs.get("run-a")).rejects.toBeInstanceOf(MixedCredentialsError);
  expect(script.requests).toHaveLength(1);
});
