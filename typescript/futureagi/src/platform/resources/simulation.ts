// Hand-written additions to `client.simulation`.
//
// Scaffolded once by sdkgen/generate.py and never overwritten: methods added here survive
// regeneration. The generated methods live in `./base`.
//
// The wait helpers poll the generated read methods the way the futureagi CLI's `--wait` does
// (`fi sim run`, `fi sim env status`, `fi agents push`, `fi sim runs insights`), so a script gets
// the same notion of "finished":
//
//   const started = await client.simulation.environments.run(envId, { scenario_ids: ["1", "2"] });
//   const run = await client.simulation.waitForRun(started.job_id!, { testExecutionId: started.test_execution_id });
//
// Each returns the last thing it read; none of them treats a failed outcome as an error (read
// `status.state` or the returned status). A wait that runs out of time throws `WaitTimeoutError`.

import type * as models from "../models";
import { SimulationResource } from "./base";

// The same terminal states as the CLI (internal/cli/sim_runs_status.go, sim_runs_insights.go).
export const JOB_TERMINAL: ReadonlySet<string> = new Set(["completed", "failed", "canceled"]);
export const EXECUTION_TERMINAL: ReadonlySet<string> = new Set(["completed", "failed", "cancelled"]);
export const INSIGHTS_TERMINAL: ReadonlySet<string> = new Set(["completed", "failed", "not_requested"]);
// A builder chat turn still running (internal/cli/sim_env_jobs.go simConvBusy).
export const CONVERSATION_BUSY: ReadonlySet<string> = new Set(["starting", "hydrating", "responding"]);

/** How long to wait and how often to look, in milliseconds. */
export interface WaitOptions {
  /** Default one hour (30 minutes for Insights). */
  timeoutMs?: number;
  /** Default 5 seconds. */
  pollIntervalMs?: number;
}

/** A wait helper ran out of time; the operation may still finish on the server. */
export class WaitTimeoutError extends Error {
  constructor(what: string, timeoutMs: number) {
    super(`${what} did not finish within ${timeoutMs}ms`);
    this.name = "WaitTimeoutError";
  }
}

type Json = Record<string, unknown>;

function field(value: unknown, dotted: string): unknown {
  let current = value;
  for (const key of dotted.split(".")) {
    if (current === null || typeof current !== "object") {
      return undefined;
    }
    current = (current as Json)[key];
  }
  return current;
}

/**
 * The builder's unanswered question on a job (`conversation.blocking_input`), or null. A question
 * already answered by a message the builder has not processed yet counts as answered. Reply with
 * `client.simulation.jobs.sendMessage(jobId, { content, kind: "user_response", reply_to: question.message_id, client_request_id })`.
 */
export function openQuestion(job: unknown): Json | null {
  const question = field(job, "conversation.blocking_input");
  if (question === null || typeof question !== "object" || Array.isArray(question)) {
    return null;
  }
  const messages = field(job, "conversation.messages");
  for (const message of Array.isArray(messages) ? messages : []) {
    const replyTo = field(message, "reply_to");
    if (replyTo && replyTo === (question as Json).message_id) {
      return null;
    }
  }
  return question as Json;
}

/**
 * Whether the builder is still working on a chat turn: a running invocation, a busy conversation
 * state, or a user message still queued. A message sent to a finished build (`jobs.sendMessage`)
 * changes the conversation, not `status.state`, so a finished job can still be busy. A chat the
 * server cannot run (`runtime.available` false) never is.
 */
export function conversationBusy(job: unknown): boolean {
  const conversation = field(job, "conversation");
  if (conversation === null || typeof conversation !== "object" || field(conversation, "runtime.available") === false) {
    return false;
  }
  const active = field(conversation, "active_invocation_id");
  if ((active !== null && active !== undefined) || CONVERSATION_BUSY.has(String(field(conversation, "state")))) {
    return true;
  }
  const messages = field(conversation, "messages");
  return (Array.isArray(messages) ? messages : []).some((m) => field(m, "role") === "user" && field(m, "state") === "queued");
}

// The CLI's builderDone: an open question, or a terminal job whose chat is idle.
function jobSettled(job: unknown): boolean {
  return openQuestion(job) !== null || (JOB_TERMINAL.has(String(field(job, "status.state"))) && !conversationBusy(job));
}

