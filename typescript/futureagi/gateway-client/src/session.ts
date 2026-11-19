/**
 * Session management — groups related requests for tracking.
 *
 * @module
 */

export interface SessionOptions {
  sessionId?: string;
  name?: string;
  metadata?: Record<string, unknown>;
}

export class Session {
  readonly sessionId: string;
  readonly name: string;
  readonly metadata: Record<string, unknown>;
  private _path = "/";
  private _totalCost = 0;
  private _requestCount = 0;
  private _totalTokens = 0;

  constructor(opts: SessionOptions = {}) {
    this.sessionId = opts.sessionId ?? generateId();
    this.name = opts.name ?? "";
    this.metadata = opts.metadata ?? {};
  }

  /** Append a step to the current path (e.g. "/" → "/research" → "/research/summarize"). */
  step(name: string): void {
    if (this._path === "/") {
      this._path = `/${name}`;
    } else {
      this._path = `${this._path}/${name}`;
    }
  }

  /** Reset path to root. */
  resetPath(): void {
    this._path = "/";
  }

  get path(): string {
    return this._path;
  }

  get totalCost(): number {
    return this._totalCost;
  }

  get requestCount(): number {
    return this._requestCount;
  }

  get totalTokens(): number {
    return this._totalTokens;
  }

  /** Record a completed request's metrics. */
  trackRequest(cost: number, tokens: number): void {
    this._totalCost += cost;
    this._totalTokens += tokens;
    this._requestCount++;
  }

  /** Convert to headers for HTTP requests. */
  toHeaders(): Record<string, string> {
    const h: Record<string, string> = {
      "x-agentcc-session-id": this.sessionId,
    };
    if (this.name) h["x-agentcc-session-name"] = this.name;
    if (this._path !== "/") h["x-agentcc-session-path"] = this._path;
    if (Object.keys(this.metadata).length > 0) {
      h["x-agentcc-metadata"] = JSON.stringify(this.metadata);
    }
    return h;
  }
}

// Simple ID generator — no external dependency needed
function generateId(): string {
  // Use crypto.randomUUID if available (Node 19+, all modern browsers)
  if (typeof globalThis.crypto?.randomUUID === "function") {
    return globalThis.crypto.randomUUID();
  }
  // Fallback: timestamp + random
  return `sess-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 10)}`;
}
