/**
 * Test fixtures (not shipped API): an operation table shaped like the pinned contract's, a scripted
 * fetch that records every request, and a core over them. No sockets are opened.
 */

import { PlatformCore, type PlatformShared } from "../platform-base";
import type { PlatformOrigin } from "../origins";
import type { OperationTable } from "../policy";
import * as E from "../errors";

// Regression-only bindings let the TESTS patch run before the production rename.
// root-error-identities.test.ts separately requires the new names without fallback.
const errorExports = E as unknown as Record<string, typeof E.FutureAGIAPIError>;
export const CoreRateLimitError = (errorExports.CoreRateLimitError ?? errorExports.RateLimitError)!;
export const CoreServerError = (errorExports.CoreServerError ?? errorExports.ServerError)!;
export type CoreRateLimitError = InstanceType<typeof CoreRateLimitError>;
export type CoreServerError = InstanceType<typeof CoreServerError>;

const RUN_EVENTS = ["message_delta", "message_complete", "activity", "activity_output", "status", "error", "done"];

export const OPS: OperationTable = {
  "platform.capabilities.get": { name: "platform.capabilities.get", family: "platform", method: "GET", path: "/workspace/capabilities" },
  "runs.create": {
    name: "runs.create",
    family: "runs",
    method: "POST",
    path: "/workspace/conversations",
    body: "json",
    idempotent: true,
    durable: true,
  },
  "runs.get": { name: "runs.get", family: "runs", method: "GET", path: "/workspace/conversations/{id}", pathParams: ["id"] },
  "runs.list": {
    name: "runs.list",
    family: "runs",
    method: "GET",
    path: "/workspace/conversations",
    query: ["agentId", "cursor", "limit"],
    pagination: { style: "cursor", itemsField: "conversations", cursorParam: "cursor", limitParam: "limit", nextCursorField: "nextCursor" },
  },
  "runs.events": {
    name: "runs.events",
    family: "runs",
    method: "GET",
    path: "/workspace/conversations/{id}/events",
    pathParams: ["id"],
    query: ["transport", "wait"],
    stream: {
      kind: "sse-get",
      resume: "last-event-id",
      knownEvents: RUN_EVENTS,
      pollParam: "transport",
      pollValue: "poll",
      pollWaitParam: "wait",
      pollMaxWaitMs: 25_000,
    },
  },
  "environments.create": {
    name: "environments.create",
    family: "environments",
    method: "POST",
    path: "/workspace/environments",
    body: "json",
    idempotent: true,
    durable: false,
  },
  "sandboxes.create": { name: "sandboxes.create", family: "sandboxes", method: "POST", path: "/workspace/sandboxes", body: "json" },
  "sandboxes.kill": {
    name: "sandboxes.kill",
    family: "sandboxes",
    method: "DELETE",
    path: "/workspace/sandboxes/{id}",
    pathParams: ["id"],
    notFoundMeansApplied: true,
  },
  "sandboxes.list": {
    name: "sandboxes.list",
    family: "sandboxes",
    method: "GET",
    path: "/workspace/sandboxes",
    pagination: { style: "single-page", itemsField: "sandboxes" },
  },
  "files.write": {
    name: "files.write",
    family: "sandboxes",
    method: "PUT",
    path: "/workspace/sandboxes/{id}/files/{path}",
    pathParams: ["id", "path"],
    multiSegment: ["path"],
    body: "bundle",
    contentType: "application/octet-stream",
  },
  "approvals.decide": {
    name: "approvals.decide",
    family: "platform",
    method: "POST",
    path: "/workspace/approvals/{id}",
    pathParams: ["id"],
    body: "json",
    humanOnly: true,
  },
};

export const ORIGIN = "https://api.futureagi.com/omega/api";

export function keysOrigin(base = ORIGIN): PlatformOrigin {
  return {
    url: new URL(base),
    base,
    mode: "keys",
    source: "derived",
    custom: false,
    headers: { "X-Api-Key": "k-test-1234", "X-Secret-Key": "s-test-1234" },
    secrets: ["k-test-1234", "s-test-1234"],
  };
}

export type Answer = Response | Error | ((request: Request) => Response | Promise<Response>);

export const json = (status: number, body?: unknown, headers: Record<string, string> = {}): Response =>
  new Response(body === undefined ? null : JSON.stringify(body), { status, headers: { "content-type": "application/json", ...headers } });

export const netError = (code: string, message = code): Error =>
  Object.assign(new TypeError("fetch failed"), { cause: Object.assign(new Error(message), { code }) });

export const sse = (frames: [string | undefined, string, unknown][]): Response =>
  new Response(
    frames
      .map(([id, event, data]) => `${id !== undefined ? `id: ${id}\n` : ""}event: ${event}\ndata: ${JSON.stringify(data)}\n\n`)
      .join(""),
    {
      status: 200,
      headers: { "content-type": "text/event-stream" },
    },
  );

/** A body that sends `text`, then fails like a dropped connection (on the next read: erroring a stream
 * drops whatever is still queued). */
export const dropped = (text: string, error: Error = netError("ECONNRESET")): Response => {
  let sent = false;
  return new Response(
    new ReadableStream<Uint8Array>({
      pull(controller) {
        if (sent || text === "") return controller.error(error);
        sent = true;
        controller.enqueue(new TextEncoder().encode(text));
      },
    }),
    { status: 200, headers: { "content-type": "text/event-stream" } },
  );
};

/** Plays a script of answers (the last one repeats). A Response answer is buffered once and replayed as
 * a fresh Response each time (repeated `clone()` of one body deadlocks once a clone is cancelled);
 * streaming answers are functions that build a new Response per request. */
export class Script {
  readonly requests: Request[] = [];
  readonly sleeps: number[] = [];
  private readonly buffered = new Map<Response, Promise<ArrayBuffer>>();
  constructor(private readonly answers: Answer[]) {}

  readonly fetch = (async (input: RequestInfo | URL, init?: RequestInit): Promise<Response> => {
    const request = new Request(input as RequestInfo, init);
    this.requests.push(request);
    const answer = this.answers[Math.min(this.requests.length - 1, this.answers.length - 1)];
    if (answer instanceof Error) throw answer;
    if (typeof answer === "function") return answer(request);
    const response = answer as Response;
    if (!this.buffered.has(response)) this.buffered.set(response, response.clone().arrayBuffer());
    const bytes = await this.buffered.get(response)!;
    return new Response(bytes.byteLength === 0 ? null : bytes, { status: response.status, headers: response.headers });
  }) as typeof fetch;

  get keys(): (string | null)[] {
    return this.requests.map((r) => r.headers.get("Idempotency-Key"));
  }
}

export function makeCore(script: Script, extra: Partial<PlatformShared> = {}): PlatformCore {
  return new PlatformCore({
    resolveOrigin: () => keysOrigin(),
    table: OPS,
    fetch: script.fetch,
    retries: 3,
    sleep: async (ms: number) => {
      script.sleeps.push(ms);
    },
    ...extra,
  });
}

/** Every status and the class it maps to, on core and platform namespaces alike. */
export const STATUS_CLASSES: [number, new (...args: never[]) => E.FutureAGIAPIError][] = [
  [400, E.BadRequestError],
  [401, E.AuthenticationError],
  [403, E.PermissionDeniedError],
  [404, E.NotFoundError],
  [409, E.ConflictError],
  [413, E.PayloadTooLargeError],
  [418, E.FutureAGIAPIError],
  [422, E.UnprocessableEntityError],
  [429, CoreRateLimitError],
  [500, CoreServerError],
  [502, CoreServerError],
  [503, CoreServerError],
  [504, CoreServerError],
];
