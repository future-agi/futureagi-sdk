import type * as Wire from "../../generated/platform/types.gen";
/** Managed runs use the shared platform executor and generated operation policy. */
import { Handle, pollUntil, type PollOptions } from "../../_core/handles";
import { ConfigurationError } from "../../_core/errors";
import { listPage, type PagePromise } from "../../_core/pagination";
import type { PlatformCore } from "../../_core/platform-base";
import { resumableEvents, type ResumableOptions } from "../../_core/resumable";
import type {
  OmegaPostWorkspaceConversationsRequest, OmegaPostWorkspaceConversationsByIdMessagesRequest,
  RetryWorkspaceConversationRequest, ForkWorkspaceConversationRequest, RecordConversationRatingRequest,
} from "../../generated/platform/types.gen";

const FINAL = new Set(["done", "error", "canceled"]);
type Data = Record<string, unknown>;
/** Create body plus replay and waiter settings. Timeout is in seconds in both languages. */
export type CreateOptions = OmegaPostWorkspaceConversationsRequest & { idempotencyKey?: string; wait?: boolean; timeout?: number };
/** Run-list filters are converted by the shared request builder, never by a URL concatenation. */
export interface ListOptions {
  /** Maximum items in one page. */
  limit?: number;
  /** Opaque cursor from the preceding page. */
  cursor?: string;
  /** Restrict to one managed agent. */
  agentId?: string;
  /** Restrict to a server status. */
  status?: string;
  /** Restrict to an agent definition version. */
  agentVersion?: number;
  /** Restrict to an agent release version. */
  deploymentVersion?: number;
  /** Normalized channel identifier. */
  channelId?: string;
  /** Provider event or delivery identifier. */
  providerEventId?: string;
  /** Caller-defined external correlation identifier. */
  externalCorrelationId?: string;
}

function object(value: unknown): Data {
  if (value === null || typeof value !== "object" || Array.isArray(value))
    throw new ConfigurationError("run response must be an object", "invalid_run_response");
  return value as Data;
}
function snapshot(response: Data): Data {
  const data = object(response.conversation ?? response);
  if (typeof data.id !== "string" || data.id === "")
    throw new ConfigurationError("run response has no conversation id", "invalid_run_response");
  return data;
}
function sequence(after?: number | string): string | undefined {
  if (after === undefined) return undefined;
  const value = String(after);
  if (!/^(0|[1-9][0-9]*)$/u.test(value) || (typeof after === "number" && !Number.isSafeInteger(after)))
    throw new ConfigurationError("after must be a canonical non-negative event sequence", "invalid_sequence");
  return value;
}

/** Read, set or clear the caller's latest rating, without retrying a sent write. */
export class RunRating {
  constructor(private readonly core: PlatformCore, private readonly runId: string) {}
  /** Return the ratings and their response metadata. */
  get(): Promise<Wire.GetConversationRatingsResponse> { return Promise.resolve(this.core.call<Wire.GetConversationRatingsResponse>("runs.rating.get", { path: { id: this.runId } })); }
  /** Null clears a rating; messageId targets one message rather than the whole run. */
  set(options: RecordConversationRatingRequest): Promise<Wire.RecordConversationRatingResponse> {
    if (![null, "up", "down"].includes(options.rating)) throw new ConfigurationError("invalid rating", "invalid_rating");
    return Promise.resolve(this.core.call<Wire.RecordConversationRatingResponse>("runs.rating.set", { path: { id: this.runId }, body: options }));
  }
}