const sleep = (ms: number) => new Promise<void>((resolve) => setTimeout(resolve, ms));

async function poll<T>(read: () => Promise<T>, done: (value: T) => boolean, what: string, opts: WaitOptions | undefined, defaultTimeoutMs: number): Promise<T> {
  const timeoutMs = opts?.timeoutMs ?? defaultTimeoutMs;
  const every = opts?.pollIntervalMs ?? 5000;
  if (!(timeoutMs > 0) || !(every > 0)) {
    throw new RangeError("timeoutMs and pollIntervalMs must be positive");
  }
  const deadline = Date.now() + timeoutMs;
  for (;;) {
    const value = await read();
    if (done(value)) {
      return value;
    }
    if (Date.now() + every > deadline) {
      throw new WaitTimeoutError(what, timeoutMs);
    }
    await sleep(every);
  }
}

/** `client.simulation`: every generated `simulation.*` method, plus the hand-written additions in this file. */
export class Simulation extends SimulationResource {
  /**
   * Poll a harness job (an environment build, or a run's job) until it is completed, failed or
   * canceled and its builder chat is idle (see `conversationBusy`), or until the builder asks a
   * question (see `openQuestion`). Resolves to the job.
   */
  waitForJob(jobId: string, opts?: WaitOptions): Promise<Json> {
    return poll(
      async () => (await this.jobs.get(jobId)) as Json,
      jobSettled,
      `job ${jobId}`,
      opts,
      3_600_000,
    );
  }

  /**
   * Wait for a run started with `environments.run`: its job settles, then its test execution, whose
   * grading can outlast the job whatever the job's end state (a failed or canceled re-run can still
   * be grading the calls that finished). The execution is `testExecutionId`, or the job's own
   * `job.test_execution_id`; `executionStatus` is null when the run has no execution to read.
   */
  async waitForRun(jobId: string, opts?: WaitOptions & { testExecutionId?: string | null }): Promise<{ job: Json; executionStatus: string | null }> {
    const started = Date.now();
    const timeoutMs = opts?.timeoutMs ?? 3_600_000;
    const job = await this.waitForJob(jobId, opts);
    const fromJob = field(job, "job.test_execution_id");
    const executionId = opts?.testExecutionId || (typeof fromJob === "string" ? fromJob : "");
    if (!executionId) {
      return { job, executionStatus: null };
    }
    const every = opts?.pollIntervalMs ?? 5000;
    const status = await poll(
      async () => {
        const value = field(await this._t.raw("GET", `/simulate/test-executions/${encodeURIComponent(executionId)}/`, { query: { limit: 1 } }), "status");
        return typeof value === "string" ? value : "";
      },
      // An execution without a status cannot be waited on (the CLI's pollRun returns then too).
      (value) => value === "" || EXECUTION_TERMINAL.has(value),
      `test execution ${executionId}`,
      { pollIntervalMs: every, timeoutMs: Math.max(timeoutMs - (Date.now() - started), every) },
      timeoutMs,
    );
    return { job, executionStatus: status || null };
  }

  /**
   * Poll an environment's agent version until its connection check leaves `pending`
   * (`preflight_status`), after `versions.createAgent`, `versions.retryAgent` or `jobs.setSecretValues`.
   */
  waitForAgentVersion(environmentId: string, versionId: string, opts?: WaitOptions): Promise<models.HarnessVersion & { preflight_status?: string }> {
    return poll(
      async () => {
        const versions = await this.environments.versions.list(environmentId);
        const version = (versions.agent ?? []).find((v) => v?.id === versionId);
        if (!version) {
          throw new Error(`agent version ${versionId} is no longer listed for environment ${environmentId}`);
        }
        return version as models.HarnessVersion & { preflight_status?: string };
      },
      (version) => version.preflight_status !== "pending",
      `agent version ${versionId}`,
      opts,
      3_600_000,
    );
  }

  /** Poll a run's Insights (after `executions.insights.start`) until completed or failed. */
  waitForInsights(testExecutionId: string, opts?: WaitOptions): Promise<models.TestExecutionDebugAnalysisResponse> {
    return poll(
      () => this.executions.insights.get(testExecutionId),
      (analysis) => INSIGHTS_TERMINAL.has(String(analysis.status)),
      `insights of ${testExecutionId}`,
      opts,
      1_800_000,
    );
  }
}
