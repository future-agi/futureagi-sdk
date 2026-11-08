// ---------------------------------------------------------------------------
// W3C Trace Context — traceparent generation, parsing, propagation
// ---------------------------------------------------------------------------

// ---------------------------------------------------------------------------
// ID generators
// ---------------------------------------------------------------------------

function randomHex(bytes: number): string {
  // Use crypto.randomUUID when available, fallback to Math.random
  if (typeof crypto !== "undefined" && crypto.randomUUID) {
    // Generate enough UUIDs to get the hex chars we need
    let hex = "";
    while (hex.length < bytes * 2) {
      hex += crypto.randomUUID().replace(/-/g, "");
    }
    return hex.slice(0, bytes * 2);
  }
  // Fallback
  let result = "";
  for (let i = 0; i < bytes * 2; i++) {
    result += Math.floor(Math.random() * 16).toString(16);
  }
  return result;
}

/** Generate a 32-char hex trace ID. */
export function generateTraceId(): string {
  return randomHex(16);
}

/** Generate a 16-char hex span ID. */
export function generateSpanId(): string {
  return randomHex(8);
}

// ---------------------------------------------------------------------------
// Traceparent parsing / formatting
// ---------------------------------------------------------------------------

export interface TraceContext {
  version: string; // "00"
  traceId: string; // 32 hex
  spanId: string; // 16 hex
  flags: string; // "01" = sampled
}

const TRACEPARENT_RE =
  /^([0-9a-f]{2})-([0-9a-f]{32})-([0-9a-f]{16})-([0-9a-f]{2})$/;

/**
 * Parse a W3C `traceparent` header.
 * Returns null if the format is invalid.
 */
export function parseTraceparent(header: string): TraceContext | null {
  const match = header.trim().match(TRACEPARENT_RE);
  if (!match) return null;
  return {
    version: match[1],
    traceId: match[2],
    spanId: match[3],
    flags: match[4],
  };
}

/**
 * Format a TraceContext into a W3C `traceparent` header string.
 */
export function formatTraceparent(ctx: TraceContext): string {
  return `${ctx.version}-${ctx.traceId}-${ctx.spanId}-${ctx.flags}`;
}

// ---------------------------------------------------------------------------
// TraceContextManager — manages trace context across requests
// ---------------------------------------------------------------------------

export interface TraceContextManagerOptions {
  /** Enable auto-generation of traceparent headers. */
  enabled?: boolean;
  /** Propagate from an upstream traceparent header. */
  traceparent?: string;
}

export class TraceContextManager {
  private _traceId: string;
  private _enabled: boolean;

  constructor(opts: TraceContextManagerOptions = {}) {
    this._enabled = opts.enabled ?? true;

    if (opts.traceparent) {
      const parsed = parseTraceparent(opts.traceparent);
      this._traceId = parsed ? parsed.traceId : generateTraceId();
    } else {
      this._traceId = generateTraceId();
    }
  }

  /** Whether trace context is active. */
  get enabled(): boolean {
    return this._enabled;
  }

  /** The trace ID (stable across the lifetime of this manager). */
  get traceId(): string {
    return this._traceId;
  }

  /** Generate a new span ID for each request. */
  nextSpanId(): string {
    return generateSpanId();
  }

  /** Get the current traceparent header value (with a fresh span ID). */
  getTraceparent(): string {
    if (!this._enabled) return "";
    return formatTraceparent({
      version: "00",
      traceId: this._traceId,
      spanId: this.nextSpanId(),
      flags: "01",
    });
  }

  /**
   * Get headers to inject into outgoing requests.
   * Returns `traceparent` and `x-agentcc-trace-id`.
   */
  getHeaders(): Record<string, string> {
    if (!this._enabled) return {};
    const traceparent = this.getTraceparent();
    return {
      traceparent,
      "x-agentcc-trace-id": this._traceId,
    };
  }
}