/** A run snapshot with refresh, one waiter, resumable events and read-only approvals. */
export class Run extends Handle<Data> {
  protected readonly noun = "run";
  private envelope: Data;
  private snapshotStale = false;
  constructor(private readonly namespace: Runs, response: Data) {
    super(snapshot(response));
    this.envelope = response;
  }
  /** The full last read/create response, including messages, receipts and unknown fields. */
  get response(): Data { return this.envelope; }
  /** Server-stamped execution identity, if available. */
  get identity(): unknown { return this.data.managedExecution; }
  /** The constructor verifies that every run has a nonempty id. */
  get id(): string { return this.data.id as string; }
  /** This caller's per-run or per-message ratings. */
  get rating(): RunRating { return new RunRating(this.namespace.core, this.id); }
  protected async fetchData(options: { signal?: AbortSignal } = {}): Promise<Data> {
    const fresh = await this.namespace.core.call<Data>("runs.get", { path: { id: this.id } }, options);
    const data = snapshot(fresh);
    this.envelope = fresh;
    this.snapshotStale = false;
    return data;
  }
  protected isDone(): boolean { return !this.snapshotStale && typeof this.status === "string" && FINAL.has(this.status); }
  /** The shared waiter; timeout is seconds, timeoutMs is the core's optional millisecond override. */
  wait(options: PollOptions & { timeout?: number } = {}): Promise<this> {
    return super.wait({ ...options, timeoutMs: options.timeoutMs ?? (options.timeout ?? 300) * 1000 });
  }
  /** Resume after a durable sequence. Close the iterator when leaving early; this does not cancel the run. */
  events(options: { after?: number | string; bounds?: ResumableOptions } = {}): ReturnType<typeof resumableEvents> {
    const lastEventId = sequence(options.after);
    return resumableEvents(this.namespace.core, "runs.events", { path: { id: this.id } },
      event => event.type === "done", { ...options.bounds, ...(lastEventId !== undefined ? { lastEventId } : {}) });
  }
  /** Send a turn with a replay key; wait re-reads completion after acceptance. */
  async send(options: OmegaPostWorkspaceConversationsByIdMessagesRequest & { idempotencyKey?: string }): Promise<Wire.OmegaPostWorkspaceConversationsByIdMessagesResponse | Wire.OmegaPostWorkspaceConversationsByIdMessagesResponse2> {
    const { idempotencyKey, ...body } = options;
    const receipt = await this.namespace.core.call<Wire.OmegaPostWorkspaceConversationsByIdMessagesResponse | Wire.OmegaPostWorkspaceConversationsByIdMessagesResponse2>("runs.send", { path: { id: this.id }, body }, { idempotencyKey });
    // Keep the last server snapshot intact, but do not use it to finish a new turn.
    this.snapshotStale = true;
    return receipt;
  }
  /** Request cancellation and return its receipt. */
  cancel(): Promise<Wire.OmegaRunCancelResult> { return this.readOrControl<Wire.OmegaRunCancelResult>("runs.cancel"); }
  /** Park the run without destroying it; never retry a sent interruption. */
  interrupt(): Promise<Wire.InterruptWorkspaceConversationResponse> { return this.readOrControl<Wire.InterruptWorkspaceConversationResponse>("runs.interrupt"); }
  /** Continue with a replay key; wait re-reads completion after acceptance. */
  async resume(options: { idempotencyKey?: string } = {}): Promise<Wire.ContinueWorkspaceConversationResponse> {
    const receipt = await this.namespace.core.call<Wire.ContinueWorkspaceConversationResponse>("runs.continue", { path: { id: this.id } }, options);
    this.snapshotStale = true;
    return receipt;
  }
  /** Retry with audit attribution; wait re-reads completion after acceptance. */
  async retry(options: RetryWorkspaceConversationRequest & { idempotencyKey?: string } = {}): Promise<Wire.RetryWorkspaceConversationResponse> {
    const { idempotencyKey, ...body } = options;
    const receipt = await this.namespace.core.call<Wire.RetryWorkspaceConversationResponse>("runs.retry", { path: { id: this.id }, body }, { idempotencyKey });
    this.snapshotStale = true;
    return receipt;
  }
  /** Fork the transcript into a separate run. The inclusive cut point is optional. */
  async fork(options: ForkWorkspaceConversationRequest & { idempotencyKey?: string } = {}): Promise<Run> {
    const { idempotencyKey, ...body } = options;
    const raw = await this.namespace.core.call<Data>("runs.fork", { path: { id: this.id }, body }, { idempotencyKey });
    return new Run(this.namespace, raw);
  }
  /** Canonical task tree, unchanged from the server. */
  tree(): Promise<Wire.GetWorkspaceConversationTaskTreeResponse> { return this.readOrControl<Wire.GetWorkspaceConversationTaskTreeResponse>("runs.tree"); }
  /** Observation window, retaining truncation and ownership metadata. */
  observations(options: { taskId?: string; kind?: string; limit?: number } = {}): Promise<Wire.GetWorkspaceConversationObservationsResponse> {
    return Promise.resolve(this.namespace.core.call<Wire.GetWorkspaceConversationObservationsResponse>("runs.observations", { path: { id: this.id }, query: options }));
  }
  /** Durable filesystem and browser evidence manifest. */
  evidence(): Promise<Wire.OmegaGetWorkspaceConversationsByIdEvidenceResponse> { return this.readOrControl<Wire.OmegaGetWorkspaceConversationsByIdEvidenceResponse>("runs.evidence"); }
  /** Portable proof bundle; the SDK does not alter the proof. */
  proofPack(): Promise<Wire.OmegaGetWorkspaceConversationsByIdProofPackResponse> { return this.readOrControl<Wire.OmegaGetWorkspaceConversationsByIdProofPackResponse>("runs.proofPack"); }
  /** Joined control status, preserving null/unpriced spend. */
  controlStatus(): Promise<Wire.OmegaRunControlStatus> { return this.readOrControl<Wire.OmegaRunControlStatus>("runs.controlStatus"); }
  /** Pending approvals, read only. Approval decisions belong in the app. */
  approvals(): Promise<Wire.OmegaGetWorkspaceConversationsByIdApprovalsResponse> { return this.readOrControl<Wire.OmegaGetWorkspaceConversationsByIdApprovalsResponse>("runs.approvals"); }
  /** Wait for a nonempty approvals response; timeout is in seconds. */
  waitForApproval(options: { timeout?: number } = {}): Promise<Wire.OmegaGetWorkspaceConversationsByIdApprovalsResponse> {
    return pollUntil(async () => {
      const raw = await this.approvals();
      return Array.isArray(raw.approvals) && raw.approvals.length > 0 ? raw : undefined;
    }, { timeoutMs: (options.timeout ?? 300) * 1000, label: "waiting for approval" });
  }
  /** `await using` cleanup refreshes and cancels a nonterminal run, without deleting history. */
  async dispose(): Promise<void> { await this.refresh(); if (!this.isDone()) await this.cancel(); }
  private readOrControl<T extends object>(operation: string): Promise<T> {
    return Promise.resolve(this.namespace.core.call<T>(operation, { path: { id: this.id } }));
  }
}

