/**
 * The shape of one platform operation and the retry class it gets; the twin of
 * Python's `fi._core.policy`. The contract generator writes the table (`src/generated/platform/policy.gen.ts`)
 * from the pinned customer contract; namespaces call operations by SDK name only.
 *
 * | Class               | Which operations                                  | Retried on                 |
 * |---------------------|---------------------------------------------------|----------------------------|
 * | `keyed`             | `x-omega-idempotent`, `durable: true`             | 429, 502-504, network      |
 * | `keyed-not-durable` | `x-omega-idempotent`, `durable: false`            | 429, pre-send errors       |
 * | `http-idempotent`   | not keyed; GET, HEAD, OPTIONS, PUT, DELETE        | 429, 502-504, network      |
 * | `unsafe`            | not keyed; POST, PATCH                            | 429, pre-send errors       |
 */

import type { RetryClass } from "../transport";
import { PlatformNotConfiguredError } from "./errors";

export type HttpMethod = "GET" | "HEAD" | "OPTIONS" | "POST" | "PUT" | "PATCH" | "DELETE";
export type BodyClass = "none" | "json" | "bundle";

/** How a streaming operation streams (`x-omega-stream`). */
export interface StreamSpec {
  readonly kind: "sse-get" | "sse-post";
  readonly resume: "last-event-id" | "none";
  readonly events?: string;
  /** The event types this SDK knows; any other type is yielded as an unknown event. */
  readonly knownEvents: readonly string[];
  readonly keepaliveSeconds?: number;
  readonly cancelOnDisconnect?: boolean;
  readonly pollParam?: string;
  readonly pollValue?: string;
  readonly pollWaitParam?: string;
  readonly pollMaxWaitMs?: number;
}

/** How a list operation pages (`x-omega-pagination`). Cursors are opaque. */
export interface PaginationSpec {
  readonly style: "cursor" | "single-page" | "window";
  readonly itemsField: string;
  readonly cursorParam?: string;
  readonly limitParam?: string;
  readonly nextCursorField?: string;
  readonly hasMoreField?: string;
  readonly truncatedField?: string;
}

/** One in-scope operation of the pinned customer contract. */
export interface OperationSpec {
  /** `<family>.<method>` from `x-omega-sdk`. */
  readonly name: string;
  readonly family: string;
  readonly method: HttpMethod;
  /** The path template under the platform origin, with `{name}` placeholders. */
  readonly path: string;
  readonly pathParams?: readonly string[];
  /** The query keys the contract declares; no other key is ever sent. */
  readonly query?: readonly string[];
  readonly body?: BodyClass;
  readonly headers?: readonly string[];
  readonly contentType?: string;
  readonly idempotent?: boolean;
  /** Default true: a restarted server still remembers the key. */
  readonly durable?: boolean;
  readonly idempotencyKeyRequired?: boolean;
  readonly notFoundMeansApplied?: boolean;
  readonly humanOnly?: boolean;
  readonly multiSegment?: readonly string[];
  readonly stream?: StreamSpec;
  readonly pagination?: PaginationSpec;
  readonly secretFields?: readonly string[];
  readonly operationId?: string;
}

export type OperationTable = Readonly<Record<string, OperationSpec>>;

const HTTP_IDEMPOTENT = new Set(["GET", "HEAD", "OPTIONS", "PUT", "DELETE"]);

/** The operation's retry class (the table in this module's comment). */
export function retryClassOf(op: OperationSpec): RetryClass {
  if (op.idempotent === true) return op.durable === false ? "keyed-not-durable" : "keyed";
  return HTTP_IDEMPOTENT.has(op.method) ? "http-idempotent" : "unsafe";
}

/** The operation named `name`; a name the table lacks throws `PlatformNotConfiguredError`. */
export function lookup(table: OperationTable, name: string): OperationSpec {
  const op = table[name];
  if (op === undefined) {
    throw new PlatformNotConfiguredError(
      `no platform operation is named ${JSON.stringify(name)} in this SDK's contract`,
      "unknown_operation",
      name,
    );
  }
  return op;
}

/** Operations per retry class, plus streams and paginated lists. */
export function counts(table: OperationTable): Record<string, number> {
  const out: Record<string, number> = { keyed: 0, "keyed-not-durable": 0, "http-idempotent": 0, unsafe: 0, stream: 0, paginated: 0 };
  for (const op of Object.values(table)) {
    out[retryClassOf(op)] += 1;
    if (op.stream !== undefined) out.stream += 1;
    if (op.pagination !== undefined) out.paginated += 1;
  }
  return out;
}
