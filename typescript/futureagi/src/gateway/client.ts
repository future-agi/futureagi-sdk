import { BaseClient, type ClientOptions } from "./base-client";
import { Chat } from "./resources/chat/index";
import { Embeddings } from "./resources/embeddings";
import { Images } from "./resources/images";
import { Audio } from "./resources/audio";
import { Models } from "./resources/models";
import { Moderations } from "./resources/moderations";
import { Completions } from "./resources/completions";
import { Batches } from "./resources/batches";
import { Files } from "./resources/files";
import { Rerank } from "./resources/rerank";
import { Session, type SessionOptions } from "./session";
import { invokeCallbacks } from "./callbacks";
import type { ChatCompletion } from "./types/chat/chat-completion";

/**
 * AgentCC client — the main entry point for the SDK.
 *
 * @example
 * ```typescript
 * import { AgentCC } from "@future-agi/sdk/gateway";
 *
 * const client = new AgentCC({ apiKey: "sk-..." });
 *
 * const response = await client.chat.completions.create({
 *   model: "gpt-4o",
 *   messages: [{ role: "user", content: "Hello!" }],
 * });
 * ```
 */
export class AgentCC extends BaseClient {
  public readonly chat: Chat;
  public readonly completions: Completions;
  public readonly embeddings: Embeddings;
  public readonly images: Images;
  public readonly audio: Audio;
  public readonly models: Models;
  public readonly moderations: Moderations;
  public readonly batches: Batches;
  public readonly files: Files;
  public readonly rerank: Rerank;

  constructor(opts: ClientOptions = {}) {
    super(opts);
    this.chat = new Chat(this);
    this.completions = new Completions(this);
    this.embeddings = new Embeddings(this);
    this.images = new Images(this);
    this.audio = new Audio(this);
    this.models = new Models(this);
    this.moderations = new Moderations(this);
    this.batches = new Batches(this);
    this.files = new Files(this);
    this.rerank = new Rerank(this);
  }

  /**
   * Create a new client with the same config but overridden options.
   */
  withOptions(overrides: Partial<ClientOptions>): this {
    // The same class as this client (a `Gateway` stays a `Gateway`), with its middlewares and,
    // for a session-scoped client, its session.
    const Ctor = this.constructor as new (opts: ClientOptions) => AgentCC;
    const copy = new Ctor({
      apiKey: this._apiKey,
      baseUrl: this._baseUrl,
      timeout: this._timeout,
      maxRetries: this._maxRetries,
      defaultHeaders: { ...this._defaultHeaders },
      defaultQuery: { ...this._defaultQuery },
      sessionId: this._sessionId,
      metadata: this._metadata ? { ...this._metadata } : undefined,
      config: this._config,
      fetch: this._fetch,
      callbacks: this._callbacks.length > 0 ? [...this._callbacks] : undefined,
      retryPolicy: this._retryPolicy,
      dropParams: this._dropParams,
      modifyParams: this._modifyParams,
      redactMessages: this._redactMessages,
      traceContext: this._traceManager?.enabled,
      preCallRules: this._preCallRules.length > 0 ? [...this._preCallRules] : undefined,
      enableJsonSchemaValidation: this._enableJsonSchemaValidation || undefined,
      ...overrides,
    }) as this;
    copy._middlewares = [...this._middlewares];
    copy._session = this._session;
    return copy;
  }

  /**
   * Create a session-scoped client. All requests made through the returned
   * client include session headers and track session-level metrics.
   *
   * @example
   * ```typescript
   * const sess = client.session({ name: "research-agent" });
   * await sess.client.chat.completions.create({...});
   * sess.session.step("summarize");
   * await sess.client.chat.completions.create({...});
   * console.log(sess.session.totalCost, sess.session.requestCount);
   * await sess.end();   // fires onSessionEnd with the totals
   * ```
   */
  session(opts?: SessionOptions): { client: AgentCC; session: Session; end: () => Promise<void> } {
    const session = new Session(opts);

    // Create a tracking callback that records cost/tokens per request
    const trackingCallback = new SessionTrackingCallback(session);

    // A scoped client that reads the session's headers on every request, so the path set by
    // `session.step()` is the one sent.
    const scopedClient = this.withOptions({
      callbacks: [...this._callbacks, trackingCallback],
    });
    scopedClient._session = session;

    // Fire onSessionStart callbacks
    if (this._callbacks.length > 0) {
      invokeCallbacks(this._callbacks, "onSessionStart", session).catch(
        () => {},
      );
    }

    const callbacks = this._callbacks;
    const end = async (): Promise<void> => {
      await invokeCallbacks(callbacks, "onSessionEnd", session, {
        totalCost: session.totalCost,
        requestCount: session.requestCount,
        totalTokens: session.totalTokens,
      });
    };

    return { client: scopedClient, session, end };
  }

  /**
   * Quick health check against the gateway.
   * Returns `true` if the gateway is reachable and healthy.
   */
  async healthCheck(): Promise<boolean> {
    try {
      await this.request({ method: "GET", path: "/healthz" });
      return true;
    } catch {
      return false;
    }
  }
}

// ---------------------------------------------------------------------------
// Internal: session tracking callback
// ---------------------------------------------------------------------------

class SessionTrackingCallback {
  private _session: Session;

  constructor(session: Session) {
    this._session = session;
  }

  onRequestEnd(
    _request: unknown,
    response: { agentcc?: { cost?: number | null; latencyMs?: number }; body?: unknown },
  ): void {
    const cost = response?.agentcc?.cost ?? 0;
    this._session.trackRequest(cost, totalTokens(response?.body));
  }

  // A stream's usage arrives with its last chunk, after the request was counted.
  onStreamEnd(_request: unknown, _stream: unknown, completion: ChatCompletion): void {
    this._session.trackTokens(totalTokens(completion));
  }

  // Satisfy CallbackHandler shape — no-ops for all other hooks
  onRequestStart() {}
  onStreamStart() {}
  onStreamChunk() {}
  onError() {}
  onRetry() {}
  onGuardrailWarning() {}
  onGuardrailBlock() {}
  onCacheHit() {}
  onCostUpdate() {}
  onBudgetWarning() {}
  onFallback() {}
  onSessionStart() {}
  onSessionEnd() {}
}

function totalTokens(body: unknown): number {
  const usage = (body as { usage?: { total_tokens?: unknown } } | null | undefined)?.usage;
  return typeof usage?.total_tokens === "number" ? usage.total_tokens : 0;
}