/** Managed-run collection on the shared client. */
export class Runs {
  /** @internal Shared request executor; resource handles use the same policy and pool. */
  readonly core: PlatformCore;
  constructor(core: PlatformCore) { this.core = core; }
  /** Create, optionally waiting for done/error/canceled. A timeout never cancels the run. */
  async create(options: CreateOptions): Promise<Run> {
    const { idempotencyKey, wait = false, timeout = 300, ...body } = options;
    const raw = await this.core.call<Data>("runs.create", { body }, { idempotencyKey });
    const run = new Run(this, raw);
    if (wait) await run.wait({ timeoutMs: timeout * 1000 });
    return run;
  }
  /** Fetch a run and its complete detail envelope. */
  async get(runId: string): Promise<Run> {
    return new Run(this, await this.core.call<Data>("runs.get", { path: { id: runId } }));
  }
  /** Delete one run, returning the server's deletion receipt. */
  delete(runId: string): Promise<Wire.OmegaDeleteWorkspaceConversationsByIdResponse> { return Promise.resolve(this.core.call<Wire.OmegaDeleteWorkspaceConversationsByIdResponse>("runs.delete", { path: { id: runId } })); }
  /** Await the first page, or iterate every matching run with for-await. */
  list(options: ListOptions = {}): PagePromise<Run> {
    const { cursor, ...query } = options;
    return listPage(this.core, "runs.list", { query }, { cursor, transform: raw => new Run(this, object(raw)) });
  }
  /** Read pending/decided approvals; pass a decided response's nextCursor to continue. */
  listApprovals(options: { conversationId?: string; state?: string; limit?: number; cursor?: string } = {}): Promise<Wire.OmegaGetWorkspaceApprovalsResponse> {
    return Promise.resolve(this.core.call<Wire.OmegaGetWorkspaceApprovalsResponse>("platform.approvals.list", { query: options }));
  }
}

/** Aggregate satisfaction reads. These metrics are not a claim of learning. */
export class Ratings {
  constructor(private readonly core: PlatformCore) {}
  /** Latest-wins rating counts and satisfaction rate. */
  summary(): Promise<Wire.GetWorkspaceRatingsSummaryResponse> { return Promise.resolve(this.core.call<Wire.GetWorkspaceRatingsSummaryResponse>("platform.ratings.summary")); }
  /** Satisfaction time series, unchanged from the server. */
  trajectory(): Promise<Wire.GetWorkspaceRatingsTrajectoryResponse> { return Promise.resolve(this.core.call<Wire.GetWorkspaceRatingsTrajectoryResponse>("platform.ratings.trajectory")); }
}
